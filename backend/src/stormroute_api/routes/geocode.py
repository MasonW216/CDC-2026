"""Place search and reverse lookup for the trip planner.

    GET /api/v1/geocode/search?text=...
    GET /api/v1/geocode/reverse?lat=...&lon=...

Proxies OpenRouteService's geocoder so the API key never reaches the browser
(see services/geocode_service.py). Not part of the locked API surface in
docs/build_guide.md section 13 -- added to fill a real gap, since nothing in
the plan turns a typed destination into coordinates. Flagged for the team as
a new endpoint, not a canonical schema change.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Request

from stormroute_api.config import Settings
from stormroute_api.services import geocode_service

router = APIRouter(prefix="/api/v1/geocode", tags=["geocode"])


def _api_key(request: Request) -> str:
    settings: Settings = request.app.state.settings
    if not settings.ors_api_key:
        raise HTTPException(
            status_code=503,
            detail="Geocoding is not configured: set ORS_API_KEY in .env (see .env.example).",
        )
    return settings.ors_api_key


@router.get("/search")
def search(request: Request, text: str = Query(min_length=1)) -> dict[str, list[dict[str, object]]]:
    """Look up candidate places for a typed query."""
    try:
        results = geocode_service.search(text, _api_key(request))
    except geocode_service.GeocodeUnavailableError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
    return {"results": [result.model_dump() for result in results]}


@router.get("/reverse")
def reverse(
    request: Request, lat: float = Query(ge=-90, le=90), lon: float = Query(ge=-180, le=180)
) -> dict[str, list[dict[str, object]]]:
    """Look up a display label for coordinates (e.g. the browser's GPS location)."""
    try:
        results = geocode_service.reverse(lat, lon, _api_key(request))
    except geocode_service.GeocodeUnavailableError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
    return {"results": [result.model_dump() for result in results]}
