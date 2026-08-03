// Auto-generado por split_api.py
import { API_PREFIX, withQuery } from "./_shared";
import { apiRequest } from "../../../../apps/web/src/shared/api/client";

export type LogisticsDeliveryPoint = {
  id: string;
  tenant_id: string;
  customer_id: string;
  customer_name: string | null;
  contact_name: string | null;
  contact_email: string | null;
  address: string;
  phone: string | null;
  warehouse_id: string | null;
  address_id: string | null;
  is_primary: boolean;
  delivery_day: string | null;
  visit_day: string | null;
  time_window: string | null;
  instructions: string | null;
  service_time_min: number | null;
  demand_units: number | null;
  demand_weight_kg: number | null;
  agent_user_id: string | null;
  fiscal_operation_document: string | null;
  fiscal_operation_type: string | null;
  gps_link: string | null;
  gps_coordinates: { lat: number; lng: number } | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export function listDeliveryPoints() {
  return apiRequest<LogisticsDeliveryPoint[]>(`${API_PREFIX}/delivery-points`);
}

export function createDeliveryPoint(payload: Record<string, unknown>) {
  return apiRequest<LogisticsDeliveryPoint>(`${API_PREFIX}/delivery-points`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateDeliveryPoint(deliveryPointId: string, payload: Record<string, unknown>) {
  return apiRequest<LogisticsDeliveryPoint>(`${API_PREFIX}/delivery-points/${deliveryPointId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function listDeliveryPointsByCustomers(customerIds: string) {
  return apiRequest<LogisticsDeliveryPoint[]>(
    `${API_PREFIX}/delivery-points/by-customers?customer_ids=${encodeURIComponent(customerIds)}`
  );
}

export function listCustomerAddressesByCustomers(customerIds: string) {
  return apiRequest<
    Array<{
      id: string;
      customer_id: string;
      line1: string;
      latitude: number | null;
      longitude: number | null;
    }>
  >(`/api/v1/plugins/crm/customer-addresses/gps?customer_ids=${encodeURIComponent(customerIds)}`);
}
