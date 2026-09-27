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
import markerIcon2x from 'leaflet/dist/images/marker-icon-2x.png';
import markerIcon from 'leaflet/dist/images/marker-icon.png';
import markerShadow from 'leaflet/dist/images/marker-shadow.png';
import { Fragment, useEffect } from 'react';
import {
  MapContainer,
  Marker,
  Polyline,
  Popup,
  TileLayer,
  useMap,
  ZoomControl,
} from 'react-leaflet';

import { splitRouteAtSegment } from '@/utils/routeSegments';
import type { Location } from '@/types/trip';

const defaultIcon = L.icon({
  iconUrl: markerIcon,
  iconRetinaUrl: markerIcon2x,
  shadowUrl: markerShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
});

const dangerIcon = L.divIcon({
  className: 'danger-marker',
  html: '<span>!</span>',
  iconSize: [26, 26],
  iconAnchor: [13, 13],
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

interface LiveRouteMapProps {
  origin: Location;
  destination: Location;
  routes: RouteRender[];
  dangerMarker?: { position: [number, number]; label: string } | null;
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
      <Marker position={[origin.lat, origin.lon]} icon={defaultIcon} />
      <Marker position={[destination.lat, destination.lon]} icon={defaultIcon} />
      {dangerMarker && (
        <Marker position={dangerMarker.position} icon={dangerIcon}>
          <Popup>{dangerMarker.label}</Popup>
        </Marker>
      )}
      <FitToRoutes routes={routes} />
      <ZoomControl position="bottomright" />
    </MapContainer>
  );
}
