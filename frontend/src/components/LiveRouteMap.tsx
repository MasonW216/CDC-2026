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
    <MapContainer
      center={center}
      zoom={8}
      zoomControl={false}
      style={{ height: '420px', width: '100%' }}
    >
      {/* CARTO's Positron: a muted, low-contrast basemap built on OSM data, so
          route lines and markers stay the focus. Requires OSM + CARTO credit. */}
      <TileLayer
        url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
        subdomains="abcd"
        maxZoom={19}
      />
      <Marker position={[origin.lat, origin.lon]} icon={defaultIcon} />
      <Marker position={[destination.lat, destination.lon]} icon={defaultIcon} />
      <Polyline positions={path} pathOptions={{ color: '#0f766e', weight: 5 }} />
      <FitToPath path={path} />
      <ZoomControl position="bottomright" />
    </MapContainer>
  );
}
