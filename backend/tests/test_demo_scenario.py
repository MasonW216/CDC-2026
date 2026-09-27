"""Cached scenario endpoints stay complete without external services."""

import json
from pathlib import Path
from typing import Never

import pytest
from fastapi.testclient import TestClient

from stormroute.config import REPO_ROOT
from stormroute_api.main import create_app


def test_lists_only_ready_cached_scenarios():
    response = TestClient(create_app()).get("/api/v1/scenarios")

    assert response.status_code == 200
    assert response.json() == {
        "default_scenario": "helene_asheville_charlotte",
        "scenarios": [
            {
                "scenario_id": "helene_asheville_charlotte",
                "label": "Hurricane Helene replay — Asheville to Charlotte",
                "description": (
                    "A westbound-to-Piedmont trip during the September 2024 Helene "
                    "period, when flood-hazard exposure varied sharply by departure time."
                ),
                "departure_time": "2024-09-27T12:00:00-04:00",
            }
        ],
    }


def test_returns_frozen_scenario_without_calling_network(monkeypatch):
    def network_must_not_run(*args: object, **kwargs: object) -> Never:
        raise AssertionError("cached scenario attempted network access")

    monkeypatch.setattr("httpx.get", network_must_not_run)
    response = TestClient(create_app()).get("/api/v1/scenarios/helene_asheville_charlotte")

    assert response.status_code == 200
    body = response.json()
    assert body["scenario_id"] == "helene_asheville_charlotte"
    assert body["schema_version"] == "prototype-score/1"
    assert body["mode"] == "historical_case_study"
    assert body["routes"]
    assert isinstance(body["comparison"], dict)
    assert isinstance(body["coverage"], dict)
    assert isinstance(body["alerts"], list)
    assert isinstance(body["limitations"], list)
    assert body["case_study"]["name"] == "Hurricane Helene"


def test_unknown_scenario_returns_helpful_404():
    response = TestClient(create_app()).get("/api/v1/scenarios/not-a-scenario")

    assert response.status_code == 404
    assert response.json()["detail"] == "Unknown cached scenario: not-a-scenario"


def test_missing_frozen_artifact_returns_503(monkeypatch, tmp_path: Path):
    missing = tmp_path / "missing.json"
    monkeypatch.setattr(
        "stormroute_api.routes.scenarios.SCENARIO_ARTIFACTS",
        {"helene_asheville_charlotte": missing},
    )

    response = TestClient(create_app()).get("/api/v1/scenarios/helene_asheville_charlotte")

    assert response.status_code == 503
    assert "cached artifact is unavailable" in response.json()["detail"]


@pytest.mark.parametrize("scenarios", [None, [], "invalid"])
def test_invalid_scenarios_mapping_returns_helpful_503(monkeypatch, tmp_path: Path, scenarios):
    config = tmp_path / "demo.yaml"
    config.write_text(f"scenarios: {json.dumps(scenarios)}\n", encoding="utf-8")
    monkeypatch.setattr("stormroute_api.routes.scenarios.SCENARIO_CONFIG", config)

    response = TestClient(create_app()).get("/api/v1/scenarios")

    assert response.status_code == 503
    assert "scenarios" in response.json()["detail"]


@pytest.mark.parametrize(
    "scenario",
    [
        None,
        [],
        {},
        {"label": "Replay", "description": "Details"},
        {"label": "Replay", "departure_time": "2024-09-27T12:00:00-04:00"},
        {"description": "Details", "departure_time": "2024-09-27T12:00:00-04:00"},
    ],
)
def test_invalid_ready_scenario_summary_returns_helpful_503(monkeypatch, tmp_path: Path, scenario):
    config = tmp_path / "demo.yaml"
    config.write_text(
        "scenarios:\n  helene_asheville_charlotte: " + json.dumps(scenario) + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr("stormroute_api.routes.scenarios.SCENARIO_CONFIG", config)

    response = TestClient(create_app()).get("/api/v1/scenarios")

    assert response.status_code == 503
    assert "helene_asheville_charlotte" in response.json()["detail"]
    assert "summary" in response.json()["detail"]


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"placeholder": True},
        {"schema_version": "prototype-score/1", "mode": "historical_case_study"},
        {
            "schema_version": "wrong-version",
            "mode": "historical_case_study",
            "routes": [{}],
            "comparison": {},
            "coverage": {},
            "alerts": [],
            "limitations": [],
        },
        {
            "schema_version": "prototype-score/1",
            "mode": "historical_case_study",
            "routes": [],
            "comparison": {},
            "coverage": {},
            "alerts": [],
            "limitations": [],
        },
    ],
)
def test_incomplete_frozen_artifact_returns_helpful_503(monkeypatch, tmp_path: Path, payload):
    artifact = tmp_path / "scenario.json"
    artifact.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setattr(
        "stormroute_api.routes.scenarios.SCENARIO_ARTIFACTS",
        {"helene_asheville_charlotte": artifact},
    )

    response = TestClient(create_app()).get("/api/v1/scenarios/helene_asheville_charlotte")

    assert response.status_code == 503
    assert "artifact is invalid" in response.json()["detail"]


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("routes", [{}]),
        ("comparison", None),
        ("coverage", []),
        ("alerts", None),
        ("limitations", None),
        ("placeholder", True),
    ],
)
def test_malformed_contract_field_returns_503(monkeypatch, tmp_path: Path, field, value):
    source = REPO_ROOT / "artifacts" / "demo" / "helene_case_study.json"
    payload = json.loads(source.read_text(encoding="utf-8"))
    payload[field] = value
    artifact = tmp_path / "scenario.json"
    artifact.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setattr(
        "stormroute_api.routes.scenarios.SCENARIO_ARTIFACTS",
        {"helene_asheville_charlotte": artifact},
    )

    response = TestClient(create_app()).get("/api/v1/scenarios/helene_asheville_charlotte")

    assert response.status_code == 503
    assert "artifact is invalid" in response.json()["detail"]
