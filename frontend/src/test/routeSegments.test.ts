import { splitRouteAtSegment } from '../utils/routeSegments';

// A straight north-south line at the equator, longitude 0, 0.01 degrees apart.
// 1 degree of latitude is ~111.19 km, so 11 points span roughly 11.1 km.
const STRAIGHT_PATH: [number, number][] = Array.from({ length: 12 }, (_, i) => [i * 0.01, 0]);

describe('splitRouteAtSegment', () => {
  it('returns the whole path as "before" when nothing is highlighted', () => {
    const result = splitRouteAtSegment(STRAIGHT_PATH, [4, 4, 4], null);
    expect(result.before).toEqual(STRAIGHT_PATH);
    expect(result.highlighted).toEqual([]);
    expect(result.after).toEqual([]);
  });

  it('highlights roughly the middle third for the middle segment of three equal segments', () => {
    const result = splitRouteAtSegment(STRAIGHT_PATH, [4, 4, 4], 1);
    // The path covers ~11.1 km; segments sum to 12, so scale is ~0.925.
    // Middle segment should start around km 3.7 and end around km 7.4.
    const firstHighlightedLat = result.highlighted[0]![0];
    const lastHighlightedLat = result.highlighted[result.highlighted.length - 1]![0];
    expect(firstHighlightedLat).toBeGreaterThan(0.02);
    expect(firstHighlightedLat).toBeLessThan(0.045);
    expect(lastHighlightedLat).toBeGreaterThan(0.06);
    expect(lastHighlightedLat).toBeLessThan(0.085);
    // before ends where highlighted starts, after starts where highlighted ends.
    expect(result.before[result.before.length - 1]).toEqual(result.highlighted[0]);
    expect(result.after[0]).toEqual(result.highlighted[result.highlighted.length - 1]);
  });

  it('highlighting the first segment leaves "before" as just the start point', () => {
    const result = splitRouteAtSegment(STRAIGHT_PATH, [4, 4, 4], 0);
    expect(result.before.length).toBe(1);
    expect(result.before[0]![0]).toBeCloseTo(0, 5);
  });

  it('highlighting the last segment leaves "after" as just the end point', () => {
    const result = splitRouteAtSegment(STRAIGHT_PATH, [4, 4, 4], 2);
    expect(result.after.length).toBe(1);
    expect(result.after[0]![0]).toBeCloseTo(STRAIGHT_PATH[STRAIGHT_PATH.length - 1]![0], 3);
  });

  it('covers the full path with no gaps: before + highlighted + after span start to end', () => {
    const result = splitRouteAtSegment(STRAIGHT_PATH, [4, 4, 4], 1);
    expect(result.before[0]).toEqual(STRAIGHT_PATH[0]);
    expect(result.after[result.after.length - 1]).toEqual(STRAIGHT_PATH[STRAIGHT_PATH.length - 1]);
  });

  it('degrades to the whole path when segment data is empty or zero-length', () => {
    expect(splitRouteAtSegment(STRAIGHT_PATH, [], 0)).toEqual({
      before: STRAIGHT_PATH,
      highlighted: [],
      after: [],
    });
    expect(splitRouteAtSegment(STRAIGHT_PATH, [0, 0], 0)).toEqual({
      before: STRAIGHT_PATH,
      highlighted: [],
      after: [],
    });
  });
});
