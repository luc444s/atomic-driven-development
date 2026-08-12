import { Alert } from "../../../../../apps/web/src/shared/ui/alert";
import { Button } from "../../../../../apps/web/src/shared/ui/button";
import {
  Card,
  CardContent,
} from "../../../../../apps/web/src/shared/ui/card";
import { useMutation, useQuery, useQueryClient } from "../../../../../apps/web/src/lib/react-query";
import {
  commitRouteOrder,
  getAssignedRoute,
  getRoute,
  getRouteStopProgress,
  listRouteStops,
  logisticsKeys,
  optimizeRouteCalculation,
  type RoutingCalculationResponse,
} from "../../api";
import { formatRouteLabel } from "../../lib/route-labels";
import { RouteContextMap } from "../route-builder/RouteContextMap";
import { SessionWaybillCard } from "./SessionWaybillCard";
import { SessionRouteTabDialogs } from "./SessionRouteTabDialogs";
import { useSessionRouteTabController } from "./useSessionRouteTabController";

type Props = {
  open: boolean;
  routeId: string | null;
  routeDate: string | null;
  routeOriginLabel: string | null;
  routeDestinationLabel: string | null;
  sessionId: string;
  sessionStatus: string;
};

export function SessionRouteTab({
  open,
  routeId,
  routeDate,
  routeOriginLabel,
  routeDestinationLabel,
  sessionId,
  sessionStatus,
}: Props) {
  const controller = useSessionRouteTabController({ open, routeId, sessionId, sessionStatus });
  const queryClient = useQueryClient();

  const stopsQuery = useQuery({
    queryKey: routeId ? logisticsKeys.routes.stops(routeId) : ["logistics", "routes", "none", "stops"],
    queryFn: () => listRouteStops(routeId!),
    enabled: open && Boolean(routeId),
  });
  const routeQuery = useQuery({
    queryKey: routeId ? logisticsKeys.routes.detail(routeId) : ["logistics", "routes", "none", "detail"],
    queryFn: () => getRoute(routeId!),
    enabled: open && Boolean(routeId),
  });
  const assignedRouteQuery = useQuery({
    queryKey: routeId ? logisticsKeys.routes.assigned(routeId) : ["logistics", "routes", "none", "assigned-route"],
    queryFn: () => getAssignedRoute(routeId!),
    enabled: open && Boolean(routeId),
  });
  const stopProgressQuery = useQuery({
    queryKey: logisticsKeys.vehicleSessions.routeStopProgress(sessionId),
    queryFn: () => getRouteStopProgress(sessionId),
    enabled: open,
  });

  const stops = stopsQuery.data ?? [];
  const stopProgress = stopProgressQuery.data ?? [];
  const completedStopIds = new Set(
    stopProgress.filter((p) => p.progress_status === "COMPLETED").map((p) => p.route_stop_id)
  );
  const routeStart = routeQuery.data?.gps_start_coordinates as { lat?: number; lng?: number } | null | undefined;
  const startPoint =
    routeStart?.lat != null && routeStart?.lng != null
      ? {
          lat: routeStart.lat,
          lng: routeStart.lng,
          label: routeOriginLabel ?? "Inicio",
        }
      : null;
  const canRecalculate = Boolean(routeId && routeQuery.data?.vehicle_id && startPoint && stops.length > 0);

  function buildOptimizePayload() {
    if (!routeId || !routeQuery.data?.vehicle_id || !startPoint || stops.length === 0) {
      throw new Error("Faltan datos mínimos para recalcular la ruta")
    }
    return {
      route_id: routeId,
      session_id: sessionId,
      mode: "optimize",
      vehicle: {
        vehicle_id: routeQuery.data.vehicle_id,
        start_lat: startPoint.lat,
        start_lng: startPoint.lng,
      },
      stops: stops
        .map((stop) => {
          const coords = stop.gps_coordinates as { lat?: number; lng?: number } | null;
          if (coords?.lat == null || coords?.lng == null) {
            return null;
          }
          return {
            stop_id: stop.id,
            customer_id: stop.customer_id,
            customer_name: stop.customer_name_snapshot,
            lat: coords.lat,
            lng: coords.lng,
            service_minutes: 0,
          };
        })
        .filter((item): item is NonNullable<typeof item> => item !== null),
    };
  }

  const optimizeMutation = useMutation({
    mutationFn: () => optimizeRouteCalculation(buildOptimizePayload()),
  });
  const commitOptimizeMutation = useMutation({
    mutationFn: (preview: RoutingCalculationResponse) =>
      commitRouteOrder({
        route_id: routeId!,
        session_id: sessionId,
        preview,
      }),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: logisticsKeys.routes.stops(routeId!) }),
        queryClient.invalidateQueries({ queryKey: logisticsKeys.routes.assigned(routeId!) }),
      ]);
      optimizeMutation.reset();
    },
  });
  const proposedRoute = optimizeMutation.data;
  const hasAssignedRouteSnapshot = Boolean(assignedRouteQuery.data);
  const currentDistance = Number(assignedRouteQuery.data?.totals?.distance_m ?? 0);
  const proposedDistance = proposedRoute?.totals.distance_m ?? 0;
  const distanceDelta = proposedRoute ? proposedDistance - currentDistance : 0;

  return (
    <div className="space-y-4">
      {controller.error ? <Alert title="No se pudo actualizar la jornada en ruta">{controller.error}</Alert> : null}
      {optimizeMutation.error ? (
        <Alert title="No se pudo recalcular la ruta">
          {optimizeMutation.error instanceof Error
            ? optimizeMutation.error.message
            : "Error al generar propuesta de ruta."}
        </Alert>
      ) : null}
      {proposedRoute ? (
        <Alert title={hasAssignedRouteSnapshot ? "Propuesta nueva de ruta" : "Primera propuesta de ruta"}>
          {hasAssignedRouteSnapshot
            ? `Actual: ${currentDistance} m · Propuesta: ${proposedDistance} m · Delta: ${distanceDelta} m.`
            : `Propuesta: ${proposedDistance} m.`}
          {proposedRoute.violations.length ? ` Violaciones: ${proposedRoute.violations.join(", ")}.` : " Sin violaciones."}
        </Alert>
      ) : null}
      <div className="grid gap-4 xl:grid-cols-[minmax(420px,620px)_minmax(0,1fr)] 2xl:grid-cols-[680px_minmax(0,1fr)]">
        <div className="space-y-4 xl:sticky xl:top-0 self-start">
          <SessionWaybillCard
            waybillState={controller.waybillState}
            history={controller.waybillHistory}
            isLoading={controller.isWaybillLoading}
            canRegenerate={controller.canRegenerate}
            isRegenerating={controller.isRegeneratingWaybill}
            onRegenerate={controller.regenerateWaybill}
          />
        </div>

        <div className="space-y-4">
          <Card>
           <CardContent className="flex flex-wrap items-center justify-between gap-3 text-sm text-muted-foreground">
              <span>
                Ruta asignada:{" "}
                {formatRouteLabel({
                  route_date: routeDate,
                  route_id: routeId,
                  origin_label: routeOriginLabel,
                  destination_label: routeDestinationLabel,
                })}
              </span>
              <div className="flex flex-wrap items-center gap-2">
                <Button variant="secondary" onClick={controller.openCompositionModal}>
                  Mis envases
                </Button>
                <Button variant="secondary" onClick={controller.openStopProgressModal}>
                  Progreso de parada
                </Button>
                <Button variant="secondary" onClick={controller.openOperationsModal}>
                  Operaciones confirmadas{controller.routeOperations.length ? ` (${controller.routeOperations.length})` : ""}
                </Button>
                <Button variant="secondary" onClick={controller.openStopResultsModal}>
                  Resultados de parada
                </Button>
                <Button variant="secondary" onClick={controller.openIncidentsModal}>
                  Incidencias{controller.routeIncidents.length ? ` (${controller.routeIncidents.length})` : ""}
                </Button>
                <Button
                  variant="secondary"
                  disabled={!canRecalculate || optimizeMutation.isPending}
                  onClick={() => optimizeMutation.mutate()}
                >
                  {optimizeMutation.isPending ? "Calculando..." : "Recalcular ruta"}
                </Button>
                {proposedRoute ? (
                  <Button
                    disabled={commitOptimizeMutation.isPending}
                    onClick={() => commitOptimizeMutation.mutate(proposedRoute)}
                  >
                    {commitOptimizeMutation.isPending ? "Aceptando..." : "Aceptar propuesta"}
                  </Button>
                ) : null}
                <Button disabled={!controller.canRegisterOperation} onClick={controller.openEventModal}>
                  Registrar movimiento
                </Button>
              </div>
            </CardContent>
          </Card>

          {routeId && stops.length > 0 ? (
            <RouteContextMap
              stops={stops}
              startPoint={startPoint}
              activeStopId={null}
              completedStops={completedStopIds.size}
              totalStops={stops.length}
              completedStopIds={completedStopIds}
              assignedPolyline={assignedRouteQuery.data?.polyline ?? null}
            />
          ) : null}
        </div>
      </div>

      <SessionRouteTabDialogs controller={controller} />
    </div>
  );
}
