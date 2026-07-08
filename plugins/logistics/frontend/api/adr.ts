// Auto-generado por split_api.py
import { API_PREFIX, withQuery } from "./_shared";
import { apiRequest } from "../../../../apps/web/src/shared/api/client";

export type AdrProductConfig = {
  id: string;
  tenant_id: string;
  product_id: string;
  adr_class: string | null;
  adr_points: number | null;
  adr_tunnel: string | null;
  max_quantity: number | null;
  valid_from: string;
  valid_to: string | null;
  created_at: string;
  updated_at: string;
};

export type AdrIncompatibility = {
  id: string;
  tenant_id: string;
  product_id_1: string;
  product_id_2: string;
  created_at: string;
};

export function getAdrProductConfig(productId: string) {
  return apiRequest<AdrProductConfig | null>(`${API_PREFIX}/adr/product-config/${productId}`);
}

export function upsertAdrProductConfig(productId: string, payload: {
  adr_class?: string; adr_points?: number; adr_tunnel?: string;
  max_quantity?: number; valid_from: string; valid_to?: string;
}) {
  return apiRequest<AdrProductConfig>(`${API_PREFIX}/adr/product-config/${productId}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function listAdrIncompatibilities() {
  return apiRequest<AdrIncompatibility[]>(`${API_PREFIX}/adr/incompatibilities`);
}

export function createAdrIncompatibility(payload: { product_id_1: string; product_id_2: string }) {
  return apiRequest<AdrIncompatibility>(`${API_PREFIX}/adr/incompatibilities`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function deleteAdrIncompatibility(id: string) {
  return apiRequest<void>(`${API_PREFIX}/adr/incompatibilities/${id}`, { method: "DELETE" });
}

