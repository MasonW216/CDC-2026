"""Score the cached routes with the prototype hazard indicator, offline.

Makefile target : none (MVP prototype)
Reads           : artifacts/demo/prototype_routes_provisional.json (or --routes),
                  artifacts/demo/prototype_inputs_helene.json
Writes          : artifacts/demo/prototype_result.json

No network. The same inputs always produce byte-identical output. The trip level is
the highest segment level. A route is offered as a lower-concern alternative only
when its trip level is lower; a shorter route with the same level is not a hazard
improvement.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from stormroute.config import REPO_ROOT
from stormroute.scoring.prototype import assess_trip
from stormroute.scoring.prototype_inputs import build_segments, load_inputs

DEMO = REPO_ROOT / "artifacts" / "demo"


def run(routes_path: Path, inputs_path: Path) -> dict[str, Any]:
    """Assess every route in the fixture and compare them."""
    fixture = json.loads(routes_path.read_text(encoding="utf-8"))
    inputs = load_inputs(inputs_path)
    decision = datetime.fromisoformat(fixture["departure_utc"])
    results: dict[str, Any] = {}
    for route_id, route in fixture["routes"].items():
        trip = assess_trip(build_segments(route["stretches"], inputs), decision)
        names = {s["county_fips"]: s["county_name"] for s in route["stretches"]}
        for seg in trip["segments"]:
            seg["county_name"] = names[seg["county_fips"]]
        if trip["highest_concern_segment"]:
            trip["highest_concern_segment"]["county_name"] = names[
                trip["highest_concern_segment"]["county_fips"]
            ]
        trip["duration_minutes"] = route["duration_minutes"]
        trip["distance_km"] = route["distance_km"]
        results[route_id] = trip

    ranked = sorted(
        results,
        key=lambda r: (
            results[r]["trip_level"] if results[r]["trip_level"] is not None else 99,
            results[r]["duration_minutes"],
        ),
    )
    best, other = ranked[0], ranked[-1]
    comparison = None
    if len(ranked) > 1 and results[best]["trip_level"] is not None:
        same_level = results[best]["trip_level"] == results[other]["trip_level"]
        comparison = {
            "lower_indicated_concern_route": None if same_level else best,
            "other_route": None if same_level else other,
            "levels": {best: results[best]["trip_level"], other: results[other]["trip_level"]},
            "extra_minutes": None
            if same_level
            else round(results[best]["duration_minutes"] - results[other]["duration_minutes"], 1),
            "note": (
                "Both routes have the same indicator level; no lower-concern alternative "
                "was found. This indicator does not establish that either route is safe."
                if same_level
                else "Both routes were scored by the same rule on the same cached inputs. "
                "This compares indicator levels; it does not say either route is safe."
            ),
        }
    return {
        "scenario": fixture["scenario"],
        "origin": fixture["origin"],
        "destination": fixture["destination"],
        "departure_time": fixture["departure_time"],
        "inputs_provenance": {
            "retrieved_utc": inputs["retrieved_utc"],
            "sources": inputs["sources"],
            "zone_coded_alert_rows_excluded": inputs["alerts"]["zone_coded_rows_excluded"],
        },
        "route_fixture_provenance": fixture["provenance"],
        "routes": results,
        "comparison": comparison,
    }


def main() -> None:
    """Command-line entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--routes", type=Path, default=DEMO / "prototype_routes_provisional.json")
    parser.add_argument("--inputs", type=Path, default=DEMO / "prototype_inputs_helene.json")
    parser.add_argument("--out", type=Path, default=DEMO / "prototype_result.json")
    args = parser.parse_args()
    result = run(args.routes, args.inputs)
    args.out.write_text(json.dumps(result, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    for route_id, trip in result["routes"].items():
        worst = trip["highest_concern_segment"]
        print(
            route_id,
            trip["trip_label"],
            "| worst:",
            worst and worst["county_name"],
            "|",
            trip["duration_minutes"],
            "min",
        )
    print("wrote", args.out)


if __name__ == "__main__":
    main()
