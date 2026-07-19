export type SessionContextKey = "load" | "route" | "reconciliation";

export const SESSION_STEPS = [
  { status: "DRAFT", label: "Borrador", context: "load" as const },
  { status: "LOADING", label: "Cargando", context: "load" as const },
  { status: "READY_TO_DEPART", label: "Listo para salir", context: "load" as const },
  { status: "OUTBOUND", label: "En ruta", context: "route" as const },
  { status: "RETURNING", label: "De regreso", context: "route" as const },
  {
    status: "AWAITING_RECONCILIATION",
    label: "Pend. conciliación",
    context: "reconciliation" as const,
  },
] as const;

export const CONTEXT_TITLE: Record<SessionContextKey, string> = {
  load: "Carga",
  route: "Ruta",
  reconciliation: "Conciliación",
};

export const STATUS_PHRASE: Record<string, string> = {
  DRAFT: "Sin carga planificada",
  LOADING: "Carga incompleta",
  READY_TO_DEPART: "Vehículo listo",
  OUTBOUND: "Operación activa",
  RETURNING: "Retorno en curso",
  AWAITING_RECONCILIATION: "Revisar diferencias",
  CLOSED: "Jornada finalizada",
  CANCELLED: "Jornada cancelada",
};

export const MANUAL_ACTION_LABELS: Record<string, string> = {
  DRAFT: "Iniciar carga",
  READY_TO_DEPART: "Iniciar ruta",
  OUTBOUND: "Marcar retorno",
  RETURNING: "Retornar remanente",
  CANCELLED: "Jornada cancelada",
};

export const AUTO_ACTION_HINTS: Record<string, string> = {
  LOADING: "La carga válida avanza automáticamente.",
  AWAITING_RECONCILIATION: "El cierre ocurre al guardar un conteo sin diferencias.",
};

export const STEPPER_ACTIONABLE_STATUSES = new Set([
  "DRAFT",
  "READY_TO_DEPART",
  "OUTBOUND",
  "RETURNING",
]);
