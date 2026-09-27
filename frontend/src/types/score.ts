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
    ok: boolean;
    error: string | null;
    from_cache: boolean;
    /** Flood alerts that could not be matched to a county. */
    unmapped_alerts: number;
    flood_alerts_in_effect_statewide: number;
  };
  geography: { supported: boolean; message: string | null };
}

export interface ScoreResponse {
  schema_version: 'prototype-score/1';
  score_name: string;
  /** 'live' for a new trip, 'cached' when replayed from saved upstream responses. */
  mode: 'live' | 'cached';
  requested_at_utc: string;
  departure_utc: string;
  routes: RouteScore[];
  comparison: Comparison;
  coverage: Coverage;
  /** Every alert across all routes, for the banner above any recommendation. */
  alerts: AlertUse[];
  limitations: string[];
}
