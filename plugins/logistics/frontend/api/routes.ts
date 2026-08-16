// Auto-generado por split_api.py
import { API_PREFIX, withQuery } from "./_shared";
import { LogisticsAgendaTask } from "./agenda";
import { RouteAgendaReport } from "./reports";
import { apiRequest } from "@systutor/shell/api/client";

export type LogisticsRoute = {
  id: string;
  tenant_id: string;
  branch_id: string | null;
  route_date: string;
  driver_id: string;
  vehicle_id: string | null;
  origin_label: string | null;
  destination_label: string | null;
  status: string;
  gps_start_coordinates: Record<string, unknown> | null;
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

export type LogisticsAssignedRoute = {
  calculation_id: string;
  route_id: string;
  session_id: string | null;
  planning_reservation_id: string | null;
  provider_stack: string;
  ordered_stop_ids: string[];
  totals: Record<string, unknown>;
  violations: string[];
  polyline: string | null;
  created_at: string;
};

export type RoutingStopInput = {
  stop_id: string;
  customer_id?: string | null;
  customer_name?: string | null;
  address_id?: string | null;
  address_label?: string | null;
  lat: number;
  lng: number;
  service_minutes?: number;
  time_window_start?: string | null;
  time_window_end?: string | null;
  demand_units?: number;
  demand_weight_kg?: number;
  demand_volume_m3?: number;
  adr_required?: boolean;
  priority?: number | null;
};

export type RoutingVehicleInput = {
  vehicle_id: string;
  start_warehouse_id?: string | null;
  end_warehouse_id?: string | null;
  start_lat: number;
  start_lng: number;
  end_lat?: number | null;
  end_lng?: number | null;
  capacity_units?: number | null;
  capacity_weight_kg?: number | null;
  capacity_volume_m3?: number | null;
  adr_capable?: boolean;
};

export type RoutingCalculationRequest = {
  route_id?: string | null;
  session_id?: string | null;
  planning_reservation_id?: string | null;
  vehicle: RoutingVehicleInput;
  stops: RoutingStopInput[];
  departure_at?: string | null;
  mode?: string;
  commit_order?: boolean;
};

export type RoutingCalculatedStop = {
  stop_id: string;
  sequence: number;
  eta_at: string | null;
  etd_at: string | null;
  distance_from_prev_m: number | null;
  travel_seconds_from_prev: number | null;
  service_minutes: number;
  violation_codes: string[];
};

export type RoutingCalculationResponse = {
  provider_stack: string;
  route_id: string | null;
  session_id: string | null;
  ordered_stops: RoutingCalculatedStop[];
  totals: {
    distance_m: number;
    travel_seconds: number;
    service_seconds: number;
    total_seconds: number;
  };
  polyline: string | null;
  violations: string[];
  committed: boolean;
};

export type RoutingCommitOrderRequest = {
  route_id: string;
  session_id?: string | null;
  planning_reservation_id?: string | null;
  preview: RoutingCalculationResponse;
};

export type RoutingCommitOrderResponse = {
  calculation_id: string;
  route_id: string;
  committed: boolean;
  stop_count: number;
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

export function getAssignedRoute(routeId: string) {
  return apiRequest<LogisticsAssignedRoute | null>(`${API_PREFIX}/routing/assigned-route/${routeId}`);
}

export function previewRouteCalculation(payload: RoutingCalculationRequest) {
  return apiRequest<RoutingCalculationResponse>(`${API_PREFIX}/routing/preview`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function optimizeRouteCalculation(payload: RoutingCalculationRequest) {
  return apiRequest<RoutingCalculationResponse>(`${API_PREFIX}/routing/optimize`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function commitRouteOrder(payload: RoutingCommitOrderRequest) {
  return apiRequest<RoutingCommitOrderResponse>(`${API_PREFIX}/routing/commit-order`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
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
