/**
 * Trip planner: one page, sidebar plus map, no separate results route.
 *
 * The sidebar takes origin/destination/departure, then shows the prototype
 * hazard index (RiskGauge) and the real reasons behind it
 * (`RouteScore.reasons`, from the actual scoring pipeline, not invented copy)
 * for whichever route the comparison favors. The map draws every candidate
 * route -- recommended in blue, others in gray, a third alternative dashed --
 * and cuts the recommended route's own highest-concern county stretch into a
 * separate, differently colored piece using the real per-segment distances
 * (utils/routeSegments), not an illustrative overlay.
 *
 * The saved-trip button scores the hardcoded DEMO_SCENARIO directly,
 * bypassing TripForm entirely -- it never fills the form or reads its state.
 * That is deliberate: an earlier version filled the form and inferred the
 * mode from "was demo loaded," which broke the moment someone loaded the
 * demo and then edited a field (still cached_replay, but scoring whatever
 * they'd typed). Two independent paths with no shared state cannot have that
 * bug. TripForm's own submit always sends mode: 'live'.
 *
 * The saved trip is a contemporary replay (artifacts/demo/saved_trip_request.json),
 * not Hurricane Helene -- per the team's frontend handoff, the button and
 * copy used to wrongly claim otherwise. The real, separate Helene replay
 * lives at /case-studies/helene and is never reachable from here.
 */
import { useMemo, useState } from 'react';

import LiveRouteMap, { type RouteRender } from '@/components/LiveRouteMap';
import RiskGauge from '@/components/RiskGauge';
import TripForm from '@/components/TripForm';
import { useHeaderSearch } from '@/contexts/HeaderSearchContext';
import { ApiError, fetchRoute, scoreTrip } from '@/services/api';
import type { RouteScore, ScoreResponse } from '@/types/score';
import type { Location, TripRequest } from '@/types/trip';
import { toEasternIso } from '@/utils/departureTime';
import { splitRouteAtSegment } from '@/utils/routeSegments';

const DEMO_SCENARIO: { origin: Location; destination: Location; departureLocal: string } = {
  origin: { label: 'Asheville, NC', lat: 35.5951, lon: -82.5515 },
  destination: { label: 'Charlotte, NC', lat: 35.2271, lon: -80.8431 },
  departureLocal: '2024-09-27T12:00',
};

type Status =
  | { kind: 'idle' }
  | { kind: 'loading' }
  | { kind: 'error'; message: string }
  | {
      kind: 'success';
      origin: Location;
      destination: Location;
      score: ScoreResponse;
      geometry: Map<string, [number, number][]>;
    };

function bandLevel(band: string): 0 | 1 | 2 | 3 | 'none' {
  const map: Record<string, 0 | 1 | 2 | 3> = {
    'Lower concern': 0,
    'Elevated concern': 1,
    'High concern': 2,
    'Severe concern': 3,
  };
  return map[band] ?? 'none';
}

