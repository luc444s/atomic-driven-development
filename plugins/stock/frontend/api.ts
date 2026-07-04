import { apiRequest } from "../../../apps/web/src/shared/api/client";

import type {
  LogisticsWarehouseOption,
  StockAdjustPayload,
  StockBalanceItem,
  StockBalancePage,
  StockConfig,
  StockConfigPayload,
  StockLedgerItem,
  StockTransferPayload,
  StockTransferResult,
} from "./types";

const STOCK_BASE = "/api/v1/plugins/stock";

export const stockKeys = {
  all: ["stock"] as const,
  balances: {
    all: ["stock", "balances"] as const,
    list: (params: Record<string, unknown>) => ["stock", "balances", params] as const,
    detail: (productId: string, warehouseId: string) =>
      ["stock", "balances", productId, warehouseId] as const,
    byProduct: (productId: string) => ["stock", "balances", productId] as const,
  },
  ledger: {
    all: (params: Record<string, unknown>) =>
      ["stock", "ledger", params] as const,
    byProduct: (productId: string, params: Record<string, unknown>) =>
      ["stock", "ledger", productId, params] as const,
    byWarehouse: (productId: string, warehouseId: string, params: Record<string, unknown>) =>
      ["stock", "ledger", productId, warehouseId, params] as const,
  },
  config: {
    list: (params: Record<string, unknown>) => ["stock", "config", params] as const,
  },
  warehouses: ["stock", "warehouses"] as const,
};

function buildQuery(params: Record<string, unknown>) {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null || value === "") {
      continue;
    }
    query.set(key, String(value));
  }
  const stringified = query.toString();
  return stringified ? `?${stringified}` : "";
}

export async function listBalances(params: Record<string, unknown>): Promise<StockBalancePage> {
  return apiRequest(`${STOCK_BASE}/balance${buildQuery(params)}`);
}

export async function getBalanceDetail(productId: string, warehouseId: string): Promise<StockBalanceItem> {
  return apiRequest(`${STOCK_BASE}/balance/${productId}/${warehouseId}`);
}

export async function listProductLedger(
  productId: string,
  params: Record<string, unknown>,
): Promise<StockLedgerItem[]> {
  return apiRequest(`${STOCK_BASE}/ledger/${productId}${buildQuery(params)}`);
}

export async function listProductWarehouseLedger(
  productId: string,
  warehouseId: string,
  params: Record<string, unknown>,
): Promise<StockLedgerItem[]> {
  return apiRequest(`${STOCK_BASE}/ledger/${productId}/${warehouseId}${buildQuery(params)}`);
}

export async function listGlobalLedger(
  params: Record<string, unknown>,
): Promise<StockLedgerItem[]> {
  return apiRequest(`${STOCK_BASE}/ledger${buildQuery(params)}`);
}

export async function adjustStock(payload: StockAdjustPayload): Promise<StockBalanceItem> {
  return apiRequest(`${STOCK_BASE}/adjust`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function transferStock(payload: StockTransferPayload): Promise<StockTransferResult> {
  return apiRequest(`${STOCK_BASE}/transfer`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function listConfigs(params: Record<string, unknown>): Promise<StockConfig[]> {
  return apiRequest(`${STOCK_BASE}/config${buildQuery(params)}`);
}

export async function upsertConfig(payload: StockConfigPayload): Promise<StockConfig> {
  return apiRequest(`${STOCK_BASE}/config`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export async function listWarehousesCatalog(): Promise<LogisticsWarehouseOption[]> {
  return apiRequest(`${STOCK_BASE}/catalog/warehouses`);
}
