"""Score a trip end to end: routes in, `prototype-score/1` response out.

This is what the API calls. It gathers the forecast for the counties the routes cross and
the active flood alerts, then applies `concern.py`. Nothing here decides the score; it only
fetches inputs and reports coverage honestly.

  * Past departures are refused (`TripNotSupportedError`): historical replay is a separate mode.
  * If the forecast or the alert feed fails, the response says so and declines a confident
    ranking instead of treating missing data as low concern.
  * With `offline=True`, or on a network failure, the newest cached upstream response is
    used and flagged `from_cache`, with its retrieval time.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import httpx

from stormroute.config import REPO_ROOT
from stormroute.scoring.concern import (
    HORIZON_HOURS,
    LIMITATIONS,
    SCHEMA_VERSION,
    SCORE_NAME,
    RouteInput,
    Stretch,
    compare,
    score_route,
)
from stormroute.scoring.live_forecast import (
    AlertData,
    ForecastData,
    ForecastError,
    fetch_alerts,
    fetch_forecast,
)

DEFAULT_CACHE = REPO_ROOT / "artifacts" / "demo" / "live_cache"
PAST_TOLERANCE = timedelta(minutes=15)


class TripNotSupportedError(ValueError):
    """The request is outside what this prototype supports. The message says why."""


def _utc(value: datetime | str) -> datetime:
    stamp = value if isinstance(value, datetime) else datetime.fromisoformat(str(value))
    if stamp.tzinfo is None:
        raise TripNotSupportedError("timestamps must include a timezone")
    return stamp.astimezone(UTC)


def county_points() -> dict[str, tuple[float, float]]:
    """One representative (lat, lon) per NC county, from the tracked county fixture."""
    from stormroute.data.geography import load_sample_counties

    counties = load_sample_counties()
    points = counties.geometry.representative_point()
    return {
        str(fips): (round(float(pt.y), 4), round(float(pt.x), 4))
        for fips, pt in zip(counties["county_fips"], points, strict=True)
    }


def routes_from_fixture(fixture: Mapping[str, Any]) -> list[RouteInput]:
    """Build routes from `artifacts/demo/prototype_routes_provisional.json`-style data."""
    routes = []
    for route_id, route in fixture["routes"].items():
        stretches = [
            Stretch(
                county_fips=s["county_fips"],
                county_name=s.get("county_name") or str(s["county_fips"]),
                arrival_utc=_utc(s["arrival_utc"]),
                minutes=float(s["minutes"]),
                km=float(s["km"]),
            )
            for s in route["stretches"]
        ]
        routes.append(
            RouteInput(
                route_id, float(route["duration_minutes"]), float(route["distance_km"]), stretches
            )
        )
    return routes


def routes_from_intervals(
    intervals: Any, durations: Mapping[str, float], names: Mapping[str, str]
) -> list[RouteInput]:
    """Build routes from `routing.spatial_join.collapse_intervals` output.

    `durations` maps route_id to total minutes (`CandidateRoute.duration_s / 60`); `names`
    maps county FIPS to its name. A row whose `county_fips` is None becomes a stretch
    outside coverage, so the route is reported as partial.
    """
    routes = []
    for route_id, group in intervals.groupby("route_id", sort=False):
        stretches = [
            Stretch(
                county_fips=row.county_fips if row.in_modeled_geography else None,
                county_name=names.get(row.county_fips, "Outside North Carolina")
                if row.in_modeled_geography
                else "Outside North Carolina",
                arrival_utc=_utc(row.entry_utc.floor("us").to_pydatetime()),
                minutes=float(row.exposure_minutes),
                km=float(row.distance_km),
            )
            for row in group.sort_values("interval_order").itertuples()
        ]
        routes.append(
            RouteInput(
                str(route_id),
                float(durations[str(route_id)]),
                float(group["distance_km"].sum()),
                stretches,
            )
        )
    return routes


def score_trip(
    routes: Sequence[RouteInput],
    departure_utc: datetime | str,
    *,
    now: datetime | None = None,
    offline: bool = False,
    cache_dir: Path | None = None,
    client: httpx.Client | None = None,
    points: Mapping[str, tuple[float, float]] | None = None,
) -> dict[str, Any]:
    """Score all routes for a departure and return the `prototype-score/1` response.

    Raises:
        TripNotSupportedError: departure in the past, or a naive timestamp.
    """
    requested = _utc(now) if now else datetime.now(UTC)
    departure = _utc(departure_utc)
    if departure < requested - PAST_TOLERANCE:
        raise TripNotSupportedError(
            "Departure is in the past. Live scoring needs a future departure; use the "
            "separately labelled replay mode for past dates."
        )
    cache = cache_dir or DEFAULT_CACHE
    all_points = dict(points) if points is not None else county_points()
    needed = sorted({s.county_fips for r in routes for s in r.stretches if s.county_fips})
    forecast: ForecastData | None
    forecast_error: str | None = None
    try:
        forecast = (
            fetch_forecast(
                {f: all_points[f] for f in needed}, cache_dir=cache, offline=offline, client=client
            )
            if needed
            else None
        )
    except ForecastError as error:
        forecast, forecast_error = None, str(error)
    alerts = fetch_alerts(cache_dir=cache, offline=offline, client=client)

    scored = [score_route(r, forecast, alerts, requested) for r in routes]
    outside = sorted({s.county_name for r in routes for s in r.stretches if s.county_fips is None})
    missing = sorted(
        {
            s["county_fips"]
            for r in scored
            for s in r["segments"]
            if s["status"] == "unassessed" and s["county_fips"]
        }
    )
    every_alert: dict[str, dict[str, Any]] = {}
    for route in scored:
        for alert in route["alerts"]:
            every_alert.setdefault(alert["id"], alert)
    retrieved = forecast.retrieved_utc if forecast else requested
    return {
        "schema_version": SCHEMA_VERSION,
        "score_name": SCORE_NAME,
        "mode": "cached" if (forecast and forecast.from_cache) or alerts.from_cache else "live",
        "requested_at_utc": requested.isoformat(),
        "departure_utc": departure.isoformat(),
        "routes": scored,
        "comparison": compare(scored),
        "coverage": {
            "forecast": {
                "source": forecast.source if forecast else "Open-Meteo forecast API",
                "retrieved_utc": retrieved.isoformat(),
                "horizon_hours": HORIZON_HOURS,
                "missing_counties": missing,
                "from_cache": bool(forecast and forecast.from_cache),
                "error": forecast_error,
            },
            "alerts": _alerts_block(alerts),
            "geography": {
                "supported": not outside,
                "message": (
                    "Part of this route is outside North Carolina, where this prototype has "
                    "no coverage. Those stretches are not assessed."
                    if outside
                    else None
                ),
            },
        },
        "alerts": sorted(every_alert.values(), key=lambda a: (-a["floor"], a["id"])),
        "limitations": list(LIMITATIONS),
    }


def replay_saved_trip(saved: Mapping[str, Any], *, cache_dir: Path | None = None) -> dict[str, Any]:
    """Re-score a saved trip from cached upstream responses only, with no network.

    `saved` holds `routes` (as in `routes_from_fixture`), `departure_utc`, and `as_of_utc`,
    the moment the trip was originally requested. The result carries `mode: "cached"` and
    the original retrieval times, so the screen can show how old the data is.
    """
    return score_trip(
        routes_from_fixture(saved),
        saved["departure_utc"],
        now=_utc(saved["as_of_utc"]),
        offline=True,
        cache_dir=cache_dir,
    )


def _alerts_block(alerts: AlertData) -> dict[str, Any]:
    return {
        "source": alerts.source,
        "retrieved_utc": alerts.retrieved_utc.isoformat(),
        "ok": alerts.ok,
        "error": alerts.error,
        "from_cache": alerts.from_cache,
        "unmapped_alerts": alerts.unmapped,
        "flood_alerts_in_effect_statewide": len(alerts.alerts),
    }
