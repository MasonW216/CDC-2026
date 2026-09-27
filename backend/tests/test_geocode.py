"""GET /api/v1/geocode/search and /reverse: the HTTP contract.

The ORS provider is mocked at the httpx layer by monkeypatching the geocode
service module's request function, so no network call is made.
"""

import os

import pytest
from fastapi.testclient import TestClient

from stormroute_api.config import Settings
from stormroute_api.main import create_app
from stormroute_api.services import geocode_service


@pytest.fixture
def app_with_key():
    return create_app(Settings(model_path="x", demo_artifact_paths=[], ors_api_key="test-key"))


@pytest.fixture
def app_without_key():
    return create_app(Settings(model_path="x", demo_artifact_paths=[], ors_api_key=None))


def test_search_returns_results(app_with_key, monkeypatch):
    monkeypatch.setattr(
        geocode_service,
        "search",
        lambda text, key, **kw: [
            geocode_service.GeocodeResult(
                label="Asheville, NC", lat=35.6, lon=-82.6, confidence=1.0
            )
        ],
    )
    response = TestClient(app_with_key).get("/api/v1/geocode/search", params={"text": "Asheville"})
    assert response.status_code == 200
    assert response.json() == {
        "results": [{"label": "Asheville, NC", "lat": 35.6, "lon": -82.6, "confidence": 1.0}]
    }


def test_search_with_no_matches_is_200_with_an_empty_list(app_with_key, monkeypatch):
    monkeypatch.setattr(geocode_service, "search", lambda text, key, **kw: [])
    response = TestClient(app_with_key).get("/api/v1/geocode/search", params={"text": "zzz"})
    assert response.status_code == 200
    assert response.json() == {"results": []}


def test_search_requires_nonempty_text(app_with_key):
    response = TestClient(app_with_key).get("/api/v1/geocode/search", params={"text": ""})
    assert response.status_code == 422


def test_missing_key_is_a_clear_503_not_a_crash(app_without_key):
    response = TestClient(app_without_key).get(
        "/api/v1/geocode/search", params={"text": "Asheville"}
    )
    assert response.status_code == 503
    assert "ORS_API_KEY" in response.json()["detail"]


def test_provider_failure_is_a_502(app_with_key, monkeypatch):
    def boom(text: str, key: str, **kw: object) -> None:
        raise geocode_service.GeocodeUnavailableError("geocoding provider returned HTTP 401")

    monkeypatch.setattr(geocode_service, "search", boom)
    response = TestClient(app_with_key).get("/api/v1/geocode/search", params={"text": "Asheville"})
    assert response.status_code == 502


def test_reverse_returns_a_label(app_with_key, monkeypatch):
    monkeypatch.setattr(
        geocode_service,
        "reverse",
        lambda lat, lon, key, **kw: [
            geocode_service.GeocodeResult(label="Asheville, NC", lat=lat, lon=lon, confidence=1.0)
        ],
    )
    response = TestClient(app_with_key).get(
        "/api/v1/geocode/reverse", params={"lat": 35.6, "lon": -82.6}
    )
    assert response.status_code == 200
    assert response.json()["results"][0]["label"] == "Asheville, NC"


@pytest.mark.parametrize(("lat", "lon"), [(91, -80), (35, 200), (-91, -80)])
def test_reverse_rejects_out_of_range_coordinates(app_with_key, lat, lon):
    response = TestClient(app_with_key).get(
        "/api/v1/geocode/reverse", params={"lat": lat, "lon": lon}
    )
    assert response.status_code == 422


@pytest.mark.network
@pytest.mark.skipif(
    os.environ.get("STORMROUTE_NETWORK_TESTS") != "1",
    reason="set STORMROUTE_NETWORK_TESTS=1 to call the live ORS API",
)
def test_live_ors_search_for_asheville():
    settings = Settings()
    assert settings.ors_api_key, "ORS_API_KEY must be set in .env for this test"
    response = TestClient(create_app(settings)).get(
        "/api/v1/geocode/search", params={"text": "Asheville, NC"}
    )
    assert response.status_code == 200
    assert response.json()["results"][0]["label"]
