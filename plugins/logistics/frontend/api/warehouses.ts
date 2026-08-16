// Auto-generado por split_api.py
import { API_PREFIX, withQuery } from "./_shared";
import { apiRequest } from "@systutor/shell/api/client";

export type LogisticsWarehouse = {
  id: string;
  tenant_id: string;
  name: string;
  code: string;
  warehouse_type: string;
  address: string | null;
  phone: string | null;
  is_primary: boolean;
  latitude: number | null;
  longitude: number | null;
  formatted_address: string | null;
  place_id: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export function isRealWarehouse(warehouse: LogisticsWarehouse) {
  return warehouse.warehouse_type !== "MOBILE";
}

export function getRealWarehouses(warehouses: LogisticsWarehouse[]) {
  return warehouses.filter(isRealWarehouse);
}

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

export function setPrimaryWarehouse(warehouseId: string) {
  return apiRequest<LogisticsWarehouse>(
    `${API_PREFIX}/warehouses/${warehouseId}/primary`,
    { method: "PATCH" }
  );
}
