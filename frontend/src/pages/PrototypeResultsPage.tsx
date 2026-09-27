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
import type { PrototypeResult, PrototypeRoute } from '@/types/prototype';

const result = prototypeResult as PrototypeResult;

const DATA_STATUS_LABEL: Record<string, string> = {
  complete: 'Complete data',
  partial_weather: 'Partial weather data',
  missing_weather: 'Missing weather data',
};

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
    <article aria-labelledby={`route-heading-${label}`}>
      <h3 id={`route-heading-${label}`}>
        {label}: {route.trip_label}
      </h3>
      <p>
        {route.distance_km} km &middot; {Math.round(route.duration_minutes)} min &middot; departure
        decision at {formatInstant(route.decision_time_utc, 'UTC')}
      </p>

      {alerts.length > 0 && (
        <div role="alert" aria-label={`Official alerts for ${label}`}>
          <h4>Official alerts</h4>
          <ul>
            {alerts.map((alert) => (
              <li key={alert}>{alert}</li>
            ))}
          </ul>
        </div>
      )}

      <p>{route.advisory}</p>

      {route.highest_concern_segment && (
        <section aria-label={`Highest-concern segment for ${label}`}>
          <h4>
            Highest-concern segment: {route.highest_concern_segment.county_name} (
            {route.highest_concern_segment.label})
          </h4>
          <p>{route.highest_concern_segment.reason}</p>
          <p>Arrival: {formatInstant(route.highest_concern_segment.arrival_utc, 'UTC')}</p>
        </section>
      )}

      <h4>Route timeline</h4>
      <table>
        <caption>County stretches for {label}, in order of arrival</caption>
        <thead>
          <tr>
            <th scope="col">County</th>
            <th scope="col">Arrival (UTC)</th>
            <th scope="col">Prototype indicator</th>
            <th scope="col">Data status</th>
          </tr>
        </thead>
        <tbody>
          {route.segments.map((segment) => (
            <tr key={`${segment.county_fips}-${segment.arrival_utc}`}>
              <td>{segment.county_name}</td>
              <td>{formatInstant(segment.arrival_utc, 'UTC')}</td>
              <td>{segment.label}</td>
              <td>{DATA_STATUS_LABEL[segment.data_status] ?? segment.data_status}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {route.unassessed_segments.length > 0 && (
        <p role="note">Not assessed: {route.unassessed_segments.join(', ')}</p>
      )}

      <p role="note">{route.replay_caveat}</p>
    </article>
  );
}

export default function PrototypeResultsPage() {
  const routeIds = Object.keys(result.routes);
  const comparison = result.comparison;

  return (
    <section aria-labelledby="results-heading">
      <h2 id="results-heading">
        {result.origin.label} to {result.destination.label}
      </h2>
      <p role="note">
        Prototype hazard indicator: a rule over rainfall and NWS flood products, based on available
        weather data. It is not a model, not a probability, and not a validated score.
      </p>
      <p>Departing {formatInstant(result.departure_time, 'America/New_York')}</p>

      {routeIds.map((id, index) => {
        const route = result.routes[id];
        if (!route) {
          return null;
        }
        return <RouteCard key={id} label={`Route ${index + 1}`} route={route} />;
      })}

      {comparison && (
        <section aria-labelledby="comparison-heading">
          <h3 id="comparison-heading">Comparison</h3>
          <p>{comparison.note}</p>
          {(() => {
            const bestIndex = routeIds.indexOf(comparison.lower_indicated_concern_route);
            const otherIndex = routeIds.indexOf(comparison.other_route);
            const bestLevel = comparison.levels[comparison.lower_indicated_concern_route];
            const otherLevel = comparison.levels[comparison.other_route];
            const bestLabel =
              bestIndex >= 0 ? `Route ${bestIndex + 1}` : comparison.lower_indicated_concern_route;
            const otherLabel = otherIndex >= 0 ? `Route ${otherIndex + 1}` : comparison.other_route;
            const minutes = Math.abs(comparison.extra_minutes);
            const shorterOrLonger = comparison.extra_minutes <= 0 ? 'shorter' : 'longer';
            return bestLevel === otherLevel ? (
              <p>
                Both routes show the same prototype indicator level; {bestLabel} is {minutes}{' '}
                minutes {shorterOrLonger} than {otherLabel}.
              </p>
            ) : (
              <p>
                {bestLabel} shows a lower prototype indicator level than {otherLabel}, and is{' '}
                {minutes} minutes {shorterOrLonger}. This compares indicator levels only; it does
                not say either route is safe.
              </p>
            );
          })()}
        </section>
      )}

      <section aria-labelledby="provenance-heading">
        <h3 id="provenance-heading">Inputs and provenance</h3>
        <ul>
          <li>Precipitation: {result.inputs_provenance.sources.precipitation}</li>
          <li>Alerts: {result.inputs_provenance.sources.alerts}</li>
        </ul>
        <p>Retrieved {result.inputs_provenance.retrieved_utc}.</p>
        <p>
          {result.inputs_provenance.zone_coded_alert_rows_excluded} zone-coded alert rows were not
          mapped to a county and are excluded from this replay.
        </p>
        <p>{result.route_fixture_provenance}</p>
      </section>
    </section>
  );
}
