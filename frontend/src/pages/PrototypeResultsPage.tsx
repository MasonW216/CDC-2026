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
import { Link, useLocation } from 'react-router-dom';

import type { AlertUse, RouteScore, ScoreResponse } from '@/types/score';
import type { TripRequest } from '@/types/trip';

const BAND_CLASS: Record<string, string> = {
  'Lower concern': 'level-badge--0',
  'Elevated concern': 'level-badge--1',
  'High concern': 'level-badge--2',
  'Severe concern': 'level-badge--3',
  'Not assessed': 'level-badge--none',
};

/** Color is always paired with the text label (`band`), never used alone. */
function LevelBadge({ band, index }: { band: string; index: number | null }) {
  return (
    <span className={`level-badge ${BAND_CLASS[band] ?? 'level-badge--none'}`}>
      {band}
      {index !== null ? ` (${Math.round(index)}/100)` : ''}
    </span>
  );
}

function formatInstant(iso: string): string {
  return `${new Intl.DateTimeFormat('en-US', {
    timeZone: 'UTC',
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(iso))} UTC`;
}

function AlertList({ alerts }: { alerts: AlertUse[] }) {
  if (alerts.length === 0) {
    return null;
  }
  return (
    <div role="alert" className="alert-banner">
      <h4>Official NWS flood products</h4>
      <ul>
        {alerts.map((alert) => (
          <li key={alert.id}>
            {alert.event}
            {alert.headline ? `: ${alert.headline}` : ''}
          </li>
        ))}
      </ul>
    </div>
  );
}

function RouteCard({ label, route }: { label: string; route: RouteScore }) {
  return (
    <article className="card" aria-labelledby={`route-heading-${label}`}>
      <h3 id={`route-heading-${label}`} className="subsection-title" style={{ marginTop: 0 }}>
        {label}: <LevelBadge band={route.band} index={route.index} />
      </h3>
      <p className="note">
        {route.distance_km} km &middot; {Math.round(route.duration_minutes)} min
        {route.status !== 'assessed' ? ` · ${route.status}` : ''}
        {route.is_lower_bound ? ' · index is a lower bound (partial data)' : ''}
      </p>

      <AlertList alerts={route.alerts} />

      {route.reasons.length > 0 && (
        <ul>
          {route.reasons.map((reason) => (
            <li key={reason}>{reason}</li>
          ))}
        </ul>
      )}

      {route.highest_concern_segment && (
        <section aria-label={`Highest-concern segment for ${label}`}>
          <h4 className="subsection-title">
            Highest-concern segment: {route.highest_concern_segment.county_name} (
            <LevelBadge
              band={route.highest_concern_segment.band}
              index={route.highest_concern_segment.index}
            />
            )
          </h4>
          <p>{route.highest_concern_segment.reason}</p>
          <p>Arrival: {formatInstant(route.highest_concern_segment.arrival_utc)}</p>
        </section>
      )}

      <h4 className="subsection-title">Route timeline</h4>
      <table className="timeline">
        <caption
          style={{
            textAlign: 'left',
            color: 'var(--color-text-faint)',
            fontSize: '0.8rem',
            marginBottom: 'var(--space-1)',
          }}
        >
          County stretches for {label}, in order of arrival
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
          {route.segments.map((segment) => (
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
    </article>
  );
}

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
          <RouteCard key={route.route_id} label={`Route ${index + 1}`} route={route} />
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
