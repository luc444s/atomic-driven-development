import { API_PREFIX, withQuery } from "./_shared";
import { apiRequest } from "../../../../apps/web/src/shared/api/client";

export type DriverOption = {
  id: string;
  full_name: string;
  email: string;
};

export type SessionStockSummary = {
  warehouse_id: string;
  warehouse_code: string;
  warehouse_name: string;
  total_products: number;
  total_units: number;
};

export type SessionHistoryEntry = {
  occurred_at: string;
  category: string;
  label: string;
};

export type VehicleSession = {
  id: string;
  vehicle_id: string;
  vehicle_plate: string;
  driver_id: string;
  driver_name: string;
  origin_warehouse_id: string;
  origin_warehouse_name: string;
  mobile_warehouse_id: string;
  mobile_warehouse_code: string;
  mobile_warehouse_name: string;
  route_id: string | null;
  status: string;
  opened_at: string;
  ready_at: string | null;
  departed_at: string | null;
  returned_at: string | null;
  closed_at: string | null;
  planned_weight_kg: number | null;
  loaded_weight_kg: number | null;
  occupancy_percent: number | null;
  last_activity: string | null;
  can_depart: boolean;
  can_close: boolean;
  next_transition_allowed: boolean;
  next_transition_blocker: string | null;
  current_stock: SessionStockSummary;
};

export type VehicleSessionDetail = VehicleSession & {
  history: SessionHistoryEntry[];
};

export type CreateVehicleSessionPayload = {
  vehicle_id: string;
  driver_id: string;
  origin_warehouse_id?: string | null;
  route_id?: string | null;
};

export type SessionActionPayload = {
  notes?: string | null;
};

export const VEHICLE_SESSION_STATUS_LABELS: Record<string, string> = {
  DRAFT: "Borrador",
  LOADING: "Cargando",
  READY_TO_DEPART: "Listo para salir",
  OUTBOUND: "En ruta",
  RETURNING: "De regreso",
  AWAITING_RECONCILIATION: "Pendiente de conciliación",
  CLOSED: "Cerrada",
  CANCELLED: "Cancelada",
};

export function listVehicleSessions(filters: { status?: string } = {}) {
  return apiRequest<VehicleSession[]>(withQuery(`${API_PREFIX}/vehicle-sessions`, { status: filters.status }));
}

export function listActiveVehicleSessions() {
  return apiRequest<VehicleSession[]>(`${API_PREFIX}/vehicle-sessions/active`);
}

export function getVehicleSession(sessionId: string) {
  return apiRequest<VehicleSessionDetail>(`${API_PREFIX}/vehicle-sessions/${sessionId}`);
}

export function listVehicleSessionHistory(sessionId: string) {
  return apiRequest<SessionHistoryEntry[]>(`${API_PREFIX}/vehicle-sessions/${sessionId}/history`);
}

export function listDriverOptions() {
  return apiRequest<DriverOption[]>(`${API_PREFIX}/vehicle-sessions/drivers/catalog`);
}

export function createVehicleSession(payload: CreateVehicleSessionPayload) {
  return apiRequest<VehicleSessionDetail>(`${API_PREFIX}/vehicle-sessions`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function startLoadingSession(sessionId: string) {
  return apiRequest<VehicleSessionDetail>(`${API_PREFIX}/vehicle-sessions/${sessionId}/start-loading`, {
    method: "POST",
  });
}

export function markSessionReady(sessionId: string) {
  return apiRequest<VehicleSessionDetail>(`${API_PREFIX}/vehicle-sessions/${sessionId}/ready`, {
    method: "POST",
  });
}

export function departSession(sessionId: string) {
  return apiRequest<VehicleSessionDetail>(`${API_PREFIX}/vehicle-sessions/${sessionId}/depart`, {
    method: "POST",
  });
}

export function markSessionReturning(sessionId: string) {
  return apiRequest<VehicleSessionDetail>(`${API_PREFIX}/vehicle-sessions/${sessionId}/mark-returning`, {
    method: "POST",
  });
}

export function cancelSession(sessionId: string, payload: SessionActionPayload = {}) {
  return apiRequest<VehicleSessionDetail>(`${API_PREFIX}/vehicle-sessions/${sessionId}/cancel`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
