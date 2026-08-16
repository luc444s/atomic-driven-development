// Auto-generado por split_api.py
import { API_PREFIX, withQuery } from "./_shared";
import { LogisticsOrderItem } from "./orders";
import { StockBalancePageRead } from "./_shared";
import { LogisticsMovement } from "./movements";
import { apiRequest } from "@systutor/shell/api/client";

export type PlanningStockSummaryItem = {
  product_id: string;
  product_name: string;
  warehouse_id: string;
  stock_actual: number;
  stock_comprometido: number;
  stock_planificado: number;
  stock_disponible: number;
  coverage_status: string;
};

export type PlanningStockOwnerBalanceItem = {
  product_id: string;
  product_name: string;
  warehouse_id: string;
  quantity: number;
};

export type PlanningPendingOrderItem = {
  order_item_id: string;
  product_id: string | null;
  product_name: string;
  quantity_requested: number;
  quantity_planned: number;
  quantity_pending: number;
  stock_disponible: number;
  coverage_status: string;
};

export type PlanningPendingOrder = {
  order_id: string;
  customer_id: string | null;
  customer_name: string;
  warehouse_id: string | null;
  status: string;
  coverage_status: string;
  items: PlanningPendingOrderItem[];
};

export type PlanningPlanOrderResult = {
  order_id: string;
  mode: string;
  updated_items: LogisticsOrderItem[];
};

export type PlanningPreloadItem = {
  id: string;
  tenant_id: string;
  preload_id: string;
  order_item_id: string;
  product_id: string;
  product_name: string | null;
  quantity_planned: number;
  quantity_loaded: number;
  created_at: string;
};

export type PlanningPreload = {
  id: string;
  tenant_id: string;
  warehouse_id: string;
  branch_id: string | null;
  preload_date: string;
  status: string;
  notes: string | null;
  created_by: string;
  created_at: string;
  updated_at: string;
  items: PlanningPreloadItem[];
};

export type PlanningPreloadActionResult = {
  preload: PlanningPreload;
  movement: LogisticsMovement | null;
};

export type PlanningExpectedLoadSummary = {
  items: {
    product_id: string;
    product_name: string;
    sku: string | null;
    quantity: number;
    adr_required: boolean;
    unit_weight_kg: number | null;
    total_weight_kg: number | null;
  }[];
  total_products: number;
  total_units: number;
  total_weight_kg: number | null;
};

export type PlanningReservation = {
  id: string;
  tenant_id: string;
  branch_id: string | null;
  vehicle_id: string;
  vehicle_plate: string;
  origin_warehouse_id: string;
  origin_warehouse_name: string;
  planned_start_at: string;
  planned_end_at: string;
  expected_load_summary: PlanningExpectedLoadSummary;
  expected_weight_total: number | null;
  expected_volume_total: number | null;
  service_type: string | null;
  route_id: string | null;
  driver_id: string | null;
  driver_name: string | null;
  customer_ids: string[];
  address_ids: string[];
  adr_required: boolean;
  notes: string | null;
  status: string;
  conflict_reason: string | null;
  permit_override: boolean;
  override_reason: string | null;
  linked_session_id: string | null;
  actual_start_at: string | null;
  actual_end_at: string | null;
  actual_load_summary: PlanningExpectedLoadSummary | null;
  created_at: string;
  updated_at: string;
};

export type PlanningReservationPayload = {
  vehicle_id: string;
  origin_warehouse_id: string;
  planned_start_at: string;
  planned_end_at: string;
  expected_load_summary: PlanningExpectedLoadSummary;
  expected_weight_total?: number | null;
  expected_volume_total?: number | null;
  service_type?: string | null;
  route_id?: string | null;
  driver_id?: string | null;
  customer_ids?: string[];
  address_ids?: string[];
  adr_required?: boolean;
  notes?: string | null;
  permit_override?: boolean;
  override_reason?: string | null;
};

export function getPlanningStock(warehouse_id?: string) {
  return apiRequest<PlanningStockSummaryItem[]>(
    withQuery(`${API_PREFIX}/planning/stock`, { warehouse_id })
  );
}

export function postPlanningStockSummary(payload: { warehouse_id: string; product_ids?: string[] }) {
  return apiRequest<PlanningStockSummaryItem[]>(`${API_PREFIX}/planning/stock/summary`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function listPlanningStockBalances(
  warehouse_id: string,
): Promise<PlanningStockOwnerBalanceItem[]> {
  const limit = 200;
  const items: PlanningStockOwnerBalanceItem[] = [];
  let offset = 0;
  let total = 0;

  do {
    const page = await apiRequest<StockBalancePageRead>(
      withQuery("/api/v1/plugins/stock/balance", {
        warehouse_id,
        limit,
        offset,
      }),
    );
    items.push(
      ...page.items.map((item) => ({
        product_id: item.product_id,
        product_name: item.product_name,
        warehouse_id: item.warehouse_id,
        quantity: item.quantity,
      })),
    );
    total = page.total;
    offset += page.limit;
  } while (items.length < total);

  return items;
}

export function listPlanningPendingOrders(warehouse_id?: string) {
  return apiRequest<PlanningPendingOrder[]>(
    withQuery(`${API_PREFIX}/planning/pending-orders`, { warehouse_id }),
  );
}

export function postPlanOrder(orderId: string, payload: { mode: string; permit_without_stock?: boolean }) {
  return apiRequest<PlanningPlanOrderResult>(`${API_PREFIX}/planning/plan-order/${orderId}`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function generatePreload(payload: { warehouse_id: string; preload_date: string; order_ids?: string[]; notes?: string }) {
  return apiRequest<PlanningPreload>(`${API_PREFIX}/planning/generate-preload`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function listPreloads(warehouse_id?: string) {
  return apiRequest<PlanningPreload[]>(withQuery(`${API_PREFIX}/planning/preloads`, { warehouse_id }));
}

export function getPreload(preloadId: string) {
  return apiRequest<PlanningPreload>(`${API_PREFIX}/planning/preloads/${preloadId}`);
}

export function acceptPreload(preloadId: string) {
  return apiRequest<PlanningPreloadActionResult>(`${API_PREFIX}/planning/preloads/${preloadId}/accept`, {
    method: "POST",
  });
}

export function cancelPreload(preloadId: string) {
  return apiRequest<PlanningPreload>(`${API_PREFIX}/planning/preloads/${preloadId}/cancel`, {
    method: "POST",
  });
}

export function listPlanningReservations(filters: {
  start?: string;
  end?: string;
  vehicle_id?: string;
} = {}) {
  return apiRequest<PlanningReservation[]>(withQuery(`${API_PREFIX}/planning/reservations`, filters));
}

export function createPlanningReservation(payload: PlanningReservationPayload) {
  return apiRequest<PlanningReservation>(`${API_PREFIX}/planning/reservations`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updatePlanningReservation(reservationId: string, payload: Partial<PlanningReservationPayload>) {
  return apiRequest<PlanningReservation>(`${API_PREFIX}/planning/reservations/${reservationId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function activatePlanningReservation(reservationId: string) {
  return apiRequest<PlanningReservation>(`${API_PREFIX}/planning/reservations/${reservationId}/activate`, {
    method: "POST",
  });
}

export function cancelPlanningReservation(reservationId: string) {
  return apiRequest<PlanningReservation>(`${API_PREFIX}/planning/reservations/${reservationId}/cancel`, {
    method: "POST",
  });
}
