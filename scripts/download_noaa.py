"""Download NOAA Storm Events detail files for 2015-2024.

Makefile target : make download
Milestone       : 1
Reads           : configs/data.yaml, the NCEI directory listing
Writes          : data/raw/noaa_storm_events/*.csv.gz,
                  data/raw/noaa_storm_events/download_record.json

Behavior required by the build guide:
  * identify the annual detail file for each year 2015-2024;
  * record the resolved filename (the c-date suffix changes on republication),
    checksum, and access time, so a run is reproducible;
  * never silently overwrite a file whose content differs; stop and report;
  * support --sample for CI and notebook smoke tests (no network);
  * do NOT filter here. The raw layer stays a faithful copy of the source;
    North Carolina and hazard filtering happen in stormroute.data.noaa.

Exit codes: 0 success, 1 conflict or failure, 2 bad arguments.
"""

from __future__ import annotations

import argparse
import sys

import httpx

from stormroute.config import REPO_ROOT, data_path, load_config
from stormroute.data.noaa import (
    NCEI_DETAILS_URL,
    DownloadRecord,
    download_file,
    parse_listing,
    plan_downloads,
    sha256_of,
)

TIMEOUT = httpx.Timeout(30.0, read=300.0)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    period = load_config("data")["period"]
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument(
        "--years",
        type=int,
        nargs="+",
        default=list(range(period["start_year"], period["end_year"] + 1)),
        help="years to fetch (default: the locked period in configs/data.yaml)",
    )
    parser.add_argument(
        "--sample", action="store_true", help="use the tracked fixture; no network access"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="show what would happen without downloading"
    )
    parser.add_argument(
        "--accept-republished",
        action="store_true",
        help="switch to NCEI's newer file for years it has re-published",
    )
    parser.add_argument(
        "--adopt-existing",
        action="store_true",
        help="record unrecorded files already on disk instead of refusing",
    )
    return parser.parse_args(argv)


def run_sample() -> int:
    fixture = data_path("sample") / "storm_events_sample.csv"
    if not fixture.exists():
        print(f"Sample fixture missing: {fixture}", file=sys.stderr)
        return 1
    print(f"Sample mode: using tracked fixture {fixture.relative_to(REPO_ROOT)}")
    print("No network access. Set STORMROUTE_DATA_MODE=sample for notebooks and tests.")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.sample:
        return run_sample()

    raw_dir = data_path("noaa_raw")
    raw_dir.mkdir(parents=True, exist_ok=True)
    record = DownloadRecord.load(raw_dir)

    with httpx.Client(timeout=TIMEOUT, follow_redirects=True) as client:
        listing = client.get(NCEI_DETAILS_URL)
        listing.raise_for_status()
        sources = parse_listing(listing.text, args.years)
        actions = plan_downloads(
            sources,
            record,
            raw_dir,
            accept_republished=args.accept_republished,
            adopt_existing=args.adopt_existing,
        )

        conflicts = [action for action in actions if action.kind == "conflict"]
        for action in actions:
            source = action.source
            print(f"  {source.year}  {action.kind:<8}  {source.filename}  ({action.reason})")
        if conflicts:
            print(f"\n{len(conflicts)} conflict(s); nothing was downloaded.", file=sys.stderr)
            return 1
        if args.dry_run:
            print("\nDry run: nothing was downloaded.")
            return 0

        for action in actions:
            destination = raw_dir / action.source.filename
            if action.kind == "download":
                print(f"Downloading {action.source.filename} ...", flush=True)
                sha256, size = download_file(client, action.source.url, destination)
                record.add(action.source, sha256, size)
                record.save(raw_dir)  # after every file, so an interruption loses nothing
            elif action.kind == "adopt":
                record.add(
                    action.source,
                    sha256_of(destination),
                    destination.stat().st_size,
                    note="adopted from disk",
                )
                record.save(raw_dir)

    record_path = record.save(raw_dir)
    print(f"\nDownload record: {record_path.relative_to(REPO_ROOT)}")
    print("\nFor data/data_manifest.yaml (noaa_storm_events_details):")
    print("  resolved_files:")
    for year in sorted(args.years):
        filename = record.active[str(year)]
        print(f"    - {{file: {filename}, sha256: {record.files[filename]['sha256']}}}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
