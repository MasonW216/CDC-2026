"""Prototype weather-concern index (prototype-score/1): the agreed acceptance cases."""

import json
from datetime import UTC, datetime, timedelta

import httpx
import pytest

from stormroute.scoring.concern import (
    RouteInput,
    Stretch,
    band,
    compare,
    score_route,
    score_segment,
)
from stormroute.scoring.live_forecast import (
    Alert,
    AlertData,
    ForecastData,
    ForecastError,
    fetch_alerts,
    fetch_forecast,
    parse_alerts,
)
from stormroute.scoring.trip import TripNotSupportedError, build_response, score_trip

NOW = datetime(2026, 9, 27, 6, 0, tzinfo=UTC)
NO_ALERTS = AlertData((), NOW, True)


def hours(start: datetime, count: int) -> list[datetime]:
    return [start + timedelta(hours=k) for k in range(count)]


def forecast(
    rain: dict[str, float | dict[int, float]], with_gaps: set[str] = frozenset()
) -> ForecastData:
    """Hourly forecast from NOW-48h to NOW+96h. A float is constant; a dict maps hour offset."""
    table: dict[str, dict[str, float | None]] = {}
    for fips, spec in rain.items():
        series: dict[str, float | None] = {}
        for k in range(-48, 97):
            stamp = (NOW + timedelta(hours=k)).strftime("%Y-%m-%dT%H:00")
            value = spec if isinstance(spec, float) else spec.get(k, 0.0)
            series[stamp] = None if fips in with_gaps else value
        table[fips] = series
    return ForecastData(table, NOW, from_cache=False)


def stretch(fips="37021", at=2, minutes=30.0, name="Buncombe") -> Stretch:
    return Stretch(fips, name, NOW + timedelta(hours=at), minutes, 20.0)


def route(rid, stretches, minutes=120.0) -> RouteInput:
    return RouteInput(rid, minutes, 100.0, stretches)


def warning(fips="37021", floor=80, event="Flash Flood Warning", begins=0, ends=10) -> Alert:
    return Alert(
        f"id-{event}-{fips}",
        event,
        floor,
        None,
        NOW + timedelta(hours=begins),
        NOW + timedelta(hours=ends),
        (fips,),
    )


def test_bands_never_call_anything_safe():
    assert [band(i) for i in (0, 24, 25, 49, 50, 79, 80, 100)] == [
        "Lower concern",
        "Lower concern",
        "Elevated concern",
        "Elevated concern",
        "High concern",
        "High concern",
        "Severe concern",
        "Severe concern",
    ]
    assert band(None) == "Not assessed"


def test_dry_forecast_is_lower_concern_but_assessed():
    seg = score_segment(stretch(), forecast({"37021": 0.0}), NO_ALERTS, NOW)
    assert seg["status"] == "assessed" and seg["index"] == 0


def test_rain_rate_and_accumulation_set_the_index():
    fc = forecast({"37021": {k: 10.0 for k in range(-30, 5)}})
    seg = score_segment(stretch(), fc, NO_ALERTS, NOW)
    assert seg["rain_rate_mm_h"] == 10.0
    assert seg["rain_24h_mm"] == 240.0
    assert seg["index"] == 100  # 24 h accumulation is at full scale


def test_missing_forecast_is_unassessed_never_zero():
    seg = score_segment(stretch(), forecast({"37021": 0.0}, {"37021"}), NO_ALERTS, NOW)
    assert seg["status"] == "unassessed" and seg["index"] is None
    assert seg["band"] == "Not assessed"


def test_missing_forecast_with_alert_gives_a_lower_bound():
    fc = forecast({"37021": 0.0}, {"37021"})
    alerts = AlertData((warning(),), NOW, True)
    seg = score_segment(stretch(), fc, alerts, NOW)
    assert seg["status"] == "unassessed" and seg["index"] == 80
    assert "Lower bound" in seg["reason"]


def test_arrival_beyond_horizon_is_unassessed():
    seg = score_segment(stretch(at=80), forecast({"37021": 0.0}), NO_ALERTS, NOW)
    assert seg["status"] == "unassessed" and "horizon" in seg["reason"]


def test_stretch_outside_north_carolina_is_unassessed():
    seg = score_segment(stretch(fips=None, name="Outside"), forecast({}), NO_ALERTS, NOW)
    assert seg["status"] == "unassessed" and "outside North Carolina" in seg["reason"]


