"""API settings from the environment.

Pydantic settings for the variables in `.env.example`: data directory, model
path, NWS User-Agent, routing base URL, CORS origins, and timeouts.

Settings are never echoed in a response or a log line.
"""

from pathlib import Path
from typing import Annotated

import yaml
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

from stormroute.config import REPO_ROOT

DEMO_CONFIG = REPO_ROOT / "configs" / "demo.yaml"
DEMO_ARTIFACT_KEYS = ("routes", "scores", "weather")


def _demo_artifact_paths() -> list[Path]:
    """Return the cached-replay artifacts listed in configs/demo.yaml.

    An unreadable config yields no paths, which /health reports as the demo
    being unavailable rather than crashing the service at import.
    """
    try:
        artifacts = yaml.safe_load(DEMO_CONFIG.read_text())["artifacts"]
        return [REPO_ROOT / artifacts[key] for key in DEMO_ARTIFACT_KEYS]
    except (OSError, yaml.YAMLError, KeyError, TypeError):
        return []


class Settings(BaseSettings):
    """Runtime configuration, read from STORMROUTE_* environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="STORMROUTE_", env_file=REPO_ROOT / ".env", extra="ignore"
    )

    env: str = "development"
    cors_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://127.0.0.1:5173"]
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]) -> list[str]:
        """Parse env origins and reject wildcard access."""
        if isinstance(value, str):
            value = [origin.strip() for origin in value.split(",") if origin.strip()]
        if any("*" in origin for origin in value):
            raise ValueError("CORS wildcard origins are not allowed")
        return value

    model_path: Path = REPO_ROOT / "artifacts" / "models" / "stormroute_model.joblib"
    demo_artifact_paths: list[Path] = Field(default_factory=_demo_artifact_paths)
    # Unprefixed, like NWS_USER_AGENT and ORS_API_KEY: an external-service
    # setting, not a STORMROUTE_-namespaced one.
    ors_api_key: str | None = Field(default=None, validation_alias="ORS_API_KEY")
    routing_base_url: str = Field(
        default="https://router.project-osrm.org", validation_alias="ROUTING_BASE_URL"
    )
