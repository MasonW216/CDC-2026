"""Liveness and readiness endpoint.

    GET /health

Reports service status plus whether the model artifact and the cached demo
assets are actually present. A health check that returns 200 while the demo
assets are missing would hide the exact failure this endpoint exists to catch.
"""

import json
from pathlib import Path

from fastapi import APIRouter, Request
from pydantic import BaseModel

from stormroute.config import resolve_path
from stormroute_api import __version__
from stormroute_api.config import Settings

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    """Service status and artifact availability."""

    status: str
    version: str
    model_available: bool
    demo_available: bool


def _is_real_artifact(path: Path) -> bool:
    """Return True if a demo artifact exists and is not the scaffold placeholder.

    The scaffold commits placeholder files marked ``"placeholder": true`` until
    ``make demo-cache`` replaces them.
    """
    if not path.is_file():
        return False
    try:
        content = json.loads(path.read_text())
    except (OSError, ValueError):
        return False
    if not isinstance(content, dict):
        return True
    return content.get("placeholder") is not True


@router.get("/health")
def health(request: Request) -> HealthResponse:
    """Report liveness and whether the model and demo artifacts exist."""
    settings: Settings = request.app.state.settings
    return HealthResponse(
        status="ok",
        version=__version__,
        model_available=resolve_path(settings.model_path).is_file(),
        demo_available=bool(settings.demo_artifact_paths)
        and all(_is_real_artifact(resolve_path(path)) for path in settings.demo_artifact_paths),
    )