@pytest.mark.parametrize("floor", [35, 50, 80, 98])
def test_alert_never_lowers_the_index(floor):
    for rain in (0.0, 3.0, 12.0, 30.0):
        fc = forecast({"37021": rain})
        base = score_segment(stretch(), fc, NO_ALERTS, NOW)["index"]
        raised = score_segment(stretch(), fc, AlertData((warning(floor=floor),), NOW, True), NOW)[
            "index"
        ]
        assert raised >= base


def test_more_rain_never_lowers_the_index():
    indexes = [
        score_segment(
            stretch(), forecast({"37021": {k: r for k in range(-30, 6)}}), NO_ALERTS, NOW
        )["index"]
        for r in (0.0, 0.5, 1.0, 2.0, 4.0, 8.0)
    ]
    assert indexes == sorted(indexes)


def test_alert_outside_the_stretch_time_or_county_is_ignored():
    fc = forecast({"37021": 0.0, "37115": 0.0})
    later = AlertData((warning(begins=6, ends=9),), NOW, True)
    other = AlertData((warning(fips="37115"),), NOW, True)
    assert score_segment(stretch(), fc, later, NOW)["index"] == 0
    assert score_segment(stretch(), fc, other, NOW)["index"] == 0


def test_splitting_a_stretch_does_not_change_the_route_index():
    fc = forecast({"37021": {2: 15.0, 3: 4.0}})
    whole = route("r", [stretch(at=2, minutes=90.0)])
    pieces = route(
        "r",
        [stretch(at=2, minutes=30.0), stretch(at=2.5, minutes=30.0), stretch(at=3, minutes=30.0)],
    )
    a = score_route(whole, fc, NO_ALERTS, NOW)["index"]
    b = score_route(pieces, fc, NO_ALERTS, NOW)["index"]
    assert a == b


def test_partial_route_is_a_lower_bound_and_blocks_ranking():
    fc = forecast({"37021": 0.0, "37115": 0.0}, {"37115"})
    a = score_route(route("a", [stretch()]), fc, NO_ALERTS, NOW)
    b = score_route(route("b", [stretch(), stretch("37115", 3, name="Person")]), fc, NO_ALERTS, NOW)
    assert b["status"] == "partial" and b["is_lower_bound"]
    comparison = compare([a, b])
    assert comparison["ranking"] == "unavailable"
    assert comparison["lowest_concern_route_id"] is None


def test_failed_alert_feed_blocks_a_confident_ranking():
    fc = forecast({"37021": 0.0})
    dead = AlertData((), NOW, False, "no alert data")
    a = score_route(route("a", [stretch()]), fc, dead, NOW)
    b = score_route(route("b", [stretch()], 130.0), fc, dead, NOW)
    assert a["status"] == "partial" and compare([a, b])["ranking"] == "unavailable"


def test_tied_routes_make_no_lower_concern_claim():
    fc = forecast({"37021": 0.0, "37115": 0.0})
    a = score_route(route("a", [stretch()]), fc, NO_ALERTS, NOW)
    b = score_route(route("b", [stretch("37115", name="Person")], 140.0), fc, NO_ALERTS, NOW)
    result = compare([a, b])
    assert result["ranking"] == "tie" and result["lowest_concern_route_id"] is None
    assert "safer" not in result["message"].lower()


def test_distinguishable_reports_added_minutes_and_index_difference():
    fc = forecast({"37021": {3: 20.0}, "37115": 0.0})
    fast = score_route(route("fast", [stretch()], 100.0), fc, NO_ALERTS, NOW)
    slow = score_route(route("slow", [stretch("37115", name="Person")], 130.0), fc, NO_ALERTS, NOW)
    result = compare([fast, slow])
    assert result["ranking"] == "distinguishable"
    assert result["fastest_route_id"] == "fast" and result["lowest_concern_route_id"] == "slow"
    assert result["extra_minutes"] == 30.0 and result["index_difference"] == 100


def test_both_routes_severe_keeps_the_delay_advice():
    fc = forecast({"37021": 0.0, "37115": 0.0})
    alerts = AlertData((warning(), warning("37115")), NOW, True)
    a = score_route(route("a", [stretch()]), fc, alerts, NOW)
    b = score_route(route("b", [stretch("37115", name="Person")], 140.0), fc, alerts, NOW)
    result = compare([a, b])
    assert result["severe_advice"] and "delaying" in result["severe_advice"]


