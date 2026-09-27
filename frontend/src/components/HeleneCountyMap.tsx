/**
 * Helene case study map: real NC county boundaries (public/nc_counties.geojson,
 * Census TIGER via data/sample/nc_counties_2024.geojson -- see data_card.md),
 * each one colored by the concern level this route reports for it -- yellow
 * (Elevated), orange (High), red (Severe) -- using the same accessible
 * --level-N-fg tokens as every badge and gauge elsewhere, not new colors
 * invented for this map. A county the route does not pass through gets no
 * fill, just a thin outline for context.
 *
 * Color is never the only channel: hovering (or tabbing to, for keyboard
 * users) a colored county opens a tooltip naming the county and its band in
 * words, and clicking it syncs with the county rail below the map (same
 * `activeIndex`) -- one interaction, two views of the same selection.
 *
 * The thin route line and endpoint markers come from a live OSRM lookup
 * keyed on the case study's real origin/destination (services/api.fetchRoute),
 * not historical routing -- roads open today aren't guaranteed to match
 * September 2024, which is exactly why this page never claims to show which
 * roads were actually closed (see "Known limits").
 */
import type { Feature, FeatureCollection } from 'geojson';
import L, { type Layer, type PathOptions } from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { useEffect, useMemo } from 'react';
import {
  GeoJSON,
  MapContainer,
  Marker,
  Polyline,
  TileLayer,
  useMap,
  ZoomControl,
} from 'react-leaflet';

import type { RouteScore, SegmentScore } from '@/types/score';
import { BAND_LEVEL } from '@/utils/scoreDisplay';

const originIcon = L.divIcon({
  className: 'trip-endpoint trip-endpoint--origin',
  html: '<span></span>',
  iconSize: [20, 20],
  iconAnchor: [10, 10],
});

const destinationIcon = L.divIcon({
  className: 'trip-endpoint trip-endpoint--destination',
  html: '<span></span>',
  iconSize: [20, 20],
  iconAnchor: [10, 10],
});

interface HeleneCountyMapProps {
  counties: FeatureCollection;
  origin: { lat: number; lon: number };
  destination: { lat: number; lon: number };
  path?: [number, number][] | undefined;
  route: RouteScore;
  activeIndex: number;
  onSelect: (index: number) => void;
}

function levelFill(segment: SegmentScore | undefined): string | null {
  if (!segment) return null;
  const level = BAND_LEVEL[segment.band];
  if (level === 'none' || level === undefined) return null;
  return `var(--level-${level}-fg)`;
}

function FitToLayer({
  counties,
  path,
}: {
  counties: L.Layer | null;
  path?: [number, number][] | undefined;
}) {
  const map = useMap();
  useEffect(() => {
    if (counties && (counties as L.GeoJSON).getBounds().isValid()) {
      map.fitBounds((counties as L.GeoJSON).getBounds(), { padding: [32, 32] });
    } else if (path && path.length > 0) {
      map.fitBounds(L.latLngBounds(path), { padding: [32, 32] });
    }
    // Re-fit only when the thing we fit to changes, not on every render.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [map, counties, path]);
  return null;
}

export default function HeleneCountyMap({
  counties,
  origin,
  destination,
  path,
  route,
  activeIndex,
  onSelect,
}: HeleneCountyMapProps) {
  const byFips = useMemo(() => {
    const map = new Map<string, { segment: SegmentScore; index: number }>();
    route.segments.forEach((segment, index) => {
      map.set(segment.county_fips, { segment, index });
    });
    return map;
  }, [route]);

  const highlighted: FeatureCollection = useMemo(
    () => ({
      type: 'FeatureCollection',
      features: counties.features.filter((f) => byFips.has(String(f.properties?.GEOID))),
    }),
    [counties, byFips],
  );

  function styleFor(feature: Feature | undefined): PathOptions {
    const fips = String(feature?.properties?.GEOID ?? '');
    const entry = byFips.get(fips);
    const fill = levelFill(entry?.segment);
    const active = entry?.index === activeIndex;
    if (!fill) {
      return {
        fillOpacity: 0,
        color: 'var(--color-border-strong)',
        weight: 1,
      };
    }
    return {
      fillColor: fill,
      fillOpacity: active ? 0.75 : 0.5,
      color: active ? 'var(--color-primary)' : fill,
      weight: active ? 3 : 1.5,
    };
  }

  function onEachCounty(feature: Feature, layer: Layer) {
    const fips = String(feature.properties?.GEOID ?? '');
    const name = String(feature.properties?.NAME ?? 'Unknown county');
    const entry = byFips.get(fips);
    if (!entry) {
      layer.bindTooltip(name, { sticky: true });
      return;
    }
    const { segment } = entry;
    const rain =
      segment.rain_24h_mm !== null
        ? `${Math.round(segment.rain_24h_mm)} mm rain over the prior 24h`
        : 'rainfall not available';
    layer.bindTooltip(
      `<strong>${name}</strong><br/>${segment.band}${
        segment.index !== null ? ` (${Math.round(segment.index)}/100)` : ''
      }<br/>${rain}`,
      { sticky: true, direction: 'top' },
    );
    layer.on('click', () => onSelect(entry.index));
  }

  return (
    <MapContainer
      center={[origin.lat, origin.lon]}
      zoom={8}
      zoomControl={false}
      style={{ height: '100%', width: '100%' }}
    >
      <TileLayer
        className="muted-tiles"
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        maxZoom={19}
      />
      <GeoJSON
        key={`${route.route_id}-${activeIndex}`}
        data={counties}
        style={styleFor}
        onEachFeature={onEachCounty}
      />
      {path && path.length > 1 && (
        <Polyline
          positions={path}
          pathOptions={{ color: 'var(--color-primary)', weight: 3, dashArray: '2 8' }}
        />
      )}
      <Marker position={[origin.lat, origin.lon]} icon={originIcon} />
      <Marker position={[destination.lat, destination.lon]} icon={destinationIcon} />
      <FitToLayer
        counties={highlighted.features.length > 0 ? new L.GeoJSON(highlighted) : null}
        path={path}
      />
      <ZoomControl position="topright" />
    </MapContainer>
  );
}