function formatInstant(iso: string): string {
  return new Intl.DateTimeFormat('en-US', {
    timeZone: 'UTC',
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(iso));
}

export default function PlannerPage() {
  const { searchedLocation } = useHeaderSearch();
  const [status, setStatus] = useState<Status>({ kind: 'idle' });

  async function score(request: TripRequest) {
    setStatus({ kind: 'loading' });
    try {
      // KNOWN GAP, tracked with the backend: this fetches geometry and score
      // as two independent OSRM calls and matches them by route_id string.
      // That's only safe because both calls happen to query OSRM the same
      // way for the same coordinates; it is not a guarantee, and the backend
      // assignment (see team chat, Priority 1) is replacing this with a
      // single fetch or a verified stable route identity. Update this match
      // once that contract change lands -- don't extend this assumption
      // further in the meantime.
      const [scoreResult, routeResult] = await Promise.all([
        scoreTrip(request),
        fetchRoute(request.origin, request.destination),
      ]);
      const geometry = new Map(
        routeResult.routes.map((candidate) => [
          candidate.route_id,
          candidate.coordinates.map(([lon, lat]) => [lat, lon] as [number, number]),
        ]),
      );
      setStatus({
        kind: 'success',
        origin: request.origin,
        destination: request.destination,
        score: scoreResult,
        geometry,
      });
    } catch (error) {
      setStatus({
        kind: 'error',
        message: error instanceof ApiError ? error.message : 'Could not score this trip.',
      });
    }
  }

  function runSavedTripReplay() {
    void score({
      origin: DEMO_SCENARIO.origin,
      destination: DEMO_SCENARIO.destination,
      departure_time: toEasternIso(DEMO_SCENARIO.departureLocal),
      mode: 'cached_replay',
    });
  }

  function handleFormSubmit(request: TripRequest) {
    void score({ ...request, mode: 'live' });
  }

  const view = useMemo(() => {
    if (status.kind !== 'success') return null;
    const { score: result, geometry, origin, destination } = status;
    const { comparison } = result;
    const recommendedId =
      comparison.ranking === 'distinguishable' ? comparison.lowest_concern_route_id : null;
    const primaryId = recommendedId ?? comparison.fastest_route_id ?? result.routes[0]?.route_id;
    const primary = result.routes.find((r) => r.route_id === primaryId) ?? result.routes[0] ?? null;

    const routes: RouteRender[] = result.routes
      .map((route, index): RouteRender | null => {
        const path = geometry.get(route.route_id);
        if (!path) return null;
        const isRecommended = recommendedId !== null && route.route_id === recommendedId;
        const isPrimaryFallback = recommendedId === null && route.route_id === primaryId;
        const dashed = !isRecommended && !isPrimaryFallback && index > 1;
        const color =
          isRecommended || isPrimaryFallback ? 'var(--route-recommended)' : 'var(--route-current)';
        const highlightIndex =
          route.route_id === primary?.route_id && primary.highest_concern_segment
            ? primary.segments.findIndex(
                (s) =>
                  s.county_fips === primary.highest_concern_segment!.county_fips &&
                  s.arrival_utc === primary.highest_concern_segment!.arrival_utc,
              )
            : -1;
        return {
          id: route.route_id,
          path,
          color,
          dashed,
          weight: isRecommended || isPrimaryFallback ? 5 : 4,
          highlight:
            highlightIndex >= 0
              ? {
                  segmentKm: route.segments.map((s) => s.km),
                  index: highlightIndex,
                  color: `var(--level-${bandLevel(route.highest_concern_segment!.band)}-fg)`,
                }
              : null,
        };
      })
      .filter((r): r is RouteRender => r !== null);

    let dangerMarker: { position: [number, number]; label: string } | null = null;
    const primaryPath = primary ? geometry.get(primary.route_id) : undefined;
    if (primary?.highest_concern_segment && primaryPath) {
      const segIndex = primary.segments.findIndex(
        (s) =>
          s.county_fips === primary.highest_concern_segment!.county_fips &&
          s.arrival_utc === primary.highest_concern_segment!.arrival_utc,
      );
      if (segIndex >= 0) {
        const { highlighted } = splitRouteAtSegment(
          primaryPath,
          primary.segments.map((s) => s.km),
          segIndex,
        );
        const mid = highlighted[Math.floor(highlighted.length / 2)];
        if (mid) {
          dangerMarker = {
            position: mid,
            label: `${primary.highest_concern_segment.county_name} · ${formatInstant(
              primary.highest_concern_segment.arrival_utc,
            )}`,
          };
        }
      }
    }

    return { primary, routes, dangerMarker, origin, destination, comparison, mode: result.mode };
  }, [status]);

  return (
    <div className="pivot-layout">
      <aside className="pivot-sidebar">
        <p role="note" className="note" style={{ marginBottom: 'var(--space-3)' }}>
          StormRoute compares the modeled weather-hazard exposure of routes and departure times
          based on available weather data. It is a comparative decision index, not a guarantee of
          safety, and it never overrides an official National Weather Service warning. Type a real,
          future trip below to score it live; the saved-trip button replays a cached, offline
          example instead of calling live weather. For a real historical storm, see the Helene case
          study.
        </p>
        <TripForm onSubmit={handleFormSubmit} initialOrigin={searchedLocation} />
        <button
          type="button"
          onClick={runSavedTripReplay}
          disabled={status.kind === 'loading'}
          className="btn"
          style={{ width: '100%', marginTop: 'var(--space-2)' }}
        >
          Load saved trip (offline demo)
        </button>

        {status.kind === 'loading' && (
          <p role="status" className="note" style={{ marginTop: 'var(--space-3)' }}>
            Scoring this trip&hellip;
          </p>
        )}
        {status.kind === 'error' && (
          <p role="alert" style={{ marginTop: 'var(--space-3)' }}>
            {status.message}
          </p>
        )}

        {view?.primary && (
          <RouteBreakdown
            route={view.primary}
            mode={view.mode}
            comparisonMessage={view.comparison.message}
          />
        )}
      </aside>

      <main className="pivot-map-area">
        {view ? (
          <LiveRouteMap
            origin={view.origin}
            destination={view.destination}
            routes={view.routes}
            dangerMarker={view.dangerMarker}
          />
        ) : (
          <div className="pivot-map-empty note">
            Enter a trip, or load the saved trip, to see it on the map.
          </div>
        )}
        {view && (
          <div className="map-view__overlay map-legend" aria-label="Route color legend">
            <div className="map-legend__row">
              <span
                className="map-legend__swatch"
                style={{ background: 'var(--route-current)' }}
                aria-hidden="true"
              />
              <span>
                <strong>Current route</strong>
                <span>Higher modeled weather risk.</span>
              </span>
            </div>
            <div className="map-legend__row">
              <span
                className="map-legend__swatch"
                style={{ background: 'var(--route-recommended)' }}
                aria-hidden="true"
              />
              <span>
                <strong>Recommended route</strong>
                <span>Lower modeled weather risk, on this trip.</span>
              </span>
            </div>
            {view.routes.some((r) => r.dashed) && (
              <div className="map-legend__row">
                <span
                  className="map-legend__swatch map-legend__swatch--dashed"
                  style={{ borderColor: 'var(--route-recommended)' }}
                  aria-hidden="true"
                />
                <span>
                  <strong>Alternative option</strong>
                  <span>A third candidate route.</span>
                </span>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}

function RouteBreakdown({
  route,
  mode,
  comparisonMessage,
}: {
  route: RouteScore;
  mode: ScoreResponse['mode'];
  comparisonMessage: string;
}) {
  return (
    <div className="route-breakdown">
      {mode === 'cached' && (
        <p className="note">This is a saved replay, not a live-scored request.</p>
      )}

      <h3 className="section-title" style={{ marginTop: 0 }}>
        Prototype hazard index
      </h3>
      <RiskGauge index={route.index} band={route.band} />
      {route.is_lower_bound && (
        <p role="note" className="note" style={{ textAlign: 'center' }}>
          This index is a lower bound: some inputs for this route are missing, so the true concern
          could be higher.
        </p>
      )}
      <p className="note" style={{ textAlign: 'center' }}>
        {comparisonMessage}
      </p>

      <h3 className="section-title">What lowered this score</h3>
      <ul className="breakdown-list">
        {route.reasons.map((reason) => (
          <li key={reason}>
            <span className="breakdown-list__icon" aria-hidden="true">
              {'☁'}
            </span>
            {reason}
          </li>
        ))}
        {route.alerts.map((alert) => (
          <li key={alert.id} className="breakdown-list__item--danger">
            <span className="breakdown-list__icon" aria-hidden="true">
              {'⚠'}
            </span>
            <span>
              <strong>{alert.event}</strong>
              {alert.headline ? <span className="note"> {alert.headline}</span> : null}
            </span>
          </li>
        ))}
        {route.reasons.length === 0 && route.alerts.length === 0 && (
          <li className="note">No rainfall or official alerts pushed this score up.</li>
        )}
      </ul>
    </div>
  );
}
