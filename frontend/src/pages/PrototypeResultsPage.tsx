/**
 * Trip results screen: the prototype hazard indicator, live or replayed.
 *
 * Reads `{ score, request }` from router navigation state (PlannerPage posts
 * to POST /api/v1/trips/score, then navigates here). `request` supplies the
 * origin/destination labels for the heading -- the score response itself
 * carries no place names, only county-level data. A direct visit with no
 * state (a refresh, a bookmark) shows a plain "plan a trip first" message
 * instead of crashing.
 *
 * Renders the `prototype-score/1` contract (types/score.ts), not the
 * milestone-7 production Weather Safety Score (see ResultsPage.tsx).
 *
 * Layout rule: official NWS alerts render above the advisory, never below or
 * beside it.
 */
import { useEffect, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';

import { RouteCard } from '@/components/ScoreDisplay';
import { fetchCountyBoundaries } from '@/services/api';
import type { CountyBoundaries } from '@/types/geography';
import type { ScoreResponse } from '@/types/score';
import type { TripRequest } from '@/types/trip';
import { formatInstant } from '@/utils/scoreDisplay';

function NoTripYet() {
  return (
    <section aria-labelledby="results-heading">
      <h2 id="results-heading" className="page-title">
        No trip to show yet
      </h2>
      <p className="note">
        Results only render right after submitting a trip on the planner -- a page refresh or a
        direct link loses that. <Link to="/">Plan a trip</Link> to see a result here.
      </p>
    </section>
  );
}

interface PrototypeResultsPageProps {
  score?: ScoreResponse;
  request?: Pick<TripRequest, 'origin' | 'destination'>;
}

export default function PrototypeResultsPage(props: PrototypeResultsPageProps = {}) {
  const location = useLocation();
  const state = location.state as {
    score?: ScoreResponse;
    request?: Pick<TripRequest, 'origin' | 'destination'>;
  } | null;
  const score = props.score ?? state?.score;
  const request = props.request ?? state?.request;
  const [counties, setCounties] = useState<CountyBoundaries | null>(null);

  useEffect(() => {
    let cancelled = false;
    // Map decoration only -- a failure here must not block the page; RouteMap already
    // handles counties === null (no county coloring, still shows the road geometry).
    fetchCountyBoundaries()
      .then((data) => {
        if (!cancelled) setCounties(data);
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, []);

  if (!score || !request) {
    return <NoTripYet />;
  }

  const { comparison, coverage } = score;

  return (
    <section aria-labelledby="results-heading">
      <h2 id="results-heading" className="page-title">
        {request.origin.label} to {request.destination.label}
      </h2>
      <p role="note" className="note">
        Prototype hazard indicator: a team-defined 0-100 comparison index over rainfall and NWS
        flood products, based on available weather data. It is not a probability, a trained model,
        or a validated score.
        {score.mode === 'cached'
          ? ' This result replays a saved trip; it is not this request scored live.'
          : ''}
      </p>
      <p className="note">Departing {formatInstant(score.departure_utc)}</p>

      <div className="card-grid" style={{ marginTop: 'var(--space-4)' }}>
        {score.routes.map((route, index) => (
          <RouteCard
            key={route.route_id}
            label={`Route ${index + 1}`}
            route={route}
            origin={request.origin}
            destination={request.destination}
            counties={counties}
          />
        ))}
      </div>

      <section aria-labelledby="comparison-heading" className="card">
        <h3 id="comparison-heading" className="section-title" style={{ marginTop: 0 }}>
          Comparison
        </h3>
        <p>{comparison.message}</p>
        {comparison.severe_advice && <p>{comparison.severe_advice}</p>}
      </section>

      {score.limitations.length > 0 && (
        <section aria-labelledby="limitations-heading" className="card">
          <h3 id="limitations-heading" className="section-title" style={{ marginTop: 0 }}>
            Known limits
          </h3>
          <ul className="note">
            {score.limitations.map((limitation) => (
              <li key={limitation}>{limitation}</li>
            ))}
          </ul>
        </section>
      )}

      <section aria-labelledby="provenance-heading" className="card">
        <h3 id="provenance-heading" className="section-title" style={{ marginTop: 0 }}>
          Inputs and provenance
        </h3>
        <ul className="note">
          <li>
            Forecast: {coverage.forecast.source}
            {coverage.forecast.from_cache ? ' (from cache)' : ''}
            {coverage.forecast.error ? ` — ${coverage.forecast.error}` : ''}
          </li>
          <li>
            Alerts: {coverage.alerts.source}
            {coverage.alerts.from_cache ? ' (from cache)' : ''}
            {!coverage.alerts.ok && coverage.alerts.error ? ` — ${coverage.alerts.error}` : ''}
          </li>
        </ul>
        <p className="note">Requested {formatInstant(score.requested_at_utc)}.</p>
        {coverage.forecast.missing_counties.length > 0 && (
          <p className="note">
            No usable forecast for: {coverage.forecast.missing_counties.join(', ')}.
          </p>
        )}
      </section>
    </section>
  );
}
