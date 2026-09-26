"""Shared fixtures for the test suite.

Provides repository-root and sample-data path fixtures so no test depends on
the directory it was invoked from, and loaders for the tracked fixtures in
`data/sample/`.

Tests must never reach the network. Anything that would is marked
`@pytest.mark.network` and excluded from CI.
"""

from pathlib import Path

import pytest

from stormroute.config import REPO_ROOT


@pytest.fixture(scope="session")
def repo_root() -> Path:
    """Absolute path to the repository root."""
    return REPO_ROOT


@pytest.fixture(scope="session")
def sample_dir(repo_root: Path) -> Path:
    """Directory holding the tracked sample fixtures."""
    return repo_root / "data" / "sample"


@pytest.fixture(scope="session")
def storm_events_sample(sample_dir: Path) -> Path:
    """Path to the NOAA Storm Events details fixture."""
    return sample_dir / "storm_events_sample.csv"
