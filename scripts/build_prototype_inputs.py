"""Freeze the inputs for the MVP prototype hazard indicator.

Makefile target : none (run by hand; needs the network once)
Milestone       : MVP (prototype, not the Milestone 3 pipeline)
Reads           : Open-Meteo archive API (ERA5 reanalysis), IEM NWS VTEC archive,
                  data/sample/nc_counties_sample.geojson
Writes          : artifacts/demo/prototype_inputs_helene.json

Caches what the indicator needs for a replay of the Hurricane Helene period, for
all 100 counties, so any candidate route can be scored offline:

  * hourly precipitation (mm) at one point per county, 2024-09-23 to 2024-09-28 UTC.
    ERA5 reanalysis is published days after the fact, so this is a replay input, not
    something a traveler would have had at departure time.
  * county-coded NWS flood products (FA, FF, FL) from the IEM archive. Zone-coded
    products are counted but not mapped to counties (no crosswalk yet).

This is not the production weather retrieval (ADR 0005 / Milestone 3).
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
from datetime import UTC, datetime
from typing import Any

import geopandas as gpd
import httpx

from stormroute.config import REPO_ROOT

OUT = REPO_ROOT / "artifacts" / "demo" / "prototype_inputs_helene.json"
WEATHER_START, WEATHER_END = "2024-09-23", "2024-09-28"
ALERT_START, ALERT_END = "2024-09-25T00:00Z", "2024-09-29T00:00Z"
OPEN_METEO = "https://archive-api.open-meteo.com/v1/archive"
IEM = "https://mesonet.agron.iastate.edu/cgi-bin/request/gis/watchwarn.py"
BATCH = 20


def county_points() -> list[tuple[str, str, float, float]]:
    """Return (fips, name, lat, lon) using one interior point per county."""
    counties = gpd.read_file(REPO_ROOT / "data" / "sample" / "nc_counties_sample.geojson")
    points = counties.geometry.representative_point()
    return [
        (str(row.county_fips), str(row["name"]), round(pt.y, 4), round(pt.x, 4))
        for (_, row), pt in zip(counties.iterrows(), points, strict=True)
    ]


def fetch_precip(points: list[tuple[str, str, float, float]]) -> dict[str, list[float | None]]:
    """Hourly precipitation per county, one request per batch of counties."""
    result: dict[str, list[float | None]] = {}
    for i in range(0, len(points), BATCH):
        batch = points[i : i + BATCH]
        params = {
            "latitude": ",".join(str(p[2]) for p in batch),
            "longitude": ",".join(str(p[3]) for p in batch),
            "start_date": WEATHER_START,
            "end_date": WEATHER_END,
            "hourly": "precipitation",
            "models": "era5_seamless",
            "timezone": "UTC",
        }
        reply = httpx.get(OPEN_METEO, params=params, timeout=120)
        reply.raise_for_status()
        body: Any = reply.json()
        for point, series in zip(batch, body if isinstance(body, list) else [body], strict=True):
            result[point[0]] = series["hourly"]["precipitation"]
            times = series["hourly"]["time"]
    result["_times"] = times
    return result


def fetch_alerts() -> tuple[list[dict[str, str]], int]:
    """County-coded flood products, plus the count of zone-coded ones left out."""
    params = {
        "sts": ALERT_START,
        "ets": ALERT_END,
        "location_group": "states",
        "states": "NC",
        "accept": "csv",
    }
    reply = httpx.get(IEM, params=params, timeout=180)
    reply.raise_for_status()
    rows = list(csv.DictReader(io.StringIO(reply.text)))
    flood = [r for r in rows if r["phenomena"] in {"FA", "FF", "FL"} and r["gtype"] == "C"]
    county = [r for r in flood if r["ugc"].startswith("NCC")]
    keep = ["wfo", "phenomena", "significance", "eventid", "status", "ugc"]
    keep += ["utc_issue", "utc_expire", "utc_prodissue", "utc_init_expire"]
    return [{k: r[k] for k in keep} for r in county], len(flood) - len(county)


def main() -> None:
    """Fetch, assemble, and write the cache with provenance."""
    points = county_points()
    precip = fetch_precip(points)
    times = precip.pop("_times")
    alerts, zone_coded = fetch_alerts()
    payload = {
        "purpose": "Inputs for the prototype hazard indicator replay. Not a forecast.",
        "retrieved_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%MZ"),
        "sources": {
            "precipitation": f"Open-Meteo archive API, model era5_seamless, {OPEN_METEO}",
            "alerts": f"IEM VTEC archive, {IEM}, states=NC, {ALERT_START} to {ALERT_END}",
        },
        "precipitation": {
            "units": "mm per hour, ending at the stated UTC hour",
            "times_utc": times,
            "county_point": {p[0]: {"name": p[1], "lat": p[2], "lon": p[3]} for p in points},
            "mm": precip,
        },
        "alerts": {
            "note": (
                "County-coded FA/FF/FL rows only, one row per event and county with the "
                "final archived status and expiry. Zone-coded rows are not mapped."
            ),
            "zone_coded_rows_excluded": zone_coded,
            "rows": alerts,
        },
    }
    text = json.dumps(payload, separators=(",", ":"))
    payload["sha256_of_compact_json_without_this_field"] = hashlib.sha256(text.encode()).hexdigest()
    OUT.write_text(json.dumps(payload, separators=(",", ":")) + "\n", encoding="utf-8")
    print(
        f"wrote {OUT} ({OUT.stat().st_size / 1024:.0f} KB): {len(points)} counties, "
        f"{len(alerts)} alert rows, {zone_coded} zone-coded rows excluded"
    )


if __name__ == "__main__":
    main()
