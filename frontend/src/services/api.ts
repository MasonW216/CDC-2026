/**
 * Typed client for the StormRoute API.
 *
 * Wraps fetch against VITE_API_BASE_URL with explicit timeouts and typed errors.
 *
 * Implemented so far: geocoding (place search and reverse lookup for the
 * planner page), the live routing preview, and trip scoring.
 */

import type { RouteResponse } from '@/types/route';
import type { ScoreResponse } from '@/types/score';
import type { Location, TripRequest } from '@/types/trip';

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '';
const TIMEOUT_MS = 8000;

export class ApiError extends Error {
  status: number | null;

  constructor(message: string, status: number | null) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

export interface GeocodeResult {
  label: string;
  lat: number;
  lon: number;
  confidence: number;
}

async function get<T>(path: string, params: Record<string, string>): Promise<T> {
  const url = `${BASE_URL}${path}?${new URLSearchParams(params)}`;
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), TIMEOUT_MS);
  let response: Response;
  try {
    response = await fetch(url, { signal: controller.signal });
  } catch (error) {
    throw new ApiError(
      error instanceof Error ? error.message : 'Could not reach the StormRoute API.',
      null,
    );
  } finally {
    clearTimeout(timeout);
  }
  const body: unknown = await response.json().catch(() => null);
  if (!response.ok) {
    const detail =
      body && typeof body === 'object' && 'detail' in body
        ? String(body.detail)
        : response.statusText;
    throw new ApiError(detail, response.status);
  }
  return body as T;
}

async function post<T>(path: string, body: unknown, timeoutMs: number): Promise<T> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  let response: Response;
  try {
    response = await fetch(`${BASE_URL}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal: controller.signal,
    });
  } catch (error) {
    throw new ApiError(
      error instanceof Error ? error.message : 'Could not reach the StormRoute API.',
      null,
    );
  } finally {
    clearTimeout(timeout);
  }
  const responseBody: unknown = await response.json().catch(() => null);
  if (!response.ok) {
    const detail =
      responseBody && typeof responseBody === 'object' && 'detail' in responseBody
        ? String(responseBody.detail)
        : response.statusText;
    throw new ApiError(detail, response.status);
  }
  return responseBody as T;
}

/** Forward geocode: a typed place name to candidate locations. Empty array on no match. */
export function geocodeSearch(text: string): Promise<GeocodeResult[]> {
  return get<{ results: GeocodeResult[] }>('/api/v1/geocode/search', { text }).then(
    (r) => r.results,
  );
}

/** Reverse geocode: coordinates (e.g. the browser's GPS location) to a display label. */
export function geocodeReverse(lat: number, lon: number): Promise<GeocodeResult[]> {
  return get<{ results: GeocodeResult[] }>('/api/v1/geocode/reverse', {
    lat: String(lat),
    lon: String(lon),
  }).then((r) => r.results);
}

/**
 * Live driving route between two points (GET /api/v1/routing/route).
 *
 * A route preview, not a hazard assessment -- see types/route.ts. Calls the
 * public OSRM demo server through the backend; expect it to be slow or
 * unavailable if it's rate-limited, and never rely on it during a live demo.
 */
export function fetchRoute(origin: Location, destination: Location): Promise<RouteResponse> {
  return get<RouteResponse>('/api/v1/routing/route', {
    origin_lat: String(origin.lat),
    origin_lon: String(origin.lon),
    destination_lat: String(destination.lat),
    destination_lon: String(destination.lon),
  });
}

/**
 * Score a trip (POST /api/v1/trips/score): the prototype hazard indicator,
 * live or replayed. See types/score.ts for the `prototype-score/1` contract.
 *
 * `mode: 'live'` chains real OSRM + Open-Meteo + NWS calls, so this gets a
 * longer timeout than a single geocode/routing request.
 */
export function scoreTrip(request: TripRequest): Promise<ScoreResponse> {
  return post<ScoreResponse>('/api/v1/trips/score', request, 20000);
}
