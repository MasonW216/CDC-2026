/**
 * Hurricane Helene case study: a standalone historical demo, not a trip result.
 *
 * Fetches GET /api/v1/demo/helene on mount -- never posts anything, never reachable from
 * the planner. Renders with the exact same components as the live results page
 * (LevelBadge, AlertList, RouteCard, from PrototypeResultsPage.tsx) so a Severe-concern
 * result looks identical whether it came from a live trip or from here: one visual
 * language, one prototype-score/1 contract, two different `mode` values.
 *
 * Shows a clear "historical, not live" banner above everything else on the page, so it
 * can never be mistaken for a scored trip -- see docs/prototype_score_spec.md's
 * "Historical case study" section for why this must stay a separate page.
 */
import { useEffect, useState } from 'react';

import { AlertList, RouteCard } from '@/components/ScoreDisplay';
import { ApiError, fetchHeleneCaseStudy } from '@/services/api';
import type { ScoreResponse } from '@/types/score';
import { formatInstant } from '@/utils/scoreDisplay';

type LoadState =
  | { kind: 'loading' }
  | { kind: 'error'; message: string }
  | { kind: 'ready'; score: ScoreResponse };

export default function HeleneCaseStudyPage() {
  const [state, setState] = useState<LoadState>({ kind: 'loading' });

  useEffect(() => {
    let cancelled = false;
    fetchHeleneCaseStudy()
      .then((score) => {
        if (!cancelled) setState({ kind: 'ready', score });
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

  return (
    <section aria-labelledby="helene-heading">
      <h2 id="helene-heading" className="page-title">
        Case study: Hurricane Helene
      </h2>

      <div role="note" className="card" style={{ borderLeft: '4px solid var(--color-accent)' }}>
        <p style={{ margin: 0, fontWeight: 600 }}>
          This is a historical replay, not a live trip result.
        </p>
        <p className="note" style={{ marginBottom: 0 }}>
          It shows what StormRoute's prototype hazard indicator reports for a real severe-weather
          period (Hurricane Helene, 23&ndash;28 September 2024), using the same scoring rule as a
          live trip. The rainfall here is historical reanalysis, retrieved after the fact — a
          traveler would not have had it at departure. This page never feeds into, and is never
          shown as, a live or saved trip result. Plan a real trip on the{' '}
          <a href="/">planner page</a> instead.
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

      {state.kind === 'ready' && (
        <>
          <p className="note">
            {state.score.case_study?.origin.label} to {state.score.case_study?.destination.label}
            , departing {formatInstant(state.score.departure_utc)}.{' '}
            {state.score.case_study?.note}
          </p>

          <div className="card-grid" style={{ marginTop: 'var(--space-4)' }}>
            {state.score.routes.map((route, index) => (
              <RouteCard key={route.route_id} label={`Route ${index + 1}`} route={route} />
            ))}
          </div>

          <section aria-labelledby="helene-comparison-heading" className="card">
            <h3 id="helene-comparison-heading" className="section-title" style={{ marginTop: 0 }}>
              Comparison
            </h3>
            <p>{state.score.comparison.message}</p>
            {state.score.comparison.severe_advice && <p>{state.score.comparison.severe_advice}</p>}
          </section>

          <AlertList alerts={state.score.alerts} />

          {state.score.limitations.length > 0 && (
            <section aria-labelledby="helene-limits-heading" className="card">
              <h3 id="helene-limits-heading" className="section-title" style={{ marginTop: 0 }}>
                Known limits
              </h3>
              <ul className="note">
                {state.score.limitations.map((limitation) => (
                  <li key={limitation}>{limitation}</li>
                ))}
              </ul>
            </section>
          )}

          <section aria-labelledby="helene-provenance-heading" className="card">
            <h3 id="helene-provenance-heading" className="section-title" style={{ marginTop: 0 }}>
              Inputs and provenance
            </h3>
            <ul className="note">
              <li>Rainfall: {state.score.coverage.forecast.source}</li>
              <li>Alerts: {state.score.coverage.alerts.source}</li>
            </ul>
          </section>
        </>
      )}
    </section>
  );
}
