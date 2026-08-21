import { describe, expect, it } from "vitest";

import { buildRouteControlMapView } from "../../../../plugins/logistics/frontend/components/vehicle-sessions/route-control-view";

const stopBase = {
  id: "stop-1",
  route_id: "route-1",
  delivery_point_id: "dp-1",
  stop_order: 1,
  scheduled_time: null,
  status: "PLANNED",
  arrival_time: null,
  departure_time: null,
  gps_coordinates: null,
  customer_id: "cust-1",
  customer_name_snapshot: "Cliente A",
  notes: null,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
};

const deliveryPointBase = {
  id: "dp-1",
  tenant_id: "tenant-1",
  customer_id: "cust-1",
  customer_name: "Cliente A",
  contact_name: null,
  contact_email: null,
  address: "Av. Lima 123",
  phone: null,
  warehouse_id: null,
  address_id: null,
  is_primary: true,
  delivery_day: null,
  visit_day: null,
  time_window: null,
  instructions: null,
  service_time_min: null,
  demand_units: null,
  demand_weight_kg: null,
  agent_user_id: null,
  fiscal_operation_document: null,
  fiscal_operation_type: null,
  gps_link: null,
  gps_coordinates: { lat: -12.04, lng: -77.04 },
  is_active: true,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
};

describe("buildRouteControlMapView", () => {
  it("posiciona el vehículo desde el control-state cuando existe telemetría", () => {
    const view = buildRouteControlMapView({
      stops: [stopBase],
      deliveryPoints: [deliveryPointBase],
      controlState: {
        session_id: "s-1",
        route_id: "route-1",
        vehicle_id: "v-1",
        active_stop_id: null,
        active_stop_started_at: null,
        current_stop_id: null,
        current_stop_index: null,
        status: "OUTBOUND",
        last_lat: -12.1,
        last_lng: -77.1,
        last_speed: 30,
        last_heading: 90,
        last_recorded_at: "2026-01-01T10:00:00Z",
        completed_stops: 0,
        total_stops: 1,
        progress_percent: 0,
        off_route: false,
        next_stop_eta_minutes: null,
        geofence_state: null,
        updated_at: "2026-01-01T10:00:00Z",
      },
      history: [],
    });

    expect(view.vehiclePosition).toEqual({ lat: -12.1, lng: -77.1 });
    expect(view.traveledPath).toEqual([]);
    expect(view.stops).toHaveLength(1);
    expect(view.stops[0].label).toContain("Cliente A");
  });

  it("usa el último evento de historial si el control-state no tiene posición", () => {
    const view = buildRouteControlMapView({
      stops: [stopBase],
      deliveryPoints: [deliveryPointBase],
      controlState: {
        session_id: "s-1",
        route_id: "route-1",
        vehicle_id: "v-1",
        active_stop_id: null,
        active_stop_started_at: null,
        current_stop_id: null,
        current_stop_index: null,
        status: "OUTBOUND",
        last_lat: null,
        last_lng: null,
        last_speed: null,
        last_heading: null,
        last_recorded_at: null,
        completed_stops: 0,
        total_stops: 1,
        progress_percent: 0,
        off_route: false,
        next_stop_eta_minutes: null,
        geofence_state: null,
        updated_at: "2026-01-01T10:00:00Z",
      },
      history: [
        {
          id: "ev-1",
          session_id: "s-1",
          route_id: "route-1",
          vehicle_id: "v-1",
          driver_id: "d-1",
          lat: -12.5,
          lng: -77.5,
          speed: null,
          heading: null,
          accuracy_meters: null,
          source: "WEB",
          recorded_at: "2026-01-01T09:59:00Z",
          received_at: "2026-01-01T09:59:01Z",
        },
      ],
    });

    expect(view.vehiclePosition).toEqual({ lat: -12.5, lng: -77.5 });
    expect(view.traveledPath).toEqual([{ lat: -12.5, lng: -77.5 }]);
  });

  it("queda sin vehículo cuando no hay telemetría ni posición en control-state", () => {
    const view = buildRouteControlMapView({
      stops: [stopBase],
      deliveryPoints: [deliveryPointBase],
      controlState: null,
      history: [],
    });

    expect(view.vehiclePosition).toBeNull();
    expect(view.traveledPath).toEqual([]);
    expect(view.stops).toHaveLength(1);
  });
});