def test_single_route_invents_no_alternative():
    fc = forecast({"37021": 0.0})
    result = compare([score_route(route("only", [stretch()]), fc, NO_ALERTS, NOW)])
    assert result["ranking"] == "single_route" and result["lowest_concern_route_id"] is None


def test_no_routes():
    assert compare([])["ranking"] == "no_routes"


def test_result_is_deterministic():
    fc = forecast({"37021": {2: 7.5, 3: 2.5}})
    alerts = AlertData((warning(floor=50, event="Flood Advisory"),), NOW, True)
    one = json.dumps(score_route(route("r", [stretch()]), fc, alerts, NOW), sort_keys=True)
    assert one == json.dumps(score_route(route("r", [stretch()]), fc, alerts, NOW), sort_keys=True)


def test_parse_alerts_keeps_flood_products_maps_same_codes_and_flags_emergency():
    payload = {
        "features": [
            {
                "properties": {
                    "id": "a",
                    "event": "Flash Flood Warning",
                    "headline": "h",
                    "onset": "2026-09-27T01:00:00-04:00",
                    "ends": "2026-09-27T05:00:00-04:00",
                    "geocode": {"SAME": ["037021", "037089"]},
                    "parameters": {"flashFloodDamageThreat": ["CATASTROPHIC"]},
                }
            },
            {
                "properties": {
                    "id": "b",
                    "event": "Coastal Flood Advisory",
                    "geocode": {"SAME": ["037141"]},
                }
            },
            {"properties": {"id": "c", "event": "Flood Watch", "geocode": {}}},
        ]
    }
    alerts, unmapped, total = parse_alerts(payload)
    assert [a.id for a in alerts] == ["a"] and alerts[0].floor == 98
    assert alerts[0].county_fips == ("37021", "37089")
    assert unmapped == 1 and total == 3
    assert alerts[0].effective_utc == datetime(2026, 9, 27, 5, 0, tzinfo=UTC)


def _forecast_payload(count: int) -> list[dict]:
    times = [(NOW + timedelta(hours=k)).strftime("%Y-%m-%dT%H:00") for k in range(-48, 97)]
    return [{"hourly": {"time": times, "precipitation": [0.0] * len(times)}} for _ in range(count)]


def test_forecast_falls_back_to_cache_and_says_so(tmp_path):
    points = {"37021": (35.6, -82.5), "37119": (35.2, -80.8)}
    good = httpx.Client(
        transport=httpx.MockTransport(lambda r: httpx.Response(200, json=_forecast_payload(2)))
    )
    first = fetch_forecast(points, cache_dir=tmp_path, client=good)
    assert not first.from_cache
    down = httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(503)))
    second = fetch_forecast(points, cache_dir=tmp_path, client=down)
    assert second.from_cache and second.retrieved_utc == first.retrieved_utc
    assert fetch_forecast(points, cache_dir=tmp_path, offline=True).from_cache


def test_forecast_with_no_cache_raises(tmp_path):
    down = httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(503)))
    with pytest.raises(ForecastError):
        fetch_forecast({"37021": (35.6, -82.5)}, cache_dir=tmp_path, client=down)


def test_alert_failure_is_reported_not_raised(tmp_path):
    down = httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(500)))
    result = fetch_alerts(cache_dir=tmp_path, client=down)
    assert not result.ok and result.error and result.alerts == ()


def test_stale_forecast_fallback_is_refused_not_silently_served(tmp_path):
    points = {"37021": (35.6, -82.5)}
    good = httpx.Client(
        transport=httpx.MockTransport(lambda r: httpx.Response(200, json=_forecast_payload(1)))
    )
    fetch_forecast(points, cache_dir=tmp_path, client=good, now=NOW)
    down = httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(503)))
    # Just inside the policy: served.
    fresh_fallback = fetch_forecast(
        points, cache_dir=tmp_path, client=down, now=NOW + timedelta(hours=2)
    )
    assert fresh_fallback.from_cache
    # Past the policy: refused, same as no cache at all.
    with pytest.raises(ForecastError, match="freshness policy"):
        fetch_forecast(points, cache_dir=tmp_path, client=down, now=NOW + timedelta(hours=4))


