import { describe, expect, it } from "vitest";

import { buildRouteContextView } from "../../../../../plugins/logistics/frontend/components/vehicle-sessions/route-context-view";
import type { RouteContext } from "../../../../../plugins/logistics/frontend/api/route-context";

function buildContext(overrides: Partial<RouteContext> = {}): RouteContext {
  return {
    session: {
      id: "session-1",
      vehicle_id: "vehicle-1",
      vehicle_plate: "TRK-1",
      driver_id: "driver-1",
      driver_name: "Driver",
      origin_warehouse_id: "wh-1",
      origin_warehouse_name: "Base",
      mobile_warehouse_id: "wh-mobile",
      mobile_warehouse_code: "MOB",
      mobile_warehouse_name: "Camion",
      route_id: "route-1",
      route_date: null,
      route_origin_label: null,
      route_destination_label: null,
      status: "OUTBOUND",
      opened_at: "2026-08-14T08:00:00Z",
      ready_at: null,
      departed_at: null,
      returned_at: null,
      closed_at: null,
      planned_weight_kg: null,
      loaded_weight_kg: null,
      occupancy_percent: null,
      last_activity: null,
      can_depart: false,
      can_close: false,
      next_transition_allowed: false,
      next_transition_blocker: null,
      current_stock: {
        warehouse_id: "wh-mobile",
        warehouse_code: "MOB",
        warehouse_name: "Camion",
        total_products: 0,
        total_units: 0,
        total_adr_points: 0,
      },
      history: [],
    },
    route_detail: null,
    assigned_route: null,
    stops: [],
    operations: [],
    composition: null,
    waybill: null,
    waybill_history: [],
    incidents: [],
    stop_progress: [],
    stop_results: [],
    customers: [],
    warehouses: [],
    ...overrides,
  };
}

describe("buildRouteContextView", () => {
  it("maps empty context into empty defaults", () => {
    const view = buildRouteContextView(null);

    expect(view.stops).toEqual([]);
    expect(view.routeOperations).toEqual([]);
    expect(view.routeIncidents).toEqual([]);
    expect(view.routeStopResults).toEqual([]);
    expect(view.routeStopProgress).toEqual([]);
    expect(view.waybillHistory).toEqual([]);
    expect(view.composition).toBeNull();
    expect(view.waybill).toBeNull();
    expect(view.stopOptions).toEqual([]);
    expect(view.customerOptions).toEqual([]);
    expect(view.warehouseOptions).toEqual([]);
    expect(view.routeOperationOptions).toEqual([]);
  });

  it("maps stops into stop options with order and status label", () => {
    const view = buildRouteContextView(
      buildContext({
        stops: [
          {
            id: "stop-1",
            route_id: "route-1",
            delivery_point_id: null,
            stop_order: 1,
            scheduled_time: null,
            status: "PENDIENTE",
            arrival_time: null,
            departure_time: null,
            gps_coordinates: null,
            customer_id: null,
            customer_name_snapshot: null,
            notes: null,
            created_at: "",
            updated_at: "",
          },
        ],
      })
    );

    expect(view.stopOptions).toEqual([
      { value: "stop-1", label: "Parada 1 · Pendiente" },
    ]);
  });

  it("filters out mobile warehouses from warehouse options", () => {
    const view = buildRouteContextView(
      buildContext({
        warehouses: [
          {
            id: "wh-real",
            tenant_id: "t",
            name: "Base Norte",
            code: "BASE",
            warehouse_type: "FISICO",
            address: null,
            phone: null,
            is_primary: true,
            latitude: null,
            longitude: null,
            formatted_address: null,
            place_id: null,
            is_active: true,
            created_at: "",
            updated_at: "",
          },
          {
            id: "wh-mobile",
            tenant_id: "t",
            name: "Camion",
            code: "MOB",
            warehouse_type: "MOBILE",
            address: null,
            phone: null,
            is_primary: false,
            latitude: null,
            longitude: null,
            formatted_address: null,
            place_id: null,
            is_active: true,
            created_at: "",
            updated_at: "",
          },
        ],
      })
    );

    expect(view.warehouseOptions).toEqual([
      { value: "wh-real", label: "BASE · Base Norte" },
    ]);
  });

  it("maps customers into options preferring commercial name", () => {
    const view = buildRouteContextView(
      buildContext({
        customers: [
          {
            id: "cust-1",
            legal_name: "Legal SA",
            commercial_name: "Comercial",
            external_code: null,
            document_type_code: "RUC",
            document_number: "20100070970",
            country_code: "PE",
            email: null,
            phone: null,
            mobile: null,
            payment_term_code: null,
            billing_type: null,
            is_exempt: false,
            accounting_code: null,
            is_intracommunity: false,
            fiscal_operation_key: null,
            tax_regime_code: null,
            equivalence_surcharge_applicable: false,
            cash_criterion_applicable: false,
            is_active: true,
            fiscal_address_id: null,
            created_at: "",
            updated_at: "",
          },
        ],
      })
    );

    expect(view.customerOptions).toEqual([
      { value: "cust-1", label: "Comercial · 20100070970" },
    ]);
  });

  it("preserves composition and waybill from context", () => {
    const composition = {
      session_id: "session-1",
      composition_version: 1,
      product_lines: [],
      totals: { total_packages: 0, total_weight_kg: 0, total_adr_points: 0 },
    };
    const waybill = {
      active: null,
      issued: null,
      sync_status: null,
      can_regenerate: false,
      can_emit: false,
      can_reissue: false,
      emit_block_reason: null,
    };

    const view = buildRouteContextView(
      buildContext({ composition, waybill: waybill as never })
    );

    expect(view.composition).toEqual(composition);
    expect(view.waybill).toEqual(waybill);
  });
});
