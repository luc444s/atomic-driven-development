import { useMemo, useRef } from "react";
import { LocationMap } from "../../../../../apps/web/src/shared/ui/location-map";
import { DEFAULT_MAP_CENTER } from "./map-defaults";
import { type BuilderPhase, type RouteStopDraft } from "./useRouteBuilder";

type Props = {
  phase: BuilderPhase;
  startPoint: RouteStopDraft | null;
  endPoint: RouteStopDraft | null;
  stops: RouteStopDraft[];
  onClickMap: (lat: number, lng: number) => void;
  onDragMarker: (id: string, lat: number, lng: number) => void;
};

export function RouteBuilderMap({
  phase,
  startPoint,
  endPoint,
  stops,
  onClickMap,
  onDragMarker,
}: Props) {
  const markers = [
    ...(startPoint
      ? [
          {
            id: "start",
            position: { lat: startPoint.lat, lng: startPoint.lng },
            label: `Partida: ${startPoint.name}`,
          },
        ]
      : []),
    ...(endPoint
      ? [
          {
            id: "end",
            position: { lat: endPoint.lat, lng: endPoint.lng },
            label: `Destino: ${endPoint.name}`,
          },
        ]
      : []),
    ...stops.map((stop, index) => ({
      id: `stop-${index}`,
      position: { lat: stop.lat, lng: stop.lng },
      label: `Parada ${index + 1}: ${stop.name}`,
    })),
  ];

  const plannedPath = useMemo(() => [
    ...(startPoint ? [{ lat: startPoint.lat, lng: startPoint.lng }] : []),
    ...stops.map((s) => ({ lat: s.lat, lng: s.lng })),
    ...(endPoint ? [{ lat: endPoint.lat, lng: endPoint.lng }] : []),
  ], [startPoint, endPoint, stops]);

  const initialCenter = useRef(
    plannedPath.length > 0
      ? plannedPath[0]
      : DEFAULT_MAP_CENTER
  );

  if (plannedPath.length > 0 && initialCenter.current === DEFAULT_MAP_CENTER) {
    initialCenter.current = plannedPath[0];
  }

  const center = plannedPath.length > 0 ? initialCenter.current : DEFAULT_MAP_CENTER;

  const isBuilding = phase !== "idle";
  const phaseLabel =
    phase === "picking_start"
      ? "Haz clic en el mapa para elegir la partida"
      : phase === "picking_end"
        ? "Haz clic en otro punto para elegir el destino"
        : phase === "picking_stops"
          ? "Haz clic en el mapa para agregar paradas intermedias"
          : null;

  return (
    <div className="space-y-2">
      {isBuilding ? (
        <p className="text-sm text-muted-foreground">{phaseLabel}</p>
      ) : null}
      <LocationMap
        center={center}
        zoom={plannedPath.length > 0 ? 12 : 6}
        height={400}
        markers={markers}
        polylines={plannedPath.length > 1 ? [{ id: "planned", points: plannedPath, color: "#2563eb" }] : []}
        onMapClick={isBuilding ? (latlng) => onClickMap(latlng.lat, latlng.lng) : undefined}
        onMarkerDrag={isBuilding ? (id, latlng) => onDragMarker(id, latlng.lat, latlng.lng) : undefined}
      />
    </div>
  );
}
