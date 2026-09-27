"""Trip scoring endpoint.

    POST /api/v1/trips/score

Body: `TripRequest` (schemas.py). Returns the `prototype-score/1` response from
`stormroute.scoring.trip.score_trip` / `replay_saved_trip`, unchanged: that module is
the single source of truth for the shape, mirrored for the frontend in
`frontend/src/types/score.ts`.

Two modes:
  * `mode: "live"` (default) -- fetch real OSRM alternatives for the submitted origin
    and destination, sample them into county stretches, and score with the live
    forecast and alert adapters. Falls back to the newest cached upstream response
    (`mode: "cached"` in the result) if the network fails.
  * `mode: "cached_replay"` -- ignore the submitted origin/destination and replay the
    saved contemporary trip (`artifacts/demo/saved_trip_request.json`) through this
    same code path and response shape, for the demo fallback. The request's
    `departure_time` is ignored in this mode; the saved trip's own departure is used.

Errors:
  * 422 -- unsupported request (past departure; see `TripNotSupportedError`), or a
    malformed body (handled by Pydantic).
  * 502 -- OSRM could not be reached and there is no cached route to fall back to.

Invalid coordinates or timestamps return 422 with a message that says what to fix,
per this module's original docstring contract.
"""

from __future__ import annotations

import json
from typing import Any

import pandas as pd
from fastapi import APIRouter, HTTPException, Request

from stormroute.config import REPO_ROOT
from stormroute.data.geography import load_sample_counties
from stormroute.routing.client import LatLon, RoutingError, fetch_routes
from stormroute.routing.sampling import sample_route
from stormroute.routing.spatial_join import collapse_intervals
from stormroute.scoring.trip import (
    DEFAULT_CACHE,
    TripNotSupportedError,
    replay_saved_trip,
    routes_from_intervals,
    score_trip,
)
from stormroute_api.config import Settings
from stormroute_api.schemas import TripRequest

router = APIRouter(prefix="/api/v1/trips", tags=["trips"])

SAVED_TRIP = REPO_ROOT / "artifacts" / "demo" / "saved_trip_request.json"


@router.post("/score")
def score(request: Request, body: TripRequest) -> dict[str, Any]:
    """Score every candidate route for the submitted (or saved) trip."""
    if body.mode == "cached_replay":
        return _score_cached_replay()
    return _score_live(request, body)


def _score_cached_replay() -> dict[str, Any]:
    if not SAVED_TRIP.exists():
        raise HTTPException(
            status_code=503,
            detail="No saved demo trip is cached yet. Run scripts/save_live_trip.py once with "
            "network access, or submit mode=live.",
        )
    saved = json.loads(SAVED_TRIP.read_text(encoding="utf-8"))
    return replay_saved_trip(saved)


def _score_live(request: Request, body: TripRequest) -> dict[str, Any]:
    settings: Settings = request.app.state.settings
    origin = LatLon(body.origin.lat, body.origin.lon)
    destination = LatLon(body.destination.lat, body.destination.lon)
    try:
        candidates = fetch_routes(
            origin,
            destination,
            base_url=settings.routing_base_url,
            cache_dir=DEFAULT_CACHE / "routes",
        )
    except RoutingError as error:
        raise HTTPException(status_code=502, detail=f"routing failed: {error}") from error
    if not candidates:
        raise HTTPException(status_code=502, detail="OSRM returned no route between those points")

    counties = load_sample_counties()
    names = dict(zip(counties["county_fips"], counties["name"], strict=True))
    departure = pd.Timestamp(body.departure_time)
    frames = [collapse_intervals(sample_route(c, departure, counties)) for c in candidates]
    intervals = pd.concat(frames, ignore_index=True)
    durations = {c.route_id: c.duration_s / 60 for c in candidates}
    routes = routes_from_intervals(intervals, durations, names)

    try:
        return score_trip(routes, body.departure_time)
    except TripNotSupportedError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
