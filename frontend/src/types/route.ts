/**
 * Shape of `GET /api/v1/routing/route` (backend/src/stormroute_api/routes/routing.py).
 *
 * A live OSRM driving route -- not the prototype hazard indicator
 * (types/prototype.ts) and not the locked score contract (types/trip.ts).
 * This is a preview of the actual path between two points, with no hazard
 * assessment at all.
 */

export interface RouteCandidate {
  route_id: string;
  /** (lon, lat) pairs, OSRM/GeoJSON order. Reverse for Leaflet. */
  coordinates: [number, number][];
  duration_minutes: number;
  distance_km: number;
}

export interface RouteResponse {
  routes: RouteCandidate[];
}
