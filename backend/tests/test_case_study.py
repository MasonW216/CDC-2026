"""GET /api/v1/demo/helene: the standalone Helene case-study endpoint."""

from fastapi.testclient import TestClient

from stormroute_api.main import create_app


def test_returns_the_helene_case_study():
    response = TestClient(create_app()).get("/api/v1/demo/helene")
    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "historical_case_study"
    assert body["schema_version"] == "prototype-score/1"
    assert body["case_study"]["name"] == "Hurricane Helene"
    assert all(route["band"] == "Severe concern" for route in body["routes"])


def test_route_never_needs_a_request_body():
    """A GET, not a POST -- there is nothing for a caller to submit or get wrong."""
    response = TestClient(create_app()).get("/api/v1/demo/helene")
    assert response.status_code == 200
