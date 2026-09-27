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
import AlertSummary from './AlertSummary';
import ContributingFactorChips from './ContributingFactorChips';
import RouteMap from './RouteMap';
import type { CountyBoundaries } from '@/types/geography';
import type { AlertUse, RouteScore } from '@/types/score';
import { BAND_CLASS, formatInstant } from '@/utils/scoreDisplay';

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

interface RouteCardProps {
  label: string;
  route: RouteScore;
  origin: { lat: number; lon: number };
  destination: { lat: number; lon: number };
  counties: CountyBoundaries | null;
}

export function RouteCard({ label, route, origin, destination, counties }: RouteCardProps) {
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

      <AlertSummary route={route} />

      <ContributingFactorChips factors={route.contributing_factors} />

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

      <h4 className="subsection-title">Route map</h4>
      <p className="note" style={{ marginTop: 0 }}>
        Counties this route crosses, colored by indicated concern. Click or tap a county for
        detail.
      </p>
      <RouteMap origin={origin} destination={destination} route={route} counties={counties} />
    </article>
  );
}
