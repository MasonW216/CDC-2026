"""Validate the offline county inventory and reject corrupted boundaries."""

import geopandas as gpd
import pytest

from stormroute.data import geography


def test_sample_has_complete_county_inventory():
    counties = geography.load_counties("sample")
    assert len(counties) == 100
    assert counties.GEOID.is_unique
    assert counties.GEOID.str.fullmatch(r"37\d{3}").all()
    assert counties.geometry.is_valid.all()
    assert (counties.ALAND > 0).all()


def test_checksum_mismatch_rejected(monkeypatch):
    monkeypatch.setattr(geography, "sha256_of", lambda path: "incorrect")
    with pytest.raises(ValueError, match="checksum"):
        geography.load_counties("sample")


def test_incomplete_inventory_rejected(monkeypatch):
    original = gpd.read_file
    monkeypatch.setattr(gpd, "read_file", lambda path: original(path).iloc[:-1])
    with pytest.raises(ValueError, match="100 unique"):
        geography.load_counties("sample")
