/**
 * Shared rendering for a `prototype-score/1` response (types/score.ts).
 *
 * Used by both PrototypeResultsPage (live/cached trip results) and
 * HeleneCaseStudyPage (the standalone historical replay) so a route, a level, and an
 * alert list look identical wherever a score is shown -- one set of components, not a
 * duplicate per page. Extracted here rather than exported from a page file so React
 * Fast Refresh stays happy (a page file should export only its component).
 *
 * Layout rule inherited by every caller: official NWS alerts render above any advisory
 * or recommendation, never below or beside it.
 */
import RiskGauge from '@/components/RiskGauge';
import { BAND_CLASS, formatInstant } from '@/utils/scoreDisplay';
import type { AlertUse, RouteScore } from '@/types/score';

/** Color is always paired with the text label (`band`), never used alone. */
export function LevelBadge({ band, index }: { band: string; index: number | null }) {
  return (
    <span className={`level-badge ${BAND_CLASS[band] ?? 'level-badge--none'}`}>
      {band}
      {index !== null ? ` (${Math.round(index)}/100)` : ''}
    </span>
  );
}

export function AlertList({ alerts }: { alerts: AlertUse[] }) {
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

export function RouteCard({ label, route }: { label: string; route: RouteScore }) {
  return (
    <article className="card" aria-labelledby={`route-heading-${label}`}>
      <h3 id={`route-heading-${label}`} className="subsection-title" style={{ marginTop: 0 }}>
        {label}: <LevelBadge band={route.band} index={route.index} />
      </h3>
      <RiskGauge index={route.index} band={route.band} />
      <p className="note" style={{ textAlign: 'center' }}>
        {route.distance_km} km &middot; {Math.round(route.duration_minutes)} min
        {route.status !== 'assessed' ? ` · ${route.status}` : ''}
      </p>
      {route.is_lower_bound && (
        <p role="note" className="note" style={{ textAlign: 'center' }}>
          This index is a lower bound: some inputs for this route are missing, so the true concern
          could be higher.
        </p>
      )}

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
