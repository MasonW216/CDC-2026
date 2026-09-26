"""Load the locked YAML configuration and resolve repository paths.

Single entry point for `configs/data.yaml`, `configs/model.yaml`,
`configs/scoring.yaml`, and `configs/demo.yaml`, plus the environment
variables documented in `.env.example`.

Responsibilities:
  * resolve every path relative to the repository root, never the caller's cwd;
  * load each config file once and hand out the parsed mapping;
  * expose the active data mode (`full` or `sample`) from STORMROUTE_DATA_MODE.

No module may read a config file directly or hard-code a path that this module
already owns.

Implemented so far: the minimum Milestone 1 needs. Typed config objects can
replace the plain mappings once more modules depend on them.
"""

from __future__ import annotations

import os
from functools import cache
from pathlib import Path
from typing import Any, Literal

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]

ConfigName = Literal["data", "model", "scoring", "demo"]
DataMode = Literal["full", "sample"]

DATA_MODE_ENV_VAR = "STORMROUTE_DATA_MODE"


@cache
def load_config(name: ConfigName) -> dict[str, Any]:
    """Return the parsed contents of `configs/<name>.yaml`.

    Cached: every caller sees the same mapping, so treat it as read-only.
    """
    path = REPO_ROOT / "configs" / f"{name}.yaml"
    with path.open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    if not isinstance(config, dict):
        raise ValueError(f"{path} must contain a mapping at the top level")
    return config


def resolve_path(path: str | Path) -> Path:
    """Resolve a config-style path against the repository root.

    Absolute paths are returned unchanged, so tests can point at a temporary
    directory.
    """
    candidate = Path(path)
    return candidate if candidate.is_absolute() else REPO_ROOT / candidate


def data_path(key: str) -> Path:
    """Resolve a named entry from the `paths` section of `configs/data.yaml`."""
    paths: dict[str, str] = load_config("data")["paths"]
    if key not in paths:
        raise KeyError(f"No path named {key!r} in configs/data.yaml; known: {sorted(paths)}")
    return resolve_path(paths[key])


def data_mode() -> DataMode:
    """Return `sample` or `full`, from the environment or the config default."""
    modes = load_config("data")["modes"]
    mode = os.environ.get(DATA_MODE_ENV_VAR, modes["default"])
    if mode not in modes["allowed"]:
        raise ValueError(f"{DATA_MODE_ENV_VAR}={mode!r} is not one of {modes['allowed']}")
    return "sample" if mode == "sample" else "full"
