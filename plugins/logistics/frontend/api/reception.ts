// Auto-generado por split_api.py
import { API_PREFIX, withQuery } from "./_shared";
import { LogisticsMovement, LogisticsMovementItem } from "./movements";
import { apiRequest } from "../../../../apps/web/src/shared/api/client";

export type ReceptionIncident = {
  id: string;
  tenant_id: string;
  movement_id: string;
  cylinder_id: string | null;
  reason_code: string;
  description: string | null;
  created_by: string;
  created_at: string;
};

export type ReceptionReceiveResult = {
  movement: LogisticsMovement;
  incidents: ReceptionIncident[];
  shortage_items: LogisticsMovementItem[];
};

export type IncidentReason = {
  code: string;
  description: string;
  target_state: string | null;
};

export function listPendingReceptions(warehouse_id?: string) {
  return apiRequest<LogisticsMovement[]>(
    withQuery(`${API_PREFIX}/reception/pending`, { warehouse_id })
  );
}

export function getReceptionDetail(movementId: string) {
  return apiRequest<LogisticsMovement>(`${API_PREFIX}/reception/${movementId}`);
}

export function receiveMovement(movementId: string, payload: { items: { movement_item_id: string; quantity_received: number }[]; notes?: string }) {
  return apiRequest<ReceptionReceiveResult>(`${API_PREFIX}/reception/${movementId}/receive`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function createReceptionIncident(movementId: string, payload: { cylinder_id?: string; reason_code: string; description?: string }) {
  return apiRequest<ReceptionIncident>(`${API_PREFIX}/reception/${movementId}/incident`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function listIncidentReasons() {
  return apiRequest<IncidentReason[]>(`${API_PREFIX}/reception/incident-reasons`);
}

