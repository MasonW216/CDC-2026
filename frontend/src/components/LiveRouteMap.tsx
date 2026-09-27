/**
 * The map: real OSRM route geometry, colored by role (recommended / current /
 * alternative), with the actual highest-concern county stretch of the
 * recommended route drawn in a different color -- not an illustration, a real
 * cut of the polyline at that segment's real distance (utils/routeSegments).
 *
 * Color is never the only channel: the legend spells out what each color
 * means in words, and the danger marker carries a text label.
 */
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { Fragment, useEffect } from 'react';
import {
  MapContainer,
  Marker,
  Polyline,
  Popup,
  TileLayer,
  Tooltip,
  useMap,
  ZoomControl,
} from 'react-leaflet';

import { splitRouteAtSegment } from '@/utils/routeSegments';
import type { Location } from '@/types/trip';

// Rider-app style endpoints: a ringed dot for the start, a solid square for
// the end. Pure CSS divIcons (styles.css .trip-endpoint), no image assets.
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

const dangerIcon = L.divIcon({
  className: 'danger-marker',
  html: '<span>!</span>',
  iconSize: [28, 28],
  iconAnchor: [14, 14],
});

export interface RouteRender {
  id: string;
  /** (lat, lon) pairs, Leaflet order -- the caller reverses OSRM's (lon, lat). */
  path: [number, number][];
  color: string;
  dashed?: boolean;
  weight?: number;
  /** The one county stretch to draw in a different color, if any. */
  highlight?: { segmentKm: number[]; index: number; color: string } | null;
}

/** Back-compat name for callers with no per-segment highlight (e.g. LiveRoutePage). */
export type ColoredRoute = RouteRender;

export interface DangerMarker {
  position: [number, number];
  countyName: string;
  band: string;
  index: number | null;
  arrivalLabel: string;
  /** The segment's own real `reason` text -- what actually drove the score (rainfall,
   * an official alert, or county history), never an unexplained icon. */
  reason: string;
}

interface LiveRouteMapProps {
  origin: Location;
  destination: Location;
  routes: RouteRender[];
  dangerMarker?: DangerMarker | null;
}

function FitToRoutes({ routes }: { routes: RouteRender[] }) {
  const map = useMap();
  useEffect(() => {
    const allPoints = routes.flatMap((route) => route.path);
    if (allPoints.length > 0) {
      map.fitBounds(L.latLngBounds(allPoints), { padding: [32, 32] });
    }
  }, [map, routes]);
  return null;
}

export default function LiveRouteMap({
  origin,
  destination,
  routes,
  dangerMarker,
}: LiveRouteMapProps) {
  const center: [number, number] = routes[0]?.path[0] ?? [origin.lat, origin.lon];

  return (
    <MapContainer
      center={center}
      zoom={8}
      zoomControl={false}
      style={{ height: '100%', width: '100%' }}
    >
      {/* Plain OSM tiles -- verified working with no API key. A CSS filter on
          .muted-tiles (styles.css) desaturates them to match the reference's
          muted basemap without depending on a tile provider that might start
          requiring a key (as CARTO's free tier did -- see git history). */}
      <TileLayer
        className="muted-tiles"
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        maxZoom={19}
      />
      {routes.map((route) => {
        if (!route.highlight) {
          return (
            <Polyline
              key={route.id}
              positions={route.path}
              pathOptions={{
                color: route.color,
                weight: route.weight ?? 4,
                dashArray: route.dashed ? '10 8' : undefined,
              }}
            />
          );
        }
        const { before, highlighted, after } = splitRouteAtSegment(
          route.path,
          route.highlight.segmentKm,
          route.highlight.index,
        );
        return (
          <Fragment key={route.id}>
            {[before, after].map((part, i) =>
              part.length > 1 ? (
                <Polyline
                  key={`${route.id}-base-${i}`}
                  positions={part}
                  pathOptions={{
                    color: route.color,
                    weight: route.weight ?? 4,
                    dashArray: route.dashed ? '10 8' : undefined,
                  }}
                />
              ) : null,
            )}
            {highlighted.length > 1 && (
              <Polyline
                positions={highlighted}
                pathOptions={{ color: route.highlight.color, weight: (route.weight ?? 4) + 1 }}
              />
            )}
          </Fragment>
        );
      })}
      <Marker position={[origin.lat, origin.lon]} icon={originIcon} />
      <Marker position={[destination.lat, destination.lon]} icon={destinationIcon} />
      {dangerMarker && (
        <Marker position={dangerMarker.position} icon={dangerIcon}>
          <Tooltip direction="top" offset={[0, -14]}>
            Highest-concern stretch on this route &mdash; click for why
          </Tooltip>
          <Popup>
            <strong>{dangerMarker.countyName}</strong>
            {' — '}
            {dangerMarker.band}
            {dangerMarker.index !== null ? ` (${Math.round(dangerMarker.index)}/100)` : ''}
            <br />
            <span style={{ opacity: 0.75 }}>Arrival {dangerMarker.arrivalLabel}</span>
            <p style={{ margin: '0.4em 0 0' }}>{dangerMarker.reason}</p>
          </Popup>
        </Marker>
      )}
      <FitToRoutes routes={routes} />
      <ZoomControl position="topright" />
    </MapContainer>
  );
}
