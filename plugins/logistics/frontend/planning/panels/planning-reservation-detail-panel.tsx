import { useMutation, useQuery } from "../../../../../apps/web/src/lib/react-query";
import { Button } from "@systutor/shell/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@systutor/shell/ui/card";
import {
  getRoute,
  listRouteStops,
  optimizeRouteCalculation,
  type PlanningReservation,
} from "../../api";
import { PlanningConflictPanel } from "./planning-conflict-panel";
import { formatReservationWindow } from "../utils/planning-calendar-formatters";

type Props = {
  reservation: PlanningReservation | null;
  onEdit: () => void;
  onActivate: () => void;
  onCancel: () => void;
  onOpenSession: (sessionId: string) => void;
  isActivating: boolean;
  isCancelling: boolean;
};

export function PlanningReservationDetailPanel({
  reservation,
  onEdit,
  onActivate,
  onCancel,
  onOpenSession,
  isActivating,
  isCancelling,
}: Props) {
  const routeQuery = useQuery({
    queryKey: reservation?.route_id ? ["planning", "route", reservation.route_id] : ["planning", "route", "none"],
    queryFn: () => getRoute(reservation!.route_id!),
    enabled: Boolean(reservation?.route_id),
  });
  const routeStopsQuery = useQuery({
    queryKey: reservation?.route_id ? ["planning", "route-stops", reservation.route_id] : ["planning", "route-stops", "none"],
    queryFn: () => listRouteStops(reservation!.route_id!),
    enabled: Boolean(reservation?.route_id),
  });
  const previewMutation = useMutation({
    mutationFn: async () => {
      if (!reservation?.route_id) {
        throw new Error("La reserva no tiene ruta para calcular")
      }
      const start = routeQuery.data?.gps_start_coordinates as { lat?: number; lng?: number } | null | undefined;
      if (start?.lat == null || start?.lng == null) {
        throw new Error("La ruta no tiene origen geográfico para cálculo")
      }
      const stops = (routeStopsQuery.data ?? [])
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
        .filter((item): item is NonNullable<typeof item> => item !== null)
      if (!stops.length) {
        throw new Error("La ruta no tiene paradas geográficas para cálculo")
      }
      return optimizeRouteCalculation({
        route_id: reservation.route_id,
        vehicle: {
          vehicle_id: reservation.vehicle_id,
          start_lat: start.lat,
          start_lng: start.lng,
        },
        stops,
      });
    },
  });

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Detalle</CardTitle>
        <CardDescription>Selecciona una reserva del calendario para operarla.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {reservation ? (
          <>
            <div className="space-y-1 text-sm">
              <div><span className="text-muted-foreground">Vehículo:</span> {reservation.vehicle_plate}</div>
              <div><span className="text-muted-foreground">Almacén:</span> {reservation.origin_warehouse_name}</div>
              <div><span className="text-muted-foreground">Ventana:</span> {formatReservationWindow(reservation.planned_start_at, reservation.planned_end_at)}</div>
              <div><span className="text-muted-foreground">Carga:</span> {reservation.expected_load_summary.total_units} unidades / {reservation.expected_load_summary.total_products} productos</div>
              <div><span className="text-muted-foreground">Estado:</span> {reservation.status}</div>
            </div>

            <PlanningConflictPanel reason={reservation.conflict_reason} />

            {previewMutation.data ? (
              <div className="rounded-md border border-border p-3 text-sm text-foreground">
                Preview ruta: {previewMutation.data.totals.distance_m} m · {previewMutation.data.totals.travel_seconds}s.
              </div>
            ) : null}

            <div className="flex flex-wrap gap-2">
              <Button variant="secondary" onClick={onEdit}>Editar</Button>
              {reservation.route_id ? (
                <Button variant="secondary" onClick={() => previewMutation.mutate()} disabled={previewMutation.isPending}>
                  {previewMutation.isPending ? "Calculando ruta..." : "Preview ruta"}
                </Button>
              ) : null}
              {reservation.linked_session_id ? (
                <Button onClick={() => onOpenSession(reservation.linked_session_id!)}>Abrir jornada</Button>
              ) : (
                <Button onClick={onActivate} disabled={isActivating || reservation.status === "CONFLICT"}>
                  {isActivating ? "Activando..." : "Materializar jornada"}
                </Button>
              )}
              {!reservation.linked_session_id ? (
                <Button variant="secondary" onClick={onCancel} disabled={isCancelling}>
                  {isCancelling ? "Cancelando..." : "Cancelar"}
                </Button>
              ) : null}
            </div>
          </>
        ) : (
          <p className="text-sm text-muted-foreground">Sin reserva seleccionada.</p>
        )}
      </CardContent>
    </Card>
  );
}
