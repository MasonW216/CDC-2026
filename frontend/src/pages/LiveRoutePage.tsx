/**
 * Live route preview: an actual driving path between two arbitrary points,
 * like a Maps app -- not a hazard assessment.
 *
 * Separate from the MVP replay at /results on purpose. That screen shows the
 * prototype hazard indicator over the fixed, cached Hurricane Helene
 * scenario; this one calls the live routing endpoint for whatever origin and
 * destination the user actually types. They don't share a fixture, a
 * contract, or a code path.
 *
 * Calls the public OSRM demo server (through the backend, see
 * routes/routing.py). That server is rate-limited and must never be a live
 * dependency during judging -- this page is for development, not the staged
 * demo.
 */
import { useState } from 'react';

import LiveRouteMap from '@/components/LiveRouteMap';
import TripForm from '@/components/TripForm';
import { ApiError, fetchRoute } from '@/services/api';
import type { Location, TripRequest } from '@/types/trip';

type Status =
  | { kind: 'idle' }
  | { kind: 'loading' }
  | { kind: 'error'; message: string }
  | {
      kind: 'success';
      origin: Location;
      destination: Location;
      path: [number, number][];
      durationMinutes: number;
      distanceKm: number;
    };

export default function LiveRoutePage() {
  const [status, setStatus] = useState<Status>({ kind: 'idle' });

  async function handleSubmit(request: TripRequest) {
    setStatus({ kind: 'loading' });
    try {
      const { routes } = await fetchRoute(request.origin, request.destination);
      const best = routes[0];
      if (!best) {
        setStatus({ kind: 'error', message: 'OSRM returned no route between those points.' });
        return;
      }
      setStatus({
        kind: 'success',
        origin: request.origin,
        destination: request.destination,
        // OSRM/GeoJSON gives (lon, lat); Leaflet wants (lat, lon).
        path: best.coordinates.map(([lon, lat]) => [lat, lon]),
        durationMinutes: best.duration_minutes,
        distanceKm: best.distance_km,
      });
    } catch (error) {
      setStatus({
        kind: 'error',
        message: error instanceof ApiError ? error.message : 'Could not fetch a route.',
      });
    }
  }

  return (
    <section aria-labelledby="live-route-heading">
      <h2 id="live-route-heading" className="page-title">
        Live route preview
      </h2>
      <p role="note" className="note">
        This shows an actual driving route between any two points. It carries no weather-hazard
        assessment of any kind -- for that, see the Hurricane Helene replay on the planner page. It
        calls the public OSRM demo server directly and may be slow, rate-limited, or unavailable; it
        is a development preview, not the staged demo.
      </p>

      <div className="card" style={{ marginTop: 'var(--space-4)' }}>
        <TripForm onSubmit={handleSubmit} />
      </div>

      {status.kind === 'loading' && (
        <p role="status" className="note">
          Fetching the route&hellip;
        </p>
      )}
      {status.kind === 'error' && <p role="alert">{status.message}</p>}
      {status.kind === 'success' && (
        <div className="card">
          <p style={{ fontWeight: 600, marginTop: 0 }}>
            {Math.round(status.distanceKm)} km &middot; {Math.round(status.durationMinutes)} min
          </p>
          <div className="map-card">
            <LiveRouteMap
              origin={status.origin}
              destination={status.destination}
              path={status.path}
            />
          </div>
        </div>
      )}
    </section>
  );
}
