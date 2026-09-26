"""North Carolina county geometry: filtering, FIPS format, count, and download safety.

Unit tests use tiny synthetic GeoDataFrames shaped like TIGER/Line rows, so they
need no download. The tracked sample fixture must satisfy the same contract as
the real file, and the real file is checked when it is present on disk.
"""

import json
from pathlib import Path

import geopandas as gpd
import pytest
from shapely.geometry import Polygon, box

from stormroute.config import data_path
from stormroute.data.geography import (
    COUNTY_COLUMNS,
    COUNTY_CRS,
    TIGER_COUNTY_FILENAME,
    counties_from_tiger,
    load_nc_counties,
    plan_boundary_download,
    record_boundary_download,
    validate_counties,
)
from stormroute.data.noaa import sha256_of
from stormroute.data.validation import DataContractError

FIPS_PATTERN = r"^37\d{3}$"


def tiger_rows(nc_count: int = 100, *, countyfp_as_int: bool = False) -> gpd.GeoDataFrame:
    """Synthetic TIGER-shaped rows: `nc_count` NC counties plus two other states."""
    rows = []
    for i in range(nc_count):
        code = 2 * i + 1  # NC county codes are odd: 001, 003, ..., 199
        rows.append(
            {
                "STATEFP": "37",
                "COUNTYFP": code if countyfp_as_int else f"{code:03d}",
                "NAME": f"County {code}",
                "geometry": box(i, 0, i + 1, 1),
            }
        )
    rows.append({"STATEFP": "47", "COUNTYFP": "001", "NAME": "Anderson", "geometry": box(0, 5, 1, 6)})
    rows.append({"STATEFP": "45", "COUNTYFP": "001", "NAME": "Abbeville", "geometry": box(0, 7, 1, 8)})
    return gpd.GeoDataFrame(rows, crs="EPSG:4269")


# --- counties_from_tiger ----------------------------------------------------


def test_keeps_only_north_carolina_with_canonical_columns():
    counties = counties_from_tiger(tiger_rows())
    assert list(counties.columns) == COUNTY_COLUMNS
    assert len(counties) == 100
    assert counties["county_fips"].str.match(FIPS_PATTERN).all()


def test_fips_are_zero_padded_strings_even_if_source_codes_are_numeric():
    counties = counties_from_tiger(tiger_rows(countyfp_as_int=True))
    assert counties["county_fips"].map(type).eq(str).all()
    assert "37001" in set(counties["county_fips"])


def test_output_crs_is_explicit_and_geographic():
    counties = counties_from_tiger(tiger_rows())
    assert counties.crs == COUNTY_CRS
    assert counties.crs.is_geographic


def test_rows_are_sorted_by_fips():
    counties = counties_from_tiger(tiger_rows())
    assert counties["county_fips"].is_monotonic_increasing


# --- validate_counties ------------------------------------------------------


def test_wrong_county_count_is_an_error():
    with pytest.raises(DataContractError, match="100"):
        counties_from_tiger(tiger_rows(nc_count=99))


def test_duplicate_fips_is_an_error():
    counties = counties_from_tiger(tiger_rows())
    counties.loc[counties.index[1], "county_fips"] = counties["county_fips"].iloc[0]
    with pytest.raises(DataContractError, match="duplicate"):
        validate_counties(counties)


def test_malformed_fips_is_an_error():
    counties = counties_from_tiger(tiger_rows())
    counties.loc[counties.index[0], "county_fips"] = "3701"
    with pytest.raises(DataContractError, match="FIPS"):
        validate_counties(counties)


def test_missing_or_invalid_geometry_is_an_error():
    counties = counties_from_tiger(tiger_rows())
    counties.loc[counties.index[0], "geometry"] = None
    bowtie = Polygon([(0, 0), (1, 1), (1, 0), (0, 1)])
    counties.loc[counties.index[1], "geometry"] = bowtie
    with pytest.raises(DataContractError, match="geometr"):
        validate_counties(counties)


def test_missing_crs_is_an_error():
    counties = counties_from_tiger(tiger_rows()).set_crs(None, allow_override=True)
    with pytest.raises(DataContractError, match="CRS"):
        validate_counties(counties)


# --- load_nc_counties -------------------------------------------------------


def test_sample_fixture_meets_the_county_contract(monkeypatch):
    monkeypatch.setenv("STORMROUTE_DATA_MODE", "sample")
    counties = load_nc_counties()
    assert len(counties) == 100
    assert counties["county_fips"].str.match(FIPS_PATTERN).all()
    assert counties["county_fips"].is_unique
    assert counties.crs == COUNTY_CRS


def test_full_mode_without_download_explains_how_to_get_the_file(tmp_path):
    with pytest.raises(FileNotFoundError, match="make download"):
        load_nc_counties(tmp_path / TIGER_COUNTY_FILENAME)


REAL_FILE = data_path("boundaries_raw") / TIGER_COUNTY_FILENAME


@pytest.mark.slow
@pytest.mark.skipif(not REAL_FILE.exists(), reason="TIGER file not downloaded (make download)")
def test_real_tiger_file_yields_exactly_100_nc_counties():
    counties = load_nc_counties(REAL_FILE)
    assert len(counties) == 100
    assert counties["county_fips"].str.match(FIPS_PATTERN).all()
    assert {"37001", "37021", "37119", "37199"} <= set(counties["county_fips"])


# --- download planning ------------------------------------------------------


def write_file(path: Path, content: bytes = b"zip bytes") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return path


def test_plan_downloads_when_file_is_absent(tmp_path):
    assert plan_boundary_download(tmp_path).kind == "download"


def test_plan_skips_a_recorded_file_with_matching_checksum(tmp_path):
    path = write_file(tmp_path / TIGER_COUNTY_FILENAME)
    record_boundary_download(tmp_path, sha256_of(path), path.stat().st_size)
    assert plan_boundary_download(tmp_path).kind == "skip"


def test_plan_refuses_an_unrecorded_file_unless_adopting(tmp_path):
    write_file(tmp_path / TIGER_COUNTY_FILENAME)
    assert plan_boundary_download(tmp_path).kind == "conflict"
    assert plan_boundary_download(tmp_path, adopt_existing=True).kind == "adopt"


def test_plan_never_overwrites_a_file_that_differs_from_its_record(tmp_path):
    path = write_file(tmp_path / TIGER_COUNTY_FILENAME)
    record_boundary_download(tmp_path, sha256_of(path), path.stat().st_size)
    path.write_bytes(b"changed bytes")
    action = plan_boundary_download(tmp_path)
    assert action.kind == "conflict"
    assert "checksum" in action.reason


def test_record_stores_url_checksum_size_and_utc_time(tmp_path):
    record_path = record_boundary_download(tmp_path, "ab" * 32, 123)
    entry = json.loads(record_path.read_text())["files"][TIGER_COUNTY_FILENAME]
    assert entry["sha256"] == "ab" * 32
    assert entry["bytes"] == 123
    assert entry["url"].endswith(TIGER_COUNTY_FILENAME)
    assert entry["recorded_at_utc"].endswith("+00:00")
