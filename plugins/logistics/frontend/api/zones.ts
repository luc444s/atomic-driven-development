// Auto-generado por split_api.py
import { API_PREFIX, withQuery } from "./_shared";
import { apiRequest } from "../../../../apps/web/src/shared/api/client";

export type LogisticsZone = {
  id: string;
  tenant_id: string;
  name: string;
  code: string;
  is_active: boolean;
  created_at: string;
};

export function listZones() {
  return apiRequest<LogisticsZone[]>(`${API_PREFIX}/zones`);
}

export function createZone(payload: Record<string, unknown>) {
  return apiRequest<LogisticsZone>(`${API_PREFIX}/zones`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

