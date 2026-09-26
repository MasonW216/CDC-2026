"""API settings from the environment.

Pydantic settings for the variables in `.env.example`: data directory, model
path, NWS User-Agent, routing base URL, CORS origins, and timeouts.

Settings are never echoed in a response or a log line.
"""

from pathlib import Path

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]
DEMO_CONFIG = REPO_ROOT / "configs" / "demo.yaml"
DEMO_ARTIFACT_KEYS = ("routes", "scores", "weather")


def _demo_artifact_paths() -> list[Path]:
    """Return the cached-replay artifacts listed in configs/demo.yaml."""
    artifacts = yaml.safe_load(DEMO_CONFIG.read_text())["artifacts"]
    return [REPO_ROOT / artifacts[key] for key in DEMO_ARTIFACT_KEYS]


class Settings(BaseSettings):
    """Runtime configuration, read from STORMROUTE_* environment variables."""

    model_config = SettingsConfigDict(env_prefix="STORMROUTE_", extra="ignore")

    env: str = "development"
    model_path: Path = REPO_ROOT / "artifacts" / "models" / "stormroute_model.joblib"
    demo_artifact_paths: list[Path] = Field(default_factory=_demo_artifact_paths)

    def resolve(self, path: Path) -> Path:
        """Resolve a configured path against the repository root."""
        return path if path.is_absolute() else REPO_ROOT / path
