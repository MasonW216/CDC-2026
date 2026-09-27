/**
 * MVP demo results screen: the prototype hazard indicator, not the production
 * Weather Safety Score.
 *
 * Reads the cached Helene replay straight from `fixtures/prototypeResult.json`
 * (a byte copy of `artifacts/demo/prototype_result.json`, produced offline by
 * `scripts/run_prototype.py`). No network call, no backend dependency, so the
 * demo survives a wifi-off run.
 *
 * This is a stand-in for the real `/results` page (see `ResultsPage.tsx`,
 * milestone 7, the 0-100 Weather Safety Score). It is wired at the same route
 * only until that page exists; the two contracts and components are kept
 * separate (`types/prototype.ts` vs `types/trip.ts`) so replacing this one
 * later does not touch production code.
 *
 * Layout rule carried over from the real page: official NWS alerts render
 * above the advisory, never below or beside it.
 */
import prototypeResult from '@/fixtures/prototypeResult.json';
import type { ConcernLevel, PrototypeResult, PrototypeRoute } from '@/types/prototype';

const result = prototypeResult as PrototypeResult;

const DATA_STATUS_LABEL: Record<string, string> = {
  complete: '24 h and 72 h rainfall available',
  partial_weather: 'Incomplete rainfall',
  missing_weather: 'No rainfall available',
};

function routeLabel(id: string): string {
  const match = /^route_(\d+)$/.exec(id);
  return match ? `Route ${match[1]}` : id;
}

/** Color is always paired with the text label (`label`), never used alone. */
function LevelBadge({ level, label }: { level: ConcernLevel | null; label: string }) {
  return <span className={`level-badge level-badge--${level ?? 'none'}`}>{label}</span>;
}

function formatInstant(iso: string, timeZone: string): string {
  return `${new Intl.DateTimeFormat('en-US', {
    timeZone,
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(iso))} ${timeZone === 'UTC' ? 'UTC' : 'Eastern'}`;
}

function routeAlerts(route: PrototypeRoute): string[] {
  const seen = new Set<string>();
  for (const segment of route.segments) {
    for (const alert of segment.alerts_used) {
      seen.add(alert);
    }
  }
  return Array.from(seen);
}

function RouteCard({ label, route }: { label: string; route: PrototypeRoute }) {
  const alerts = routeAlerts(route);
  return (
    <article className="card" aria-labelledby={`route-heading-${label}`}>
      <h3 id={`route-heading-${label}`} className="subsection-title" style={{ marginTop: 0 }}>
        {label}: <LevelBadge level={route.trip_level} label={route.trip_label} />
      </h3>
      <p className="note">
        {route.distance_km} km &middot; {Math.round(route.duration_minutes)} min &middot; departure
        decision at {formatInstant(route.decision_time_utc, 'UTC')}
      </p>

      {alerts.length > 0 && (
        <div
          role="alert"
          className="alert-banner"
          aria-label={`County-coded NWS flood products for ${label}`}
        >
          <h4>County-coded NWS flood products active at a displayed stretch's arrival</h4>
          <ul>
            {alerts.map((alert) => (
              <li key={alert}>{alert}</li>
            ))}
          </ul>
        </div>
      )}

      <p>{route.advisory}</p>

      {route.highest_concern_segment && (
        <section aria-label={`First stretch at the highest concern level for ${label}`}>
          <h4 className="subsection-title">
            First stretch at highest concern level: {route.highest_concern_segment.county_name} (
            <LevelBadge
              level={route.highest_concern_segment.level}
              label={route.highest_concern_segment.label}
            />
            )
          </h4>
          <p>{route.highest_concern_segment.reason}</p>
          <p>Arrival: {formatInstant(route.highest_concern_segment.arrival_utc, 'UTC')}</p>
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
            <th scope="col">Rainfall coverage</th>
          </tr>
        </thead>
        <tbody>
          {route.segments.map((segment) => (
            <tr key={`${segment.county_fips}-${segment.arrival_utc}`}>
              <td>{segment.county_name}</td>
              <td>{formatInstant(segment.arrival_utc, 'UTC')}</td>
              <td>
                <LevelBadge level={segment.level} label={segment.label} />
              </td>
              <td>{DATA_STATUS_LABEL[segment.data_status] ?? segment.data_status}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {route.unassessed_segments.length > 0 && (
        <p role="note" className="note">
          Not assessed: {route.unassessed_segments.join(', ')}
        </p>
      )}

      <p role="note" className="note">
        {route.replay_caveat}
      </p>
    </article>
  );
}

export default function PrototypeResultsPage({
  data = result,
}: {
  data?: PrototypeResult;
} = {}) {
  const routeIds = Object.keys(data.routes);
  const comparison = data.comparison;

  return (
    <section aria-labelledby="results-heading">
      <h2 id="results-heading" className="page-title">
        {data.origin.label} to {data.destination.label}
      </h2>
      <p role="note" className="note">
        Prototype hazard indicator: a rule over cached historical rainfall and county-coded NWS
        flood products. It is not a live forecast, trained model, probability, or validated score.
      </p>
      <p className="note">Departing {formatInstant(data.departure_time, 'America/New_York')}</p>

      <div className="card-grid" style={{ marginTop: 'var(--space-4)' }}>
        {routeIds.map((id) => {
          const route = data.routes[id];
          if (!route) {
            return null;
          }
          return <RouteCard key={id} label={routeLabel(id)} route={route} />;
        })}
      </div>

      {comparison && (
        <section aria-labelledby="comparison-heading" className="card">
          <h3 id="comparison-heading" className="section-title" style={{ marginTop: 0 }}>
            Comparison
          </h3>
          <p>{comparison.note}</p>
        </section>
      )}

      <section aria-labelledby="provenance-heading" className="card">
        <h3 id="provenance-heading" className="section-title" style={{ marginTop: 0 }}>
          Inputs and provenance
        </h3>
        <ul className="note">
          <li>Precipitation: {data.inputs_provenance.sources.precipitation}</li>
          <li>Alerts: {data.inputs_provenance.sources.alerts}</li>
        </ul>
        <p className="note">Retrieved {data.inputs_provenance.retrieved_utc}.</p>
        <p className="note">
          {data.inputs_provenance.zone_coded_alert_rows_excluded} zone-coded alert rows were not
          mapped to a county and are excluded from this replay.
        </p>
        <p className="note">{data.route_fixture_provenance}</p>
      </section>
    </section>
  );
}
