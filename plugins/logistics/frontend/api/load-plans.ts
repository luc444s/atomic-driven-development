import { API_PREFIX } from "./_shared";
import { apiRequest } from "@systutor/shell/api/client";

export type LoadPlanItem = {
  id: string;
  product_id: string;
  product_name: string;
  planned_quantity: number;
  planned_weight_kg: number | null;
  source_warehouse_id: string;
  notes: string | null;
  requires_serials: boolean;
  selected_serials_count: number;
  serials_complete: boolean;
  created_at: string;
};

export type LoadPlan = {
  id: string | null;
  session_id: string;
  status: string;
  notes: string | null;
  planned_weight_kg: number;
  items: LoadPlanItem[];
};

export type LoadPlanUpsertPayload = {
  notes?: string | null;
    items: Array<{
      product_id: string;
      planned_quantity: number;
      source_warehouse_id?: string | null;
      notes?: string | null;
  }>;
};

export type ConfirmLoadPayload = {
  notes?: string | null;
};

export type ReturnRemainingPayload = {
  destination_warehouse_id?: string | null;
  notes?: string | null;
};

export function getLoadPlan(sessionId: string) {
  return apiRequest<LoadPlan>(`${API_PREFIX}/vehicle-sessions/${sessionId}/load-plan`);
}

export function upsertLoadPlan(sessionId: string, payload: LoadPlanUpsertPayload) {
  return apiRequest<LoadPlan>(`${API_PREFIX}/vehicle-sessions/${sessionId}/load-plan`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function confirmLoad(sessionId: string, payload: ConfirmLoadPayload = {}) {
  return apiRequest<{ session_id: string; loaded_weight_kg: number }>(
    `${API_PREFIX}/vehicle-sessions/${sessionId}/confirm-load`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    }
  );
}

export function confirmAndReady(sessionId: string, payload: ConfirmLoadPayload = {}) {
  return apiRequest<{ id: string; status: string; loaded_weight_kg: number | null }>(
    `${API_PREFIX}/vehicle-sessions/${sessionId}/confirm-and-ready`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    }
  );
}

export function returnRemaining(sessionId: string, payload: ReturnRemainingPayload = {}) {
  return apiRequest<{ session_id: string; status: string }>(
    `${API_PREFIX}/vehicle-sessions/${sessionId}/return-remaining`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    }
  );
}
