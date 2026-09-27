/**
 * TypeScript mirror of the API wire contract.
 *
 * Hand-mirrors backend/src/stormroute_api/schemas.py. These two files change
 * together in the same pull request; a silent divergence between them is the most
 * likely cause of a demo that renders undefined.
 *
 * Only the score *request* shape is defined so far (build guide "Score request"
 * example, section 13): the request is what #19 (the planner page) needs to send.
 * ScoreResponse and its nested shapes (RouteSegment, OfficialAlert,
 * Recommendation, ConfidenceReport, Limitation) belong to #18/#20 and stay
 * TODO here until the API defines them, so this file never gets ahead of the
 * contract it mirrors.
 */

/** A named point: a label for display plus WGS84 coordinates. */
export interface Location {
  label: string;
  lat: number;
  lon: number;
}

export type TripMode = 'live' | 'cached_replay';

/** Body of `POST /api/v1/trips/score`. */
export interface TripRequest {
  origin: Location;
  destination: Location;
  /** ISO 8601 with an explicit UTC offset, e.g. "2024-09-27T12:00:00-04:00". */
  departure_time: string;
  mode?: TripMode;
}

// TODO(milestone-6/7): ScoreResponse, RouteSegment, OfficialAlert,
// Recommendation, ConfidenceReport, Limitation. See docs/build_guide.md and
// backend/src/stormroute_api/schemas.py.
