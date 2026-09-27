/**
 * Leaflet map showing one live-routed driving path between two points.
 *
 * Not the milestone-7 RouteMap (per-segment hazard styling over a scored
 * route) -- this is a plain path preview with no hazard assessment at all.
 * OpenStreetMap attribution is required by its license and always visible.
 */
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import markerIcon2x from 'leaflet/dist/images/marker-icon-2x.png';
import markerIcon from 'leaflet/dist/images/marker-icon.png';
import markerShadow from 'leaflet/dist/images/marker-shadow.png';
import { useEffect } from 'react';
import { MapContainer, Marker, Polyline, TileLayer, useMap } from 'react-leaflet';

import type { Location } from '@/types/trip';

// Vite's bundled asset URLs replace Leaflet's default (broken) relative paths.
const defaultIcon = L.icon({
  iconUrl: markerIcon,
  iconRetinaUrl: markerIcon2x,
  shadowUrl: markerShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
});

interface LiveRouteMapProps {
  origin: Location;
  destination: Location;
  /** (lat, lon) pairs, Leaflet order -- the caller reverses OSRM's (lon, lat). */
  path: [number, number][];
}

function FitToPath({ path }: { path: [number, number][] }) {
  const map = useMap();
  useEffect(() => {
    if (path.length > 0) {
      map.fitBounds(L.latLngBounds(path), { padding: [24, 24] });
    }
  }, [map, path]);
  return null;
}

export default function LiveRouteMap({ origin, destination, path }: LiveRouteMapProps) {
  const center: [number, number] = path[0] ?? [origin.lat, origin.lon];
  return (
    <MapContainer center={center} zoom={8} style={{ height: '400px', width: '100%' }}>
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
      />
      <Marker position={[origin.lat, origin.lon]} icon={defaultIcon} />
      <Marker position={[destination.lat, destination.lon]} icon={defaultIcon} />
      <Polyline positions={path} pathOptions={{ color: '#1a56db', weight: 5 }} />
      <FitToPath path={path} />
    </MapContainer>
  );
}
