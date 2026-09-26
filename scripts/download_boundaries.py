"""Download Census TIGER/Line county boundaries.

Makefile target : make download
Milestone       : 1
Reads           : data/data_manifest.yaml
Writes          : data/raw/census_tiger/

Restricting to STATEFP 37 happens downstream in stormroute.data.geography.
Exactly 100 North Carolina counties are expected; any other count is an error.
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime

import httpx
import yaml

from stormroute.config import REPO_ROOT, data_path
from stormroute.data.noaa import download_file, sha256_of


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--write-sample", action="store_true", help="Rebuild simplified NC map fixture"
    )
    args = parser.parse_args()
    manifest = yaml.safe_load((REPO_ROOT / "data/data_manifest.yaml").read_text(encoding="utf-8"))
    source = next(d for d in manifest["datasets"] if d["name"] == "census_tiger_counties_2024")
    directory = data_path("boundaries_raw")
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / source["expected_file_pattern"]
    record_path = directory / "download_record.json"
    url = source["source_url"].rstrip("/") + "/" + target.name
    if target.exists():
        if not record_path.exists():
            raise RuntimeError(
                "County archive exists without provenance; review it before retrying."
            )
        record = json.loads(record_path.read_text(encoding="utf-8"))
        if record["sha256"] != sha256_of(target) or record["source_url"] != url:
            raise RuntimeError("County archive differs from its provenance record; refusing reuse.")
        print(f"Verified existing {target.name}")
        if args.write_sample:
            write_sample(record)
        return
    with httpx.Client(timeout=httpx.Timeout(30.0, read=300.0), follow_redirects=True) as client:
        checksum, size = download_file(client, url, target)
    record_path.write_text(
        json.dumps(
            {
                "source_url": url,
                "filename": target.name,
                "sha256": checksum,
                "size_bytes": size,
                "retrieved_at_utc": datetime.now(UTC).isoformat(),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Downloaded {target.name}; SHA-256 {checksum}")
    if args.write_sample:
        write_sample(json.loads(record_path.read_text(encoding="utf-8")))


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
    main()
