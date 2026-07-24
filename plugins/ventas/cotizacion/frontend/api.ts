import { apiRequest } from "../../../../apps/web/src/shared/api/client";

export interface QuoteDraftDTO {
  id: string;
  status: string;
  customer: { id: string; name: string };
  items: Array<{
    id: string;
    product_id: string;
    product_name: string | null;
    quantity: number;
    unit_weight_kg: number | null;
  }>;
  delivery_date: string;
  delivery_time: string | null;
  vehicle: { id: string; plate: string } | null;
  conditions: string | null;
  created_at: string;
}

export interface QuoteDraftListItem {
  id: string;
  status: string;
  customer_name: string | null;
  delivery_date: string;
  created_at: string;
}

export function executeCotizacion(command: string): Promise<QuoteDraftDTO> {
  return apiRequest<QuoteDraftDTO>("/api/v1/plugins/ventas/cotizaciones", {
    method: "POST",
    body: JSON.stringify({ command }),
  });
}

export function listCotizaciones(): Promise<QuoteDraftListItem[]> {
  return apiRequest<QuoteDraftListItem[]>("/api/v1/plugins/ventas/cotizaciones");
}

export function getCotizacion(id: string): Promise<QuoteDraftDTO> {
  return apiRequest<QuoteDraftDTO>(`/api/v1/plugins/ventas/cotizaciones/${id}`);
}

export const cotizacionKeys = {
  all: () => ["ventas", "cotizaciones"] as const,
  list: () => [...cotizacionKeys.all(), "list"] as const,
  detail: (id: string) => [...cotizacionKeys.all(), "detail", id] as const,
};
