/**
 * Leaflet map showing one or more live-routed driving paths between two
 * points, each colored by the caller (e.g. lower vs. higher modeled weather
 * concern). Color is a hint only: the legend and the AI panel state the same
 * thing in words, since color is never the only channel for risk.
 *
 * Not the milestone-7 RouteMap (per-segment hazard styling over a scored
 * route) -- this is a whole-route preview. OpenStreetMap/CARTO attribution is
 * required by their license and always visible.
 */
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import markerIcon2x from 'leaflet/dist/images/marker-icon-2x.png';
import markerIcon from 'leaflet/dist/images/marker-icon.png';
import markerShadow from 'leaflet/dist/images/marker-shadow.png';
import { useEffect } from 'react';
import { MapContainer, Marker, Polyline, TileLayer, useMap, ZoomControl } from 'react-leaflet';

import type { Location } from '@/types/trip';

// Vite's bundled asset URLs replace Leaflet's default (broken) relative paths.
const defaultIcon = L.icon({
  iconUrl: markerIcon,
  iconRetinaUrl: markerIcon2x,
  shadowUrl: markerShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
});

export interface ColoredRoute {
  id: string;
  /** (lat, lon) pairs, Leaflet order -- the caller reverses OSRM's (lon, lat). */
  path: [number, number][];
  color: string;
  /** Drawn last (on top) and thicker, so it reads as the highlighted route. */
  emphasized?: boolean;
}

interface LiveRouteMapProps {
  origin: Location;
  destination: Location;
  routes: ColoredRoute[];
}

function FitToRoutes({ routes }: { routes: ColoredRoute[] }) {
  const map = useMap();
  useEffect(() => {
    const allPoints = routes.flatMap((route) => route.path);
    if (allPoints.length > 0) {
      map.fitBounds(L.latLngBounds(allPoints), { padding: [32, 32] });
    }
  }, [map, routes]);
  return null;
}

export default function LiveRouteMap({ origin, destination, routes }: LiveRouteMapProps) {
  const center: [number, number] = routes[0]?.path[0] ?? [origin.lat, origin.lon];
  // Draw non-emphasized routes first so the emphasized one sits on top.
  const ordered = [...routes].sort(
    (a, b) => Number(Boolean(a.emphasized)) - Number(Boolean(b.emphasized)),
  );
  return (
    <MapContainer
      center={center}
      zoom={8}
      zoomControl={false}
      style={{ height: '100%', width: '100%' }}
    >
      {/* Standard OSM raster tiles: no key, no account, verified working.
          (CARTO's Positron looked closer to the reference design, but its
          free tier now demands an API key -- checked against the actual
          rendered tiles, not assumed, so switched back to what's confirmed
          to work with zero setup.) */}
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        maxZoom={19}
      />
      {ordered.map((route) => (
        <Polyline
          key={route.id}
          positions={route.path}
          pathOptions={{
            color: route.color,
            weight: route.emphasized ? 6 : 4,
            opacity: route.emphasized ? 0.95 : 0.75,
          }}
        />
      ))}
      <Marker position={[origin.lat, origin.lon]} icon={defaultIcon} />
      <Marker position={[destination.lat, destination.lon]} icon={defaultIcon} />
      <FitToRoutes routes={routes} />
      <ZoomControl position="bottomright" />
    </MapContainer>
  );
}
