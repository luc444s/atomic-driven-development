// Auto-generado por split_api.py
import { API_PREFIX, withQuery } from "./_shared";
import { apiRequest } from "@systutor/shell/api/client";

export type RouteAgendaReportStop = {
  stop_id: string;
  stop_order: number;
  customer_name: string | null;
  address: string | null;
  scheduled_time: string | null;
  status: string;
};

export type RouteAgendaReport = {
  route_id: string;
  route_date: string;
  driver_id: string;
  vehicle_id: string | null;
  stops: RouteAgendaReportStop[];
};

export type AdrPointsItem = {
  product_id: string | null;
  product_name: string | null;
  quantity: number;
  adr_points_per_unit: number;
  total_adr_points: number;
};

export type AdrPointsSummary = {
  movement_id: string;
  total_adr_points: number;
  items: AdrPointsItem[];
};

export function getAdrSummary(movementId: string) {
  return apiRequest<AdrPointsSummary>(`${API_PREFIX}/reports/adr-summary/${movementId}`);
}

