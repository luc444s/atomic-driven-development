// Auto-generado por split_api.py
import { API_PREFIX, withQuery } from "./_shared";
import { LogisticsOrderItem } from "./orders";
import { StockBalancePageRead } from "./_shared";
import { LogisticsMovement } from "./movements";
import { apiRequest } from "../../../../apps/web/src/shared/api/client";

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

