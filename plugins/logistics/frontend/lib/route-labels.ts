type RouteLabelSource = {
  route_date?: string | null;
  route_id?: string | null;
  notes?: string | null;
  origin_label?: string | null;
  destination_label?: string | null;
};

const ROUTE_LABEL_PREFIX_RE = /^\d+\s*·\s*/;

function cleanLabel(value: string | null | undefined) {
  const normalized = value?.replace(ROUTE_LABEL_PREFIX_RE, "").trim();
  return normalized ? normalized : null;
}

export function formatRouteLabel(route: RouteLabelSource) {
  const originLabel = cleanLabel(route.origin_label);
  const destinationLabel = cleanLabel(route.destination_label);
  if (originLabel && destinationLabel) {
    return `${originLabel} → ${destinationLabel}`;
  }
  if (originLabel || destinationLabel) {
    return originLabel ?? destinationLabel ?? "Sin ruta";
  }
  const notes = cleanLabel(route.notes);
  if (notes?.includes("→")) {
    return notes;
  }
  return cleanLabel(route.route_date) ?? cleanLabel(route.route_id) ?? "Sin ruta";
}
