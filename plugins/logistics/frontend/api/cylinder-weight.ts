// Auto-generado por split_api.py
import { API_PREFIX, withQuery } from "./_shared";
import { apiRequest } from "@systutor/shell/api/client";

export type CylinderWeight = {
  cylinder_id: string;
  serial: string;
  product_id: string | null;
  product_name: string | null;
  tara_weight_kg: number | null;
  current_weight_kg: number | null;
  content_kg: number | null;
  total_weight_kg: number | null;
};

export type ProductContent = {
  product_id: string;
  product_name: string;
  content_kg: number | null;
};

export type SerializedCylinderSummary = {
  product_id: string;
  product_sku: string;
  product_name: string;
  serialized_count: number;
};

export function listAvailableCylindersWithWeight(warehouse_id?: string) {
  return apiRequest<CylinderWeight[]>(
    withQuery(`${API_PREFIX}/cylinders/available-with-weight`, { warehouse_id })
  );
}

export function listSerializedCylinderSummary(warehouse_id: string) {
  return apiRequest<SerializedCylinderSummary[]>(
    withQuery(`${API_PREFIX}/cylinders/serialized-summary`, { warehouse_id })
  );
}

export function getCylinderWeight(cylinderId: string) {
  return apiRequest<CylinderWeight>(`${API_PREFIX}/cylinders/${cylinderId}/weight`);
}

export function getProductContent(productId: string) {
  return apiRequest<ProductContent>(`${API_PREFIX}/products/${productId}/content`);
}
