"""Resolve county identities and geometry for North Carolina.

Loads Census TIGER/Line boundaries, restricts to STATEFP 37, and provides the
canonical county lookup used by both the label pipeline and the route spatial
join -- one shared definition of "which county is this", so training
geography and serving geography cannot drift apart.

Also owns the zone-to-county crosswalk for NOAA zone-coded events. Events
that cannot be resolved confidently are reported, never guessed.

Expects exactly 100 counties. A different count is an error, not a warning.

Contract for the county table (`COUNTY_COLUMNS`):
  * `county_fips` is a 5-character string, state FIPS + zero-padded county
    code (`37001`), never an integer;
  * `name` is the TIGER short name (`Alamance`, not `Alamance County`);
  * `land_area_m2` is TIGER's ALAND. TIGER polygons include inland and coastal
    water (so bridges and ferry legs still join to a county), which makes
    geometry area overstate coastal counties; normalize by land area instead;
  * geometry is stored in `crs_storage` from configs/data.yaml (EPSG:4326).
    Project to `AREA_CRS` (`crs_area`, EPSG:5070) before measuring distances
    or areas;
  * rows are sorted by `county_fips`.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

import geopandas as gpd
from pyproj import CRS

from stormroute.config import data_mode, data_path, load_config
from stormroute.data.noaa import sha256_of
from stormroute.data.validation import DataContractError

_GEOGRAPHY = load_config("data")["geography"]
STATE_FIPS: str = _GEOGRAPHY["state_fips"]
EXPECTED_COUNTY_COUNT: int = _GEOGRAPHY["expected_county_count"]
COUNTY_CRS = CRS.from_user_input(_GEOGRAPHY["crs_storage"])
AREA_CRS = CRS.from_user_input(_GEOGRAPHY["crs_area"])
COUNTY_COLUMNS = ["county_fips", "name", "land_area_m2", "geometry"]

# ---------------------------------------------------------------------------
# Source file
# ---------------------------------------------------------------------------

TIGER_COUNTY_FILENAME = "tl_2024_us_county.zip"
TIGER_COUNTY_URL = f"https://www2.census.gov/geo/tiger/TIGER2024/COUNTY/{TIGER_COUNTY_FILENAME}"
RECORD_FILENAME = "download_record.json"
SAMPLE_FILENAME = "nc_counties_sample.geojson"

BoundaryActionKind = Literal["skip", "download", "adopt", "conflict"]


@dataclass(frozen=True)
class BoundaryAction:
    """What the boundary downloader will do, and why."""

    kind: BoundaryActionKind
    reason: str


def _load_record(raw_dir: Path) -> dict[str, dict[str, object]]:
    path = raw_dir / RECORD_FILENAME
    if not path.exists():
        return {}
    files: dict[str, dict[str, object]] = json.loads(path.read_text(encoding="utf-8"))["files"]
    return files


def plan_boundary_download(raw_dir: Path, *, adopt_existing: bool = False) -> BoundaryAction:
    """Decide, without touching the network, what to do with the TIGER file.

    A file on disk is never replaced: an unrecorded file is a conflict unless the
    caller opts in to adopting it, and a file whose checksum no longer matches
    its record is always a conflict.
    """
    path = raw_dir / TIGER_COUNTY_FILENAME
    recorded = _load_record(raw_dir).get(TIGER_COUNTY_FILENAME)
    if not path.exists():
        return BoundaryAction("download", "not yet downloaded")
    if recorded is None:
        if adopt_existing:
            return BoundaryAction("adopt", "file is on disk but not in the download record")
        return BoundaryAction(
            "conflict",
            "file is on disk but not in the download record; delete it or pass "
            "--adopt-existing to record it as-is",
        )
    if sha256_of(path) != recorded["sha256"]:
        return BoundaryAction(
            "conflict",
            "file on disk differs from its recorded checksum; it was modified or "
            "corrupted. Delete it to re-download",
        )
    return BoundaryAction("skip", "present and checksum verified")


def record_boundary_download(
    raw_dir: Path, sha256: str, size: int, note: str = "downloaded"
) -> Path:
    """Write the TIGER file's checksum, size, and access time; return the record path."""
    raw_dir.mkdir(parents=True, exist_ok=True)
    path = raw_dir / RECORD_FILENAME
    files = _load_record(raw_dir)
    files[TIGER_COUNTY_FILENAME] = {
        "url": TIGER_COUNTY_URL,
        "sha256": sha256,
        "bytes": size,
        "recorded_at_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "note": note,
    }
    payload = {"source": TIGER_COUNTY_URL, "files": files}
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# County table
# ---------------------------------------------------------------------------

