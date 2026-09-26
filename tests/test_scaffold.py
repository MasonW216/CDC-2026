"""Verify the repository scaffold itself.

The only executable test in the Milestone 0 scaffold. It exists for two
reasons: it satisfies the acceptance criterion that `import stormroute`
succeeds in a fresh environment, and it keeps `pytest` from exiting non-zero on
an empty suite while every other test file is still a stub.

Replace nothing here as later milestones land; extend it instead.
"""

from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]

REQUIRED_DIRECTORIES = [
    "configs",
    "data/sample",
    "docs/adr",
    "notebooks",
    "outputs/figures",
    "outputs/metrics",
    "reports/eda",
    "scripts",
    "src/stormroute",
    "backend/src/stormroute_api",
    "frontend/src",
    "tests",
]

REQUIRED_FILES = [
    ".devcontainer/devcontainer.json",
    ".env.example",
    ".github/workflows/ci.yml",
    ".gitignore",
    "CONTRIBUTING.md",
    "LICENSE",
    "Makefile",
    "README.md",
    "data/data_manifest.yaml",
    "docs/build_guide.md",
    "docs/project_specification.md",
    "pyproject.toml",
]

CONFIG_FILES = ["data.yaml", "model.yaml", "scoring.yaml", "demo.yaml"]


def test_package_imports() -> None:
    import stormroute

    assert stormroute.__doc__, "stormroute must document what it is responsible for"


@pytest.mark.parametrize("relative_path", REQUIRED_DIRECTORIES)
def test_required_directory_exists(relative_path: str) -> None:
    assert (REPO_ROOT / relative_path).is_dir()


@pytest.mark.parametrize("relative_path", REQUIRED_FILES)
def test_required_file_exists(relative_path: str) -> None:
    assert (REPO_ROOT / relative_path).is_file()


@pytest.mark.parametrize("filename", CONFIG_FILES)
def test_config_parses_and_is_versioned(filename: str) -> None:
    config = yaml.safe_load((REPO_ROOT / "configs" / filename).read_text())
    assert isinstance(config, dict)
    assert "version" in config, f"{filename} must declare a version"


def test_data_manifest_lists_the_required_sources() -> None:
    manifest = yaml.safe_load((REPO_ROOT / "data/data_manifest.yaml").read_text())
    names = {dataset["name"] for dataset in manifest["datasets"]}
    assert {
        "noaa_storm_events_details",
        "era5_land_hourly",
        "census_tiger_counties_2024",
        "nws_api",
        "osrm_routing",
    } <= names


def test_locked_hazard_definition() -> None:
    """The three hazards are locked; see docs/adr/0000-specification-precedence.md."""
    data_config = yaml.safe_load((REPO_ROOT / "configs/data.yaml").read_text())
    assert data_config["label"]["hazard_event_types"] == ["Flood", "Flash Flood", "Debris Flow"]


def test_alert_floors_only_raise_risk() -> None:
    """An official alert may never improve a score, so no floor may be negative."""
    scoring = yaml.safe_load((REPO_ROOT / "configs/scoring.yaml").read_text())
    floors = scoring["alerts"]["floors"]
    assert scoring["alerts"]["direction"] == "raise_only"
    assert floors["none"] == 0.0
    assert list(floors.values()) == sorted(floors.values()), "floors must be ordered by severity"


def test_no_env_file_is_tracked() -> None:
    """A committed .env is a leaked secret, not a convenience."""
    assert not (REPO_ROOT / ".env").exists() or (REPO_ROOT / ".gitignore").read_text().count(".env")
