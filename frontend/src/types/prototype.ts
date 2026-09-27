/**
 * Shape of `fixtures/prototypeResult.json`, the MVP replay result.
 *
 * Mirrors artifacts/demo/prototype_result.json, written by
 * scripts/run_prototype.py. The fixture is a byte copy of that file; a Python test
 * fails if they drift. Keep this separate from types/trip.ts, which mirrors the
 * production API contract.
 *
 * This is a prototype hazard indicator: a rule over rainfall and NWS flood
 * products, not a model, a probability, or a validated score.
 */

export type ConcernLevel = 0 | 1 | 2 | 3;

export interface PrototypeSegment {
  county_fips: string;
  county_name: string;
  /** ISO 8601 UTC, when the traveler is expected to enter this stretch. */
  arrival_utc: string;
  /** Start of the six-hour UTC window containing the arrival. */
  window_start_utc: string;
  /** Null means "Not assessed". It never means low concern. */
  level: ConcernLevel | null;
  /** "Lower concern" | "Elevated concern" | "High concern" | "Severe concern" | "Not assessed" */
  label: string;
  /** Exact explanation to show the user. */
  reason: string;
  sources: string[];
  data_status: 'complete' | 'partial_weather' | 'missing_weather';
  precip_24h_mm: number | null;
  precip_72h_mm: number | null;
  /** Official NWS products in effect at arrival, e.g. "Flash Flood Warning (event GSP-97)". */
  alerts_used: string[];
}

export interface PrototypeRoute {
  indicator_name: string;
  trip_level: ConcernLevel | null;
  trip_label: string;
  highest_concern_segment: PrototypeSegment | null;
  /** Advice text. Show it below any official alerts. */
  advisory: string;
  unassessed_segments: string[];
  segments: PrototypeSegment[];
  decision_time_utc: string;
  duration_minutes: number;
  distance_km: number;
  /** Must be shown on screen. */
  replay_caveat: string;
}

export interface PrototypeResult {
  scenario: string;
  origin: { label: string; lat: number; lon: number };
  destination: { label: string; lat: number; lon: number };
  departure_time: string;
  inputs_provenance: {
    retrieved_utc: string;
    sources: Record<string, string>;
    zone_coded_alert_rows_excluded: number;
  };
  route_fixture_provenance: string;
  routes: Record<string, PrototypeRoute>;
  comparison: {
    lower_indicated_concern_route: string;
    other_route: string;
    levels: Record<string, ConcernLevel>;
    extra_minutes: number;
    note: string;
  } | null;
}
