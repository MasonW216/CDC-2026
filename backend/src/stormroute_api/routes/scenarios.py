"""Cached demo scenario endpoints.

    GET /api/v1/scenarios
    GET /api/v1/scenarios/{scenario_id}
Serves frozen scenarios from ``artifacts/demo``. No handler in this module
calls an external service; this is the path that keeps the presentation
working when conference Wi-Fi does not.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml
from fastapi import APIRouter, HTTPException

from stormroute.config import REPO_ROOT

router = APIRouter(prefix="/api/v1/scenarios", tags=["scenarios"])

SCENARIO_CONFIG = REPO_ROOT / "configs" / "demo.yaml"
SCENARIO_ARTIFACTS: dict[str, Path] = {
    "helene_asheville_charlotte": REPO_ROOT / "artifacts" / "demo" / "helene_case_study.json"
}


def _config() -> dict[str, Any]:
    try:
        loaded = yaml.safe_load(SCENARIO_CONFIG.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        raise HTTPException(
            status_code=503, detail=f"Cached scenario configuration is unavailable: {error}"
        ) from error
    if not isinstance(loaded, dict):
        raise HTTPException(status_code=503, detail="Cached scenario configuration is invalid")
    return loaded


def _ready_scenarios(config: dict[str, Any]) -> list[dict[str, str]]:
    scenarios = config.get("scenarios")
    if not isinstance(scenarios, dict):
        raise HTTPException(
            status_code=503, detail="Cached scenario configuration has invalid scenarios mapping"
        )
    summaries = []
    for scenario_id, scenario in scenarios.items():
        if scenario_id not in SCENARIO_ARTIFACTS:
            continue
        if not isinstance(scenario, dict):
            raise HTTPException(
                status_code=503,
                detail=f"Cached scenario {scenario_id} has an invalid summary",
            )
        if scenario.get("status") == "stretch":
            continue
        if any(
            not isinstance(scenario.get(field), str) or not scenario[field].strip()
            for field in ("label", "description", "departure_time")
        ):
            raise HTTPException(
                status_code=503,
                detail=f"Cached scenario {scenario_id} has an invalid summary",
            )
        summaries.append(
            {
                "scenario_id": scenario_id,
                "label": scenario["label"],
                "description": " ".join(scenario["description"].split()),
                "departure_time": scenario["departure_time"],
            }
        )
    return summaries


def _valid_artifact(payload: Any) -> bool:
    return (
        isinstance(payload, dict)
        and payload.get("schema_version") == "prototype-score/1"
        and isinstance(payload.get("mode"), str)
        and bool(payload["mode"].strip())
        and isinstance(payload.get("routes"), list)
        and bool(payload["routes"])
        and all(isinstance(route, dict) and bool(route) for route in payload["routes"])
        and isinstance(payload.get("comparison"), dict)
        and bool(payload["comparison"])
        and isinstance(payload.get("coverage"), dict)
        and bool(payload["coverage"])
        and isinstance(payload.get("alerts"), list)
        and isinstance(payload.get("limitations"), list)
        and bool(payload["limitations"])
        and not payload.get("placeholder")
    )


@router.get("")
def list_scenarios() -> dict[str, Any]:
    """List replay scenarios that have a frozen response artifact."""
    config = _config()
    return {
        "default_scenario": config.get("default_scenario"),
        "scenarios": _ready_scenarios(config),
    }


@router.get("/{scenario_id}")
def get_scenario(scenario_id: str) -> dict[str, Any]:
    """Return one frozen scored response without using the network."""
    artifact = SCENARIO_ARTIFACTS.get(scenario_id)
    if artifact is None:
        raise HTTPException(status_code=404, detail=f"Unknown cached scenario: {scenario_id}")
    try:
        payload = json.loads(artifact.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise HTTPException(
            status_code=503,
            detail=f"Scenario {scenario_id} cached artifact is unavailable",
        ) from error
    if not _valid_artifact(payload):
        raise HTTPException(
            status_code=503, detail=f"Cached scenario {scenario_id} artifact is invalid"
        )
    return {"scenario_id": scenario_id, **payload}
