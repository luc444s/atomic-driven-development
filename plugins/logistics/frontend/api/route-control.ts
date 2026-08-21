import { API_PREFIX } from "./_shared";
import { apiRequest } from "@systutor/shell/api/client";
import type { RouteControlState, VehicleLocationEvent } from "./sessions";

export type VehicleLocationRecordPayload = {
  lat: number;
  lng: number;
  speed?: number | null;
  heading?: number | null;
  accuracy_meters?: number | null;
  recorded_at: string;
  source?: string;
};

export type LocationHistoryFilters = {
  from?: string;
  to?: string;
  limit?: number;
};

export function getRouteControlState(sessionId: string) {
  return apiRequest<RouteControlState>(
    `${API_PREFIX}/vehicle-sessions/${sessionId}/control-state`
  );
}

export function getVehicleLocationHistory(sessionId: string, filters: LocationHistoryFilters = {}) {
  const params = new URLSearchParams();
  if (filters.from) {
    params.set("from", filters.from);
  }
  if (filters.to) {
    params.set("to", filters.to);
  }
  if (filters.limit != null) {
    params.set("limit", String(filters.limit));
  }
  const qs = params.toString();
  return apiRequest<VehicleLocationEvent[]>(
    `${API_PREFIX}/vehicle-sessions/${sessionId}/location-history${qs ? `?${qs}` : ""}`
  );
}

export function reportVehicleLocation(sessionId: string, payload: VehicleLocationRecordPayload) {
  return apiRequest<VehicleLocationEvent>(`${API_PREFIX}/vehicle-sessions/${sessionId}/location`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function postRouteStopArrive(sessionId: string, stopId: string) {
  return apiRequest<RouteControlState>(`${API_PREFIX}/vehicle-sessions/${sessionId}/stops/${stopId}/arrive`, {
    method: "POST",
  });
}

export function postRouteStopDepart(sessionId: string, stopId: string) {
  return apiRequest<RouteControlState>(`${API_PREFIX}/vehicle-sessions/${sessionId}/stops/${stopId}/depart`, {
    method: "POST",
  });
}