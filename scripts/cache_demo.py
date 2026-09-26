"""Freeze the offline presentation scenario.

Makefile target : make demo-cache
Milestone       : 5
Reads           : configs/demo.yaml, live routing/weather/alert APIs
Writes          : artifacts/demo/*.json, artifacts/demo/demo_routes.geojson,
                  frontend/src/fixtures/demoScore.json

The only script permitted to depend on a live external API, and the reason the
stage demo does not. Artifacts are checksummed; the expected scores are copied
into docs/demo_runbook.md and must match what the site shows on stage.
"""

# TODO(milestone-5): implement. See docs/build_guide.md.
