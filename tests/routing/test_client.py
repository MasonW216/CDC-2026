"""OSRM client: request shape, response parsing, caching, and offline replay.

Uses httpx.MockTransport, so nothing here reaches the network except the one
opt-in test at the bottom.
"""

import json
import os

import httpx
import pytest

from stormroute.routing.client import (
    CandidateRoute,
    LatLon,
    RoutingError,
    build_route_url,
    fetch_routes,
    parse_osrm_response,
)

ASHEVILLE = LatLon(35.5951, -82.5515)
CHARLOTTE = LatLon(35.2271, -80.8431)
BASE_URL = "https://router.example.org"


def osrm_route(coords, seconds, meters, legs=1):
    """Build one OSRM route; `legs` splits the edges across that many legs."""
    per_leg = len(seconds) // legs
    leg_list = []
    for i in range(legs):
        lo, hi = i * per_leg, (i + 1) * per_leg if i < legs - 1 else len(seconds)
        leg_list.append(
            {
                "duration": sum(seconds[lo:hi]),
                "distance": sum(meters[lo:hi]),
                "annotation": {"duration": seconds[lo:hi], "distance": meters[lo:hi]},
            }
        )
    return {
        "duration": sum(seconds),
        "distance": sum(meters),
        "geometry": {"type": "LineString", "coordinates": coords},
        "legs": leg_list,
    }


def payload(n_routes=2):
    routes = []
    for r in range(n_routes):
        coords = [[-82.0 + 0.01 * i, 35.5 + 0.001 * r] for i in range(5)]
        routes.append(osrm_route(coords, [30.0] * 4, [900.0] * 4))
    return {"code": "Ok", "routes": routes, "waypoints": []}


# --- request --------------------------------------------------------------------


def test_url_uses_lon_lat_order_and_required_options():
    url = build_route_url(BASE_URL, ASHEVILLE, CHARLOTTE)
    assert "/route/v1/driving/-82.5515,35.5951;-80.8431,35.2271?" in url
    for option in ("alternatives=true", "overview=full", "geometries=geojson"):
        assert option in url
    assert "annotations=duration,distance" in url


def test_latlon_rejects_out_of_range_coordinates():
    with pytest.raises(ValueError, match="latitude"):
        LatLon(135.0, -82.5515)
    with pytest.raises(ValueError, match="longitude"):
        LatLon(35.5951, -182.0)


# --- parsing --------------------------------------------------------------------


def test_parses_routes_with_ids_geometry_and_edge_times():
    routes = parse_osrm_response(payload(2))
    assert routes[0].route_id != routes[1].route_id
    assert all(route.route_id.startswith("route_") for route in routes)
    first = routes[0]
    assert isinstance(first, CandidateRoute)
    assert len(first.coordinates) == len(first.edge_seconds) + 1
    assert first.duration_s == pytest.approx(120.0)
    assert first.coordinates[0] == (-82.0, 35.5)


def test_route_id_is_stable_for_the_same_route_regardless_of_position():
    """The score and the map fetch OSRM independently and can get a different order.

    score.py and routing.py are not guaranteed the same alternative order; the ID
    must still agree so the map and the score refer to the same geometry.
    """
    first_call = parse_osrm_response(payload(2))
    swapped = payload(2)
    swapped["routes"].reverse()
    second_call = parse_osrm_response(swapped)
    assert {r.route_id for r in first_call} == {r.route_id for r in second_call}
    by_id = {r.route_id: r for r in second_call}
    for route in first_call:
        assert by_id[route.route_id].coordinates == route.coordinates


def test_route_id_differs_for_genuinely_different_routes():
    routes = parse_osrm_response(payload(3))
    assert len({r.route_id for r in routes}) == 3


def test_multi_leg_annotations_are_concatenated():
    coords = [[-82.0 + 0.01 * i, 35.5] for i in range(5)]
    body = {"code": "Ok", "routes": [osrm_route(coords, [10.0, 20, 30, 40], [1.0] * 4, legs=2)]}
    route = parse_osrm_response(body)[0]
    assert route.edge_seconds == (10.0, 20.0, 30.0, 40.0)


def test_edge_times_are_scaled_to_sum_to_the_route_duration():
    body = payload(1)
    body["routes"][0]["duration"] = 132.0  # annotations sum to 120 s, as OSRM under-attributes
    route = parse_osrm_response(body)[0]
    assert sum(route.edge_seconds) == pytest.approx(132.0)
    assert route.edge_seconds[0] == pytest.approx(33.0)


def test_annotation_length_mismatch_is_an_error():
    body = payload(1)
    body["routes"][0]["legs"][0]["annotation"]["duration"].pop()
    with pytest.raises(RoutingError, match="annotation"):
        parse_osrm_response(body)