def test_stale_alerts_fallback_is_reported_not_silently_served(tmp_path):
    good = httpx.Client(
        transport=httpx.MockTransport(lambda r: httpx.Response(200, json={"features": []}))
    )
    fetch_alerts(cache_dir=tmp_path, client=good, now=NOW)
    down = httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(500)))
    fresh_fallback = fetch_alerts(cache_dir=tmp_path, client=down, now=NOW + timedelta(minutes=10))
    assert fresh_fallback.ok and fresh_fallback.from_cache
    stale_fallback = fetch_alerts(cache_dir=tmp_path, client=down, now=NOW + timedelta(hours=1))
    assert not stale_fallback.ok
    assert stale_fallback.error and "freshness policy" in stale_fallback.error


def test_explicit_offline_replay_ignores_the_freshness_policy(tmp_path):
    """The spec's own carve-out: a saved demo replay may stay old on purpose."""
    points = {"37021": (35.6, -82.5)}
    good = httpx.Client(
        transport=httpx.MockTransport(lambda r: httpx.Response(200, json=_forecast_payload(1)))
    )
    fetch_forecast(points, cache_dir=tmp_path, client=good, now=NOW)
    far_future = fetch_forecast(
        points, cache_dir=tmp_path, offline=True, now=NOW + timedelta(days=30)
    )
    assert far_future.from_cache


def test_score_trip_refuses_a_past_departure(tmp_path):
    with pytest.raises(TripNotSupportedError, match="past"):
        score_trip(
            [route("r", [stretch()])],
            NOW - timedelta(days=2),
            now=NOW,
            cache_dir=tmp_path,
            points={"37021": (35.6, -82.5)},
        )


def test_score_trip_end_to_end_with_mocked_upstreams(tmp_path):
    def handler(request: httpx.Request) -> httpx.Response:
        if "open-meteo" in str(request.url):
            return httpx.Response(200, json=_forecast_payload(1)[0])
        return httpx.Response(200, json={"features": []})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    response = score_trip(
        [route("r", [stretch()])],
        NOW + timedelta(hours=2),
        now=NOW,
        cache_dir=tmp_path,
        client=client,
        points={"37021": (35.6, -82.5)},
    )
    assert response["schema_version"] == "prototype-score/1" and response["mode"] == "live"
    assert response["routes"][0]["status"] == "assessed"
    assert response["comparison"]["ranking"] == "single_route"
    assert response["coverage"]["geography"]["supported"] is True
    assert "not a calibrated flood probability" in " ".join(response["limitations"]).lower()


def test_outside_nc_is_flagged_in_coverage(tmp_path):
    client = httpx.Client(
        transport=httpx.MockTransport(
            lambda r: httpx.Response(
                200,
                json=_forecast_payload(1)[0] if "open-meteo" in str(r.url) else {"features": []},
            )
        )
    )
    outside = Stretch(None, "Outside North Carolina", NOW + timedelta(hours=3), 20.0, 30.0)
    response = score_trip(
        [route("r", [stretch(), outside])],
        NOW + timedelta(hours=2),
        now=NOW,
        cache_dir=tmp_path,
        client=client,
        points={"37021": (35.6, -82.5)},
    )
    assert response["coverage"]["geography"]["supported"] is False
    assert response["routes"][0]["status"] == "partial"


def test_saved_trip_replays_offline_with_identical_scores():
    from pathlib import Path

    from stormroute.scoring.trip import DEFAULT_CACHE, replay_saved_trip

    root = Path(__file__).resolve().parents[2] / "artifacts" / "demo"
    request_file, response_file = (
        root / "saved_trip_request.json",
        root / "saved_trip_response.json",
    )
    if not request_file.exists() or not DEFAULT_CACHE.exists():
        pytest.skip("no saved trip")
    saved = json.loads(request_file.read_text())
    original = json.loads(response_file.read_text())
    replay = replay_saved_trip(saved)
    assert replay["mode"] == "cached"
    assert replay["routes"] == original["routes"]
    assert replay["comparison"] == original["comparison"]
    assert (
        replay["coverage"]["forecast"]["retrieved_utc"]
        == original["coverage"]["forecast"]["retrieved_utc"]
    )
    assert replay["coverage"]["forecast"]["from_cache"] is True


