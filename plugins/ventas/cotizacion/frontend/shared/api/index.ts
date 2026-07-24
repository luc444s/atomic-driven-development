import { apiRequest } from "../../../../../../apps/web/src/shared/api/client";
import type { QuoteDraftDTO, QuoteDraftListItem } from "../types";

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
