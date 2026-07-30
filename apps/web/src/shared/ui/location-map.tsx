import { useEffect } from "react";
import { MapContainer, Marker, Polyline, Popup, TileLayer, useMap } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

import { useThemeStore } from "../../features/theme/store";
import { cn } from "./cn";

type LatLng = { lat: number; lng: number };

export type LocationMapMarker = {
  id: string;
  position: LatLng;
  label?: string;
};

export type LocationMapPolyline = {
  id: string;
  points: LatLng[];
  color?: string;
  weight?: number;
  dashArray?: string;
};

type Props = {
  center: LatLng;
  zoom?: number;
  markers?: LocationMapMarker[];
  polylines?: LocationMapPolyline[];
  className?: string;
  height?: number;
};

const defaultIcon = L.icon({
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});

L.Marker.prototype.options.icon = defaultIcon;

const lightTile = "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png";
const darkTile = "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png";

function ChangeView({ center, zoom }: { center: LatLng; zoom: number }) {
  const map = useMap();
  useEffect(() => {
    map.setView([center.lat, center.lng], zoom);
  }, [center, map, zoom]);
  return null;
}

export function LocationMap({
  center,
  zoom = 12,
  markers = [],
  polylines = [],
  className,
  height = 320,
}: Props) {
  const theme = useThemeStore((s) => s.theme);
  const isDark = theme === "dark";

  return (
    <div className={cn("overflow-hidden rounded-md border border-border", className)} style={{ height }}>
      <MapContainer center={[center.lat, center.lng]} zoom={zoom} className="h-full w-full">
        <TileLayer
          url={isDark ? darkTile : lightTile}
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        />
        <ChangeView center={center} zoom={zoom} />
        {polylines.map((polyline) => (
          <Polyline
            key={polyline.id}
            positions={polyline.points.map((point) => [point.lat, point.lng] as [number, number])}
            pathOptions={{
              color: polyline.color ?? "#2563eb",
              weight: polyline.weight ?? 4,
              dashArray: polyline.dashArray,
            }}
          />
        ))}
        {markers.map((marker) => (
          <Marker key={marker.id} position={[marker.position.lat, marker.position.lng]}>
            {marker.label ? (
              <Popup>
                <span className="text-sm">{marker.label}</span>
              </Popup>
            ) : null}
          </Marker>
        ))}
      </MapContainer>
    </div>
  );
}
