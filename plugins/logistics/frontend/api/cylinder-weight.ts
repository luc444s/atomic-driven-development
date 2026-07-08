// Auto-generado por split_api.py
import { API_PREFIX, withQuery } from "./_shared";
import { apiRequest } from "../../../../apps/web/src/shared/api/client";

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

export function listAvailableCylindersWithWeight(warehouse_id?: string) {
  return apiRequest<CylinderWeight[]>(
    withQuery(`${API_PREFIX}/cylinders/available-with-weight`, { warehouse_id })
  );
}

export function getCylinderWeight(cylinderId: string) {
  return apiRequest<CylinderWeight>(`${API_PREFIX}/cylinders/${cylinderId}/weight`);
}

export function getProductContent(productId: string) {
  return apiRequest<ProductContent>(`${API_PREFIX}/products/${productId}/content`);
}

