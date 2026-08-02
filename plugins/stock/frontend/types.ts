export type StockBalanceItem = {
  id: string | null;
  tenant_id: string;
  product_id: string;
  product_sku: string;
  product_name: string;
  warehouse_id: string;
  warehouse_code: string;
  warehouse_name: string;
  quantity: number;
  min_quantity: number | null;
  max_quantity: number | null;
  is_below_min: boolean;
  updated_by: string | null;
  updated_at: string | null;
};

export type StockBalancePage = {
  items: StockBalanceItem[];
  total: number;
  limit: number;
  offset: number;
};

export type StockLedgerItem = {
  id: string;
  tenant_id: string;
  product_id: string;
  product_sku: string;
  product_name: string;
  warehouse_id: string;
  warehouse_code: string;
  warehouse_name: string;
  operation: string;
  quantity: number;
  balance_after: number;
  reference_type: string | null;
  reference_id: string | null;
  notes: string | null;
  created_by: string;
  created_at: string;
};

export type StockConfig = {
  id: string;
  tenant_id: string;
  product_id: string;
  product_sku: string;
  product_name: string;
  warehouse_id: string;
  warehouse_code: string;
  warehouse_name: string;
  min_quantity: number;
  max_quantity: number | null;
  is_active: boolean;
  updated_at: string;
  updated_by: string;
};

export type StockAdjustPayload = {
  product_id: string;
  warehouse_id: string;
  quantity: number;
  reason: string | null;
  idempotency_key?: string | null;
};

export type StockTransferPayload = {
  product_id: string;
  from_warehouse_id: string;
  to_warehouse_id: string;
  quantity: number;
  notes: string | null;
  idempotency_key?: string | null;
};

export type StockTransferResult = {
  reference_id: string;
  from_balance: StockBalanceItem;
  to_balance: StockBalanceItem;
};

export type StockConfigPayload = {
  product_id: string;
  warehouse_id: string;
  min_quantity: number;
  max_quantity: number | null;
  is_active: boolean;
};

export type LogisticsWarehouseOption = {
  id: string;
  tenant_id: string;
  branch_id: string | null;
  name: string;
  code: string;
  address: string | null;
  phone: string | null;
  is_primary: boolean; // almacen principal
  is_active: boolean;
  created_at: string;
  updated_at: string;
};
