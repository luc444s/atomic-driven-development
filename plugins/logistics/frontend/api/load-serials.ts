import { API_PREFIX } from "./_shared";
import { apiRequest } from "../../../../apps/web/src/shared/api/client";

export type LoadSerialAssignment = {
  id: string;
  session_id: string;
  product_id: string;
  cylinder_id: string;
  cylinder_serial: string;
  assignment_status: string;
  selected_by: string;
  selected_at: string;
  confirmed_by_operation_id: string | null;
  confirmed_at: string | null;
  released_at: string | null;
  release_reason: string | null;
  notes: string | null;
  updated_at: string;
};

export type LoadSerialSearchResult = {
  cylinder_id: string;
  serial: string;
  availability_status: string;
  context_label: string | null;
};

export type LoadSerialSelectionContext = "LOAD_PLAN" | "ROUTE_PICKUP" | "ROUTE_DELIVERY";

export function listSelectedLoadSerials(
  sessionId: string,
  productId: string,
  selectionContext: LoadSerialSelectionContext = "LOAD_PLAN"
) {
  const query = new URLSearchParams({ product_id: productId, selection_context: selectionContext });
  return apiRequest<LoadSerialAssignment[]>(
    `${API_PREFIX}/vehicle-sessions/${sessionId}/load-serials/selected?${query.toString()}`
  );
}

export function searchLoadSerials(
  sessionId: string,
  payload: {
    product_id: string;
    query: string;
    source_warehouse_id?: string | null;
    selection_context?: LoadSerialSelectionContext;
  }
) {
  const query = new URLSearchParams({
    product_id: payload.product_id,
    query: payload.query,
    selection_context: payload.selection_context ?? "LOAD_PLAN",
  });
  if (payload.source_warehouse_id) {
    query.set("source_warehouse_id", payload.source_warehouse_id);
  }
  return apiRequest<LoadSerialSearchResult[]>(
    `${API_PREFIX}/vehicle-sessions/${sessionId}/load-serials/search?${query.toString()}`
  );
}

export function selectLoadSerial(
  sessionId: string,
  payload: {
    product_id: string;
    source_warehouse_id?: string | null;
    selection_context?: LoadSerialSelectionContext;
    serial: string;
  }
) {
  return apiRequest<LoadSerialAssignment>(`${API_PREFIX}/vehicle-sessions/${sessionId}/load-serials/select`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function releaseLoadSerial(
  sessionId: string,
  assignmentId: string,
  payload: { release_reason: string }
) {
  return apiRequest<LoadSerialAssignment>(
    `${API_PREFIX}/vehicle-sessions/${sessionId}/load-serials/${assignmentId}/release`,
    {
      method: "PUT",
      body: JSON.stringify(payload),
    }
  );
}

export function toggleDeliverySelection(sessionId: string, assignmentId: string) {
  return apiRequest<LoadSerialAssignment>(
    `${API_PREFIX}/vehicle-sessions/${sessionId}/load-serials/${assignmentId}/delivery-toggle`,
    { method: "PUT" }
  );
}
