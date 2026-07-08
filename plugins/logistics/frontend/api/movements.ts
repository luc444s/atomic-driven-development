// Auto-generado por split_api.py
import { API_PREFIX, withQuery } from "./_shared";
import { MovementEquipment } from "./equipment";
import { apiRequest } from "../../../../apps/web/src/shared/api/client";

export type LogisticsMovementType = {
  code: string;
  name: string;
  category: string;
  moves_cylinders: boolean;
  origin_state: string | null;
  target_state: string | null;
};

export type LogisticsMovement = {
  id: string;
  tenant_id: string;
  branch_id: string | null;
  movement_type: string;
  document_series: string | null;
  document_number: string | null;
  full_document: string | null;
  order_id: string | null;
  route_id: string | null;
  customer_id: string | null;
  customer_name: string | null;
  warehouse_id: string | null;
  driver_id: string | null;
  vehicle_id: string | null;
  total: number | null;
  tax: number | null;
  discount: number | null;
  currency: string;
  exchange_rate: number;
  status: string;
  payment_status: string | null;
  carrier: string | null;
  plate: string | null;
  destination_place: string | null;
  destination_address: string | null;
  notes: string | null;
  dispatched_at: string | null;
  parent_movement_id: string | null;
  created_by: string;
  created_at: string;
  updated_at: string;
};

export type LogisticsMovementItem = {
  id: string;
  movement_id: string;
  cylinder_id: string | null;
  product_id: string | null;
  product_name: string | null;
  quantity_in: number;
  quantity_out: number;
  quantity: number;
  quantity_planned: number;
  unit_price: number | null;
  total_item: number | null;
  discount: number;
  item_status: string;
  state_before: string | null;
  state_after: string | null;
  notes: string | null;
  created_at: string;
};

export type LogisticsMovementHistory = {
  id: string;
  movement_id: string;
  field_name: string;
  from_value: string | null;
  to_value: string;
  changed_by: string;
  notes: string | null;
  created_at: string;
};

export function listMovementTypes() {
  return apiRequest<LogisticsMovementType[]>(`${API_PREFIX}/catalog/movement-types`);
}

export function listMovements(filters: { type?: string; status?: string; customer?: string }) {
  return apiRequest<LogisticsMovement[]>(
    withQuery(`${API_PREFIX}/movements`, {
      type: filters.type,
      status: filters.status,
      customer: filters.customer,
    })
  );
}

export function getMovement(movementId: string) {
  return apiRequest<LogisticsMovement>(`${API_PREFIX}/movements/${movementId}`);
}

export function listMovementItems(movementId: string) {
  return apiRequest<LogisticsMovementItem[]>(`${API_PREFIX}/movements/${movementId}/items`);
}

export function listMovementHistory(movementId: string) {
  return apiRequest<LogisticsMovementHistory[]>(`${API_PREFIX}/movements/${movementId}/history`);
}

export function createMovement(payload: Record<string, unknown>) {
  return apiRequest<LogisticsMovement>(`${API_PREFIX}/movements`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateMovement(movementId: string, payload: Record<string, unknown>) {
  return apiRequest<LogisticsMovement>(`${API_PREFIX}/movements/${movementId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function confirmMovement(movementId: string) {
  return apiRequest<LogisticsMovement>(`${API_PREFIX}/movements/${movementId}/confirm`, {
    method: "POST",
  });
}

export function cancelMovement(movementId: string, reason: string) {
  return apiRequest<LogisticsMovement>(`${API_PREFIX}/movements/${movementId}/cancel`, {
    method: "POST",
    body: JSON.stringify({ reason }),
  });
}

export function listMovementEquipment(movementId: string) {
  return apiRequest<MovementEquipment[]>(`${API_PREFIX}/movements/${movementId}/equipment`);
}

