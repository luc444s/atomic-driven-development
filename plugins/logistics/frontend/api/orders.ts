// Auto-generado por split_api.py
import { API_PREFIX, withQuery } from "./_shared";
import { apiRequest } from "@systutor/shell/api/client";

export type LogisticsOrder = {
  id: string;
  tenant_id: string;
  branch_id: string | null;
  order_date: string;
  customer_id: string;
  customer_name: string;
  movement_type: string;
  document_series: string | null;
  document_number: number | null;
  warehouse_id: string | null;
  carrier: string | null;
  commitment_date: string | null;
  time_window_start: string | null;
  time_window_end: string | null;
  status: string;
  notes: string | null;
  created_by: string;
  created_at: string;
  updated_at: string;
};

export type LogisticsOrderItem = {
  id: string;
  order_id: string;
  product_id: string | null;
  product_name: string;
  reason: string | null;
  condition: string | null;
  quantity_requested: number;
  quantity_planned: number;
  status: number;
  location: string | null;
  description: string | null;
  created_at: string;
};

export type LogisticsOrderItemCreatePayload = {
  product_id: string;
  product_name: string;
  reason?: string | null;
  condition?: string | null;
  quantity_requested?: number;
  quantity_planned?: number;
  status?: number;
  location?: string | null;
  description?: string | null;
};

export function listOrders(filters: { customer?: string; status?: string }) {
  return apiRequest<LogisticsOrder[]>(
    withQuery(`${API_PREFIX}/orders`, { customer: filters.customer, status: filters.status })
  );
}

export function getOrder(orderId: string) {
  return apiRequest<LogisticsOrder>(`${API_PREFIX}/orders/${orderId}`);
}

export function listOrderItems(orderId: string) {
  return apiRequest<LogisticsOrderItem[]>(`${API_PREFIX}/orders/${orderId}/items`);
}

export function createOrder(payload: Record<string, unknown>) {
  return apiRequest<LogisticsOrder>(`${API_PREFIX}/orders`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateOrder(orderId: string, payload: Record<string, unknown>) {
  return apiRequest<LogisticsOrder>(`${API_PREFIX}/orders/${orderId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function createOrderItem(orderId: string, payload: LogisticsOrderItemCreatePayload) {
  return apiRequest<LogisticsOrderItem>(`${API_PREFIX}/orders/${orderId}/items`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateOrderItem(orderId: string, itemId: string, payload: Record<string, unknown>) {
  return apiRequest<LogisticsOrderItem>(`${API_PREFIX}/orders/${orderId}/items/${itemId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function deleteOrderItem(orderId: string, itemId: string) {
  return apiRequest<void>(`${API_PREFIX}/orders/${orderId}/items/${itemId}`, {
    method: "DELETE",
  });
}

