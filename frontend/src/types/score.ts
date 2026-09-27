/**
 * Wire contract `prototype-score/1`: the response of the live trip score.
 *
 * Mirrors src/stormroute/scoring/concern.py and docs/prototype_score_spec.md. Change all
 * three together. `index` is a team-defined 0-100 comparison index where higher means
 * more indicated weather concern. It is not a probability. `null` means "not assessed"
 * and is never to be displayed as 0 or as low concern.
 */

export type Band = 'Lower concern' | 'Elevated concern' | 'High concern' | 'Severe concern';
export type Status = 'assessed' | 'partial' | 'unassessed';
export type RankingKind =
  | 'distinguishable'
  | 'tie'
  | 'unavailable'
  | 'single_route'
  | 'no_routes';

export interface AlertUse {
  /** e.g. "Flash Flood Warning" */
  event: string;
  /** 35 watch, 50 advisory, 80 warning, 98 emergency */
  floor: number;
  headline: string | null;
  /** ISO 8601 UTC */
  effective_utc: string | null;
  expires_utc: string | null;
  id: string;
}

export interface SegmentScore {
  county_fips: string;
  county_name: string;
  arrival_utc: string;
  minutes: number;
  km: number;
  status: 'assessed' | 'unassessed';
  index: number | null;
  band: Band | 'Not assessed';
  /** Plain-language reason, shown as written. */
  reason: string;
  rain_rate_mm_h: number | null;
  rain_24h_mm: number | null;
  alerts: AlertUse[];
}

/**
 * One thing that actually drove a stretch's index, built only from fields the rule
 * computed for it (never a fixed list). `kind` is currently only 'rain' or 'alert' --
 * a UI must not render any other factor (e.g. "saturated ground") unless a real input
 * for it exists in this contract; see docs/prototype_score_spec.md.
 */
export interface ContributingFactor {
  kind: 'rain' | 'alert';
  county_name: string;
  /** Short label: an alert's event name, or "Heavy rainfall, <county>". */
  label: string;
  /** The segment's own `reason` text, shown as written. */
  detail: string;
  arrival_utc: string;
  index: number;
}

export interface RouteScore {
  route_id: string;
  duration_minutes: number;
  distance_km: number;
  status: Status;
  /** Highest segment index. A lower bound when status is 'partial'. Null when unassessed. */
  index: number | null;
  band: Band | 'Not assessed';
  is_lower_bound: boolean;
  minutes_at_or_above_50: number;
  highest_concern_segment: SegmentScore | null;
  segments: SegmentScore[];
  /** Deduplicated official alerts on this route, to show above the advice. */
  alerts: AlertUse[];
  /** Short bullet reasons for the route level. */
  reasons: string[];
  /** Up to 3 stretches that actually set the index, for an icon list. May be empty. */
  contributing_factors: ContributingFactor[];
  /**
   * Real road polyline, [lon, lat] pairs (OSRM/GeoJSON order; each inner array has exactly
   * 2 numbers, typed as number[] rather than a tuple only so JSON-imported test fixtures
   * satisfy the type without an unsafe cast). Null means no real geometry is available --
   * fall back to a schematic line through segment county centers and say so; never draw
   * nothing, and never present a schematic line as the real road.
   */
  geometry: number[][] | null;
}

/**
 * A later departure that lowers the index by a real margin, or null if none does.
 * `duration_minutes` does not change between offsets: no live-traffic model here.
 */
export interface BetterDeparture {
  offset_hours: number;
  extra_wait_minutes: number;
  departure_utc: string;
  index_before: number;
  index_after: number;
  /** The sentence to show, already states the "same route, no faster drive" caveat. */
  message: string;
}

export interface Comparison {
  ranking: RankingKind;
  fastest_route_id: string | null;
  /** Null unless ranking is 'distinguishable'. */
  lowest_concern_route_id: string | null;
  /** Lowest-concern route minutes minus fastest route minutes; 0 when same route. */
  extra_minutes: number | null;
  /** Fastest route index minus lowest-concern route index. */
  index_difference: number | null;
  /** The sentence to show. */
  message: string;
  /** Extra advice line when concern is severe on every route, else null. */
  severe_advice: string | null;
}

export interface Coverage {
  forecast: {
    source: string;
    retrieved_utc: string;
    /** Minutes between `requested_at_utc` and `retrieved_utc`. Show this, not just `from_cache`. */
    age_minutes: number;
    horizon_hours: number;
    /** Counties with no usable forecast hours. */
    missing_counties: string[];
    from_cache: boolean;
    /** Set when the forecast could not be fetched and no cache existed. */
    error: string | null;
  };
  alerts: {
    source: string;
    retrieved_utc: string;
    age_minutes: number;
    ok: boolean;
    error: string | null;
    from_cache: boolean;
    /** Flood alerts that could not be matched to a county. */
    unmapped_alerts: number;
    flood_alerts_in_effect_statewide: number;
  };
  geography: { supported: boolean; message: string | null };
}

/** Present only when `mode === 'historical_case_study'` (GET /api/v1/demo/helene). */
export interface CaseStudyInfo {
  name: string;
  period: string;
  note: string;
  origin: { label: string; lat: number; lon: number };
  destination: { label: string; lat: number; lon: number };
}

export interface ScoreResponse {
  schema_version: 'prototype-score/1';
  score_name: string;
  /**
   * 'live': a new trip, scored just now. 'cached': replayed from saved upstream responses
   * (a contemporary trip, offline fallback). 'historical_case_study': the standalone Helene
   * page (GET /api/v1/demo/helene) — never returned by POST /api/v1/trips/score, and never
   * to be shown as, or confused with, a live or cached trip result.
   */
  mode: 'live' | 'cached' | 'historical_case_study';
  requested_at_utc: string;
  departure_utc: string;
  routes: RouteScore[];
  comparison: Comparison;
  coverage: Coverage;
  /** Every alert across all routes, for the banner above any recommendation. */
  alerts: AlertUse[];
  better_departure: BetterDeparture | null;
  limitations: string[];
  /** Only present when mode === 'historical_case_study'. */
  case_study?: CaseStudyInfo;
}
