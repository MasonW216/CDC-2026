/**
 * Helene case study map: real NC county boundaries (public/nc_counties.geojson,
 * Census TIGER via data/sample/nc_counties_2024.geojson -- see data_card.md).
 *
 * Two layers of real, modeled county color, not one: every county in the state gets a
 * faint fill from `county_risk` (its own indicator at the case study's departure
 * instant, the same rule as a route stretch -- see historical_case_study.py's
 * `statewide_county_risk`), so the surrounding region's real risk pattern is visible,
 * not just the two sampled routes. A county the active route actually passes through is
 * drawn on top with its route-specific segment score (own arrival time, can differ from
 * the departure-instant snapshot) at full opacity and a bold outline, so the route still
 * reads clearly against the statewide backdrop instead of blending into it -- real
 * visual justification for why one route was the lower-concern choice, using the actual
 * regional pattern, not an assertion.
 *
 * Yellow (Elevated), orange (High), red (Severe) -- the same accessible --level-N-fg
 * tokens as every badge and gauge elsewhere, not new colors invented for this map.
 *
 * Color is never the only channel: hovering (or tabbing to, for keyboard users) a
 * colored county opens a tooltip naming the county and its band in words, and clicking a
 * route county syncs with the county rail below the map (same `activeIndex`) -- one
 * interaction, two views of the same selection. A non-route county's tooltip names its
 * own statewide snapshot instead, clearly labeled as such, and is not clickable (it
 * isn't a stretch of this route -- nothing to select).
 *
 * The route line and endpoint markers come from `route.geometry`, real OSRM road
 * geometry already in the score response (the same real routing call that produced the
 * route's counties, sampled when the fixture was built) -- not historical routing, so
 * this page never claims to show which roads were actually closed during Helene (see
 * "Known limits"). Solid and bold, not dashed, so it reads clearly against the county
 * fills underneath it.
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

import type { CountyRiskEntry, RouteScore, SegmentScore } from '@/types/score';
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
  /** Every county's own indicator at the case study's departure instant (statewide
   * context, not route-specific). See `CaseStudyInfo.county_risk`. */
  countyRisk: Record<string, CountyRiskEntry>;
}

function levelFillForBand(band: string | undefined): string | null {
  if (!band) return null;
  const level = BAND_LEVEL[band];
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
  countyRisk,
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
    if (entry) {
      const fill = levelFillForBand(entry.segment.band);
      const active = entry.index === activeIndex;
      if (!fill) {
        return { fillOpacity: 0, color: 'var(--color-border-strong)', weight: 1 };
      }
      return {
        fillColor: fill,
        fillOpacity: active ? 0.75 : 0.5,
        color: active ? 'var(--color-primary)' : fill,
        weight: active ? 3 : 1.5,
      };
    }
    // Statewide context: this county's own real indicator, not this route's, drawn
    // faint underneath so the actual route reads clearly against it.
    const statewide = levelFillForBand(countyRisk[fips]?.band);
    if (!statewide) {
      return { fillOpacity: 0, color: 'var(--color-border-strong)', weight: 1 };
    }
    return {
      fillColor: statewide,
      fillOpacity: 0.18,
      color: 'var(--color-border-strong)',
      weight: 0.75,
    };
  }

  function onEachCounty(feature: Feature, layer: Layer) {
    const fips = String(feature.properties?.GEOID ?? '');
    const name = String(feature.properties?.NAME ?? 'Unknown county');
    const entry = byFips.get(fips);
    if (!entry) {
      const statewide = countyRisk[fips];
      if (statewide?.index !== null && statewide?.index !== undefined) {
        layer.bindTooltip(
          `<strong>${name}</strong><br/>${statewide.band} (${Math.round(statewide.index)}/100)` +
            '<br/><em>Not on this route</em>',
          { sticky: true, direction: 'top' },
        );
      } else {
        layer.bindTooltip(name, { sticky: true });
      }
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
        <>
          {/* A white casing under the colored line, like Google Maps -- the county
              fills underneath are real, saturated color, and a thin line alone got
              lost against them. */}
          <Polyline positions={path} pathOptions={{ color: '#fff', weight: 7, opacity: 0.9 }} />
          <Polyline positions={path} pathOptions={{ color: 'var(--color-primary)', weight: 4 }} />
        </>
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
