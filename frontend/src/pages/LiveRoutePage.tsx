/**
 * Live route preview: a full map view, like a maps app, with the prototype
 * hazard indicator layered on top.
 *
 * Separate from the MVP replay at /results on purpose. That screen is a
 * table-first, offline-safe report for the cached Hurricane Helene scenario;
 * this one calls two live endpoints for whatever origin, destination, and
 * departure time the user actually types:
 *
 *   - GET  /api/v1/routing/route  -- real OSRM path geometry, to draw
 *   - POST /api/v1/trips/score    -- the real 0-100 concern index per route
 *
 * Neither endpoint alone has both a path to draw and a score to color it by,
 * so this page calls both and matches routes by `route_id`. That match
 * assumes both calls return OSRM's alternatives in the same order for the
 * same coordinates -- true in practice (no live traffic, no randomness in
 * OSRM's routing), but not a guarantee, so a route missing its match still
 * renders, just uncolored (see FALLBACK_COLOR).
 *
 * Coloring is never invented: a route is only drawn green (lower concern)
 * when the score response's own comparison says so (`ranking:
 * 'distinguishable'`). On a tie or missing data, every route gets the same
 * neutral color -- exactly the "do not invent a trade-off" rule already
 * enforced in PrototypeResultsPage.
 *
 * Calls the public OSRM demo server (through the backend). That server is
 * rate-limited and must never be a live dependency during judging -- this
 * page is for development, not the staged demo.
 */
import { useState } from 'react';

import LiveRouteMap, { type RouteRender } from '@/components/LiveRouteMap';
import TripForm from '@/components/TripForm';
import { ApiError, fetchRoute, scoreTrip } from '@/services/api';
import type { RouteScore, ScoreResponse } from '@/types/score';
import type { Location, TripRequest } from '@/types/trip';
import { splitRouteAtSegment } from '@/utils/routeSegments';

function formatInstant(iso: string): string {
  return `${new Intl.DateTimeFormat('en-US', {
    timeZone: 'UTC',
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(iso))} UTC`;
}

const LOWER_CONCERN_COLOR = 'var(--level-0-fg, #157347)';
const HIGHER_CONCERN_COLOR = 'var(--level-3-fg, #b3261e)';
const NEUTRAL_COLOR = 'var(--color-primary, #0f766e)';

type Status =
  | { kind: 'idle' }
  | { kind: 'loading' }
  | { kind: 'error'; message: string }
  | {
      kind: 'success';
      origin: Location;
      destination: Location;
      routes: RouteRender[];
      score: ScoreResponse;
      dangerMarker: { position: [number, number]; label: string } | null;
    };

function routeColor(route: RouteScore, comparison: ScoreResponse['comparison']): string {
  if (comparison.ranking !== 'distinguishable' || !comparison.lowest_concern_route_id) {
    return NEUTRAL_COLOR;
  }
  return route.route_id === comparison.lowest_concern_route_id
    ? LOWER_CONCERN_COLOR
    : HIGHER_CONCERN_COLOR;
}

function bandColorVar(band: string): string {
  const level: Record<string, 0 | 1 | 2 | 3> = {
    'Lower concern': 0,
    'Elevated concern': 1,
    'High concern': 2,
    'Severe concern': 3,
  };
  return `var(--level-${level[band] ?? 'none'}-fg)`;
}

