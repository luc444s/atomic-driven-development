// Auto-generado por split_api.py
import { API_PREFIX, withQuery } from "./_shared";
import { apiRequest } from "@systutor/shell/api/client";

export type LogisticsLoad = {
  id: string;
  route_id: string;
  cylinder_id: string;
  stop_id: string | null;
  status: string;
  loaded_at: string | null;
  unloaded_at: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
};

export function listLoads(routeId: string) {
  return apiRequest<LogisticsLoad[]>(withQuery(`${API_PREFIX}/loads`, { route_id: routeId }));
}

export function createLoad(payload: Record<string, unknown>) {
  return apiRequest<LogisticsLoad>(`${API_PREFIX}/loads`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function bulkCreateLoads(payload: Record<string, unknown>) {
  return apiRequest<LogisticsLoad[]>(`${API_PREFIX}/loads/bulk`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function deleteLoad(loadId: string) {
  return apiRequest<void>(`${API_PREFIX}/loads/${loadId}`, { method: "DELETE" });
}

export function confirmLoads(routeId: string) {
  return apiRequest<LogisticsLoad[]>(`${API_PREFIX}/loads/confirm`, {
    method: "POST",
    body: JSON.stringify({ route_id: routeId }),
  });
}

export type LoadSummaryItem = {
  cylinder_id: string;
  serial: string | null;
  state: string | null;
  weight_kg: number | null;
};

export type LoadSummaryReport = {
  route_id: string;
  driver_id: string;
  vehicle_id: string | null;
  total_weight_kg: number;
  items: LoadSummaryItem[];
};

export function getLoadSummary(routeId: string) {
  return apiRequest<LoadSummaryReport>(`${API_PREFIX}/reports/load-summary/${routeId}`);
}

export type LoadWeightSummary = {
  route_id: string;
  weight_limit_kg: number;
  total_weight_kg: number;
  exceeds_limit: boolean;
};

export function getLoadWeightSummary(routeId: string) {
  return apiRequest<LoadWeightSummary>(`${API_PREFIX}/loads/weight-summary?route_id=${routeId}`);
}

