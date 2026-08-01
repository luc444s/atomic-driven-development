// Auto-generado por split_api.py
import { API_PREFIX, withQuery } from "./_shared";
import { LogisticsAgendaTask } from "./agenda";
import { RouteAgendaReport } from "./reports";
import { apiRequest } from "../../../../apps/web/src/shared/api/client";

export type LogisticsRoute = {
  id: string;
  tenant_id: string;
  branch_id: string | null;
  route_date: string;
  driver_id: string;
  vehicle_id: string | null;
  status: string;
  notes: string | null;
  created_by: string;
  created_at: string;
  updated_at: string;
};

export type LogisticsRouteStop = {
  id: string;
  route_id: string;
  delivery_point_id: string | null;
  stop_order: number;
  scheduled_time: string | null;
  status: string;
  arrival_time: string | null;
  departure_time: string | null;
  gps_coordinates: Record<string, unknown> | null;
  customer_id: string | null;
  customer_name_snapshot: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
};

export function listRoutes(filters: { date?: string; driver?: string; status?: string }) {
  return apiRequest<LogisticsRoute[]>(
    withQuery(`${API_PREFIX}/routes`, { date: filters.date, driver: filters.driver, status: filters.status })
  );
}

export function getRoute(routeId: string) {
  return apiRequest<LogisticsRoute>(`${API_PREFIX}/routes/${routeId}`);
}

export function listRouteStops(routeId: string) {
  return apiRequest<LogisticsRouteStop[]>(`${API_PREFIX}/routes/${routeId}/stops`);
}

export function createRoute(payload: Record<string, unknown>) {
  return apiRequest<LogisticsRoute>(`${API_PREFIX}/routes`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateRoute(routeId: string, payload: Record<string, unknown>) {
  return apiRequest<LogisticsRoute>(`${API_PREFIX}/routes/${routeId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function startRoute(routeId: string) {
  return apiRequest<LogisticsRoute>(`${API_PREFIX}/routes/${routeId}/start`, { method: "POST" });
}

export function completeRoute(routeId: string) {
  return apiRequest<LogisticsRoute>(`${API_PREFIX}/routes/${routeId}/complete`, { method: "POST" });
}

export function cancelRoute(routeId: string) {
  return apiRequest<LogisticsRoute>(`${API_PREFIX}/routes/${routeId}/cancel`, { method: "POST" });
}

export function createRouteStop(routeId: string, payload: Record<string, unknown>) {
  return apiRequest<LogisticsRouteStop>(`${API_PREFIX}/routes/${routeId}/stops`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateRouteStop(routeId: string, stopId: string, payload: Record<string, unknown>) {
  return apiRequest<LogisticsRouteStop>(`${API_PREFIX}/routes/${routeId}/stops/${stopId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function deleteRouteStop(routeId: string, stopId: string) {
  return apiRequest<void>(`${API_PREFIX}/routes/${routeId}/stops/${stopId}`, { method: "DELETE" });
}

export function deliverRouteStop(routeId: string, stopId: string) {
  return apiRequest<LogisticsRouteStop>(`${API_PREFIX}/routes/${routeId}/stops/${stopId}/deliver`, {
    method: "POST",
  });
}

export function createRouteAgendaTasks(routeId: string) {
  return apiRequest<LogisticsAgendaTask[]>(`${API_PREFIX}/routes/${routeId}/agenda-tasks`, {
    method: "POST",
  });
}

export function getRouteAgendaReport(routeId: string) {
  return apiRequest<RouteAgendaReport>(`${API_PREFIX}/reports/route-agenda/${routeId}`);
}

export type RouteWeekday = {
  id: string;
  tenant_id: string;
  route_id: string;
  weekday: number;
  created_at: string;
};

export function replaceRouteWeekdays(routeId: string, payload: { weekdays: number[] }) {
  return apiRequest<RouteWeekday[]>(`${API_PREFIX}/routes/${routeId}/weekly-schedule`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function updateRouteGpsStart(routeId: string, payload: { gps_coordinates: Record<string, unknown> }) {
  return apiRequest<void>(`${API_PREFIX}/routes/${routeId}/gps-start`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function updateRouteStopGps(routeId: string, stopId: string, payload: { gps_coordinates: Record<string, unknown> }) {
  return apiRequest<void>(`${API_PREFIX}/routes/${routeId}/stops/${stopId}/gps`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