export default function LiveRoutePage() {
  const [status, setStatus] = useState<Status>({ kind: 'idle' });

  async function handleSubmit(request: TripRequest) {
    setStatus({ kind: 'loading' });
    try {
      const [routeResponse, score] = await Promise.all([
        fetchRoute(request.origin, request.destination),
        scoreTrip({ ...request, mode: 'live' }),
      ]);
      const scoreByRouteId = new Map(score.routes.map((route) => [route.route_id, route]));
      let dangerMarker: { position: [number, number]; label: string } | null = null;
      const routes: RouteRender[] = routeResponse.routes.map((candidate) => {
        const matched = scoreByRouteId.get(candidate.route_id);
        // OSRM/GeoJSON gives (lon, lat); Leaflet wants (lat, lon).
        const path: [number, number][] = candidate.coordinates.map(([lon, lat]) => [lat, lon]);
        const isRecommended = matched?.route_id === score.comparison.lowest_concern_route_id;

        let highlight: RouteRender['highlight'] = null;
        if (matched?.highest_concern_segment) {
          const segIndex = matched.segments.findIndex(
            (s) =>
              s.county_fips === matched.highest_concern_segment!.county_fips &&
              s.arrival_utc === matched.highest_concern_segment!.arrival_utc,
          );
          if (segIndex >= 0) {
            highlight = {
              segmentKm: matched.segments.map((s) => s.km),
              index: segIndex,
              color: bandColorVar(matched.highest_concern_segment.band),
            };
            // Only surface one marker on the map: the recommended route's own
            // worst stretch (or, on a tie/single route, whichever we show).
            if (
              !dangerMarker &&
              (isRecommended || score.comparison.ranking !== 'distinguishable')
            ) {
              const { highlighted } = splitRouteAtSegment(path, highlight.segmentKm, segIndex);
              const mid = highlighted[Math.floor(highlighted.length / 2)];
              if (mid) {
                dangerMarker = {
                  position: mid,
                  label: `${matched.highest_concern_segment.county_name} · ${formatInstant(
                    matched.highest_concern_segment.arrival_utc,
                  )}`,
                };
              }
            }
          }
        }

        return {
          id: candidate.route_id,
          path,
          color: matched ? routeColor(matched, score.comparison) : NEUTRAL_COLOR,
          weight: isRecommended ? 5 : 4,
          highlight,
        };
      });
      if (routes.length === 0) {
        setStatus({ kind: 'error', message: 'No route was returned between those points.' });
        return;
      }
      setStatus({
        kind: 'success',
        origin: request.origin,
        destination: request.destination,
        routes,
        score,
        dangerMarker,
      });
    } catch (error) {
      setStatus({
        kind: 'error',
        message: error instanceof ApiError ? error.message : 'Could not fetch or score a route.',
      });
    }
  }

  return (
    <section aria-labelledby="live-route-heading" className="map-page-section">
      <h2 id="live-route-heading" className="page-title">
        Live route preview
      </h2>
      <p role="note" className="note">
        A real driving path between any two points, colored by the prototype hazard indicator. Not a
        live forecast, a trained model, or a guarantee of safety -- and never rely on this page for
        the staged demo, since it calls the rate-limited public OSRM server directly.
      </p>

      <div className="map-page">
        <div className="search-bar">
          <TripForm onSubmit={handleSubmit} />
        </div>

        <div className="map-view">
          {status.kind === 'success' && (
            <LiveRouteMap
              origin={status.origin}
              destination={status.destination}
              routes={status.routes}
              dangerMarker={status.dangerMarker}
            />
          )}

          {status.kind === 'success' && (
            <>
              <div className="map-view__overlay ai-badge">
                <div className="ai-badge__card">
                  {/* A weather glyph, not "AI": this is a threshold rule, not a
                      trained model -- see the disclaimer above. Labeling this
                      tag "AI" would contradict that on the same screen. */}
                  <div className="ai-badge__orb" aria-hidden="true">
                    ⛈
                  </div>
                  <div className="ai-badge__body">
                    <h4>Prototype hazard scores</h4>
                    {status.score.routes.map((route, index) => (
                      <p key={route.route_id} className="ai-badge__route-line">
                        <span
                          className="ai-badge__swatch"
                          style={{
                            background: routeColor(route, status.score.comparison),
                          }}
                          aria-hidden="true"
                        />
                        Route {index + 1}: {route.band}
                        {route.index !== null ? ` (${Math.round(route.index)}/100)` : ''}
                      </p>
                    ))}
                    <details>
                      <summary>Show details</summary>
                      <p>{status.score.comparison.message}</p>
                      {status.score.comparison.severe_advice && (
                        <p>{status.score.comparison.severe_advice}</p>
                      )}
                    </details>
                  </div>
                </div>
              </div>

              <div className="map-view__overlay map-legend" aria-label="Route color legend">
                {status.score.comparison.ranking === 'distinguishable' ? (
                  <>
                    <div className="map-legend__row">
                      <span
                        className="map-legend__swatch"
                        style={{ background: LOWER_CONCERN_COLOR }}
                        aria-hidden="true"
                      />
                      <span>
                        <strong>Lower modeled weather risk</strong>
                        <span>The route this index favors, on this trip.</span>
                      </span>
                    </div>
                    <div className="map-legend__row">
                      <span
                        className="map-legend__swatch"
                        style={{ background: HIGHER_CONCERN_COLOR }}
                        aria-hidden="true"
                      />
                      <span>
                        <strong>Higher modeled weather risk</strong>
                        <span>An alternative with a higher indicated index.</span>
                      </span>
                    </div>
                  </>
                ) : (
                  <div className="map-legend__row">
                    <span
                      className="map-legend__swatch"
                      style={{ background: NEUTRAL_COLOR }}
                      aria-hidden="true"
                    />
                    <span>
                      <strong>Similar modeled weather risk</strong>
                      <span>{status.score.comparison.message}</span>
                    </span>
                  </div>
                )}
              </div>
            </>
          )}

          {status.kind === 'loading' && (
            <p role="status" className="map-view__overlay map-status">
              Fetching and scoring the route&hellip;
            </p>
          )}
          {status.kind === 'error' && (
            <p role="alert" className="map-view__overlay map-status">
              {status.message}
            </p>
          )}
          {status.kind === 'idle' && (
            <p className="map-view__overlay map-status note">Enter a trip above to preview it.</p>
          )}
        </div>
      </div>
    </section>
  );
}
