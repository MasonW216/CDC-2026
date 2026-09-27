"""Save one live trip so the demo can replay it offline, through the same score path.

Makefile target : none (MVP)
Needs           : the network once (OSRM routing, Open-Meteo forecast, NWS alerts)
Reads           : none
Writes          : artifacts/demo/saved_trip_request.json   routes + departure + as_of time
                  artifacts/demo/saved_trip_response.json  the live `prototype-score/1` result
                  artifacts/demo/live_cache/*              raw upstream responses, timestamped

Replay with `stormroute.scoring.trip.replay_saved_trip`: no network, same response shape,
`mode: "cached"`, and the original retrieval times.
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pandas as pd

from stormroute.config import REPO_ROOT
from stormroute.data.geography import load_sample_counties
from stormroute.routing.client import LatLon, fetch_routes
from stormroute.routing.sampling import sample_route
from stormroute.routing.spatial_join import collapse_intervals
from stormroute.scoring.trip import DEFAULT_CACHE, routes_from_intervals, score_trip

DEMO = REPO_ROOT / "artifacts" / "demo"
OSRM = "https://router.project-osrm.org"


def main() -> None:
    """Fetch routes, score them live, and save request and response."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--origin", nargs=3, default=["Asheville, NC", "35.5951", "-82.5515"])
    parser.add_argument("--destination", nargs=3, default=["Charlotte, NC", "35.2271", "-80.8431"])
    parser.add_argument("--hours-ahead", type=float, default=3.0)
    args = parser.parse_args()

    as_of = datetime.now(UTC).replace(microsecond=0)
    departure = (as_of + timedelta(hours=args.hours_ahead)).replace(minute=0, second=0)
    origin = LatLon(float(args.origin[1]), float(args.origin[2]))
    destination = LatLon(float(args.destination[1]), float(args.destination[2]))
    counties = load_sample_counties()
    names = dict(zip(counties["county_fips"], counties["name"], strict=True))
    candidates = fetch_routes(
        origin, destination, base_url=OSRM, cache_dir=DEFAULT_CACHE / "routes"
    )
    frames = [
        collapse_intervals(sample_route(c, pd.Timestamp(departure), counties)) for c in candidates
    ]
    intervals = pd.concat(frames, ignore_index=True)
    durations = {c.route_id: c.duration_s / 60 for c in candidates}
    routes = routes_from_intervals(intervals, durations, names)

    geometry = {c.route_id: list(c.coordinates) for c in candidates}
    response = score_trip(routes, departure, now=as_of, cache_dir=DEFAULT_CACHE, geometry=geometry)
    request = {
        "purpose": "Saved contemporary trip for the offline demo fallback.",
        "origin": {"label": args.origin[0], "lat": origin.lat, "lon": origin.lon},
        "destination": {
            "label": args.destination[0],
            "lat": destination.lat,
            "lon": destination.lon,
        },
        "departure_utc": departure.isoformat(),
        "as_of_utc": as_of.isoformat(),
        "routes": {
            r.route_id: {
                "duration_minutes": r.duration_minutes,
                "distance_km": r.distance_km,
                # Real OSRM road geometry, [lon, lat] pairs, so the offline replay can draw
                # the actual road path, not a schematic line -- see geometry_from_fixture().
                "geometry": [list(point) for point in geometry.get(r.route_id, [])],
                "stretches": [
                    {
                        "county_fips": s.county_fips,
                        "county_name": s.county_name,
                        "arrival_utc": s.arrival_utc.isoformat(),
                        "minutes": s.minutes,
                        "km": s.km,
                    }
                    for s in r.stretches
                ],
            }
            for r in routes
        },
    }
    Path(DEMO / "saved_trip_request.json").write_text(json.dumps(request, indent=1) + "\n")
    Path(DEMO / "saved_trip_response.json").write_text(json.dumps(response, indent=1) + "\n")
    print("saved", departure.isoformat(), "as of", as_of.isoformat())
    for route in response["routes"]:
        print(route["route_id"], route["status"], route["index"], route["band"])
    print(response["comparison"]["message"])


if __name__ == "__main__":
    main()