_FIPS = re.compile(rf"^{STATE_FIPS}\d{{3}}$")


def validate_counties(counties: gpd.GeoDataFrame) -> None:
    """Check the canonical county table.

    Raises:
        DataContractError: listing every violated rule.
    """
    failures: list[str] = []
    if list(counties.columns) != COUNTY_COLUMNS:
        failures.append(f"columns are {list(counties.columns)}, expected {COUNTY_COLUMNS}")
    if len(counties) != EXPECTED_COUNTY_COUNT:
        failures.append(f"{len(counties)} counties, expected exactly {EXPECTED_COUNTY_COUNT}")
    if "county_fips" in counties:
        fips = counties["county_fips"]
        malformed = sorted({str(v) for v in fips if not (isinstance(v, str) and _FIPS.match(v))})
        if malformed:
            failures.append(f"malformed county FIPS (need '{STATE_FIPS}' + 3 digits): {malformed}")
        duplicated = sorted(set(fips[fips.duplicated()].astype(str)))
        if duplicated:
            failures.append(f"duplicate county FIPS: {duplicated}")
    if "land_area_m2" in counties:
        land = counties["land_area_m2"]
        if land.isna().any() or not (land > 0).all():
            failures.append("land_area_m2 must be present and positive for every county")
    if counties.crs is None:
        failures.append("CRS is missing")
    elif counties.crs != COUNTY_CRS:
        failures.append(f"CRS is {counties.crs.to_string()}, expected {COUNTY_CRS.to_string()}")
    geometry = counties.geometry
    bad = geometry.isna() | geometry.is_empty | ~geometry.is_valid
    if bad.any():
        failures.append(f"{int(bad.sum())} missing, empty, or invalid geometries")
    if failures:
        raise DataContractError(failures)


def counties_from_tiger(tiger: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Restrict raw TIGER/Line county rows to North Carolina in canonical form.

    FIPS are rebuilt from STATEFP + COUNTYFP with explicit zero-padding, so a
    reader that parsed either field as a number cannot drop leading zeroes.
    """
    state = tiger["STATEFP"].astype(str).str.zfill(2)
    nc = tiger[state == STATE_FIPS]
    counties = gpd.GeoDataFrame(
        {
            "county_fips": STATE_FIPS + nc["COUNTYFP"].astype(str).str.zfill(3),
            "name": nc["NAME"].astype(str),
            "land_area_m2": nc["ALAND"].astype("int64"),
        },
        geometry=nc.geometry,
        crs=tiger.crs,
    )
    counties = counties.to_crs(COUNTY_CRS).sort_values("county_fips").reset_index(drop=True)
    validate_counties(counties)
    return counties


def load_sample_counties() -> gpd.GeoDataFrame:
    """Return the tracked, simplified 100-county fixture from `data/sample/`."""
    counties = gpd.read_file(data_path("sample") / SAMPLE_FILENAME)
    counties["county_fips"] = counties["county_fips"].astype(str)
    counties["land_area_m2"] = counties["land_area_m2"].astype("int64")
    counties = counties[COUNTY_COLUMNS].to_crs(COUNTY_CRS)
    validate_counties(counties)
    return counties


def load_nc_counties(path: Path | None = None) -> gpd.GeoDataFrame:
    """Return the 100 North Carolina counties as a validated GeoDataFrame.

    With no `path`, sample mode reads the tracked simplified fixture in
    `data/sample/` and full mode reads the downloaded TIGER zip.
    """
    if path is None:
        if data_mode() == "sample":
            return load_sample_counties()
        path = data_path("boundaries_raw") / TIGER_COUNTY_FILENAME
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Run `make download` (or scripts/download_boundaries.py), "
            "or set STORMROUTE_DATA_MODE=sample to use the tracked fixture."
        )
    return counties_from_tiger(gpd.read_file(f"zip://{path}"))
