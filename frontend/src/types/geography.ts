/**
 * Shape of `GET /api/v1/geography/counties` (backend/src/stormroute_api/routes/geography.py).
 *
 * The NC county boundary GeoJSON, served unchanged. `GEOID` is the 5-character county FIPS
 * string, the exact same value as `SegmentScore.county_fips` in the score contract -- join
 * on that field, no spatial computation needed client-side.
 */
import type { FeatureCollection, Polygon } from 'geojson';

export interface CountyProperties {
  STATEFP: string;
  GEOID: string;
  NAME: string;
  ALAND: number;
}

export type CountyBoundaries = FeatureCollection<Polygon, CountyProperties>;
