"""Hurricane Helene case study: same rule as live, deterministic, historical inputs only."""

import json

from stormroute.scoring.historical_case_study import helene_case_study


def test_two_real_routes_show_genuinely_different_concern():
    """The two real OSRM alternates (Charlotte-Wilkesboro) pass through disjoint counties.

    Genuinely different real Helene exposure -- not a tie, and not fabricated: a real Wilkes
    County Flood Advisory had escalated to a Flood Warning by the time the longer, slower
    route arrives there, while the faster route arrives before that escalation.
    """
    result = helene_case_study()
    for route in result["routes"]:
        assert route["status"] == "assessed"
    indexes = {route["route_id"]: route["index"] for route in result["routes"]}
    assert len(set(indexes.values())) > 1, "expected the two real routes to actually differ"
    bands = {route["route_id"]: route["band"] for route in result["routes"]}
    assert "Severe concern" in bands.values()
    assert "High concern" in bands.values()


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
            assert factor["kind"] in ("rain", "alert", "historical")
            assert factor["county_name"]


def test_comparison_names_the_real_lower_concern_route():
    """The comparison must name the real lower-concern route, not claim a false tie.

    This scenario was chosen because the two real routes genuinely differ (see
    test_two_real_routes_show_genuinely_different_concern), and must never call the lower
    one "safe" even though it is genuinely lower-concern than the other.
    """
    result = helene_case_study()
    assert result["comparison"]["ranking"] == "distinguishable"
    assert result["comparison"]["lowest_concern_route_id"] is not None
    text = json.dumps(result["comparison"]).lower()
    for forbidden in ("safe", "safest", "guaranteed"):
        assert forbidden not in text


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


def test_county_risk_covers_every_county_not_just_the_routes():
    """Real visual justification: the whole surrounding region shows the same real pattern.

    Not just the sampled route stretches: the far-western counties (the true disaster
    core, off both routes) score Severe.
    """
    result = helene_case_study()
    risk = result["case_study"]["county_risk"]
    assert len(risk) == 100
    for fips, entry in risk.items():
        assert fips == "37" + fips[2:]
        assert entry["county_name"]
        assert entry["band"] in (
            "Lower concern",
            "Elevated concern",
            "High concern",
            "Severe concern",
            "Not assessed",
        )

    # A county far off both routes, at the real disaster's core.
    swain = next(v for v in risk.values() if v["county_name"] == "Swain")
    assert swain["band"] == "Severe concern"

    # The shared origin (Mecklenburg, both routes' first stretch, arriving exactly at
    # departure) must match its own route segment exactly -- county_risk uses the same
    # score_segment rule, just evaluated at the case study's single departure instant
    # rather than each route's own later arrival time at a county further along.
    mecklenburg_fips = next(fips for fips, v in risk.items() if v["county_name"] == "Mecklenburg")
    for route in result["routes"]:
        first_segment = route["segments"][0]
        assert first_segment["county_fips"] == mecklenburg_fips
        assert risk[mecklenburg_fips]["index"] == first_segment["index"]


def test_county_risk_is_never_used_to_score_a_route():
    """Statewide context only -- it must never leak into a route's own index."""
    import inspect

    from stormroute.scoring import trip as trip_module

    assert "county_risk" not in inspect.getsource(trip_module)
