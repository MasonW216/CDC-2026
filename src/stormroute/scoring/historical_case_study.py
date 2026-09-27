"""Hurricane Helene, Sep 2024: a standalone historical case study, same rule as live.

Answers "what does Severe concern look like?" for a presentation, using the exact same
`prototype-score/1` formula (`concern.py`) and response shape (`trip.build_response`) as a
live trip -- not a second, different scoring system. The only thing that marks this response
as historical is `mode: "historical_case_study"`.

This module is the one place ERA5 reanalysis rainfall and archived NWS alerts are allowed to
reach the scoring rule. Per the MVP brief: "Historical reanalysis rainfall is not a live
forecast and must not be fed into the live trip flow." `stormroute.scoring.trip.score_trip`
never imports this module and never touches these files; the reverse dependency (this module
uses `trip.build_response`) is the only connection, and it flows one way.

Inputs, both retrieved 2026-09-26, cached in the repo (no network here):
  - `artifacts/demo/prototype_inputs_helene.json`: hourly rainfall per county (Open-Meteo
    `era5_seamless` archive) and archived county-coded NWS flood products (IEM VTEC archive),
    2024-09-23 through 2024-09-28.
  - `artifacts/demo/prototype_routes_provisional.json`: Asheville-to-Charlotte county stretches
    for two real OSRM routes, sampled 2026-09-26.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from stormroute.config import REPO_ROOT
from stormroute.scoring.live_forecast import ALERT_FLOORS, Alert, AlertData, ForecastData
from stormroute.scoring.trip import build_response, geometry_from_fixture, routes_from_fixture

INPUTS_FILE = REPO_ROOT / "artifacts" / "demo" / "prototype_inputs_helene.json"
ROUTES_FILE = REPO_ROOT / "artifacts" / "demo" / "prototype_routes_provisional.json"

# NWS CAP event name for each VTEC (phenomena, significance) pair, in the same vocabulary
# `live_forecast.ALERT_FLOORS` uses for the live feed. FA (areal flood) and FL (river flood)
# both surface publicly as "Flood ..."; only FF (flash flood) gets its own distinct name.
VTEC_EVENT_NAMES: dict[tuple[str, str], str] = {
    ("FF", "W"): "Flash Flood Warning",
    ("FF", "A"): "Flash Flood Watch",
    ("FF", "Y"): "Flash Flood Advisory",
    ("FL", "W"): "Flood Warning",
    ("FL", "A"): "Flood Watch",
    ("FL", "Y"): "Flood Advisory",
    ("FA", "W"): "Flood Warning",
    ("FA", "A"): "Flood Watch",
    ("FA", "Y"): "Flood Advisory",
}


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _parse_archive_stamp(text: str) -> datetime:
    """`"2024-09-25 00:50"` (IEM archive, space-separated, UTC) -> aware datetime."""
    return datetime.strptime(text, "%Y-%m-%d %H:%M").replace(tzinfo=UTC)


def _original_expiry(row: dict[str, str]) -> datetime:
    """`utc_init_expire` (`"YYYYMMDDHHMM"`), not the archive's revised final expiry.

    Using the value known at issuance, not a later extension or cancellation, keeps this
    case study honest about what would have been knowable at the time -- the same reasoning
    `live_forecast`'s freshness policy applies to a live fallback, applied here to history.
    """
    text = row.get("utc_init_expire") or ""
    if len(text) == 12 and text.isdigit():
        return datetime.strptime(text, "%Y%m%d%H%M").replace(tzinfo=UTC)
    return _parse_archive_stamp(row["utc_expire"])


def historical_forecast() -> ForecastData:
    """ERA5 reanalysis rainfall for all NC counties, Helene period, from the cached archive."""
    data = _load(INPUTS_FILE)
    precip = data["precipitation"]
    times: list[str] = precip["times_utc"]
    hourly = {fips: dict(zip(times, values, strict=True)) for fips, values in precip["mm"].items()}
    return ForecastData(
        hourly=hourly,
        retrieved_utc=datetime.fromisoformat(data["retrieved_utc"].replace("Z", "+00:00")),
        from_cache=True,
        source=(
            "Open-Meteo archive API, era5_seamless reanalysis (Hurricane Helene case study; "
            "historical, not a live forecast)"
        ),
    )


def historical_alerts() -> AlertData:
    """Archived county-coded NWS flood products for the Helene period."""
    data = _load(INPUTS_FILE)
    rows = data["alerts"]["rows"]
    alerts = []
    for row in rows:
        name = VTEC_EVENT_NAMES.get((row["phenomena"], row["significance"]))
        if name is None:
            continue

        alerts.append(
            Alert(
                id=f"{row['wfo']}-{row['eventid']}-{row['ugc']}",
                event=name,
                floor=ALERT_FLOORS[name],
                headline=None,
                effective_utc=_parse_archive_stamp(row["utc_issue"]),
                expires_utc=_original_expiry(row),
                county_fips=("37" + row["ugc"][3:],),
            )
        )
    return AlertData(
        alerts=tuple(alerts),
        retrieved_utc=datetime.fromisoformat(data["retrieved_utc"].replace("Z", "+00:00")),
        ok=True,
        from_cache=True,
        unmapped=data["alerts"]["zone_coded_rows_excluded"],
        source="NWS VTEC archive (Iowa Environmental Mesonet), Hurricane Helene case study",
        raw_count=len(rows),
    )


def helene_case_study() -> dict[str, Any]:
    """The full `prototype-score/1` response for the Helene Asheville-Charlotte replay.

    Deterministic: every call with the same files on disk returns byte-identical output,
    the same guarantee the live tests hold `score_route`/`compare` to.
    """
    fixture = _load(ROUTES_FILE)
    routes = routes_from_fixture(fixture)
    departure = datetime.fromisoformat(fixture["departure_utc"])
    forecast = historical_forecast()
    alerts = historical_alerts()
    response = build_response(
        routes,
        departure,
        forecast,
        alerts,
        requested=departure,  # scored as of the decision time, not today
        mode="historical_case_study",
        geometry=geometry_from_fixture(fixture),
    )
    response["case_study"] = {
        "name": "Hurricane Helene",
        "period": "23-28 September 2024",
        "note": (
            "A standalone historical replay, not part of the live trip flow. Rainfall is "
            "ERA5 reanalysis retrieved after the fact; a traveler would not have had it at "
            "departure. Uses the same scoring rule as a live trip."
        ),
        "origin": fixture["origin"],
        "destination": fixture["destination"],
    }
    return response
