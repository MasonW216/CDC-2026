"""Live driving route between two points, for the planner's map preview.

    GET /api/v1/routing/route?origin_lat=&origin_lon=&destination_lat=&destination_lon=

Proxies OSRM so the browser never has to send the User-Agent OSRM's public
server requires -- browser JS is not allowed to set that header itself. Not
part of the locked API surface in docs/build_guide.md section 13; added to
preview an actual driving route on the map. Flagged for the team as a new
endpoint, not a canonical schema change.

Reuses stormroute.routing.client's URL-building and response-parsing (the
OSRM facts documented there), but not `fetch_routes` itself: that function
requires at least `candidate_routes_min` (2) alternatives, a rule for the
scoring pipeline's route comparison, not for a plain "show me a path"
preview. OSRM often has only one reasonable route between two points, and
that is a normal result here, not an error.

The public OSRM demo server is rate limited and must never be a live
dependency during judging (see .env.example): fine for development, but the
staged demo should use a cached replay, not this endpoint.
"""

from __future__ import annotations

import httpx
from fastapi import APIRouter, HTTPException, Query, Request

from stormroute.routing.client import (
    TIMEOUT,
    USER_AGENT,
    LatLon,
    RoutingError,
    build_route_url,
    parse_osrm_response,
)
from stormroute_api.config import Settings

router = APIRouter(prefix="/api/v1/routing", tags=["routing"])


def _get_osrm_response(url: str) -> dict[str, object]:
    """Fetch and JSON-decode one OSRM response. Split out so tests can mock it."""
    try:
        response = httpx.get(url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT)
    except httpx.HTTPError as error:
        raise RoutingError(f"routing request failed: {error}") from error
    if response.status_code != 200:
        raise RoutingError(f"routing request returned HTTP {response.status_code}")
    return response.json()  # type: ignore[no-any-return]


@router.get("/route")
def route(
    request: Request,
    origin_lat: float = Query(ge=-90, le=90),
    origin_lon: float = Query(ge=-180, le=180),
    destination_lat: float = Query(ge=-90, le=90),
    destination_lon: float = Query(ge=-180, le=180),
) -> dict[str, list[dict[str, object]]]:
    """Return every candidate driving route OSRM offers, in OSRM's order."""
    settings: Settings = request.app.state.settings
    url = build_route_url(
        settings.routing_base_url,
        LatLon(lat=origin_lat, lon=origin_lon),
        LatLon(lat=destination_lat, lon=destination_lon),
    )
    try:
        routes = parse_osrm_response(_get_osrm_response(url))
    except RoutingError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
    if not routes:
        raise HTTPException(status_code=502, detail="OSRM returned no route between those points")
    return {
        "routes": [
            {
                "route_id": candidate.route_id,
                # (lon, lat) pairs, matching OSRM/GeoJSON order -- the caller
                # reverses them for Leaflet, which wants (lat, lon).
                "coordinates": [list(point) for point in candidate.coordinates],
                "duration_minutes": round(candidate.duration_s / 60, 1),
                "distance_km": round(candidate.distance_m / 1000, 1),
            }
            for candidate in routes
        ]
    }
