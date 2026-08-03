import { LocationMap } from "../../../../../apps/web/src/shared/ui/location-map";
import type { LogisticsRouteStop } from "../../api";
import { DEFAULT_MAP_CENTER } from "./map-defaults";

type Props = {
  stops: LogisticsRouteStop[];
  startPoint?: { lat: number; lng: number; label?: string | null } | null;
  activeStopId: string | null;
  completedStops: number;
  totalStops: number;
};

export function RouteContextMap({
  stops,
  startPoint,
  activeStopId,
  completedStops,
  totalStops,
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
    })),
  ];
  const path = [
    ...(startMarker ? [startMarker.position] : []),
    ...stopList.map((s) => s.position),
  ];
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
        height={240}
        markers={markers}
        polylines={path.length > 1 ? [{ id: "route", points: path, color: "#2563eb" }] : []}
      />
    </div>
  );
}
