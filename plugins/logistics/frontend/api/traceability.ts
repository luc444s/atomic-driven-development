import { apiRequest } from "@systutor/shell/api/client";
import { API_PREFIX, withQuery } from "./_shared";

export type LogisticsTraceabilityEvent = {
  timestamp: string;
  event_type: string;
  description: string;
  actor: string | null;
  metadata: Record<string, unknown>;
};

export type LogisticsTraceabilityPagination = {
  page: number;
  per_page: number;
  total: number;
  total_pages: number;
};

export type LogisticsTraceabilitySummary = {
  total_events: number;
  first_event: string | null;
  last_event: string | null;
  current_state: string | null;
  current_location: string | null;
  gps_lat: number | null;
  gps_lng: number | null;
};

export type LogisticsCylinderTraceability = {
  cylinder_id: string;
  serial: string;
  events: LogisticsTraceabilityEvent[];
  pagination: LogisticsTraceabilityPagination;
  summary: LogisticsTraceabilitySummary;
};

export function getCylinderTraceability(cylinderId: string, page = 1, perPage = 20) {
  return apiRequest<LogisticsCylinderTraceability>(
    withQuery(`${API_PREFIX}/cylinders/${cylinderId}/traceability`, {
      page,
      per_page: perPage,
    })
  );
}
