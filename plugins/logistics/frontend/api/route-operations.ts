import { API_PREFIX } from "./_shared";
import { apiRequest } from "@systutor/shell/api/client";

export type RouteOperationItem = {
  id: string;
  product_id: string;
  product_name: string;
  quantity: number;
  direction: string;
  created_at: string;
};

export type RouteOperation = {
  id: string;
  session_id: string;
  route_stop_id: string | null;
  context_type: string | null;
  customer_id: string | null;
  customer_name_snapshot: string | null;
  warehouse_id: string | null;
  warehouse_name_snapshot: string | null;
  operation_type: string;
  status: string;
  movement_ids: string[];
  idempotency_key: string;
  location_event_id: string | null;
  location_lat: number | null;
  location_lng: number | null;
  notes: string | null;
  performed_by: string | null;
  performed_at: string | null;
  created_at: string;
  updated_at: string;
  items: RouteOperationItem[];
};

export type RouteOperationCreatePayload = {
  route_stop_id?: string | null;
  operation_type: string;
  notes?: string | null;
  idempotency_key?: string | null;
  items: Array<{
    product_id: string;
    product_name?: string | null;
    quantity: number;
    direction: string;
  }>;
};

export type ExchangeRouteOperationCreatePayload = {
  route_stop_id?: string | null;
  notes?: string | null;
  idempotency_key?: string | null;
  delivered_lines: Array<{
    product_id: string;
    product_name?: string | null;
    quantity: number;
  }>;
  picked_up_lines: Array<{
    product_id: string;
    product_name?: string | null;
    quantity: number;
  }>;
};

export type CurrentComposition = {
  session_id: string;
  composition_version: number | null;
  product_lines: Array<{
    product_id: string;
    product_name: string;
    quantity: number;
    weight_kg: number | null;
    adr_points: number | null;
  }>;
  totals: {
    total_packages: number;
    total_weight_kg: number;
    total_adr_points: number;
  };
};

export type RouteIncident = {
  id: string;
  session_id: string;
  route_stop_id: string | null;
  related_operation_id: string | null;
  type: string;
  status: string;
  corrective_operation_id: string | null;
  notes: string | null;
  created_by: string;
  closed_by: string | null;
  created_at: string;
  closed_at: string | null;
  updated_at: string;
};

export type RouteStopProgress = {
  route_stop_id: string;
  progress_status: string;
  last_operation_at: string | null;
  open_incidents: number;
  completion_percent: number | null;
  outcome_type: string | null;
  driver_note: string | null;
};

export type RouteIncidentCreatePayload = {
  route_stop_id?: string | null;
  related_operation_id?: string | null;
  type: string;
  notes?: string | null;
};

export type RouteIncidentCorrectPayload = {
  route_stop_id?: string | null;
  operation_type: string;
  notes?: string | null;
  idempotency_key?: string | null;
  items: Array<{
    product_id: string;
    product_name?: string | null;
    quantity: number;
    direction: string;
  }>;
};

export type RouteEventConfirmPayload = {
  route_stop_id?: string | null;
  context_type: string;
  customer_id?: string | null;
  warehouse_id?: string | null;
  operation_type: string;
  notes?: string | null;
  idempotency_key: string;
  items: Array<{
    product_id: string;
    product_name?: string | null;
    quantity: number;
    direction: string;
  }>;
  incident_mode: string;
  type?: string | null;
  related_operation_id?: string | null;
  target_incident_id?: string | null;
  incident_notes?: string | null;
};

export function listRouteOperations(sessionId: string) {
  return apiRequest<RouteOperation[]>(`${API_PREFIX}/vehicle-sessions/${sessionId}/route-operations`);
}

export function createRouteOperation(sessionId: string, payload: RouteOperationCreatePayload) {
  return apiRequest<RouteOperation>(`${API_PREFIX}/vehicle-sessions/${sessionId}/route-operations`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function createExchangeRouteOperation(
  sessionId: string,
  payload: ExchangeRouteOperationCreatePayload
) {
  return apiRequest<RouteOperation>(`${API_PREFIX}/vehicle-sessions/${sessionId}/route-operations/exchange`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function confirmRouteOperation(sessionId: string, operationId: string) {
  return apiRequest<RouteOperation>(
    `${API_PREFIX}/vehicle-sessions/${sessionId}/route-operations/${operationId}/confirm`,
    { method: "POST" }
  );
}

export function confirmRouteEvent(sessionId: string, payload: RouteEventConfirmPayload) {
  return apiRequest<RouteOperation>(`${API_PREFIX}/vehicle-sessions/${sessionId}/route-events/confirm`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getCurrentComposition(sessionId: string) {
  return apiRequest<CurrentComposition>(`${API_PREFIX}/vehicle-sessions/${sessionId}/composition/current`);
}

export function listRouteIncidents(sessionId: string) {
  return apiRequest<RouteIncident[]>(`${API_PREFIX}/vehicle-sessions/${sessionId}/route-incidents`);
}

export function createRouteIncident(sessionId: string, payload: RouteIncidentCreatePayload) {
  return apiRequest<RouteIncident>(`${API_PREFIX}/vehicle-sessions/${sessionId}/route-incidents`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function resolveRouteIncident(sessionId: string, incidentId: string, payload: { notes?: string | null } = {}) {
  return apiRequest<RouteIncident>(
    `${API_PREFIX}/vehicle-sessions/${sessionId}/route-incidents/${incidentId}/resolve`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    }
  );
}

export function correctRouteIncident(sessionId: string, incidentId: string, payload: RouteIncidentCorrectPayload) {
  return apiRequest<RouteIncident>(
    `${API_PREFIX}/vehicle-sessions/${sessionId}/route-incidents/${incidentId}/correct`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    }
  );
}

export function getRouteStopProgress(sessionId: string) {
  return apiRequest<RouteStopProgress[]>(`${API_PREFIX}/vehicle-sessions/${sessionId}/route-stop-progress`);
}
