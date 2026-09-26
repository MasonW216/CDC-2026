"""API settings from the environment.

Pydantic settings for the variables in `.env.example`: data directory, model
path, NWS User-Agent, routing base URL, CORS origins, and timeouts.

Settings are never echoed in a response or a log line.
"""

from pathlib import Path

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

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
    model_path: Path = REPO_ROOT / "artifacts" / "models" / "stormroute_model.joblib"
    demo_artifact_paths: list[Path] = Field(default_factory=_demo_artifact_paths)
