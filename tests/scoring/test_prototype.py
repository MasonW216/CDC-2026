"""Prototype indicator: the three cases the team agreed to verify, plus replay rules."""

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from stormroute.scoring.prototype import (
    AlertInput,
    SegmentInput,
    assess_segment,
    assess_trip,
)
from stormroute.scoring.prototype_inputs import build_segments, window_start

DECISION = datetime(2024, 9, 27, 16, 0, tzinfo=UTC)
ARRIVAL = DECISION + timedelta(minutes=30)


def alert(phen="FF", sig="W", known=-60, issued=-60, expires=300) -> AlertInput:
    """An alert with times in minutes relative to the decision time."""
    return AlertInput(
        phenomena=phen,
        significance=sig,
        eventid="GSP-1",
        issued_utc=DECISION + timedelta(minutes=issued),
        expires_utc=DECISION + timedelta(minutes=expires),
        known_utc=DECISION + timedelta(minutes=known),
    )


def seg(p24, p72, alerts=()) -> SegmentInput:
    return SegmentInput("37021", ARRIVAL, window_start(ARRIVAL), p24, p72, tuple(alerts))


def test_missing_rainfall_is_not_assessed_not_low():
    result = assess_segment(seg(None, None), DECISION)
    assert result.level is None
    assert result.label == "Not assessed"
    assert result.data_status == "missing_weather"


def test_missing_rainfall_with_alert_still_raises():
    result = assess_segment(seg(None, None, [alert()]), DECISION)
    assert result.level == 3


def test_partial_rainfall_is_reported_partial():
    assert assess_segment(seg(10.0, None), DECISION).data_status == "partial_weather"


def test_alert_never_lowers_concern():
    for p24, p72 in [(0.0, 0.0), (30.0, 80.0), (120.0, 300.0)]:
        base = assess_segment(seg(p24, p72), DECISION).level
        for phen, sig in [("FA", "A"), ("FA", "Y"), ("FL", "W"), ("FF", "W")]:
            raised = assess_segment(seg(p24, p72, [alert(phen, sig)]), DECISION).level
            assert raised is not None and base is not None and raised >= base


def test_higher_rainfall_never_lowers_concern():
    levels = [assess_segment(seg(p, p * 2.5), DECISION).level for p in range(0, 200, 5)]
    assert levels == sorted(levels)


def test_alert_issued_after_decision_is_not_used():
    late = alert(known=+30, issued=+30)
    assert assess_segment(seg(0.0, 0.0, [late]), DECISION).level == 0


def test_expired_or_not_yet_valid_alert_is_not_used():
    assert assess_segment(seg(0.0, 0.0, [alert(expires=10)]), DECISION).level == 0
    assert assess_segment(seg(0.0, 0.0, [alert(issued=+120)]), DECISION).level == 0


def test_unrecognised_product_is_ignored():
    assert assess_segment(seg(0.0, 0.0, [alert("TO", "W")]), DECISION).level == 0


def test_trip_level_is_highest_segment_and_names_it():
    trip = assess_trip([seg(0.0, 0.0), seg(120.0, 300.0), seg(30.0, 80.0)], DECISION)
    assert trip["trip_level"] == 3
    assert trip["highest_concern_segment"]["precip_24h_mm"] == 120.0


def test_unassessed_segment_does_not_lower_trip_level():
    trip = assess_trip([seg(None, None), seg(60.0, 100.0)], DECISION)
    assert trip["trip_level"] == 2
    assert trip["unassessed_segments"] == ["37021"]


def test_no_data_anywhere_says_not_assessed():
    trip = assess_trip([seg(None, None)], DECISION)
    assert trip["trip_level"] is None
    assert "Not enough data" in trip["advisory"]


def test_language_never_calls_anything_safe():
    trip = assess_trip([seg(0.0, 0.0)], DECISION)
    text = json.dumps(trip).lower()
    assert "safe route" not in text and "safest" not in text and "guaranteed" not in text
    assert trip["trip_label"] == "Lower concern"


def test_repeat_run_is_identical():
    segments = [seg(40.0, 90.0, [alert("FA", "Y")]), seg(120.0, 260.0)]
    first = json.dumps(assess_trip(segments, DECISION), sort_keys=True)
    assert first == json.dumps(assess_trip(segments, DECISION), sort_keys=True)


def test_window_start_floors_to_six_hours():
    assert window_start(datetime(2024, 9, 27, 17, 59, tzinfo=UTC)) == datetime(
        2024, 9, 27, 12, 0, tzinfo=UTC
    )


def test_trailing_rainfall_uses_only_hours_up_to_window_start():
    hours = [
        (datetime(2024, 9, 26, tzinfo=UTC) + timedelta(hours=h)).strftime("%Y-%m-%dT%H:%M")
        for h in range(72)
    ]
    mm = [1.0 if h <= 36 else 100.0 for h in range(72)]  # index 36 = 2024-09-27T12:00
    inputs = {
        "precipitation": {"times_utc": hours, "mm": {"37021": mm}},
        "alerts": {"rows": []},
    }
    stretch = [{"county_fips": "37021", "arrival_utc": "2024-09-27T16:30:00+00:00"}]
    built = build_segments(stretch, inputs)[0]
    assert built.window_start_utc == datetime(2024, 9, 27, 12, 0, tzinfo=UTC)
    assert built.precip_24h_mm == 24.0  # the 100 mm hours after 12:00 are not counted
    assert built.precip_72h_mm is None  # only 72 hours exist and 72 are needed ending at 12:00


def test_cached_result_matches_a_fresh_run():
    root = Path(__file__).resolve().parents[2] / "artifacts" / "demo"
    if not (root / "prototype_result.json").exists():
        return
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "run_prototype", root.parents[1] / "scripts/run_prototype.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    fresh = module.run(
        root / "prototype_routes_provisional.json", root / "prototype_inputs_helene.json"
    )
    cached = json.loads((root / "prototype_result.json").read_text())
    assert json.loads(json.dumps(fresh, sort_keys=True)) == cached


def test_frontend_fixture_is_a_copy_of_the_artifact():
    root = Path(__file__).resolve().parents[2]
    artifact = root / "artifacts" / "demo" / "prototype_result.json"
    fixture = root / "frontend" / "src" / "fixtures" / "prototypeResult.json"
    assert fixture.read_bytes() == artifact.read_bytes()
