import { describe, expect, it } from "vitest";

import { buildRouteControlMapView } from "../../../../../plugins/logistics/frontend/components/vehicle-sessions/route-control-view";

describe("buildRouteControlMapView", () => {
  it("derives a stable center/zoom from the route bbox and resolves stops from delivery point coordinates", () => {
    const view = buildRouteControlMapView({
      stops: [
        { id: "stop-1", route_id: "route-1", delivery_point_id: "dp-1", stop_order: 1, scheduled_time: null, status: "PENDIENTE", arrival_time: null, departure_time: null, gps_coordinates: null, customer_id: null, customer_name_snapshot: null, notes: null, created_at: "", updated_at: "" },
        { id: "stop-2", route_id: "route-1", delivery_point_id: "dp-2", stop_order: 2, scheduled_time: null, status: "PENDIENTE", arrival_time: null, departure_time: null, gps_coordinates: null, customer_id: null, customer_name_snapshot: null, notes: null, created_at: "", updated_at: "" },
      ],
      deliveryPoints: [
        { id: "dp-1", tenant_id: "t", customer_id: "c1", customer_name: "Cliente 1", contact_name: null, contact_email: null, address: "A", phone: null, warehouse_id: null, address_id: null, is_primary: true, delivery_day: null, visit_day: null, time_window: null, instructions: null, service_time_min: null, demand_units: null, demand_weight_kg: null, agent_user_id: null, fiscal_operation_document: null, fiscal_operation_type: null, gps_link: null, gps_coordinates: { lat: -12.1, lng: -77.1 }, is_active: true, created_at: "", updated_at: "" },
        { id: "dp-2", tenant_id: "t", customer_id: "c2", customer_name: "Cliente 2", contact_name: null, contact_email: null, address: "B", phone: null, warehouse_id: null, address_id: null, is_primary: true, delivery_day: null, visit_day: null, time_window: null, instructions: null, service_time_min: null, demand_units: null, demand_weight_kg: null, agent_user_id: null, fiscal_operation_document: null, fiscal_operation_type: null, gps_link: null, gps_coordinates: { lat: -12.2, lng: -77.2 }, is_active: true, created_at: "", updated_at: "" },
      ],
      controlState: {
        session_id: "session-1",
        route_id: "route-1",
        vehicle_id: "vehicle-1",
        active_stop_id: "stop-1",
        active_stop_started_at: null,
        current_stop_id: "stop-1",
        current_stop_index: 0,
        status: "EN_PARADA",
        last_lat: -12.15,
        last_lng: -77.15,
        last_speed: 0,
        last_heading: null,
        last_recorded_at: null,
        completed_stops: 0,
        total_stops: 2,
        progress_percent: 0,
        off_route: false,
        next_stop_eta_minutes: null,
        geofence_state: "INSIDE",
        updated_at: "",
      },
      history: [],
    });

    // LOGI-0032: el centro/zoom sale del bounding box de la ruta (estable);
    // la posición del vehículo se dibuja como marker pero NO mueve la vista.
    expect(view.center.lat).toBeCloseTo(-12.15, 6);
    expect(view.center.lng).toBeCloseTo(-77.15, 6);
    expect(view.zoom).toBe(11);
    expect(view.vehiclePosition).toEqual({ lat: -12.15, lng: -77.15 });
    expect(view.plannedPath).toEqual([
      { lat: -12.1, lng: -77.1 },
      { lat: -12.2, lng: -77.2 },
    ]);
    expect(view.stops[0]?.isActive).toBe(true);
  });

  it("falls back to stop gps_coordinates when the stop has no delivery point", () => {
    const view = buildRouteControlMapView({
      stops: [
        { id: "stop-1", route_id: "route-1", delivery_point_id: null, stop_order: 1, scheduled_time: null, status: "PENDIENTE", arrival_time: null, departure_time: null, gps_coordinates: { lat: -8.06, lng: -79.06 }, customer_id: null, customer_name_snapshot: "Cliente sin DP", notes: null, created_at: "", updated_at: "" },
      ],
      deliveryPoints: [],
      controlState: null,
      history: [],
    });

    expect(view.stops).toHaveLength(1);
    expect(view.stops[0]?.position).toEqual({ lat: -8.06, lng: -79.06 });
    expect(view.stops[0]?.label).toContain("Cliente sin DP");
  });
});
