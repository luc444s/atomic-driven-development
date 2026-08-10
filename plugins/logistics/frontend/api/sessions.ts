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
  total_adr_points: number;
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
  route_date: string | null;
  route_origin_label: string | null;
  route_destination_label: string | null;
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

export type VehicleSessionPage = {
  items: VehicleSession[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
};

export type SessionWaybillVehicle = {
  id: string;
  plate: string;
  kind: string | null;
};

export type SessionWaybillDriver = {
  id: string;
  name: string;
  license: string | null;
};

export type SessionWaybillDestination = {
  id: string | null;
  name: string | null;
  address: string | null;
};

export type SessionWaybillItem = {
  product_id: string;
  product_name: string;
  quantity: number;
  unit: string | null;
  weight_kg: number | null;
  adr_points: number | null;
};

export type SessionWaybillTotals = {
  total_packages: number | null;
  total_weight_kg: number | null;
  total_adr_points: number | null;
};

export type SessionWaybillSnapshot = {
  vehicle: SessionWaybillVehicle;
  driver: SessionWaybillDriver;
  destination: SessionWaybillDestination;
  transported_items: SessionWaybillItem[];
  totals: SessionWaybillTotals;
};

export type SessionWaybillVersion = {
  id: string;
  vehicle_session_id: string;
  movement_ids: string[];
  version: number;
  previous_version_id: string | null;
  status: string;
  regulatory_context: string;
  generated_at: string;
  generated_by: string | null;
  snapshot_schema_version: number;
  change_event: string;
  change_reason: string;
  snapshot: SessionWaybillSnapshot;
};

export type SessionWaybillState = {
  active: SessionWaybillVersion | null;
  sync_status: string | null;
  can_regenerate: boolean;
};

export type SessionWaybillRegeneratePayload = {
  reason: string;
  event: string;
  idempotency_key?: string | null;
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

export function listVehicleSessions(filters: { status?: string; page?: number; per_page?: number } = {}) {
  const params: Record<string, string> = {};
  if (filters.status) params.status = filters.status;
  if (filters.page) params.page = String(filters.page);
  if (filters.per_page) params.per_page = String(filters.per_page);
  return apiRequest<VehicleSessionPage>(withQuery(`${API_PREFIX}/vehicle-sessions`, params));
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

export function getSessionWaybill(sessionId: string) {
  return apiRequest<SessionWaybillState>(`${API_PREFIX}/vehicle-sessions/${sessionId}/carta-porte`);
}

export function listSessionWaybillHistory(sessionId: string) {
  return apiRequest<SessionWaybillVersion[]>(`${API_PREFIX}/vehicle-sessions/${sessionId}/carta-porte/history`);
}

export function regenerateSessionWaybill(sessionId: string, payload: SessionWaybillRegeneratePayload) {
  return apiRequest<SessionWaybillState>(`${API_PREFIX}/vehicle-sessions/${sessionId}/carta-porte/regenerate`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function assignRouteToSession(sessionId: string, routeId: string) {
  return apiRequest<VehicleSessionDetail>(`${API_PREFIX}/vehicle-sessions/${sessionId}/assign-route`, {
    method: "POST",
    body: JSON.stringify({ route_id: routeId }),
  });
}

export type VehicleLocationRecordPayload = {
  lat: number;
  lng: number;
  speed?: number | null;
  heading?: number | null;
  accuracy_meters?: number | null;
  recorded_at: string;
  source?: string;
};

export type VehicleLocationEvent = {
  id: string;
  session_id: string;
  route_id: string | null;
  vehicle_id: string;
  driver_id: string;
  lat: number;
  lng: number;
  speed: number | null;
  heading: number | null;
  accuracy_meters: number | null;
  source: string;
  recorded_at: string;
  received_at: string;
};

export type RouteControlState = {
  session_id: string;
  route_id: string | null;
  vehicle_id: string;
  active_stop_id: string | null;
  active_stop_started_at: string | null;
  current_stop_id: string | null;
  current_stop_index: number | null;
  status: string;
  last_lat: number | null;
  last_lng: number | null;
  last_speed: number | null;
  last_heading: number | null;
  last_recorded_at: string | null;
  completed_stops: number;
  total_stops: number;
  progress_percent: number;
  off_route: boolean;
  next_stop_eta_minutes: number | null;
  geofence_state: string | null;
  updated_at: string;
};
