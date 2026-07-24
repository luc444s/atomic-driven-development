import { Badge } from "../../../../../apps/web/src/shared/ui/badge";
import type { PlanningReservation } from "../../api";
import { formatReservationWindow } from "../utils/planning-calendar-formatters";

type Props = {
  reservation: PlanningReservation;
};

export function PlanningReservationContent({ reservation }: Props) {
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between gap-2">
        <div className="truncate font-medium">{reservation.vehicle_plate}</div>
        <Badge className="bg-background/70 text-[10px] text-foreground">{reservation.status}</Badge>
      </div>
      <div className="truncate text-[11px] text-muted-foreground">{formatReservationWindow(reservation.planned_start_at, reservation.planned_end_at)}</div>
      <div className="truncate text-[11px] text-muted-foreground">
        {reservation.expected_load_summary.total_units} u · {reservation.expected_load_summary.total_products} prod
      </div>
    </div>
  );
}
