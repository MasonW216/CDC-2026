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
from stormroute.scoring.trip import TripNotSupportedError, score_trip

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
