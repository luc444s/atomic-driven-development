import { Alert } from "../../../../../apps/web/src/shared/ui/alert";
import { Button } from "../../../../../apps/web/src/shared/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "../../../../../apps/web/src/shared/ui/card";
import { useQuery } from "../../../../../apps/web/src/lib/react-query";
import { getRoute, listRouteStops, logisticsKeys } from "../../api";
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

  const stops = stopsQuery.data ?? [];
  const routeStart = routeQuery.data?.gps_start_coordinates as { lat?: number; lng?: number } | null | undefined;
  const startPoint =
    routeStart?.lat != null && routeStart?.lng != null
      ? {
          lat: routeStart.lat,
          lng: routeStart.lng,
          label: routeOriginLabel ?? "Inicio",
        }
      : null;

  return (
    <div className="space-y-4">
      {controller.error ? <Alert title="No se pudo actualizar la jornada en ruta">{controller.error}</Alert> : null}
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
            <CardHeader>
              <CardTitle>Ruta</CardTitle>
              <CardDescription>
                Espacio operativo real de la jornada en calle.
              </CardDescription>
            </CardHeader>
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
                  Composición vigente
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
                <Button disabled={!controller.canRegisterOperation} onClick={controller.openEventModal}>
                  Registrar evento de ruta
                </Button>
              </div>
            </CardContent>
          </Card>

          {routeId && stops.length > 0 ? (
            <RouteContextMap
              stops={stops}
              startPoint={startPoint}
              activeStopId={null}
              completedStops={0}
              totalStops={stops.length}
            />
          ) : null}
        </div>
      </div>

      <SessionRouteTabDialogs controller={controller} />
    </div>
  );
}
