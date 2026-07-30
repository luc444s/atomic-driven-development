import { Alert } from "../../../../../apps/web/src/shared/ui/alert";
import { Button } from "../../../../../apps/web/src/shared/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../../../../apps/web/src/shared/ui/card";
import { LocationMap } from "../../../../../apps/web/src/shared/ui/location-map";

import type {
  LogisticsDeliveryPoint,
  LogisticsRouteStop,
  RouteControlState,
  VehicleLocationEvent,
} from "../../api";
import { buildRouteControlMapView } from "./route-control-view";

type Props = {
  controlState: RouteControlState | null;
  deliveryPoints: LogisticsDeliveryPoint[];
  history: VehicleLocationEvent[];
  isLoading: boolean;
  isControlPending: boolean;
  sessionStatus: string;
  stops: LogisticsRouteStop[];
  onArrive: (stopId: string) => void;
  onDepart: (stopId: string) => void;
};

export function RouteControlMapPanel({
  controlState,
  deliveryPoints,
  history,
  isLoading,
  isControlPending,
  sessionStatus,
  stops,
  onArrive,
  onDepart,
}: Props) {
  const view = buildRouteControlMapView({ stops, deliveryPoints, controlState, history });
  const canControl = ["OUTBOUND", "RETURNING"].includes(sessionStatus);
  const currentStopId = controlState?.current_stop_id ?? null;
  const activeStopId = controlState?.active_stop_id ?? null;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Mapa de contexto</CardTitle>
        <CardDescription>
          Ruta planificada, posición reportada y avance espacial de la jornada.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {controlState?.status === "NO_ROUTE_ASSIGNED" ? (
          <Alert title="Jornada sin ruta asignada">
            La telemetría puede registrarse, pero este mapa no puede proyectar siguiente parada ni control espacial de ruta.
          </Alert>
        ) : null}
        {!view.stops.length ? (
          <Alert title="Paradas sin coordenadas">
            La ruta todavía no tiene puntos con coordenadas estructuradas suficientes para dibujar el recorrido planificado.
          </Alert>
        ) : null}
        {!history.length && !view.vehiclePosition && !isLoading ? (
          <Alert title="Sin telemetría reciente">
            Aún no se recibieron ubicaciones para esta jornada. El mapa mostrará la ruta planificada apenas exista telemetría.
          </Alert>
        ) : null}
        <div className="grid gap-3 text-sm md:grid-cols-4">
          <div><span className="font-medium">Estado:</span> {controlState?.status ?? (isLoading ? "Cargando..." : "Sin datos")}</div>
          <div><span className="font-medium">Paradas completadas:</span> {controlState?.completed_stops ?? 0}/{controlState?.total_stops ?? stops.length}</div>
          <div><span className="font-medium">Progreso:</span> {controlState?.progress_percent ?? 0}%</div>
          <div><span className="font-medium">Parada activa:</span> {activeStopId ?? "Ninguna"}</div>
        </div>
        <LocationMap
          center={view.center}
          zoom={view.zoom}
          height={360}
          markers={[
            ...view.stops.map((stop) => ({
              id: stop.id,
              position: stop.position,
              label: `${stop.label}${stop.isActive ? " · Activa" : stop.isCurrent ? " · Actual" : ""}`,
            })),
            ...(view.vehiclePosition
              ? [{ id: "vehicle", position: view.vehiclePosition, label: "Vehículo" }]
              : []),
          ]}
          polylines={[
            ...(view.plannedPath.length > 1
              ? [{ id: "planned", points: view.plannedPath, color: "#2563eb", dashArray: "8 6" }]
              : []),
            ...(view.traveledPath.length > 1
              ? [{ id: "traveled", points: view.traveledPath, color: "#16a34a" }]
              : []),
          ]}
        />
        <div className="flex justify-end gap-3">
          <Button
            type="button"
            variant="secondary"
            disabled={!canControl || !currentStopId || Boolean(activeStopId) || isControlPending}
            onClick={() => {
              if (!currentStopId) {
                return;
              }
              onArrive(currentStopId);
            }}
          >
            Marcar llegada
          </Button>
          <Button
            type="button"
            disabled={!canControl || !activeStopId || isControlPending}
            onClick={() => {
              if (!activeStopId) {
                return;
              }
              onDepart(activeStopId);
            }}
          >
            Marcar salida
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
