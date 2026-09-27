"""ORS geocoder client: request shape, parsing, and provider failures.

Uses httpx.MockTransport, so nothing here reaches the network.
"""

import httpx
import pytest

from stormroute_api.services.geocode_service import GeocodeUnavailableError, reverse, search


def feature(label: str, lat: float, lon: float, confidence: float = 1.0) -> dict:
    return {
        "geometry": {"type": "Point", "coordinates": [lon, lat]},
        "properties": {"label": label, "confidence": confidence},
    }


def mock_client(status: int, body: dict, calls: list) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(status, json=body)

    return httpx.Client(transport=httpx.MockTransport(handler))


def test_search_sends_the_key_as_a_raw_authorization_header_and_biases_to_us():
    calls: list[httpx.Request] = []
    search("Asheville, NC", "secret-key", client=mock_client(200, {"features": []}, calls))
    request = calls[0]
    assert request.headers["Authorization"] == "secret-key"
    assert request.url.path == "/geocode/search"
    assert request.url.params["text"] == "Asheville, NC"
    assert request.url.params["boundary.country"] == "US"


def test_search_parses_label_lat_lon_confidence_in_result_order():
    body = {"features": [feature("Asheville, NC, USA", 35.5951, -82.5515, 0.92)]}
    results = search("Asheville", "key", client=mock_client(200, body, []))
    assert len(results) == 1
    result = results[0]
    assert result.label == "Asheville, NC, USA"
    assert result.lat == pytest.approx(35.5951)
    assert result.lon == pytest.approx(-82.5515)
    assert result.confidence == pytest.approx(0.92)


def test_no_match_is_an_empty_list_not_an_error():
    assert search("zzzzz not a place", "key", client=mock_client(200, {"features": []}, [])) == []


def test_reverse_sends_point_params():
    calls: list[httpx.Request] = []
    reverse(35.5951, -82.5515, "key", client=mock_client(200, {"features": []}, calls))
    params = calls[0].url.params
    assert params["point.lat"] == "35.5951"
    assert params["point.lon"] == "-82.5515"


def test_non_200_response_raises_geocode_unavailable():
    with pytest.raises(GeocodeUnavailableError, match="401"):
        search("Asheville", "bad-key", client=mock_client(401, {"error": "invalid key"}, []))


def test_network_failure_raises_geocode_unavailable():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("timed out", request=request)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    with pytest.raises(GeocodeUnavailableError, match="reach"):
        search("Asheville", "key", client=client)


def test_missing_label_falls_back_to_coordinates():
    body = {"features": [{"geometry": {"coordinates": [-82.55, 35.6]}, "properties": {}}]}
    result = search("x", "key", client=mock_client(200, body, []))[0]
    assert "35.6" in result.label and "-82.55" in result.label
