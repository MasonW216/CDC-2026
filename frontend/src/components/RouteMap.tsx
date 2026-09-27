/**
 * Interactive map for one scored route: real road geometry, county shapes colored and
 * outlined by concern level, hover/click for detail. Replaces the old plain HTML
 * county-timeline table and the flat repeated alert list with a real, geographic,
 * interactive view -- the point of this component.
 *
 * Not `LiveRouteMap` (the `/route` dev preview, whole-route single color, no per-county
 * detail) -- that component and its page are left untouched. This is the sibling the old
 * component's own doc comment already anticipated ("Not the milestone-7 RouteMap
 * (per-segment hazard styling over a scored route)").
 *
 * Color is never the only channel: every colored county is also outlined, and its band is
 * always stated in words in the popup (the same rule `LevelBadge` already follows). County
 * shapes come from GET /api/v1/geography/counties, joined to `route.segments` by
 * `county_fips` === the GeoJSON's `GEOID` -- no server-side spatial logic needed.
 */
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import markerIcon2x from 'leaflet/dist/images/marker-icon-2x.png';
import markerIcon from 'leaflet/dist/images/marker-icon.png';
import markerShadow from 'leaflet/dist/images/marker-shadow.png';
import { useEffect, useMemo } from 'react';
import { GeoJSON, MapContainer, Marker, Polyline, TileLayer, useMap, ZoomControl } from 'react-leaflet';

import type { CountyBoundaries, CountyProperties } from '@/types/geography';
import type { RouteScore, SegmentScore } from '@/types/score';
import { BAND_CLASS, formatInstant } from '@/utils/scoreDisplay';

import type { Feature, Polygon } from 'geojson';
import type { Layer, Path, PathOptions } from 'leaflet';

const defaultIcon = L.icon({
  iconUrl: markerIcon,
  iconRetinaUrl: markerIcon2x,
  shadowUrl: markerShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
});

// Same tokens LevelBadge uses (styles.css), so a county shape and its text badge always
// agree, and dark mode is inherited for free -- these are CSS custom property references,
// not literal colors, and Leaflet's SVG paths honor them like any other SVG paint value.
const FILL_VAR: Record<string, string> = {
  'Lower concern': 'var(--level-0-fg)',
  'Elevated concern': 'var(--level-1-fg)',
  'High concern': 'var(--level-2-fg)',
  'Severe concern': 'var(--level-3-fg)',
  'Not assessed': 'var(--level-none-fg)',
};

interface RouteMapProps {
  origin: { lat: number; lon: number };
  destination: { lat: number; lon: number };
  route: RouteScore;
  counties: CountyBoundaries | null;
}

