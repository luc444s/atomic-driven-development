// Auto-generado por split_api.py
import { API_PREFIX, withQuery } from "./_shared";
import { apiRequest } from "../../../../apps/web/src/shared/api/client";

export type LogisticsWarehouse = {
  id: string;
  tenant_id: string;
  name: string;
  code: string;
  address: string | null;
  phone: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export function listWarehouses() {
  return apiRequest<LogisticsWarehouse[]>(`${API_PREFIX}/warehouses`);
}

export function createWarehouse(payload: Record<string, unknown>) {
  return apiRequest<LogisticsWarehouse>(`${API_PREFIX}/warehouses`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateWarehouse(warehouseId: string, payload: Record<string, unknown>) {
  return apiRequest<LogisticsWarehouse>(`${API_PREFIX}/warehouses/${warehouseId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

