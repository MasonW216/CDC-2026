"""Resolve county identities and geometry for North Carolina.

Loads Census TIGER/Line boundaries, restricts to STATEFP 37, and provides the
canonical county lookup used by both the label pipeline and the route spatial
join -- one shared definition of "which county is this", so training
geography and serving geography cannot drift apart.

Also owns the zone-to-county crosswalk for NOAA zone-coded events. Events
that cannot be resolved confidently are reported, never guessed.

Expects exactly 100 counties. A different count is an error, not a warning.
"""

from __future__ import annotations

import json

import geopandas as gpd

from stormroute.config import DataMode, data_mode, data_path, load_config
from stormroute.data.noaa import sha256_of


def load_counties(mode: DataMode | None = None) -> gpd.GeoDataFrame:
    """Load and validate full TIGER geometry or the simplified offline fixture."""
    mode = mode or data_mode()
    if mode == "sample":
        path = data_path("sample") / "nc_counties_2024.geojson"
        record = json.loads(path.with_suffix(".json").read_text(encoding="utf-8"))
    else:
        directory = data_path("boundaries_raw")
        record = json.loads((directory / "download_record.json").read_text(encoding="utf-8"))
        path = directory / "tl_2024_us_county.zip"
    if sha256_of(path) != record["sha256"]:
        raise ValueError("County boundary checksum does not match its provenance record")
    counties = gpd.read_file(path)
    config = load_config("data")["geography"]
    counties = counties.loc[counties["STATEFP"] == config["state_fips"]].copy()
    if len(counties) != config["expected_county_count"] or not counties["GEOID"].is_unique:
        raise ValueError("Expected exactly 100 unique North Carolina counties")
    if not counties["GEOID"].str.fullmatch(r"37\d{3}").all():
        raise ValueError("Invalid county FIPS")
    if counties.crs is None or counties.geometry.isna().any() or counties.geometry.is_empty.any():
        raise ValueError("Missing county geometry or CRS")
    if not counties.geometry.is_valid.all():
        raise ValueError("Invalid county geometry")
    return counties.to_crs(config["crs_storage"]).sort_values("GEOID").reset_index(drop=True)
