/**
 * Split a route's raw path geometry so one stretch (the highest-concern
 * county) can be drawn in a different color -- "where it might be dangerous
 * on the road."
 *
 * The backend gives two things that don't share a coordinate system: OSRM's
 * raw lat/lon polyline (GET /api/v1/routing/route) and a list of per-county
 * segments with a distance in km each, in order along the route (POST
 * /api/v1/trips/score). Neither says which lat/lon points belong to which
 * county. This reconstructs that by walking the polyline's own cumulative
 * distance (haversine between consecutive points) and cutting it at the
 * highlighted segment's start/end distance.
 *
 * The segments' own km values rarely sum to exactly the polyline's real
 * length (independent measurements, rounding), so the cut points are scaled
 * proportionally onto the polyline's actual length rather than taken as
 * literal km along it -- an approximation, not a fabricated exact location,
 * and it degrades gracefully (a small mismatch shifts the highlighted
 * stretch slightly; it does not put it in the wrong county's neighborhood).
 */

const EARTH_RADIUS_KM = 6371;

function haversineKm(a: [number, number], b: [number, number]): number {
  const [lat1, lon1] = a;
  const [lat2, lon2] = b;
  const dLat = ((lat2 - lat1) * Math.PI) / 180;
  const dLon = ((lon2 - lon1) * Math.PI) / 180;
  const rLat1 = (lat1 * Math.PI) / 180;
  const rLat2 = (lat2 * Math.PI) / 180;
  const sinDLat = Math.sin(dLat / 2);
  const sinDLon = Math.sin(dLon / 2);
  const h = sinDLat * sinDLat + Math.cos(rLat1) * Math.cos(rLat2) * sinDLon * sinDLon;
  return 2 * EARTH_RADIUS_KM * Math.asin(Math.min(1, Math.sqrt(h)));
}

function cumulativeDistances(path: [number, number][]): number[] {
  const cumulative = [0];
  for (let i = 1; i < path.length; i += 1) {
    cumulative.push(cumulative[i - 1]! + haversineKm(path[i - 1]!, path[i]!));
  }
  return cumulative;
}

/** The point at `targetKm` along `path`, given its precomputed `cumulative` distances. */
function pointAtDistance(
  path: [number, number][],
  cumulative: number[],
  targetKm: number,
): [number, number] {
  const clamped = Math.max(0, Math.min(cumulative[cumulative.length - 1]!, targetKm));
  for (let i = 1; i < cumulative.length; i += 1) {
    if (cumulative[i]! >= clamped) {
      const segStart = cumulative[i - 1]!;
      const segEnd = cumulative[i]!;
      const t = segEnd > segStart ? (clamped - segStart) / (segEnd - segStart) : 0;
      const [lat1, lon1] = path[i - 1]!;
      const [lat2, lon2] = path[i]!;
      return [lat1 + (lat2 - lat1) * t, lon1 + (lon2 - lon1) * t];
    }
  }
  return path[path.length - 1]!;
}

export interface SplitRoute {
  before: [number, number][];
  highlighted: [number, number][];
  after: [number, number][];
}

/**
 * `path`: (lat, lon) pairs, in order along the route (Leaflet order already).
 * `segmentKm`: each segment's own distance, in the same order as the route.
 * `highlightIndex`: index into `segmentKm` to highlight, or null for none.
 */
export function splitRouteAtSegment(
  path: [number, number][],
  segmentKm: number[],
  highlightIndex: number | null,
): SplitRoute {
  if (highlightIndex === null || path.length < 2 || segmentKm.length === 0) {
    return { before: path, highlighted: [], after: [] };
  }
  const segmentTotalKm = segmentKm.reduce((sum, km) => sum + km, 0);
  const cumulative = cumulativeDistances(path);
  const pathTotalKm = cumulative[cumulative.length - 1]!;
  if (segmentTotalKm <= 0 || pathTotalKm <= 0) {
    return { before: path, highlighted: [], after: [] };
  }
  const scale = pathTotalKm / segmentTotalKm;
  const startKm = segmentKm.slice(0, highlightIndex).reduce((sum, km) => sum + km, 0) * scale;
  const endKm = startKm + segmentKm[highlightIndex]! * scale;

  const startPoint = pointAtDistance(path, cumulative, startKm);
  const endPoint = pointAtDistance(path, cumulative, endKm);
  const beforePoints = path.filter((_point, i) => cumulative[i]! < startKm);
  const highlightedPoints = path.filter(
    (_point, i) => cumulative[i]! >= startKm && cumulative[i]! <= endKm,
  );
  const afterPoints = path.filter((_point, i) => cumulative[i]! > endKm);

  return {
    before: [...beforePoints, startPoint],
    highlighted: [startPoint, ...highlightedPoints, endPoint],
    after: [endPoint, ...afterPoints],
  };
}
