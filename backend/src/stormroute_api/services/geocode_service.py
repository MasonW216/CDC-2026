"""Client for OpenRouteService geocoding (search and reverse).

Wraps the ORS-hosted Pelias geocoder. Routing itself uses OSRM (locked by ADR
0001-adjacent decisions in stormroute.routing; unrelated to this). This module
is the only path that turns a typed place name, or a browser's GPS
coordinates, into something the trip planner can use -- there is no geocoder
anywhere else in the plan.

Kept server-side rather than called from the browser: ORS's error responses
have been reported to omit CORS headers, which would surface to users as an
opaque network error instead of the real status, and this keeps the API key
out of the shipped frontend bundle.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import httpx
from pydantic import BaseModel

ORS_BASE_URL = "https://api.openrouteservice.org"
TIMEOUT = httpx.Timeout(5.0, read=8.0)
QueryParams = Mapping[str, str | int | float]


class GeocodeResult(BaseModel):
    """One candidate place: a display label and its coordinates."""

    label: str
    lat: float
    lon: float
    confidence: float


class GeocodeUnavailableError(RuntimeError):
    """The geocoding provider could not be reached or returned an error."""


def _parse(payload: dict[str, Any]) -> list[GeocodeResult]:
    results = []
    for feature in payload.get("features", []):
        lon, lat = feature["geometry"]["coordinates"]
        props = feature.get("properties", {})
        results.append(
            GeocodeResult(
                label=props.get("label") or f"{lat:.4f}, {lon:.4f}",
                lat=lat,
                lon=lon,
                confidence=float(props.get("confidence", 0.0)),
            )
        )
    return results


def _request(
    path: str, params: QueryParams, api_key: str, client: httpx.Client | None
) -> list[GeocodeResult]:
    owned = client is None
    http = client or httpx.Client(timeout=TIMEOUT)
    try:
        response = http.get(
            f"{ORS_BASE_URL}{path}", params=params, headers={"Authorization": api_key}
        )
    except httpx.HTTPError as error:
        raise GeocodeUnavailableError(f"could not reach the geocoding provider: {error}") from error
    finally:
        if owned:
            http.close()
    if response.status_code != 200:
        raise GeocodeUnavailableError(f"geocoding provider returned HTTP {response.status_code}")
    return _parse(response.json())


def search(
    text: str, api_key: str, *, size: int = 5, client: httpx.Client | None = None
) -> list[GeocodeResult]:
    """Forward geocode: a typed place name to candidate locations, biased to the US.

    An unmatched query is a normal empty list, not an error -- Pelias (ORS's
    geocoder) returns HTTP 200 with no features rather than a 404.
    """
    params: QueryParams = {"text": text, "size": size, "boundary.country": "US"}
    return _request("/geocode/search", params, api_key, client)


def reverse(
    lat: float, lon: float, api_key: str, *, client: httpx.Client | None = None
) -> list[GeocodeResult]:
    """Reverse geocode: coordinates (e.g. from the browser) to a display label."""
    params = {"point.lat": lat, "point.lon": lon, "size": 1}
    return _request("/geocode/reverse", params, api_key, client)
