const STOP_STATUS_LABELS: Record<string, string> = {
  PENDING: "Pendiente",
  IN_PROGRESS: "En progreso",
  PARTIAL: "Parcial",
  COMPLETED: "Completada",
  FAILED: "Fallida",
};

export const STOP_STATUS_BORDER_COLORS: Record<string, string> = {
  PENDING: "border-l-gray-400",
  IN_PROGRESS: "border-l-blue-500",
  PARTIAL: "border-l-amber-500",
  COMPLETED: "border-l-green-500",
  FAILED: "border-l-red-500",
};

const STOP_OUTCOME_LABELS: Record<string, string> = {
  NORMAL: "Normal",
  CUSTOMER_ABSENT: "Cliente ausente",
  FAILED_DELIVERY: "Entrega fallida",
  PARTIAL_ATTENDED: "Atencion parcial",
  UNPLANNED_RETURN: "Retorno no planificado",
  OTHER: "Otro",
};

const ROUTE_OPERATION_TYPE_LABELS: Record<string, string> = {
  DELIVERY: "Entrega",
  PICKUP: "Recojo",
  EXCHANGE: "Intercambio",
};

const ROUTE_OPERATION_STATUS_LABELS: Record<string, string> = {
  DRAFT: "Borrador",
  CONFIRMED: "Confirmada",
  CANCELLED: "Cancelada",
  FAILED: "Fallida",
};

const MOVEMENT_DIRECTION_LABELS: Record<string, string> = {
  OUT: "Salida",
  IN: "Ingreso",
};

const ROUTE_INCIDENT_TYPE_LABELS: Record<string, string> = {
  QUANTITY_MISMATCH: "Descuadre de cantidad",
  WRONG_PRODUCT: "Producto incorrecto",
  EXCESS_DELIVERY: "Exceso de entrega",
  MISSING_PICKUP: "Recojo faltante",
  CUSTOMER_ABSENT: "Cliente ausente",
  FAILED_DELIVERY: "Entrega fallida",
  UNPLANNED_RETURN: "Retorno no planificado",
};

const ROUTE_INCIDENT_STATUS_LABELS: Record<string, string> = {
  OPEN: "Abierta",
  RESOLVED: "Resuelta",
  CORRECTED: "Corregida",
};

const WAYBILL_SYNC_STATUS_LABELS: Record<string, string> = {
  SYNCED: "Sincronizada",
  OUTDATED: "Desactualizada",
  MISSING: "Faltante",
};

const WAYBILL_VERSION_STATUS_LABELS: Record<string, string> = {
  ACTIVE: "Activa",
  SUPERSEDED: "Reemplazada",
  VOID: "Anulada",
};

const WAYBILL_CHANGE_EVENT_LABELS: Record<string, string> = {
  INITIAL_GENERATION: "Generacion inicial",
  MOVEMENT_CHANGED: "Cambio de movimientos",
  DRIVER_CHANGED: "Cambio de conductor",
  VEHICLE_CHANGED: "Cambio de vehiculo",
  DESTINATION_CHANGED: "Cambio de destino",
};

const LOAD_SERIAL_ASSIGNMENT_STATUS_LABELS: Record<string, string> = {
  SELECTED: "Seleccionado",
  CONFIRMED: "Confirmado",
  RELEASED: "Liberado",
};

const HEALTH_STATUS_LABELS: Record<string, string> = {
  HEALTHY: "Sana",
  ATTENTION: "En atencion",
  BLOCKED: "Bloqueada",
};

const DATA_COMPLETENESS_LABELS: Record<string, string> = {
  FULL: "Completa",
  PARTIAL: "Parcial",
};

const ROUTE_STATUS_LABELS: Record<string, string> = {
  PLANNED: "Planificada",
  IN_PROGRESS: "En progreso",
  COMPLETED: "Completada",
  CANCELLED: "Cancelada",
};

function prettifyCode(code: string): string {
  return code
    .toLowerCase()
    .split("_")
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function formatFromMap(value: string | null | undefined, labels: Record<string, string>, fallback = "-"): string {
  if (!value) {
    return fallback;
  }
  return labels[value] ?? prettifyCode(value);
}

export function formatStopStatus(status: string | null | undefined) {
  return formatFromMap(status, STOP_STATUS_LABELS);
}

export function formatStopOutcomeType(outcomeType: string | null | undefined) {
  return formatFromMap(outcomeType, STOP_OUTCOME_LABELS);
}

export function formatRouteOperationType(operationType: string | null | undefined) {
  return formatFromMap(operationType, ROUTE_OPERATION_TYPE_LABELS);
}

export function formatRouteOperationStatus(status: string | null | undefined) {
  return formatFromMap(status, ROUTE_OPERATION_STATUS_LABELS);
}

export function formatMovementDirection(direction: string | null | undefined) {
  return formatFromMap(direction, MOVEMENT_DIRECTION_LABELS);
}

export function formatRouteIncidentType(type: string | null | undefined) {
  return formatFromMap(type, ROUTE_INCIDENT_TYPE_LABELS);
}

export function formatRouteIncidentStatus(status: string | null | undefined) {
  return formatFromMap(status, ROUTE_INCIDENT_STATUS_LABELS);
}

export function formatWaybillSyncStatus(status: string | null | undefined) {
  return formatFromMap(status, WAYBILL_SYNC_STATUS_LABELS);
}

export function formatWaybillVersionStatus(status: string | null | undefined) {
  return formatFromMap(status, WAYBILL_VERSION_STATUS_LABELS);
}

export function formatWaybillChangeEvent(event: string | null | undefined) {
  return formatFromMap(event, WAYBILL_CHANGE_EVENT_LABELS);
}

export function formatLoadSerialAssignmentStatus(status: string | null | undefined) {
  return formatFromMap(status, LOAD_SERIAL_ASSIGNMENT_STATUS_LABELS);
}

export function formatHealthStatus(status: string | null | undefined) {
  return formatFromMap(status, HEALTH_STATUS_LABELS);
}

export function formatDataCompleteness(status: string | null | undefined) {
  return formatFromMap(status, DATA_COMPLETENESS_LABELS);
}

export function formatRouteStatus(status: string | null | undefined) {
  return formatFromMap(status, ROUTE_STATUS_LABELS);
}
