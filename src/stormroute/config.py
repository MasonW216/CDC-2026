"""Load and validate the locked YAML configuration.

Single entry point for `configs/data.yaml`, `configs/model.yaml`,
`configs/scoring.yaml`, and `configs/demo.yaml`, plus the environment
variables documented in `.env.example`.

Responsibilities:
  * resolve every path relative to the repository root, never the caller's cwd;
  * parse config into typed objects so a typo fails at startup, not mid-run;
  * expose the active data mode (`full` or `sample`) from STORMROUTE_DATA_MODE.

No module may read a config file directly or hard-code a path that this module
already owns.
"""

# TODO(milestone-0): implement. See docs/build_guide.md.
