import { LocationMap } from "../../../../../apps/web/src/shared/ui/location-map";
import type { LogisticsRouteStop } from "../../api";
import { DEFAULT_MAP_CENTER } from "./map-defaults";

type Props = {
  stops: LogisticsRouteStop[];
  startPoint?: { lat: number; lng: number; label?: string | null } | null;
  activeStopId: string | null;
  completedStops: number;
  totalStops: number;
  completedStopIds?: Set<string>;
  assignedPolyline?: string | null;
};

function decodePolyline(encoded: string): { lat: number; lng: number }[] {
  let index = 0;
  let lat = 0;
  let lng = 0;
  const points: { lat: number; lng: number }[] = [];

  while (index < encoded.length) {
    let shift = 0;
    let result = 0;
    let byte = 0;
    do {
      byte = encoded.charCodeAt(index++) - 63;
      result |= (byte & 0x1f) << shift;
      shift += 5;
    } while (byte >= 0x20 && index <= encoded.length);
    const deltaLat = result & 1 ? ~(result >> 1) : result >> 1;
    lat += deltaLat;

    shift = 0;
    result = 0;
    do {
      byte = encoded.charCodeAt(index++) - 63;
      result |= (byte & 0x1f) << shift;
      shift += 5;
    } while (byte >= 0x20 && index <= encoded.length);
    const deltaLng = result & 1 ? ~(result >> 1) : result >> 1;
    lng += deltaLng;

    points.push({ lat: lat / 1e5, lng: lng / 1e5 });
  }

  return points;
}

export function RouteContextMap({
  stops,
  startPoint,
  activeStopId,
  completedStops,
  totalStops,
  completedStopIds,
  assignedPolyline,
}: Props) {
  if (!stops.length && !startPoint) {
    return (
      <div className="rounded-lg border border-dashed border-border p-4 text-center">
        <p className="text-sm text-muted-foreground">Ruta sin paradas.</p>
      </div>
    );
  }

  const stopList = stops
    .map((stop, index) => {
      if (!stop.gps_coordinates) return null;
      const coords = stop.gps_coordinates as { lat: number; lng: number };
      const isFirst = index === 0;
      const isLast = index === stops.length - 1;
      const isActive = stop.id === activeStopId;
      const label = isFirst
        ? `Partida`
        : isLast
          ? `Destino`
          : `Parada ${index}${isActive ? " (activa)" : ""}`;
      return {
        id: stop.id,
        position: { lat: coords.lat, lng: coords.lng },
        label,
      };
    })
    .filter((item): item is NonNullable<typeof item> => item !== null);

  const startMarker = startPoint
    ? {
        id: "route-start",
        position: { lat: startPoint.lat, lng: startPoint.lng },
        label: startPoint.label ?? "Inicio",
        color: "origin" as const,
      }
    : null;
  const markers = [
    ...(startMarker ? [startMarker] : []),
    ...stopList.map((s) => ({
      id: s.id,
      position: s.position,
      label: s.label,
      color: (completedStopIds?.has(s.id) ? "completed" : "default") as "completed" | "default",
    })),
  ];
  const fallbackPath = [
    ...(startMarker ? [startMarker.position] : []),
    ...stopList.map((s) => s.position),
  ];
  let assignedPath: { lat: number; lng: number }[] = [];
  if (assignedPolyline) {
    try {
      assignedPath = decodePolyline(assignedPolyline);
    } catch {
      assignedPath = [];
    }
  }
  const path = assignedPath.length > 1 ? assignedPath : fallbackPath;
  const center = path.length > 0 ? path[0] : DEFAULT_MAP_CENTER;

  return (
    <div className="space-y-2">
      <div className="grid grid-cols-3 gap-3 text-sm">
        <div>
          <span className="font-medium">Paradas:</span> {completedStops}/{totalStops}
        </div>
        <div>
          <span className="font-medium">Progreso:</span>{" "}
          {totalStops > 0 ? Math.round((completedStops / totalStops) * 100) : 0}%
        </div>
        <div>
          <span className="font-medium">Activa:</span>{" "}
          {activeStopId ? "Sí" : "Ninguna"}
        </div>
      </div>
      <LocationMap
        center={center}
        zoom={path.length > 1 ? 12 : 10}
        height={400}
        markers={markers}
        polylines={path.length > 1 ? [{ id: "route", points: path, color: "#2563eb" }] : []}
        autoFit
      />
    </div>
  );
}
