import { Button } from "../../../../../apps/web/src/shared/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../../../../apps/web/src/shared/ui/card";
import type { PlanningReservation } from "../../api";
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

            <div className="flex flex-wrap gap-2">
              <Button variant="secondary" onClick={onEdit}>Editar</Button>
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
