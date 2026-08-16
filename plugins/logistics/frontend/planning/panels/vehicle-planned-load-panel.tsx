import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@systutor/shell/ui/card";
import type { PlanningReservation } from "../../api";
import { formatReservationWindow } from "../utils/planning-calendar-formatters";

type Props = {
  reservations: PlanningReservation[];
};

export function VehiclePlannedLoadPanel({ reservations }: Props) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Carga planificada</CardTitle>
        <CardDescription>Reservas futuras no materializadas para este vehículo.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {reservations.length ? reservations.map((reservation) => (
          <div key={reservation.id} className="rounded-xl border border-border/70 p-3 text-sm">
            <div className="font-medium text-foreground">{formatReservationWindow(reservation.planned_start_at, reservation.planned_end_at)}</div>
            <div className="text-muted-foreground">{reservation.expected_load_summary.total_units} unidades · {reservation.expected_load_summary.total_products} productos</div>
          </div>
        )) : <p className="text-sm text-muted-foreground">Sin carga planificada.</p>}
      </CardContent>
    </Card>
  );
}
