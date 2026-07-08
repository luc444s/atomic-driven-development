// Auto-generado por split_api.py
import { API_PREFIX, withQuery } from "./_shared";
import { apiRequest } from "../../../../apps/web/src/shared/api/client";

export type Equipment = {
  id: string;
  tenant_id: string;
  name: string;
  equipment_type: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type MovementEquipment = {
  id: string;
  tenant_id: string;
  movement_id: string;
  equipment_id: string;
  assigned_at: string;
  returned_at: string | null;
  notes: string | null;
};

export function listEquipment() {
  return apiRequest<Equipment[]>(`${API_PREFIX}/equipment`);
}

export function createEquipment(payload: { name: string; equipment_type?: string; is_active?: boolean }) {
  return apiRequest<Equipment>(`${API_PREFIX}/equipment`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function assignEquipmentToMovement(movementId: string, payload: { equipment_id: string; notes?: string }) {
  return apiRequest<MovementEquipment>(`${API_PREFIX}/movements/${movementId}/equipment`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function returnMovementEquipment(movementId: string, eqId: string, payload?: { notes?: string }) {
  return apiRequest<MovementEquipment>(
    `${API_PREFIX}/movements/${movementId}/equipment/${eqId}/return`,
    { method: "PATCH", body: payload ? JSON.stringify(payload) : undefined }
  );
}

