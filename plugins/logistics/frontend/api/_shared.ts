// Auto-generado por split_api.py
import { apiRequest } from "../../../../apps/web/src/shared/api/client";


export type BaseCylinderPayload = {
  serial: string;
  warehouse_id?: string | null;
  description?: string | null;
  barcode1?: string | null;
  barcode2?: string | null;
  gas_group_id?: string | null;
  product_id?: string | null;
  content_kg?: number | null;
  volume_m3?: number | null;
  condition?: string | null;
  brand_id?: string | null;
  cost?: number | null;
  price?: number | null;
  country_code?: string | null;
  box_number?: string | null;
  is_service?: boolean;
  is_medical?: boolean;
  medical_notes?: string | null;
  manufacturer_date?: string | null;
  manufacturer_code?: string | null;
  manufacture_year?: number | null;
  weight_origin?: number | null;
  weight_current?: number | null;
  last_hydrotest_date?: string | null;
  location?: string | null;
  next_hydrotest_date?: string | null;
};



export const API_PREFIX = "/api/v1/plugins/logistics";



export function withQuery(path: string, params: Record<string, string | number | boolean | undefined>) {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === "") {
      continue;
    }
    search.set(key, String(value));
  }
  const query = search.toString();
  return query ? `${path}?${query}` : path;
}



// ── Planning ─────────────────────────────────────────────


export type StockBalancePageRead = {
  items: Array<{
    product_id: string;
    product_name: string;
    warehouse_id: string;
    quantity: number;
  }>;
  total: number;
  limit: number;
  offset: number;
};



// ── Reception ────────────────────────────────────────────


// ── Waybill / Carta Porte ────────────────────────────────


// ── Dispatch ─────────────────────────────────────────────


// ── Reports ──────────────────────────────────────────────


// ── Equipment ────────────────────────────────────────────


// ── Route Restrictions ───────────────────────────────────


// ── Driver Parameters ────────────────────────────────────


// ── Vehicle Delivery Points ──────────────────────────────


// ── Agenda Daily Summary ─────────────────────────────────


// ── Route Weekdays ───────────────────────────────────────


// ── Weight Summary ───────────────────────────────────────


// ── ADR ──────────────────────────────────────────────────


// ── GPS ──────────────────────────────────────────────────


// ── Cylinder Weight / Content ────────────────────────────
