// Auto-generado por split_api.py
import { API_PREFIX, withQuery } from "./_shared";
import { apiRequest } from "../../../../apps/web/src/shared/api/client";

export type LogisticsVehicle = {
  id: string;
  tenant_id: string;
  plate: string;
  vehicle_type: string | null;
  brand: string | null;
  model: string | null;
  capacity_weight: number | null;
  capacity_volume: number | null;
  useful_load: number | null;
  adr_class: string | null;
  status: string;
  warehouse_id: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export function listVehicles() {
  return apiRequest<LogisticsVehicle[]>(`${API_PREFIX}/vehicles`);
}

export function createVehicle(payload: Record<string, unknown>) {
  return apiRequest<LogisticsVehicle>(`${API_PREFIX}/vehicles`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateVehicle(vehicleId: string, payload: Record<string, unknown>) {
  return apiRequest<LogisticsVehicle>(`${API_PREFIX}/vehicles/${vehicleId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export type VehicleRouteRestriction = {
  id: string;
  tenant_id: string;
  vehicle_id: string;
  route_id: string;
  restriction_type: string;
  created_at: string;
};

export type VehicleEligibility = {
  vehicle_id: string;
  plate: string;
  adr_class: string | null;
  capacity_weight: number | null;
  eligible: boolean;
  reason: string | null;
};

export function listVehicleRouteRestrictions(vehicleId: string) {
  return apiRequest<VehicleRouteRestriction[]>(`${API_PREFIX}/vehicles/${vehicleId}/route-restrictions`);
}

export function replaceVehicleRouteRestrictions(vehicleId: string, payload: { restrictions: { route_id: string; restriction_type: string }[] }) {
  return apiRequest<VehicleRouteRestriction[]>(`${API_PREFIX}/vehicles/${vehicleId}/route-restrictions`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function listEligibleVehiclesForRoute(routeId: string) {
  return apiRequest<VehicleEligibility[]>(`${API_PREFIX}/routes/${routeId}/eligible-vehicles`);
}

export type DriverParameter = {
  id: string;
  tenant_id: string;
  driver_id: string;
  param_key: string;
  param_value: string | null;
  updated_at: string;
};

export function listDriverParameters(driverId: string) {
  return apiRequest<DriverParameter[]>(`${API_PREFIX}/drivers/${driverId}/parameters`);
}

export function upsertDriverParameters(driverId: string, payload: { parameters: Record<string, string | null> }) {
  return apiRequest<DriverParameter[]>(`${API_PREFIX}/drivers/${driverId}/parameters`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export type VehicleDeliveryPoint = {
  id: string;
  tenant_id: string;
  vehicle_id: string;
  delivery_point_id: string;
  created_at: string;
};

export function listVehicleDeliveryPoints(vehicleId: string) {
  return apiRequest<VehicleDeliveryPoint[]>(`${API_PREFIX}/vehicles/${vehicleId}/delivery-points`);
}

export function linkVehicleDeliveryPoint(vehicleId: string, payload: { delivery_point_id: string }) {
  return apiRequest<VehicleDeliveryPoint>(`${API_PREFIX}/vehicles/${vehicleId}/delivery-points`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function unlinkVehicleDeliveryPoint(vehicleId: string, dpId: string) {
  return apiRequest<void>(`${API_PREFIX}/vehicles/${vehicleId}/delivery-points/${dpId}`, {
    method: "DELETE",
  });
}

export function listEligibleVehiclesForMovement(movementId: string) {
  return apiRequest<VehicleEligibility[]>(`${API_PREFIX}/adr/eligible-vehicles/${movementId}`);
}

