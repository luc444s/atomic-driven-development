import { useQuery } from "../../../../../apps/web/src/lib/react-query";
import { Button } from "../../../../../apps/web/src/shared/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../../../../apps/web/src/shared/ui/card";
import { Dialog } from "../../../../../apps/web/src/shared/ui/dialog";
import {
  getAssignedRoute,
  getRoute,
  getRouteStopProgress,
  listRouteStops,
  logisticsKeys,
  VEHICLE_SESSION_STATUS_LABELS,
} from "../../api";
import type { PlanningReservation } from "../../api";
import { RouteContextMap } from "../route-builder/RouteContextMap";
import { VehicleSessionStatusBadge } from "./VehicleSessionStatusBadge";
import type { VehicleProjectionCard } from "./vehicle-jornadas-projection";
import { VehiclePlannedLoadPanel } from "../../planning/panels/vehicle-planned-load-panel";

type Props = {
  open: boolean;
  card: VehicleProjectionCard | null;
  onClose: () => void;
  onOpenSession: (sessionId: string) => void;
  onCreateJornada: (vehicleId: string) => void;
  plannedReservations: PlanningReservation[];
};

export function VehicleJornadasDialog({
  open,
  card,
  onClose,
  onOpenSession,
  onCreateJornada,
  plannedReservations,
}: Props) {
  const activeSession = card?.active_session ?? null;
  const routeId = activeSession?.route_id ?? null;
  // Vista rápida: si el vehículo ya tiene jornada activa con ruta, el diálogo
  // debe mostrar la ruta asignada sin obligar al usuario a abrir la jornada.
  const routeQuery = useQuery({
    queryKey: routeId ? logisticsKeys.routes.detail(routeId) : ["logistics", "routes", "none", "detail"],
    queryFn: () => getRoute(routeId!),
    enabled: open && Boolean(routeId),
  });
  const stopsQuery = useQuery({
    queryKey: routeId ? logisticsKeys.routes.stops(routeId) : ["logistics", "routes", "none", "stops"],
    queryFn: () => listRouteStops(routeId!),
    enabled: open && Boolean(routeId),
  });
  const assignedRouteQuery = useQuery({
    queryKey: routeId ? logisticsKeys.routes.assigned(routeId) : ["logistics", "routes", "none", "assigned-route"],
    queryFn: () => getAssignedRoute(routeId!),
    enabled: open && Boolean(routeId),
  });
  const stopProgressQuery = useQuery({
    queryKey: activeSession ? logisticsKeys.vehicleSessions.routeStopProgress(activeSession.id) : ["logistics", "vehicle-sessions", "none", "route-stop-progress"],
    queryFn: () => getRouteStopProgress(activeSession!.id),
    enabled: open && Boolean(activeSession?.id),
  });
  const completedStopIds = new Set(
    (stopProgressQuery.data ?? [])
      .filter((item) => item.progress_status === "COMPLETED")
      .map((item) => item.route_stop_id)
  );
  const routeStart = routeQuery.data?.gps_start_coordinates as { lat?: number; lng?: number } | null | undefined;
  const startPoint =
    routeStart?.lat != null && routeStart?.lng != null
      ? {
          lat: routeStart.lat,
          lng: routeStart.lng,
          label: activeSession?.route_origin_label ?? "Inicio",
        }
      : null;

  return (
    <Dialog
      open={open}
      title={card ? `Vehículo ${card.vehicle_plate}` : "Vehículo"}
      description="Proyección por vehículo: jornada activa, pendientes e históricas."
      onClose={onClose}
      maxWidthClassName="max-w-5xl"
    >
      {card ? (
        <div className="space-y-5">
          <div className="flex flex-wrap gap-2">
            {card.active_session ? (
              <Button onClick={() => onOpenSession(card.active_session!.id)}>Abrir jornada activa</Button>
            ) : (
              <Button onClick={() => onCreateJornada(card.vehicle_id)}>Crear jornada</Button>
            )}
          </div>

          {card.active_session ? (
            <Card>
              <CardHeader>
                <CardTitle>Jornada activa</CardTitle>
                <CardDescription>Unidad ejecutable actual del vehículo.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4 text-sm">
                <div className="flex items-center justify-between gap-4">
                  <div className="space-y-1">
                    <div className="font-medium text-foreground">
                      {VEHICLE_SESSION_STATUS_LABELS[card.active_session.status] ?? card.active_session.status}
                    </div>
                    <div className="text-muted-foreground">Conductor: {card.active_session.driver_name}</div>
                    <div className="text-muted-foreground">
                      Apertura: {new Date(card.active_session.opened_at).toLocaleString()}
                    </div>
                  </div>
                  <VehicleSessionStatusBadge status={card.active_session.status} />
                </div>

                {/* Si ya existe snapshot asignado, el mapa usa esa polyline.
                    Si no existe todavía, RouteContextMap cae a la línea simple. */}
                {routeId && (stopsQuery.data?.length ?? 0) > 0 ? (
                  <RouteContextMap
                    stops={stopsQuery.data ?? []}
                    startPoint={startPoint}
                    activeStopId={null}
                    completedStops={completedStopIds.size}
                    totalStops={(stopsQuery.data ?? []).length}
                    completedStopIds={completedStopIds}
                    assignedPolyline={assignedRouteQuery.data?.polyline ?? null}
                  />
                ) : null}
              </CardContent>
            </Card>
          ) : null}

          <div className="grid gap-4 xl:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Jornadas pendientes</CardTitle>
                <CardDescription>No cerradas, excluyendo la activa.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {card.pending_sessions.length ? (
                  card.pending_sessions.map((session) => (
                    <div
                      key={session.id}
                      className="flex items-center justify-between gap-3 rounded-xl border border-border/70 p-3 text-sm"
                    >
                      <div>
                        <div className="font-medium text-foreground">
                          {VEHICLE_SESSION_STATUS_LABELS[session.status] ?? session.status}
                        </div>
                        <div className="text-muted-foreground">
                          {new Date(session.opened_at).toLocaleString()}
                        </div>
                      </div>
                      <Button variant="secondary" onClick={() => onOpenSession(session.id)}>
                        Abrir
                      </Button>
                    </div>
                  ))
                ) : (
                  <p className="text-sm text-muted-foreground">Sin jornadas pendientes.</p>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Jornadas históricas</CardTitle>
                <CardDescription>Cerradas, ordenadas por recencia.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {card.historical_sessions.length ? (
                  card.historical_sessions.map((session) => (
                    <div
                      key={session.id}
                      className="flex items-center justify-between gap-3 rounded-xl border border-border/70 p-3 text-sm"
                    >
                      <div>
                        <div className="font-medium text-foreground">Jornada cerrada</div>
                        <div className="text-muted-foreground">
                          {new Date(session.closed_at ?? session.opened_at).toLocaleString()}
                        </div>
                      </div>
                      <Button variant="secondary" onClick={() => onOpenSession(session.id)}>
                        Ver
                      </Button>
                    </div>
                  ))
                ) : (
                  <p className="text-sm text-muted-foreground">Sin jornadas históricas.</p>
                )}
              </CardContent>
            </Card>
          </div>

          <VehiclePlannedLoadPanel reservations={plannedReservations} />
        </div>
      ) : null}
    </Dialog>
  );
}
