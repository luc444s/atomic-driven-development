import { useMemo, useRef } from "react";
import { LocationMap } from "@systutor/shell/ui/location-map";
import type { RoutingCalculationResponse } from "../../api";
import { DEFAULT_MAP_CENTER } from "./map-defaults";
import { type BuilderPhase, type RouteStopDraft } from "./useRouteBuilder";

type Props = {
  phase: BuilderPhase;
  startPoint: RouteStopDraft | null;
  endPoint: RouteStopDraft | null;
  stops: RouteStopDraft[];
  preview: RoutingCalculationResponse | null;
  onClickMap: (lat: number, lng: number) => void;
  onDragMarker: (id: string, lat: number, lng: number) => void;
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

export function RouteBuilderMap({
  phase,
  startPoint,
  endPoint,
  stops,
  preview,
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

  const previewPath = preview?.polyline ? decodePolyline(preview.polyline) : [];
  const center = (previewPath.length > 0 ? previewPath[0] : plannedPath[0]) ?? DEFAULT_MAP_CENTER;

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
        zoom={plannedPath.length > 0 || previewPath.length > 0 ? 12 : 6}
        height={400}
        markers={markers}
        polylines={
          previewPath.length > 1
            ? [{ id: "preview", points: previewPath, color: "#2563eb" }]
            : plannedPath.length > 1
              ? [{ id: "planned", points: plannedPath, color: "#2563eb" }]
              : []
        }
        onMapClick={isBuilding ? (latlng) => onClickMap(latlng.lat, latlng.lng) : undefined}
        onMarkerDrag={isBuilding ? (id, latlng) => onDragMarker(id, latlng.lat, latlng.lng) : undefined}
      />
    </div>
  );
}
