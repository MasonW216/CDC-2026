"""Fetch candidate route geometry and durations.

Thin OSRM client returning two or three candidate routes with geometry and
travel duration.

Network behavior is the point of failure on stage, so: explicit timeouts, typed
responses, and a cached replay path that needs no network at all. The public
OSRM demo server is rate limited and must never be a live dependency during
judging.

OSRM facts this module relies on (docs/http.md in Project-OSRM/osrm-backend,
checked 2026-09-26):
  * coordinates in the URL and in GeoJSON geometry are `lon,lat`;
  * `alternatives=true` asks for *up to* a few alternatives; the count is not
    guaranteed, so fewer than two routes is reported as an error;
  * with `overview=full`, each leg's `annotation.duration` / `.distance` hold one
    value per edge (coordinates - 1), in seconds and meters;
  * the public server requires an identifying User-Agent, gives no uptime
    guarantee, and uses static road speeds (no live traffic).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx

from stormroute.config import load_config

USER_AGENT = "StormRoute/0.1 (CDC 2026 Datathon prototype)"
TIMEOUT = httpx.Timeout(10.0, read=30.0)

_ROUTING = load_config("scoring")["routing"]
MIN_ROUTES: int = _ROUTING["candidate_routes_min"]
MAX_ROUTES: int = _ROUTING["candidate_routes_max"]


class RoutingError(RuntimeError):
    """Routes could not be obtained or did not meet the routing contract."""


@dataclass(frozen=True)
class LatLon:
    """A point given as latitude, longitude (the order people write them in)."""

    lat: float
    lon: float

    def __post_init__(self) -> None:
        """Reject swapped or out-of-range coordinates."""
        if not -90 <= self.lat <= 90:
            raise ValueError(f"latitude {self.lat} is outside [-90, 90]; were lat/lon swapped?")
        if not -180 <= self.lon <= 180:
            raise ValueError(f"longitude {self.lon} is outside [-180, 180]")


@dataclass(frozen=True)
class CandidateRoute:
    """One candidate route.

    `coordinates` are (lon, lat) pairs. `edge_seconds[i]` and `edge_meters[i]`
    describe the edge from coordinate i to coordinate i + 1.
    """

    route_id: str
    coordinates: tuple[tuple[float, float], ...]
    edge_seconds: tuple[float, ...]
    edge_meters: tuple[float, ...]
    duration_s: float
    distance_m: float


def build_route_url(base_url: str, origin: LatLon, destination: LatLon) -> str:
    """Return the OSRM route request for driving from `origin` to `destination`."""
    points = f"{origin.lon},{origin.lat};{destination.lon},{destination.lat}"
    options = "alternatives=true&overview=full&geometries=geojson&annotations=duration,distance"
    return f"{base_url.rstrip('/')}/route/v1/driving/{points}?{options}"


def _parse_route(index: int, route: dict[str, Any]) -> CandidateRoute:
    coordinates = tuple((float(lon), float(lat)) for lon, lat in route["geometry"]["coordinates"])
    edge_seconds: list[float] = []
    edge_meters: list[float] = []
    for leg in route["legs"]:
        edge_seconds.extend(float(value) for value in leg["annotation"]["duration"])
        edge_meters.extend(float(value) for value in leg["annotation"]["distance"])
    if not len(edge_seconds) == len(edge_meters) == len(coordinates) - 1:
        raise RoutingError(
            f"route {index}: {len(coordinates)} coordinates but {len(edge_seconds)} duration and "
            f"{len(edge_meters)} distance annotation values (expected coordinates - 1). "
            "Was the request made with overview=full?"
        )
    return CandidateRoute(
        route_id=f"route_{index}",
        coordinates=coordinates,
        edge_seconds=tuple(edge_seconds),
        edge_meters=tuple(edge_meters),
        duration_s=float(route["duration"]),
        distance_m=float(route["distance"]),
    )


def parse_osrm_response(payload: dict[str, Any]) -> list[CandidateRoute]:
    """Turn an OSRM `route` response into candidate routes, in OSRM's order."""
    code = payload.get("code")
    if code != "Ok":
        raise RoutingError(f"OSRM returned {code}: {payload.get('message', 'no message')}")
    return [_parse_route(i, route) for i, route in enumerate(payload.get("routes", []))]


def _cache_path(cache_dir: Path, url: str) -> Path:
    """Key the cache on the trip and options, not the server.

    A replay then survives a change of ROUTING_BASE_URL.
    """
    trip = url.split("/route/v1/", 1)[1]
    key = hashlib.sha256(trip.encode()).hexdigest()[:16]
    return cache_dir / f"osrm_{key}.json"


def fetch_routes(
    origin: LatLon,
    destination: LatLon,
    *,
    base_url: str,
    cache_dir: Path,
    offline: bool = False,
    client: httpx.Client | None = None,
) -> list[CandidateRoute]:
    """Return 2-3 candidate routes, from the cache when present.

    A response is cached as raw JSON before parsing, so a replay reproduces the
    exact routes. With `offline=True` only the cache is read; a miss is an error,
    never a silent network call.

    Raises:
        RoutingError: on a cache miss offline, a network or HTTP failure, a
            non-Ok OSRM response, or fewer than two routes.
    """
    url = build_route_url(base_url, origin, destination)
    cached = _cache_path(cache_dir, url)
    if cached.exists():
        payload = json.loads(cached.read_text(encoding="utf-8"))
    elif offline:
        raise RoutingError(f"offline mode and no cached route for {url} (expected {cached})")
    else:
        owned = client is None
        http = client or httpx.Client(timeout=TIMEOUT)
        try:
            response = http.get(url, headers={"User-Agent": USER_AGENT})
        except httpx.HTTPError as error:
            raise RoutingError(f"routing request failed: {error}") from error
        finally:
            if owned:
                http.close()
        if response.status_code != 200:
            try:
                parse_osrm_response(response.json())  # OSRM explains 400s in `code`
            except ValueError:
                pass
            raise RoutingError(f"routing request returned HTTP {response.status_code}")
        payload = response.json()
        parse_osrm_response(payload)  # never cache a response that does not parse
        cache_dir.mkdir(parents=True, exist_ok=True)
        cached.write_text(json.dumps(payload), encoding="utf-8")

    routes = parse_osrm_response(payload)
    if len(routes) < MIN_ROUTES:
        raise RoutingError(
            f"OSRM returned {len(routes)} route(s); at least {MIN_ROUTES} candidates are required"
        )
    return routes[:MAX_ROUTES]