def test_non_ok_code_is_an_error():
    with pytest.raises(RoutingError, match="NoRoute"):
        parse_osrm_response({"code": "NoRoute", "message": "Impossible route"})


# --- fetching and caching --------------------------------------------------------


def mock_client(body, calls):
    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(200, json=body)

    return httpx.Client(transport=httpx.MockTransport(handler))


def test_fetch_sends_user_agent_and_caches_the_raw_response(tmp_path):
    calls = []
    routes = fetch_routes(
        ASHEVILLE,
        CHARLOTTE,
        base_url=BASE_URL,
        cache_dir=tmp_path,
        client=mock_client(payload(), calls),
    )
    assert len(routes) == 2
    assert calls[0].headers["User-Agent"].startswith("StormRoute")
    cached = list(tmp_path.glob("osrm_*.json"))
    assert len(cached) == 1
    assert json.loads(cached[0].read_text())["code"] == "Ok"


def test_offline_replays_the_cache_without_network(tmp_path):
    fetch_routes(
        ASHEVILLE,
        CHARLOTTE,
        base_url=BASE_URL,
        cache_dir=tmp_path,
        client=mock_client(payload(), []),
    )
    replayed = fetch_routes(
        ASHEVILLE, CHARLOTTE, base_url=BASE_URL, cache_dir=tmp_path, offline=True
    )
    assert len(replayed) == 2
    assert replayed[0].route_id != replayed[1].route_id


def test_offline_replay_does_not_depend_on_the_server_url(tmp_path):
    fetch_routes(
        ASHEVILLE,
        CHARLOTTE,
        base_url=BASE_URL,
        cache_dir=tmp_path,
        client=mock_client(payload(), []),
    )
    replayed = fetch_routes(
        ASHEVILLE, CHARLOTTE, base_url="https://other.example.org", cache_dir=tmp_path, offline=True
    )
    assert len(replayed) == 2


def test_cached_response_is_used_before_the_network(tmp_path):
    fetch_routes(
        ASHEVILLE,
        CHARLOTTE,
        base_url=BASE_URL,
        cache_dir=tmp_path,
        client=mock_client(payload(), []),
    )
    calls = []
    fetch_routes(
        ASHEVILLE,
        CHARLOTTE,
        base_url=BASE_URL,
        cache_dir=tmp_path,
        client=mock_client(payload(), calls),
    )
    assert calls == []


def test_offline_cache_miss_fails_loudly(tmp_path):
    with pytest.raises(RoutingError, match="cache"):
        fetch_routes(ASHEVILLE, CHARLOTTE, base_url=BASE_URL, cache_dir=tmp_path, offline=True)


def test_a_single_route_is_accepted_not_an_error(tmp_path):
    """OSRM does not guarantee an alternative exists; one route is a normal result.

    It is scored on its own (comparison.ranking == "single_route"), not a failure.
    """
    routes = fetch_routes(
        ASHEVILLE,
        CHARLOTTE,
        base_url=BASE_URL,
        cache_dir=tmp_path,
        client=mock_client(payload(1), []),
    )
    assert len(routes) == 1


def test_zero_routes_is_an_error(tmp_path):
    with pytest.raises(RoutingError, match="zero routes"):
        fetch_routes(
            ASHEVILLE,
            CHARLOTTE,
            base_url=BASE_URL,
            cache_dir=tmp_path,
            client=mock_client({"code": "Ok", "routes": [], "waypoints": []}, []),
        )


def test_at_most_three_routes_are_kept(tmp_path):
    routes = fetch_routes(
        ASHEVILLE,
        CHARLOTTE,
        base_url=BASE_URL,
        cache_dir=tmp_path,
        client=mock_client(payload(4), []),
    )
    assert len(routes) == 3


def test_http_error_is_a_routing_error(tmp_path):
    client = httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(503)))
    with pytest.raises(RoutingError, match="503"):
        fetch_routes(ASHEVILLE, CHARLOTTE, base_url=BASE_URL, cache_dir=tmp_path, client=client)


@pytest.mark.network
@pytest.mark.skipif(
    os.environ.get("STORMROUTE_NETWORK_TESTS") != "1",
    reason="set STORMROUTE_NETWORK_TESTS=1 to call the public OSRM server",
)
def test_live_osrm_returns_two_asheville_to_charlotte_routes(tmp_path):
    routes = fetch_routes(
        ASHEVILLE, CHARLOTTE, base_url="https://router.project-osrm.org", cache_dir=tmp_path
    )
    assert len(routes) >= 2
    assert all(90 < route.duration_s / 60 < 240 for route in routes)
