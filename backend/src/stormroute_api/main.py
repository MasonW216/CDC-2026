"""Application entry point and router registration.

Creates the FastAPI app, mounts the versioned routers, configures CORS against
an explicit origin allowlist (never `*`), installs request-ID logging, and
serves the built frontend as static files so the prototype deploys as one
service behind one URL.

Planned routes:
    GET  /health
    GET  /api/v1/scenarios
    GET  /api/v1/scenarios/{scenario_id}
    POST /api/v1/trips/score
    GET  /api/v1/methodology

Run with: make api
"""

# TODO(milestone-6): implement. See docs/build_guide.md.
