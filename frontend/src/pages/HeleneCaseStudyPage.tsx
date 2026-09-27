/**
 * Hurricane Helene disaster demo: a standalone historical replay, not a trip result.
 *
 * Fetches GET /api/v1/demo/helene on mount -- never posts anything, never reachable from
 * the planner. Renders the same `prototype-score/1` atoms as the live results page
 * (LevelBadge, AlertList, from ScoreDisplay.tsx) so a Severe-concern result looks
 * identical whether it came from a live trip or from here: one visual language, one
 * prototype-score/1 contract, two different `mode` values.
 *
 * Compact by design: one hero row (gauge, headline, route toggle) instead of the
 * headline, then a separate route-tab row, then a separate spotlight card the earlier
 * version stacked; a selected segment's own detail panel already covers what a
 * "spotlight" card would have repeated. The full per-county table, limits, and
 * provenance are still all there for a reader who wants them, tucked behind <details>
 * rather than forced onto everyone.
 *
 * Shows a clear "historical, not live" note above everything else on the page, so it
 * can never be mistaken for a scored trip -- see docs/prototype_score_spec.md's
 * "Historical case study" section for why this must stay a separate page.
 *
 * The map shows the actual real road path (`RouteScore.geometry`, already in the score
 * response, the same real OSRM call that produced the route's counties -- no second,
 * separately-fetched path that could mismatch or go stale when the route toggle
 * switches), plus two real, distinct county layers: every NC county's own indicator at
 * the departure instant (`county_risk`, faint, statewide context), and the active
 * route's own segments drawn boldly on top (their own arrival-time scores). That
 * statewide layer is the actual visual justification for the route choice -- the whole
 * surrounding region, not just the sampled stretch, shows the same real pattern. If the
 * county-shapes fetch fails, the rest of the page (including the real route line) still
 * works.
 */
import type { FeatureCollection } from 'geojson';
import { useEffect, useMemo, useState } from 'react';

import { AlertList, LevelBadge } from '@/components/ScoreDisplay';
import HeleneCountyMap from '@/components/HeleneCountyMap';
import RiskGauge from '@/components/RiskGauge';
import { ApiError, fetchHeleneCaseStudy } from '@/services/api';
import type { RouteScore, ScoreResponse, SegmentScore } from '@/types/score';
import { BAND_LEVEL, formatInstant } from '@/utils/scoreDisplay';

type LoadState =
  | { kind: 'loading' }
  | { kind: 'error'; message: string }
  | { kind: 'ready'; score: ScoreResponse };

function segmentIndexOf(route: RouteScore, segment: SegmentScore | null): number {
  if (!segment) return 0;
  return Math.max(
    0,
    route.segments.findIndex(
      (s) => s.county_fips === segment.county_fips && s.arrival_utc === segment.arrival_utc,
    ),
  );
}

const FACTOR_ICON: Record<'rain' | 'alert' | 'historical', string> = {
  rain: '☔',
  alert: '⚠',
  historical: '🕰️',
};

/**
 * Runs a best-effort, secondary fetch for the map (county shapes, route
 * geometry) without letting it affect the page's main data path -- a promise
 * rejection is ignored, and so is a synchronous throw from calling `start`
 * itself (e.g. a network client that throws immediately instead of
 * rejecting), which a bare `.catch()` on the resulting promise would not
 * catch.
 */
function loadBestEffort(start: () => Promise<void>): void {
  try {
    start().catch(() => undefined);
  } catch {
    // Best effort only: the map degrades gracefully without this data.
  }
}

