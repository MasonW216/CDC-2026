"""Hurricane Helene case study: same rule as live, deterministic, historical inputs only."""

import json

from stormroute.scoring.historical_case_study import helene_case_study


def test_is_severe_on_both_real_routes():
    result = helene_case_study()
    for route in result["routes"]:
        assert route["status"] == "assessed"
        assert route["index"] == 100
        assert route["band"] == "Severe concern"


def test_uses_the_same_schema_and_rule_as_a_live_response():
    result = helene_case_study()
    assert result["schema_version"] == "prototype-score/1"
    assert result["mode"] == "historical_case_study"
    assert "case_study" in result
    assert {"routes", "comparison", "coverage", "alerts", "better_departure", "limitations"} <= (
        result.keys()
    )


def test_never_mixes_into_a_live_response():
    """The live path must not import this module (a docstring cross-reference is fine)."""
    import inspect

    import stormroute.scoring.trip as trip_module

    imported_names = {name for name, value in vars(trip_module).items() if inspect.ismodule(value)}
    assert "historical_case_study" not in imported_names
    for line in inspect.getsource(trip_module).splitlines():
        assert (
            not line.strip().startswith(("import", "from")) or "historical_case_study" not in line
        )


def test_contributing_factors_are_grounded_and_named():
    result = helene_case_study()
    for route in result["routes"]:
        assert route["contributing_factors"]
        for factor in route["contributing_factors"]:
            assert factor["kind"] in ("rain", "alert")
            assert factor["county_name"]


def test_comparison_makes_no_lower_concern_claim_when_both_are_severe():
    result = helene_case_study()
    assert result["comparison"]["ranking"] == "tie"
    assert result["comparison"]["lowest_concern_route_id"] is None
    assert result["comparison"]["severe_advice"]
    assert "safer" not in result["comparison"]["severe_advice"].lower()


def test_is_deterministic():
    first = json.dumps(helene_case_study(), sort_keys=True)
    second = json.dumps(helene_case_study(), sort_keys=True)
    assert first == second


def test_result_never_claims_probability_or_safety():
    text = json.dumps(helene_case_study()).lower()
    for forbidden in ["safe route", "safest", "guaranteed safe", "zero risk", "probability of"]:
        assert forbidden not in text


def test_checked_in_fixture_matches_a_fresh_call():
    from pathlib import Path

    fixture = Path(__file__).resolve().parents[2] / "artifacts/demo/helene_case_study.json"
    if not fixture.exists():
        return
    cached = json.loads(fixture.read_text())
    fresh = json.loads(json.dumps(helene_case_study(), sort_keys=True))
    assert fresh == cached


def test_routes_carry_real_road_geometry():
    result = helene_case_study()
    for route in result["routes"]:
        assert route["geometry"]
        assert len(route["geometry"]) > 100  # a real multi-point road polyline, not a stub
        assert all(len(point) == 2 for point in route["geometry"])
