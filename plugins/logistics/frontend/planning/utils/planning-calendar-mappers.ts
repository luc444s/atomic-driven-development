import type { CalendarItem, CalendarResource } from "@systutor/shell/ui/resource-calendar/resource-calendar";
import type { LogisticsVehicle, PlanningReservation } from "../../api";

export function buildCalendarResources(vehicles: LogisticsVehicle[]): CalendarResource[] {
  return vehicles.map((vehicle) => ({
    id: vehicle.id,
    label: vehicle.plate,
    subtitle: vehicle.vehicle_type ?? undefined,
    disabled: vehicle.is_active === false,
  }));
}

export function mapReservationsToCalendarItems(reservations: PlanningReservation[]): CalendarItem[] {
  return reservations.map((reservation) => ({
    id: reservation.id,
    resourceId: reservation.vehicle_id,
    start: reservation.planned_start_at,
    end: reservation.planned_end_at,
    title: reservation.vehicle_plate,
    status: reservation.status,
    colorVariant: reservation.status,
    isConflicted: reservation.status === "CONFLICT",
    isLocked: reservation.linked_session_id != null,
  }));
}
