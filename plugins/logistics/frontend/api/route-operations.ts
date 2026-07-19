import { API_PREFIX } from "./_shared";
import { apiRequest } from "../../../../apps/web/src/shared/api/client";

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
  operation_type: string;
  status: string;
  movement_ids: string[];
  idempotency_key: string;
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

export function listRouteOperations(sessionId: string) {
  return apiRequest<RouteOperation[]>(`${API_PREFIX}/vehicle-sessions/${sessionId}/route-operations`);
}

export function createRouteOperation(sessionId: string, payload: RouteOperationCreatePayload) {
  return apiRequest<RouteOperation>(`${API_PREFIX}/vehicle-sessions/${sessionId}/route-operations`, {
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

export function getCurrentComposition(sessionId: string) {
  return apiRequest<CurrentComposition>(`${API_PREFIX}/vehicle-sessions/${sessionId}/composition/current`);
}
