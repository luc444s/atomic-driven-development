export function formatReservationWindow(start: string, end: string) {
  return `${new Date(start).toLocaleString()} - ${new Date(end).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`;
}

export function toDateTimeLocalValue(value: string | null | undefined) {
  if (!value) {
    return "";
  }
  const date = new Date(value);
  const offset = date.getTimezoneOffset();
  const local = new Date(date.getTime() - offset * 60_000);
  return local.toISOString().slice(0, 16);
}

export function fromDateTimeLocalValue(value: string) {
  return new Date(value).toISOString();
}
