import { API_PREFIX } from "./_shared";
import { apiRequest } from "../../../../apps/web/src/shared/api/client";

export type RouteStopResult = {
  id: string;
  session_id: string;
  route_stop_id: string;
  status: string;
  completion_percent: number;
  outcome_type: string;
  driver_note: string | null;
  created_at: string;
  updated_at: string;
};

export type RouteStopResultUpsertPayload = {
  status: string;
  completion_percent: number;
  outcome_type: string;
  driver_note?: string | null;
};

export function listRouteStopResults(sessionId: string) {
  return apiRequest<RouteStopResult[]>(`${API_PREFIX}/vehicle-sessions/${sessionId}/route-stop-results`);
}

export function upsertRouteStopResult(
  sessionId: string,
  routeStopId: string,
  payload: RouteStopResultUpsertPayload
) {
  return apiRequest<RouteStopResult>(
    `${API_PREFIX}/vehicle-sessions/${sessionId}/route-stop-results/${routeStopId}`,
    {
      method: "PUT",
      body: JSON.stringify(payload),
    }
  );
}
