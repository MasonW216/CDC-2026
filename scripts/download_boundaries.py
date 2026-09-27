"""Download Census TIGER/Line county boundaries.

Makefile target : make download
Milestone       : 1
Reads           : data/data_manifest.yaml
Writes          : data/raw/census_tiger/

Restricting to STATEFP 37 happens downstream in stormroute.data.geography.
Exactly 100 North Carolina counties are expected; any other count is an error.

Behavior mirrors scripts/download_noaa.py: the checksum and access time are
recorded, a file that differs from its record is never overwritten, and
--sample validates the tracked fixture with no network access.

Exit codes: 0 success, 1 conflict or failure, 2 bad arguments.
"""

from __future__ import annotations

import argparse
import json
import sys

import httpx

from stormroute.config import REPO_ROOT, data_path
from stormroute.data.geography import (
    RECORD_FILENAME,
    SAMPLE_FILENAME,
    TIGER_COUNTY_FILENAME,
    TIGER_COUNTY_URL,
    load_nc_counties,
    load_sample_counties,
    plan_boundary_download,
    record_boundary_download,
)
from stormroute.data.noaa import download_file, sha256_of
from stormroute.data.validation import DataContractError

TIMEOUT = httpx.Timeout(30.0, read=300.0)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument(
        "--sample", action="store_true", help="validate the tracked fixture; no network access"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="show what would happen without downloading"
    )
    parser.add_argument(
        "--adopt-existing",
        action="store_true",
        help="record an unrecorded file already on disk instead of refusing",
    )
    parser.add_argument(
        "--write-sample", action="store_true", help="Rebuild Cameron's EDA display fixture"
    )
    return parser.parse_args(argv)


def run_sample() -> int:
    fixture = data_path("sample") / SAMPLE_FILENAME
    try:
        counties = load_sample_counties()
    except (OSError, DataContractError) as error:
        print(error, file=sys.stderr)
        return 1
    print(f"Sample mode: {len(counties)} counties from {fixture.relative_to(REPO_ROOT)}")
    print("No network access. Set STORMROUTE_DATA_MODE=sample for notebooks and tests.")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.sample:
        return run_sample()

    raw_dir = data_path("boundaries_raw")
    raw_dir.mkdir(parents=True, exist_ok=True)
    destination = raw_dir / TIGER_COUNTY_FILENAME

    action = plan_boundary_download(raw_dir, adopt_existing=args.adopt_existing)
    print(f"  {action.kind:<8}  {TIGER_COUNTY_FILENAME}  ({action.reason})")
    if action.kind == "conflict":
        print("\nConflict; nothing was downloaded.", file=sys.stderr)
        return 1
    if args.dry_run:
        print("\nDry run: nothing was downloaded.")
        return 0

    if action.kind == "download":
        print(f"Downloading {TIGER_COUNTY_URL} ...", flush=True)
        with httpx.Client(timeout=TIMEOUT, follow_redirects=True) as client:
            download_file(client, TIGER_COUNTY_URL, destination)

    # Validate before recording: a bad file must never become the checksum that
    # later runs trust and skip.
    try:
        counties = load_nc_counties(destination)
    except Exception as error:  # pyogrio raises its own types for unreadable files
        print(f"{destination.name} failed validation:\n{error}", file=sys.stderr)
        if action.kind == "download":
            destination.unlink(missing_ok=True)
            print("The downloaded file was deleted and not recorded.", file=sys.stderr)
        return 1

    if action.kind in ("download", "adopt"):
        note = "downloaded" if action.kind == "download" else "adopted from disk"
        record_boundary_download(
            raw_dir, sha256_of(destination), destination.stat().st_size, note=note
        )
    print(f"Validated {len(counties)} North Carolina counties.")
    record_path = raw_dir / RECORD_FILENAME
    shown = (
        record_path.relative_to(REPO_ROOT) if record_path.is_relative_to(REPO_ROOT) else record_path
    )
    print(f"Download record: {shown}")
    if args.write_sample:
        payload = json.loads(record_path.read_text(encoding="utf-8"))
        entry = payload.get("files", {}).get(TIGER_COUNTY_FILENAME, payload)
        write_sample(
            {
                "source_url": entry.get("url", entry.get("source_url", TIGER_COUNTY_URL)),
                "sha256": entry["sha256"],
                "retrieved_at_utc": entry.get(
                    "recorded_at_utc", entry.get("retrieved_at_utc", "unknown")
                ),
            }
        )
    return 0


def write_sample(source: dict[str, str]) -> None:
    from stormroute.data.geography import load_counties

    counties = load_counties("full")[["STATEFP", "GEOID", "NAME", "ALAND", "geometry"]]
    counties = counties.to_crs("EPSG:5070")
    counties.geometry = counties.geometry.simplify(1000, preserve_topology=True)
    target = data_path("sample") / "nc_counties_2024.geojson"
    counties.to_crs("EPSG:4326").to_file(target, driver="GeoJSON")
    target.with_suffix(".json").write_text(
        json.dumps(
            {
                "sha256": sha256_of(target),
                "source_url": source["source_url"],
                "source_sha256": source["sha256"],
                "retrieved_at_utc": source["retrieved_at_utc"],
                "derivation": "NC filter; EPSG:5070 simplification at 1000 m; EPSG:4326 output",
                "use": "EDA display only; not spatial joins, routing, or area measurement",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    sys.exit(main())