def test_contributing_factors_are_grounded_in_real_computed_fields():
    """No factor can appear that the rule did not actually compute."""
    fc = forecast({"37021": {2: 20.0}, "37115": 0.0})
    alerts = AlertData((warning(fips="37115", event="Flood Advisory", floor=50),), NOW, True)
    a = score_route(route("a", [stretch()]), fc, alerts, NOW)
    b = score_route(route("b", [stretch("37115", name="Person")], 130.0), fc, alerts, NOW)
    rain_driven = a["contributing_factors"][0]
    alert_driven = b["contributing_factors"][0]
    assert rain_driven["kind"] == "rain" and "Buncombe" in rain_driven["label"]
    assert alert_driven["kind"] == "alert" and alert_driven["label"] == "Flood Advisory"
    for factor in [*a["contributing_factors"], *b["contributing_factors"]]:
        assert factor["kind"] in ("rain", "alert")  # never an invented kind like "soil moisture"
        assert factor["index"] > 0


def test_contributing_factors_empty_when_nothing_drove_the_score():
    fc = forecast({"37021": 0.0})
    scored = score_route(route("a", [stretch()]), fc, NO_ALERTS, NOW)
    assert scored["contributing_factors"] == []


def test_severe_advice_wording_matches_route_count():
    fc = forecast({"37021": 0.0})
    alerts = AlertData((warning(),), NOW, True)
    single = compare([score_route(route("only", [stretch()]), fc, alerts, NOW)])
    assert single["severe_advice"] and "This route does not avoid" in single["severe_advice"]

    a = score_route(route("a", [stretch()]), fc, alerts, NOW)
    b = score_route(route("b", [stretch("37115", name="Person")], 130.0), fc, alerts, NOW)
    both = compare([a, b])
    assert both["severe_advice"] and "None of the routes avoid" in both["severe_advice"]


def test_recommend_departure_finds_a_real_improvement_without_new_network_calls(monkeypatch):
    from stormroute.scoring.trip import recommend_departure

    def boom(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("recommend_departure must not touch the network")

    monkeypatch.setattr("stormroute.scoring.trip.fetch_forecast", boom)
    monkeypatch.setattr("stormroute.scoring.trip.fetch_alerts", boom)

    # A one-hour spike right at arrival; dry every other hour, so once the arrival
    # window moves past it, both the peak rate and the 24h trailing sum drop.
    fc = forecast({"37021": {3: 25.0}})
    routes = [route("only", [stretch(at=2, minutes=30.0)])]
    base_scored = [score_route(routes[0], fc, NO_ALERTS, NOW)]
    result = recommend_departure(routes, NOW + timedelta(hours=2), base_scored, fc, NO_ALERTS, NOW)
    assert result is not None
    assert result["index_after"] < result["index_before"]
    assert result["offset_hours"] > 0
    assert "same route" in result["message"]


def test_recommend_departure_none_when_no_offset_helps():
    from stormroute.scoring.trip import recommend_departure

    fc = forecast({"37021": 0.0})
    routes = [route("only", [stretch(at=2, minutes=30.0)])]
    base_scored = [score_route(routes[0], fc, NO_ALERTS, NOW)]
    result = recommend_departure(routes, NOW + timedelta(hours=2), base_scored, fc, NO_ALERTS, NOW)
    assert result is None


def test_recommend_departure_never_trades_a_coverage_gap_for_a_lower_number():
    from stormroute.scoring.trip import recommend_departure

    # Rain is heavy now; forecast simply has no data far enough ahead to score any offset.
    fc = forecast({"37021": {k: 30.0 for k in range(-2, 5)}}, with_gaps=set())
    # Truncate the table so every shifted offset falls outside coverage.
    truncated = ForecastData(
        {"37021": {t: v for t, v in fc.hourly["37021"].items() if t <= "2026-09-27T10:00"}},
        fc.retrieved_utc,
        False,
    )
    routes = [route("only", [stretch(at=2, minutes=30.0)])]
    base_scored = [score_route(routes[0], fc, NO_ALERTS, NOW)]
    result = recommend_departure(
        routes, NOW + timedelta(hours=2), base_scored, truncated, NO_ALERTS, NOW
    )
    assert result is None


def test_geometry_is_attached_when_provided_and_null_otherwise():
    fc = forecast({"37021": 0.0})
    routes = [route("only", [stretch()])]
    with_geo = build_response(
        routes,
        NOW,
        fc,
        NO_ALERTS,
        NOW,
        mode="live",
        geometry={"only": [(-82.0, 35.6), (-81.9, 35.5)]},
    )
    assert with_geo["routes"][0]["geometry"] == [[-82.0, 35.6], [-81.9, 35.5]]

    without_geo = build_response(routes, NOW, fc, NO_ALERTS, NOW, mode="live")
    assert without_geo["routes"][0]["geometry"] is None
