import { API_PREFIX } from "./_shared";
import { apiRequest } from "@systutor/shell/api/client";

export type ReconciliationLine = {
  product_id: string;
  product_name: string;
  expected_quantity: number;
  counted_quantity: number | null;
  difference_quantity: number | null;
};

export type InventoryDiscrepancy = {
  id: string;
  product_id: string;
  product_name: string;
  expected_quantity: number;
  counted_quantity: number;
  difference_quantity: number;
  status: string;
  resolution_notes: string | null;
};

export type SessionReconciliation = {
  id: string | null;
  session_id: string;
  status: string;
  counted_by: string | null;
  counted_at: string | null;
  notes: string | null;
  can_close: boolean;
  lines: ReconciliationLine[];
  discrepancies: InventoryDiscrepancy[];
};

export type ReconciliationCountPayload = {
  notes?: string | null;
  items: Array<{
    product_id: string;
    counted_quantity: number;
  }>;
};

export type CloseSessionPayload = {
  notes?: string | null;
};

export function getSessionReconciliation(sessionId: string) {
  return apiRequest<SessionReconciliation>(`${API_PREFIX}/vehicle-sessions/${sessionId}/reconciliation`);
}

export function countSessionReconciliation(sessionId: string, payload: ReconciliationCountPayload) {
  return apiRequest<SessionReconciliation>(`${API_PREFIX}/vehicle-sessions/${sessionId}/reconciliation/count`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function closeVehicleSession(sessionId: string, payload: CloseSessionPayload = {}) {
  return apiRequest<{ session_id: string; status: string }>(`${API_PREFIX}/vehicle-sessions/${sessionId}/close`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
