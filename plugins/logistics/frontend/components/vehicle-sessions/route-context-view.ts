import type { RouteContext } from "../../api";
import { getRealWarehouses } from "../../api";
import {
  buildCustomerOptions,
  buildRouteOperationOptions,
  buildStopOptions,
  type RouteSelectOption,
} from "./session-route-tab-view";

export type RouteContextView = {
  stops: RouteContext["stops"];
  routeOperations: RouteContext["operations"];
  routeIncidents: RouteContext["incidents"];
  routeStopResults: RouteContext["stop_results"];
  routeStopProgress: RouteContext["stop_progress"];
  waybillHistory: RouteContext["waybill_history"];
  composition: RouteContext["composition"];
  waybill: RouteContext["waybill"];
  stopOptions: RouteSelectOption[];
  customerOptions: RouteSelectOption[];
  warehouseOptions: RouteSelectOption[];
  routeOperationOptions: RouteSelectOption[];
};

export function buildRouteContextView(context: RouteContext | null | undefined): RouteContextView {
  const stops = context?.stops ?? [];
  const routeOperations = context?.operations ?? [];
  const routeIncidents = context?.incidents ?? [];
  const routeStopResults = context?.stop_results ?? [];
  const routeStopProgress = context?.stop_progress ?? [];
  const waybillHistory = context?.waybill_history ?? [];

  return {
    stops,
    routeOperations,
    routeIncidents,
    routeStopResults,
    routeStopProgress,
    waybillHistory,
    composition: context?.composition ?? null,
    waybill: context?.waybill ?? null,
    stopOptions: buildStopOptions(stops),
    customerOptions: buildCustomerOptions(context?.customers ?? []),
    warehouseOptions: getRealWarehouses(context?.warehouses ?? []).map((warehouse) => ({
      value: warehouse.id,
      label: `${warehouse.code} · ${warehouse.name}`,
    })),
    routeOperationOptions: buildRouteOperationOptions(routeOperations),
  };
}
