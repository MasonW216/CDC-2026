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

Also mounted, ahead of that list (see routes/geocode.py and routes/routing.py
for why):
    GET  /api/v1/geocode/search
    GET  /api/v1/geocode/reverse
    GET  /api/v1/routing/route
    GET  /api/v1/demo/helene

Run with: make api
"""

from fastapi import FastAPI

from stormroute_api import __version__
from stormroute_api.config import Settings
from stormroute_api.routes import case_study, geocode, health, methodology, routing, score


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build the API with the given settings (read from the environment by default)."""
    app = FastAPI(title="StormRoute API", version=__version__)
    app.state.settings = settings or Settings()
    app.include_router(health.router)
    app.include_router(geocode.router)
    app.include_router(routing.router)
    app.include_router(score.router)
    app.include_router(methodology.router)
    app.include_router(case_study.router)
    return app


app = create_app()

# TODO(milestone-6+): mount /api/v1/scenarios, CORS allowlist, request-ID
# logging, and static frontend. See docs/build_guide.md.
# /api/v1/trips/score and /api/v1/methodology are mounted above.
