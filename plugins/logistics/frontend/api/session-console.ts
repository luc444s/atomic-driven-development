import { API_PREFIX } from "./_shared";
import { apiRequest } from "@systutor/shell/api/client";
import type { VehicleSessionDetail } from "./sessions";
import type { LoadPlan } from "./load-plans";
import type { SessionReconciliation } from "./reconciliation";
import type { SessionOperationalSummary } from "./operational-summary";
import type { SerializedCylinderSummary } from "./cylinder-weight";
import type { StockBalancePage } from "../../../stock/frontend/types";

export type SessionConsoleContext = {
  session: VehicleSessionDetail;
  load_plan: LoadPlan;
  reconciliation: SessionReconciliation;
  operational_summary: SessionOperationalSummary | null;
  origin_balances: StockBalancePage;
  mobile_balances: StockBalancePage;
  origin_serialized: SerializedCylinderSummary[];
};

export function getSessionConsoleContext(sessionId: string) {
  return apiRequest<SessionConsoleContext>(
    `${API_PREFIX}/vehicle-sessions/${sessionId}/console-context`
  );
}
