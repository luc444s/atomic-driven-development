import { API_PREFIX } from "./_shared";
import { apiRequest } from "../../../../apps/web/src/shared/api/client";

export type BlockingReason = "FAILED_STOP" | "WAYBILL_MISSING" | "NO_ROUTE_ASSIGNED";
export type AttentionReason = "PARTIAL_STOP" | "OPEN_INCIDENT" | "WAYBILL_OUTDATED";
export type DataCompleteness = "FULL" | "PARTIAL";
export type HealthStatus = "HEALTHY" | "ATTENTION" | "BLOCKED";

export type SessionOperationalSummary = {
  session_id: string;
  session_status: string;
  data_completeness: DataCompleteness;
  health_status: HealthStatus;
  stop_counters: {
    total: number;
    pending: number;
    in_progress: number;
    partial: number;
    completed: number;
    failed: number;
  };
  incidents: {
    open_total: number;
    corrected_total: number;
    resolved_total: number;
  };
  route_activity: {
    confirmed_operations: number;
    last_activity: {
      type: "OPERATION" | "INCIDENT" | "DOCUMENT";
      label: string;
      at: string;
    } | null;
  };
  composition: {
    total_products: number;
    total_units: number;
    total_weight_kg: number | null;
  };
  waybill: {
    has_active_version: boolean;
    sync_status: "SYNCED" | "OUTDATED" | "MISSING";
    active_version: number | null;
  };
  blocking_reasons: BlockingReason[];
  attention_reasons: AttentionReason[];
  problematic_stops: Array<{
    route_stop_id: string;
    stop_order: number;
    label: string;
    progress_status: string;
    open_incidents: number;
    last_operation_at: string | null;
    completion_percent: number | null;
    outcome_type: string | null;
    driver_note: string | null;
  }>;
  open_incidents: Array<{
    id: string;
    type: string;
    status: string;
    route_stop_id: string | null;
    stop_label: string | null;
    notes: string | null;
    created_at: string;
    updated_at: string;
  }>;
};

export function getSessionOperationalSummary(sessionId: string) {
  return apiRequest<SessionOperationalSummary>(`${API_PREFIX}/vehicle-sessions/${sessionId}/operational-summary`);
}
