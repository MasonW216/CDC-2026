/**
 * Hurricane Helene case study: a standalone historical demo, not a trip result.
 *
 * Fetches GET /api/v1/demo/helene on mount -- never posts anything, never reachable from
 * the planner. Renders the same `prototype-score/1` atoms as the live results page
 * (LevelBadge, AlertList, from ScoreDisplay.tsx) so a Severe-concern result looks
 * identical whether it came from a live trip or from here: one visual language, one
 * prototype-score/1 contract, two different `mode` values.
 *
 * Layout is a headline-first, click-to-reveal story instead of every route's full
 * timeline sitting open at once (the earlier version stacked N full RouteCards,
 * each with an 8-row table, always expanded -- a lot to read before finding the one
 * fact that mattered). Here: one headline number, a route switcher, a spotlight on
 * the segment that actually drove the index, and a clickable rail of every county
 * stretch that reveals one at a time. The full table is still there for a reader who
 * wants every row, tucked behind <details> rather than forced onto everyone.
 *
 * Shows a clear "historical, not live" banner above everything else on the page, so it
 * can never be mistaken for a scored trip -- see docs/prototype_score_spec.md's
 * "Historical case study" section for why this must stay a separate page.
 *
 * The map is county-based, not a colored route line: it loads NC county
 * boundaries (public/nc_counties.geojson, Census TIGER -- see data_card.md)
 * once, then colors each county the route passes through by its own concern
 * level. Route geometry is a second, independent fetch (GET
 * /api/v1/routing/route against the case study's real origin/destination) --
 * the score response itself carries no geometry, only county-level data. That
 * geometry renders today's live roads, not a historical snapshot, so this
 * page never claims to show which roads were actually closed during Helene --
 * only which counties the route passes through and each one's modeled
 * concern. If either fetch fails, the rest of the page still works.
 */
import type { FeatureCollection } from 'geojson';
import { useEffect, useMemo, useState } from 'react';

import { AlertList, LevelBadge } from '@/components/ScoreDisplay';
import HeleneCountyMap from '@/components/HeleneCountyMap';
import RiskGauge from '@/components/RiskGauge';
import { ApiError, fetchHeleneCaseStudy, fetchRoute } from '@/services/api';
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

const FACTOR_ICON: Record<'rain' | 'alert', string> = { rain: '☔', alert: '⚠' };

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
  const [routePath, setRoutePath] = useState<[number, number][] | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchHeleneCaseStudy()
      .then((score) => {
        if (cancelled) return;
        setState({ kind: 'ready', score });
        setActiveRouteId(score.routes[0]?.route_id ?? null);

        // Two independent, best-effort fetches for the map: county shapes
        // (a static asset) and today's live road geometry for the case
        // study's real origin/destination. Neither blocks the rest of the
        // page, and either can fail without breaking it.
        loadBestEffort(() =>
          fetch('/nc_counties.geojson')
            .then((res) => res.json())
            .then((geo: FeatureCollection) => {
              if (!cancelled) setCounties(geo);
            }),
        );

        const origin = score.case_study?.origin;
        const destination = score.case_study?.destination;
        if (origin && destination) {
          loadBestEffort(() =>
            fetchRoute(origin, destination).then((routeResponse) => {
              if (cancelled) return;
              const first = routeResponse.routes[0];
              if (first) {
                setRoutePath(first.coordinates.map(([lon, lat]) => [lat, lon]));
              }
            }),
          );
        }
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

  function selectRoute(route: RouteScore) {
    setActiveRouteId(route.route_id);
    setActiveSegment(segmentIndexOf(route, route.highest_concern_segment));
  }

  const activeSegmentData = activeRoute?.segments[activeSegment] ?? null;

  return (
    <section aria-labelledby="helene-heading" className="content-page">
      <h2 id="helene-heading" className="page-title">
        Case study: Hurricane Helene
      </h2>

      <div role="note" className="card">
        <p style={{ margin: 0, fontWeight: 600 }}>
          This is a historical replay, not a live trip result.
        </p>
        <p className="note" style={{ marginBottom: 0 }}>
          What the prototype hazard indicator would have reported during Hurricane Helene
          (23&ndash;28 September 2024), scored by the same rule as a live trip -- but fed rainfall
          reconstructed after the fact, which a traveler would not have had at departure. Plan a
          real trip on the <a href="/">planner page</a> instead.
        </p>
      </div>

      {state.kind === 'loading' && (
        <p role="status" className="note">
          Loading the case study&hellip;
        </p>
      )}

      {state.kind === 'error' && (
        <p role="alert">
          {state.message} Try reloading the page; this reads cached files and needs no network.
        </p>
      )}

      {state.kind === 'ready' && activeRoute && (
        <>
          <p className="note">
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
            </div>
          </div>

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

          <p className="note">
            {activeRoute.distance_km} km &middot; {Math.round(activeRoute.duration_minutes)} min
            {activeRoute.status !== 'assessed' ? ` · ${activeRoute.status}` : ''}
          </p>
          {activeRoute.is_lower_bound && (
            <p role="note" className="note">
              This index is a lower bound: some inputs for this route are missing, so the true
              concern could be higher.
            </p>
          )}

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
                />
              </div>
              <p className="note" style={{ marginTop: 'var(--space-2)' }}>
                Counties this route passes through, colored by concern:{' '}
                <span className="level-badge level-badge--1">Elevated</span>{' '}
                <span className="level-badge level-badge--2">High</span>{' '}
                <span className="level-badge level-badge--3">Severe</span>. Hover a county for
                details, or click one to inspect it below.
              </p>
            </div>
          )}

          {activeRoute.highest_concern_segment && (
            <div className="card spotlight-card">
              <h3 className="section-title" style={{ marginTop: 0 }}>
                What drove this route&rsquo;s score
              </h3>
              <p style={{ marginTop: 0 }}>
                <strong>{activeRoute.highest_concern_segment.county_name}</strong>, arriving{' '}
                {formatInstant(activeRoute.highest_concern_segment.arrival_utc)}:{' '}
                {activeRoute.highest_concern_segment.reason}
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
