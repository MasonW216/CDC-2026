"""GET /api/v1/geography/counties: the county-boundary GeoJSON endpoint."""

from fastapi.testclient import TestClient

from stormroute_api.main import create_app


def test_returns_100_nc_counties_with_geoid():
    response = TestClient(create_app()).get("/api/v1/geography/counties")
    assert response.status_code == 200
    body = response.json()
    assert body["type"] == "FeatureCollection"
    assert len(body["features"]) == 100
    for feature in body["features"]:
        assert feature["geometry"]["type"] == "Polygon"
        assert len(feature["properties"]["GEOID"]) == 5


def test_geoid_matches_the_county_fips_format_used_in_score_responses():
    body = TestClient(create_app()).get("/api/v1/geography/counties").json()
    geoids = {f["properties"]["GEOID"] for f in body["features"]}
    assert "37021" in geoids  # Buncombe, used throughout the scoring tests/fixtures
    assert all(g.startswith("37") for g in geoids)  # NC state FIPS
