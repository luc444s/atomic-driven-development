import { useState } from "react";
import {
  addDays,
  endOfMonth,
  endOfWeek,
  isoString,
  startOfMonth,
  startOfWeek,
} from "@systutor/shell/ui/resource-calendar/resource-calendar-dates";
import type { CalendarView } from "@systutor/shell/ui/resource-calendar/resource-calendar";

function buildRange(view: CalendarView, focusDate: Date) {
  if (view === "month") {
    return { rangeStart: isoString(startOfMonth(focusDate)), rangeEnd: isoString(endOfMonth(focusDate)) };
  }
  if (view === "week") {
    return { rangeStart: isoString(startOfWeek(focusDate)), rangeEnd: isoString(endOfWeek(focusDate)) };
  }
  const start = new Date(focusDate);
  start.setHours(0, 0, 0, 0);
  const end = new Date(focusDate);
  end.setHours(23, 59, 59, 999);
  return { rangeStart: isoString(start), rangeEnd: isoString(end) };
}

export function usePlanningCalendarRange() {
  const [view, setView] = useState<CalendarView>("month");
  const [focusDate, setFocusDate] = useState(() => new Date());

  function goToday() {
    setFocusDate(new Date());
  }

  function goPrevious() {
    setFocusDate((current) => addDays(current, view === "month" ? -30 : view === "week" ? -7 : -1));
  }

  function goNext() {
    setFocusDate((current) => addDays(current, view === "month" ? 30 : view === "week" ? 7 : 1));
  }

  return {
    view,
    setView,
    focusDate,
    setFocusDate,
    ...buildRange(view, focusDate),
    goToday,
    goPrevious,
    goNext,
  };
}
