"""Scoring endpoint request and response contract, per docs/prototype_score_spec.md.

Covers: a valid request returns the `prototype-score/1` shape with every route
scored; past-departure and out-of-range-coordinate requests return 422 with a
message that says what to fix; `mode=cached_replay` returns the same shape from
the saved trip, ignoring the submitted origin/destination; OSRM failure returns
502; no case ever returns a lower-concern claim on a tied or partial result.

Upstream HTTP (OSRM, Open-Meteo, NWS) is monkeypatched so these tests run
offline and deterministically.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from stormroute.routing.client import CandidateRoute
from stormroute.scoring.live_forecast import AlertData, ForecastData
from stormroute_api.main import create_app

NOW = datetime.now(UTC)
DEPARTURE = (NOW + timedelta(hours=3)).isoformat()

# Asheville (35.60,-82.55) -> Charlotte (35.23,-80.84): a straight two-point line
# is enough to exercise county sampling without a real OSRM geometry.
CANDIDATES = [
    CandidateRoute(
        "route_0",
        ((-82.5515, 35.5951), (-80.8431, 35.2271)),
        (12000.0,),
        (180000.0,),
        12000.0,
        180000.0,
    ),
    CandidateRoute(
        "route_1",
        ((-82.5515, 35.5951), (-81.7, 35.4), (-80.8431, 35.2271)),
        (6500.0, 6500.0),
        (95000.0, 95000.0),
        13000.0,
        190000.0,
    ),
]


def _forecast_payload() -> dict:
    times = [(NOW + timedelta(hours=k)).strftime("%Y-%m-%dT%H:00") for k in range(-48, 97)]
    return {"hourly": {"time": times, "precipitation": [0.0] * len(times)}}


@pytest.fixture
def client(monkeypatch, tmp_path):
    monkeypatch.setattr("stormroute_api.routes.score.fetch_routes", lambda *a, **kw: CANDIDATES)
    monkeypatch.setattr("stormroute_api.routes.score.DEFAULT_CACHE", tmp_path)
    monkeypatch.setattr(
        "stormroute.scoring.trip.fetch_forecast",
        lambda points, offline=False, **kw: ForecastData(
            {fips: {t: 0.0 for t in _forecast_payload()["hourly"]["time"]} for fips in points},
            NOW,
            from_cache=offline,
        ),
    )
    monkeypatch.setattr(
        "stormroute.scoring.trip.fetch_alerts",
        lambda offline=False, **kw: AlertData((), NOW, ok=True, from_cache=offline),
    )
    return TestClient(create_app())


TRIP_BODY = {
    "origin": {"label": "Asheville, NC", "lat": 35.5951, "lon": -82.5515},
    "destination": {"label": "Charlotte, NC", "lat": 35.2271, "lon": -80.8431},
    "departure_time": DEPARTURE,
    "mode": "live",
}


def test_valid_request_returns_the_prototype_score_shape(client):
    response = client.post("/api/v1/trips/score", json=TRIP_BODY)
    assert response.status_code == 200
    body = response.json()
    assert body["schema_version"] == "prototype-score/1"
    assert body["mode"] == "live"
    assert {"routes", "comparison", "coverage", "alerts", "limitations"} <= body.keys()
    assert len(body["routes"]) == 2
    for route in body["routes"]:
        assert {"route_id", "status", "index", "band", "segments", "reasons"} <= route.keys()
        assert route["geometry"]  # the mocked CANDIDATES carry real coordinate tuples


def test_response_never_makes_a_lower_concern_claim_on_a_tie(client):
    body = client.post("/api/v1/trips/score", json=TRIP_BODY).json()
    assert body["comparison"]["ranking"] == "tie"
    assert body["comparison"]["lowest_concern_route_id"] is None
    assert "safer" not in body["comparison"]["message"].lower()


def test_past_departure_returns_422_with_a_useful_message(client):
    past = (NOW - timedelta(days=1)).isoformat()
    response = client.post("/api/v1/trips/score", json={**TRIP_BODY, "departure_time": past})
    assert response.status_code == 422
    assert "past" in response.json()["detail"].lower()


def test_out_of_range_coordinates_return_422(client):
    bad = {**TRIP_BODY, "origin": {"label": "x", "lat": 999.0, "lon": 0.0}}
    assert client.post("/api/v1/trips/score", json=bad).status_code == 422


def test_naive_timestamp_returns_422(client):
    bad = {**TRIP_BODY, "departure_time": "2026-09-27T12:00:00"}
    assert client.post("/api/v1/trips/score", json=bad).status_code == 422


def test_routing_failure_returns_502(client, monkeypatch):
    from stormroute.routing.client import RoutingError

    def fail(*_args: object, **_kwargs: object) -> None:
        raise RoutingError("OSRM unreachable")

    monkeypatch.setattr("stormroute_api.routes.score.fetch_routes", fail)
    response = client.post("/api/v1/trips/score", json=TRIP_BODY)
    assert response.status_code == 502


def test_cached_replay_ignores_the_submitted_trip_and_uses_the_same_shape(client):
    saved_request = json.loads(
        (
            __import__("stormroute").config.REPO_ROOT / "artifacts/demo/saved_trip_request.json"
        ).read_text()
    )
    response = client.post(
        "/api/v1/trips/score",
        json={
            **TRIP_BODY,
            "mode": "cached_replay",
            "origin": {"label": "nowhere", "lat": 0.0, "lon": 0.0},
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["schema_version"] == "prototype-score/1"
    assert body["mode"] == "cached"
    assert body["departure_utc"] == saved_request["departure_utc"]
