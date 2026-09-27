"""Methodology endpoint: honest content, and no drift from the scoring module."""

from fastapi.testclient import TestClient

from stormroute.scoring.concern import LIMITATIONS, SCHEMA_VERSION
from stormroute_api.main import create_app


def _get() -> dict[str, object]:
    response = TestClient(create_app()).get("/api/v1/methodology")
    assert response.status_code == 200
    return response.json()


def test_returns_the_documented_shape():
    body = _get()
    assert {
        "schema_version",
        "score_name",
        "summary",
        "what_it_is_not",
        "rule_steps",
        "coverage",
        "limitations",
        "spec_document",
    } <= body.keys()


def test_schema_version_and_limitations_match_the_scoring_module():
    body = _get()
    assert body["schema_version"] == SCHEMA_VERSION
    assert body["limitations"] == list(LIMITATIONS)


def test_never_claims_a_probability_or_safety_guarantee():
    body = _get()
    text = " ".join(
        [body["summary"], body["what_it_is_not"], *body["rule_steps"], body["coverage"]]
    ).lower()
    for forbidden in [
        "safe route",
        "safest",
        "guaranteed safe",
        "zero risk",
        "probability of surviving",
        "the model knows",
    ]:
        assert forbidden not in text


def test_states_it_is_not_yet_validated():
    body = _get()
    assert "not yet implemented or validated" in body["what_it_is_not"]