export default function HeleneCaseStudyPage() {
  const [state, setState] = useState<LoadState>({ kind: 'loading' });
  const [activeRouteId, setActiveRouteId] = useState<string | null>(null);
  const [activeSegment, setActiveSegment] = useState<number>(0);
  const [counties, setCounties] = useState<FeatureCollection | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchHeleneCaseStudy()
      .then((score) => {
        if (cancelled) return;
        setState({ kind: 'ready', score });
        setActiveRouteId(score.routes[0]?.route_id ?? null);

        // County shapes: a static asset, best-effort so a fetch failure never
        // breaks the rest of the page. Each route's own real road geometry is
        // already in the score response itself (RouteScore.geometry, baked
        // into the fixture from the same real OSRM call that produced the
        // route's counties) -- no second, separately-fetched, easily
        // mismatched path needed, and it updates correctly when the route
        // toggle switches which route is active.
        loadBestEffort(() =>
          fetch('/nc_counties.geojson')
            .then((res) => res.json())
            .then((geo: FeatureCollection) => {
              if (!cancelled) setCounties(geo);
            }),
        );
      })
      .catch((error: unknown) => {
        if (cancelled) return;
        setState({
          kind: 'error',
          message: error instanceof ApiError ? error.message : 'Could not load the case study.',
        });
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const activeRoute = useMemo(() => {
    if (state.kind !== 'ready') return null;
    return state.score.routes.find((r) => r.route_id === activeRouteId) ?? state.score.routes[0];
  }, [state, activeRouteId]);

  const routePath = useMemo<[number, number][] | null>(() => {
    if (!activeRoute?.geometry) return null;
    return activeRoute.geometry.map((point) => [point[1] ?? 0, point[0] ?? 0]);
  }, [activeRoute]);

  function selectRoute(route: RouteScore) {
    setActiveRouteId(route.route_id);
    setActiveSegment(segmentIndexOf(route, route.highest_concern_segment));
  }

  const activeSegmentData = activeRoute?.segments[activeSegment] ?? null;

  return (
    <section aria-labelledby="helene-heading" className="content-page">
      <h2 id="helene-heading" className="page-title">
        Disaster demo: Hurricane Helene
      </h2>
      <p role="note" className="note" style={{ marginTop: 0 }}>
        Historical replay, not a live trip result. What the prototype hazard indicator would have
        reported during Hurricane Helene (23&ndash;28 September 2024), scored by the same rule as a
        live trip but fed rainfall reconstructed after the fact -- a traveler would not have had it
        at departure. Plan a real trip on the <a href="/">planner page</a> instead.
      </p>

      {state.kind === 'loading' && (
        <p role="status" className="note">
          Loading the disaster demo&hellip;
        </p>
      )}

      {state.kind === 'error' && (
        <p role="alert">
          {state.message} Try reloading the page; this reads cached files and needs no network.
        </p>
      )}

      {state.kind === 'ready' && activeRoute && (
        <>
          <p className="note" style={{ marginBottom: 0 }}>
            {state.score.case_study?.origin.label} to {state.score.case_study?.destination.label},
            departing {formatInstant(state.score.departure_utc)}. {state.score.case_study?.note}
          </p>

          <AlertList alerts={state.score.alerts} />

          <div className="case-hero">
            <div className="case-hero__gauge">
              <RiskGauge index={activeRoute.index} band={activeRoute.band} />
            </div>
            <div className="case-hero__text">
              <p className="case-hero__headline">{state.score.comparison.message}</p>
              {state.score.comparison.severe_advice && (
                <p className="note" style={{ fontWeight: 600 }}>
                  {state.score.comparison.severe_advice}
                </p>
              )}
              <div className="case-tabs" role="tablist" aria-label="Choose a route to inspect">
                {state.score.routes.map((route, index) => (
                  <button
                    key={route.route_id}
                    type="button"
                    role="tab"
                    aria-selected={route.route_id === activeRoute.route_id}
                    onClick={() => selectRoute(route)}
                  >
                    {`Route ${index + 1}: `}
                    <LevelBadge band={route.band} index={route.index} />
                  </button>
                ))}
              </div>
              <p className="note" style={{ margin: 0 }}>
                {activeRoute.distance_km} km &middot; {Math.round(activeRoute.duration_minutes)} min
                {activeRoute.status !== 'assessed' ? ` · ${activeRoute.status}` : ''}
                {activeRoute.is_lower_bound
                  ? ' · lower bound: some inputs are missing, true concern could be higher'
                  : ''}
              </p>
            </div>
          </div>

          {counties && state.score.case_study && (
            <div className="card-map-wrap">
              <div className="card map-card case-map">
                <HeleneCountyMap
                  counties={counties}
                  origin={state.score.case_study.origin}
                  destination={state.score.case_study.destination}
                  path={routePath ?? undefined}
                  route={activeRoute}
                  activeIndex={activeSegment}
                  onSelect={setActiveSegment}
                  countyRisk={state.score.case_study.county_risk}
                />
              </div>
              <p className="note" style={{ marginTop: 'var(--space-2)' }}>
                Bold: counties this route passes through. Faint: every other county&rsquo;s own real
                indicator at departure time -- the surrounding pattern behind the route choice, not
                just the sampled stretch.{' '}
                <span className="level-badge level-badge--1">Elevated</span>{' '}
                <span className="level-badge level-badge--2">High</span>{' '}
                <span className="level-badge level-badge--3">Severe</span>. Hover any county for
                detail, or click a route county to inspect it below.
              </p>
            </div>
          )}

          {activeRoute.contributing_factors.length > 0 && (
            <ul className="factor-chips" aria-label="Contributing factors">
              {activeRoute.contributing_factors.map((factor) => (
                <li key={`${factor.county_name}-${factor.arrival_utc}`} className="factor-chip">
                  <span className="factor-chip__icon" aria-hidden="true">
                    {FACTOR_ICON[factor.kind]}
                  </span>
                  <span>{factor.label}</span>
                </li>
              ))}
            </ul>
          )}

          <h3 className="section-title">County-by-county timeline</h3>
          <p className="note" style={{ marginTop: `calc(-1 * var(--space-2))` }}>
            In order of arrival. Select a stretch to see it below.
          </p>
          <div
            className="segment-rail"
            role="tablist"
            aria-label={`Route timeline, ${activeRoute.segments.length} stretches`}
          >
            {activeRoute.segments.map((segment, index) => {
              const level = BAND_LEVEL[segment.band] ?? 'none';
              return (
                <span
                  key={`${segment.county_fips}-${segment.arrival_utc}`}
                  className="segment-rail__step"
                >
                  <button
                    type="button"
                    role="tab"
                    aria-selected={index === activeSegment}
                    aria-current={index === activeSegment}
                    aria-label={`${segment.county_name}, ${segment.band}`}
                    className="segment-rail__dot"
                    style={{ background: `var(--level-${level}-fg)` }}
                    onClick={() => setActiveSegment(index)}
                  >
                    {index + 1}
                  </button>
                </span>
              );
            })}
          </div>

          {activeSegmentData && (
            <div className="card">
              <div className="segment-detail">
                <h4 className="subsection-title">{activeSegmentData.county_name}</h4>
                <LevelBadge band={activeSegmentData.band} index={activeSegmentData.index} />
              </div>
              <p className="note" style={{ marginBottom: 0 }}>
                Arrival {formatInstant(activeSegmentData.arrival_utc)} &middot;{' '}
                {activeSegmentData.rain_24h_mm !== null
                  ? `${Math.round(activeSegmentData.rain_24h_mm)} mm over the prior 24h`
                  : 'rainfall not available'}
              </p>
              {activeSegmentData.alerts.length > 0 && (
                <p className="note" style={{ marginBottom: 0 }}>
                  {activeSegmentData.alerts.map((a) => a.event).join(', ')}
                </p>
              )}
              <p style={{ marginBottom: 0 }}>{activeSegmentData.reason}</p>
            </div>
          )}

          <details style={{ margin: 'var(--space-4) 0' }}>
            <summary>
              See the full table for this route ({activeRoute.segments.length} stretches)
            </summary>
            <table className="timeline" style={{ marginTop: 'var(--space-3)' }}>
              <caption
                style={{
                  textAlign: 'left',
                  color: 'var(--color-text-faint)',
                  fontSize: '0.8rem',
                  marginBottom: 'var(--space-1)',
                }}
              >
                County stretches, in order of arrival
              </caption>
              <thead>
                <tr>
                  <th scope="col">County</th>
                  <th scope="col">Arrival (UTC)</th>
                  <th scope="col">Prototype indicator</th>
                  <th scope="col">24 h rainfall</th>
                </tr>
              </thead>
              <tbody>
                {activeRoute.segments.map((segment) => (
                  <tr key={`${segment.county_fips}-${segment.arrival_utc}`}>
                    <td>{segment.county_name}</td>
                    <td>{formatInstant(segment.arrival_utc)}</td>
                    <td>
                      <LevelBadge band={segment.band} index={segment.index} />
                    </td>
                    <td>
                      {segment.rain_24h_mm !== null
                        ? `${Math.round(segment.rain_24h_mm)} mm`
                        : 'not available'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </details>

          {state.score.limitations.length > 0 && (
            <details style={{ margin: 'var(--space-4) 0' }}>
              <summary>Known limits</summary>
              <ul className="note">
                {state.score.limitations.map((limitation) => (
                  <li key={limitation}>{limitation}</li>
                ))}
              </ul>
            </details>
          )}

          <details style={{ margin: 'var(--space-4) 0' }}>
            <summary>Inputs and provenance</summary>
            <ul className="note">
              <li>Rainfall: {state.score.coverage.forecast.source}</li>
              <li>Alerts: {state.score.coverage.alerts.source}</li>
            </ul>
          </details>
        </>
      )}
    </section>
  );
}
