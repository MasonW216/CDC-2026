"""GET /api/v1/routing/route: the HTTP contract.

OSRM is mocked at the routing route's own _get_osrm_response seam, so no
network call is made and no fetch_routes candidate-count rule applies.
"""

import os

import pytest
from fastapi.testclient import TestClient

from stormroute.routing.client import RoutingError
from stormroute_api.config import Settings
from stormroute_api.main import create_app
from stormroute_api.routes import routing as routing_route


@pytest.fixture
def app():
    return create_app(Settings(model_path="x", demo_artifact_paths=[]))


def _osrm_payload(count: int) -> dict[str, object]:
    """`count` routes with distinct geometry, as real OSRM alternatives would be.

    Route IDs are now derived from route content (distance, duration, geometry), not
    position, so two routes sharing identical content would collide; each gets its own
    midpoint offset to stay distinct, matching a real alternatives response.
    """
    return {
        "code": "Ok",
        "routes": [
            {
                "geometry": {
                    "coordinates": [
                        [-82.5515, 35.5951],
                        [-81.7 - 0.01 * i, 35.4],
                        [-80.8431, 35.2271],
                    ],
                },
                "legs": [
                    {
                        "annotation": {
                            "duration": [4500.0, 4500.0],
                            "distance": [95000.0, 95000.0],
                        }
                    }
                ],
                "duration": 9000.0,
                "distance": 190000.0,
            }
            for i in range(count)
        ],
    }


def _params(**overrides: float) -> dict[str, float]:
    params = {
        "origin_lat": 35.5951,
        "origin_lon": -82.5515,
        "destination_lat": 35.2271,
        "destination_lon": -80.8431,
    }
    params.update(overrides)
    return params


def test_route_returns_a_single_candidate(app, monkeypatch):
    monkeypatch.setattr(routing_route, "_get_osrm_response", lambda url: _osrm_payload(1))
    response = TestClient(app).get("/api/v1/routing/route", params=_params())
    assert response.status_code == 200
    body = response.json()
    assert len(body["routes"]) == 1
    assert body["routes"][0]["route_id"].startswith("route_")
    assert body["routes"][0]["coordinates"][0] == [-82.5515, 35.5951]
    assert body["routes"][0]["coordinates"][-1] == [-80.8431, 35.2271]
    assert body["routes"][0]["duration_minutes"] == 150.0
    assert body["routes"][0]["distance_km"] == 190.0


def test_route_does_not_require_two_alternatives(app, monkeypatch):
    """A single-candidate OSRM response is a normal result here, not an error.

    fetch_routes (used by the scoring pipeline) also accepts one route as of the same
    change; only zero routes is a routing failure anywhere in this codebase now.
    """
    monkeypatch.setattr(routing_route, "_get_osrm_response", lambda url: _osrm_payload(1))
    response = TestClient(app).get("/api/v1/routing/route", params=_params())
    assert response.status_code == 200


def test_route_returns_multiple_candidates_with_distinct_stable_ids(app, monkeypatch):
    monkeypatch.setattr(routing_route, "_get_osrm_response", lambda url: _osrm_payload(2))
    response = TestClient(app).get("/api/v1/routing/route", params=_params())
    ids = [r["route_id"] for r in response.json()["routes"]]
    assert len(ids) == 2
    assert len(set(ids)) == 2  # distinct routes get distinct IDs
    assert all(i.startswith("route_") for i in ids)


def test_osrm_failure_is_a_502(app, monkeypatch):
    def boom(url: str) -> dict[str, object]:
        raise RoutingError("routing request returned HTTP 429")

    monkeypatch.setattr(routing_route, "_get_osrm_response", boom)
    response = TestClient(app).get("/api/v1/routing/route", params=_params())
    assert response.status_code == 502
    assert "429" in response.json()["detail"]


def test_no_route_found_is_a_502_not_a_crash(app, monkeypatch):
    monkeypatch.setattr(
        routing_route, "_get_osrm_response", lambda url: {"code": "Ok", "routes": []}
    )
    response = TestClient(app).get("/api/v1/routing/route", params=_params())
    assert response.status_code == 502


@pytest.mark.parametrize(("lat", "lon"), [(91, -80), (35, 200), (-91, -80), (35, -200)])
def test_rejects_out_of_range_coordinates(app, lat, lon):
    response = TestClient(app).get(
        "/api/v1/routing/route", params=_params(origin_lat=lat, origin_lon=lon)
    )
    assert response.status_code == 422


@pytest.mark.network
@pytest.mark.skipif(
    os.environ.get("STORMROUTE_NETWORK_TESTS") != "1",
    reason="set STORMROUTE_NETWORK_TESTS=1 to call the public OSRM server",
)
def test_live_route_asheville_to_charlotte():
    response = TestClient(create_app(Settings())).get("/api/v1/routing/route", params=_params())
    assert response.status_code == 200
    assert len(response.json()["routes"]) >= 1