function escapeHtml(text: string): string {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

/** Popup content built as an HTML string -- Leaflet's per-feature popups bind outside React. */
function popupHtml(props: CountyProperties, segment: SegmentScore | undefined): string {
  if (!segment) {
    return `<strong>${escapeHtml(props.NAME)} County</strong><p class="note">Not on this route.</p>`;
  }
  const alerts = segment.alerts
    .map((a) => `<li>${escapeHtml(a.event)}${a.headline ? `: ${escapeHtml(a.headline)}` : ''}</li>`)
    .join('');
  const badgeClass = BAND_CLASS[segment.band] ?? 'level-badge--none';
  return `
    <strong>${escapeHtml(segment.county_name)} County</strong>
    <p><span class="level-badge ${badgeClass}">${escapeHtml(segment.band)}${segment.index !== null ? ` (${Math.round(segment.index)}/100)` : ''}</span></p>
    ${alerts ? `<div class="alert-banner"><h4>Official NWS flood products</h4><ul>${alerts}</ul></div>` : ''}
    <p>${escapeHtml(segment.reason)}</p>
    <p class="note">Arrival: ${escapeHtml(formatInstant(segment.arrival_utc))}</p>
  `;
}

/** A crude but adequate centroid: the mean of a polygon's outer-ring vertices. */
function polygonCentroid(polygon: Feature<Polygon, CountyProperties>): [number, number] {
  const ring = polygon.geometry.coordinates[0] ?? [];
  let sumLon = 0;
  let sumLat = 0;
  for (const point of ring) {
    sumLon += point[0] ?? 0;
    sumLat += point[1] ?? 0;
  }
  return ring.length > 0 ? [sumLat / ring.length, sumLon / ring.length] : [0, 0];
}

function FitToBounds({ points }: { points: [number, number][] }) {
  const map = useMap();
  useEffect(() => {
    if (points.length === 0) return;
    if (points.length === 1) {
      map.setView(points[0]!, 10);
      return;
    }
    map.fitBounds(L.latLngBounds(points), { padding: [32, 32] });
  }, [map, points]);
  return null;
}

export default function RouteMap({ origin, destination, route, counties }: RouteMapProps) {
  const segmentByFips = useMemo(() => {
    const map = new Map<string, SegmentScore>();
    for (const segment of route.segments) {
      if (segment.county_fips) map.set(segment.county_fips, segment);
    }
    return map;
  }, [route.segments]);

  const hasRealGeometry = Boolean(route.geometry && route.geometry.length > 0);
  const polylinePoints: [number, number][] = useMemo(() => {
    if (route.geometry) {
      return route.geometry.map((point): [number, number] => [point[1] ?? 0, point[0] ?? 0]);
    }
    if (!counties) return [];
    // Schematic fallback: a straight line through each touched county's centroid, in
    // arrival order, only used when no real road geometry was returned.
    return route.segments
      .filter((s) => s.county_fips)
      .map((s) => counties.features.find((f) => f.properties.GEOID === s.county_fips))
      .filter((f): f is Feature<Polygon, CountyProperties> => Boolean(f))
      .map(polygonCentroid);
  }, [route.geometry, route.segments, counties]);

  const featureStyle = (feature?: Feature<Polygon, CountyProperties>): PathOptions => {
    const segment = feature && segmentByFips.get(feature.properties.GEOID);
    if (!segment) {
      return { color: 'var(--color-border)', weight: 1, fillOpacity: 0, opacity: 0.5 };
    }
    const fill = FILL_VAR[segment.band] ?? FILL_VAR['Not assessed']!;
    return { color: fill, weight: 2, fillColor: fill, fillOpacity: 0.45, opacity: 0.9 };
  };

  const onEachFeature = (feature: Feature<Polygon, CountyProperties>, layer: Layer) => {
    const segment = segmentByFips.get(feature.properties.GEOID);
    layer.bindPopup(popupHtml(feature.properties, segment));
    if (!segment) return; // untouched counties are outline-only, not interactive
    const path = layer as Path;
    const normal = featureStyle(feature);
    layer.on({
      mouseover: () => path.setStyle({ weight: 4, fillOpacity: 0.7 }),
      mouseout: () => path.setStyle(normal),
    });
  };

  const boundsPoints: [number, number][] =
    polylinePoints.length > 0 ? polylinePoints : [[origin.lat, origin.lon]];

  return (
    <div className="route-map">
      {!hasRealGeometry && polylinePoints.length > 0 && (
        <p className="note" role="note">
          Road path not available for this replay; route shown schematically by county.
        </p>
      )}
      <MapContainer
        center={[origin.lat, origin.lon]}
        zoom={8}
        zoomControl={false}
        style={{ height: '100%', width: '100%' }}
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          maxZoom={19}
        />
        {counties && (
          <GeoJSON
            key={route.route_id}
            data={counties}
            style={featureStyle as (feature?: GeoJSON.Feature) => PathOptions}
            onEachFeature={onEachFeature as (feature: GeoJSON.Feature, layer: Layer) => void}
          />
        )}
        {polylinePoints.length > 0 && (
          <Polyline
            positions={polylinePoints}
            pathOptions={{
              color: 'var(--color-primary)',
              weight: 4,
              opacity: 0.9,
              dashArray: hasRealGeometry ? undefined : '8 6',
            }}
          />
        )}
        <Marker position={[origin.lat, origin.lon]} icon={defaultIcon} />
        <Marker position={[destination.lat, destination.lon]} icon={defaultIcon} />
        <FitToBounds points={boundsPoints} />
        <ZoomControl position="bottomright" />
      </MapContainer>
    </div>
  );
}
