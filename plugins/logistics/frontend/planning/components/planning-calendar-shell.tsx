import { ResourceCalendar, type CalendarResource, type CalendarView } from "@systutor/shell/ui/resource-calendar/resource-calendar";
import type { PlanningReservation } from "../../api";
import { PlanningReservationContent } from "./planning-reservation-content";
import { mapReservationsToCalendarItems } from "../utils/planning-calendar-mappers";

type Props = {
  view: CalendarView;
  focusDate: string;
  rangeStart: string;
  rangeEnd: string;
  resources: CalendarResource[];
  reservations: PlanningReservation[];
  onSlotSelect: (vehicleId: string, start: string, end: string) => void;
  onReservationClick: (reservationId: string) => void;
};

export function PlanningCalendarShell({
  view,
  focusDate,
  rangeStart,
  rangeEnd,
  resources,
  reservations,
  onSlotSelect,
  onReservationClick,
}: Props) {
  const items = mapReservationsToCalendarItems(reservations);
  const reservationsById = new Map(reservations.map((reservation) => [reservation.id, reservation]));

  return (
    <ResourceCalendar
      view={view}
      focusDate={focusDate}
      rangeStart={rangeStart}
      rangeEnd={rangeEnd}
      resources={resources}
      items={items}
      onSlotSelect={(resourceId, start, end) => onSlotSelect(resourceId ?? "", start, end)}
      onItemClick={onReservationClick}
      renderItem={(item) => {
        const reservation = reservationsById.get(item.id);
        return reservation ? <PlanningReservationContent reservation={reservation} /> : item.title;
      }}
    />
  );
}
