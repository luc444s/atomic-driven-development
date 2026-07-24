export function resolveDate(raw: string, referenceDate?: Date): Date | null {
  const ref = referenceDate ?? new Date();
  const normalized = raw.toLowerCase().trim();

  if (normalized === "hoy") return new Date(ref.getFullYear(), ref.getMonth(), ref.getDate());
  if (normalized === "mañana" || normalized === "manana") {
    const d = new Date(ref.getFullYear(), ref.getMonth(), ref.getDate());
    d.setDate(d.getDate() + 1);
    return d;
  }
  if (normalized === "pasado mañana" || normalized === "pasado manana") {
    const d = new Date(ref.getFullYear(), ref.getMonth(), ref.getDate());
    d.setDate(d.getDate() + 2);
    return d;
  }

  const weekdays: Record<string, number> = {
    domingo: 0, lunes: 1, martes: 2, miercoles: 3, miercoles: 3,
    jueves: 4, viernes: 5, sabado: 6,
  };
  if (weekdays[normalized] !== undefined) {
    const target = weekdays[normalized];
    const d = new Date(ref.getFullYear(), ref.getMonth(), ref.getDate());
    const current = d.getDay();
    let diff = target - current;
    if (diff <= 0) diff += 7;
    d.setDate(d.getDate() + diff);
    return d;
  }

  const isoMatch = normalized.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (isoMatch) {
    return new Date(Number(isoMatch[1]), Number(isoMatch[2]) - 1, Number(isoMatch[3]));
  }

  return null;
}

export function resolveTime(raw: string): string | null {
  const normalized = raw.toLowerCase().trim();

  if (normalized === "mañana" || normalized === "manana") return "06:00";
  if (normalized === "tarde") return "14:00";
  if (normalized === "noche") return "20:00";

  const timeMatch = normalized.match(/^(\d{1,2})[:h](\d{2})?/);
  if (timeMatch) {
    const h = timeMatch[1].padStart(2, "0");
    const m = timeMatch[2] ?? "00";
    return `${h}:${m.padEnd(2, "0")}`;
  }

  const simpleMatch = normalized.match(/^(\d{1,2})\s*(hrs?|h)$/);
  if (simpleMatch) {
    return `${simpleMatch[1].padStart(2, "0")}:00`;
  }

  return null;
}

export function formatDate(d: Date): string {
  return d.toISOString().slice(0, 10);
}
