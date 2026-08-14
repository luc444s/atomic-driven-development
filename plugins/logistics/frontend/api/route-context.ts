import { API_PREFIX } from "./_shared";
import { apiRequest } from "../../../../apps/web/src/shared/api/client";
import type { LogisticsAssignedRoute, LogisticsRoute, LogisticsRouteStop } from "./routes";
import type { VehicleSessionDetail, SessionWaybillState, SessionWaybillVersion } from "./sessions";
import type {
  CurrentComposition,
  RouteIncident,
  RouteOperation,
  RouteStopProgress,
} from "./route-operations";
import type { RouteStopResult } from "./route-stop-results";
import type { LogisticsWarehouse } from "./warehouses";
import type { CustomerListItem } from "../../../crm/frontend/types";

export type RouteContext = {
  session: VehicleSessionDetail;
  route_detail: LogisticsRoute | null;
  assigned_route: LogisticsAssignedRoute | null;
  stops: LogisticsRouteStop[];
  operations: RouteOperation[];
  composition: CurrentComposition | null;
  waybill: SessionWaybillState | null;
  waybill_history: SessionWaybillVersion[];
  incidents: RouteIncident[];
  stop_progress: RouteStopProgress[];
  stop_results: RouteStopResult[];
  customers: CustomerListItem[];
  warehouses: LogisticsWarehouse[];
};

export function getSessionRouteContext(sessionId: string) {
  return apiRequest<RouteContext>(`${API_PREFIX}/vehicle-sessions/${sessionId}/route-context`);
}
