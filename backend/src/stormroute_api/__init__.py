"""StormRoute HTTP API.

FastAPI service exposing the scoring engine from the `stormroute` package.
This layer owns transport concerns only -- validation, versioning, caching,
errors, and logging. No scoring or modeling logic lives here; duplicating a
formula between this package and `stormroute.scoring` is how the two drift.
"""

# TODO(milestone-6): implement. See docs/build_guide.md.
