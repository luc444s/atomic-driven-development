export type SupplierAddress = {
  id: string;
  label: string | null;
  line1: string;
  district: string | null;
  city: string | null;
  country_code: string;
  latitude: number | null;
  longitude: number | null;
  is_active: boolean;
};

export type SupplierContact = {
  id: string;
  full_name: string | null;
  role: string | null;
  phone: string | null;
  email: string | null;
  is_primary: boolean;
};

export type SupplierBankAccount = {
  id: string;
  bank_name: string;
  account_holder: string;
  iban: string;
  bic_swift: string | null;
  is_primary: boolean;
};

export type SupplierPaymentTerm = {
  id: string;
  payment_term_code: string;
  notes: string | null;
};

export type Supplier = {
  id: string;
  name: string;
  commercial_name: string | null;
  document_type_code: string | null;
  document_number: string | null;
  country_code: string | null;
  email: string | null;
  phone: string | null;
  mobile: string | null;
  payment_term_code: string | null;
  billing_type: string | null;
  accounting_code: string | null;
  fiscal_operation_key: string | null;
  tax_regime_code: string | null;
  notes: string | null;
  is_active: boolean;
  addresses: SupplierAddress[];
  contacts: SupplierContact[];
  bank_accounts: SupplierBankAccount[];
  payment_terms: SupplierPaymentTerm[];
  created_at: string;
  updated_at: string;
};

export type PurchaseItem = {
  id: string;
  product_id: string;
  quantity: number;
  unit_cost: number;
  received_qty: number;
};

export type ReceiptCostLine = {
  id: string;
  cost_type: string;
  amount: number;
  currency: string;
  notes: string | null;
};

export type PurchaseReceipt = {
  id: string;
  warehouse_id: string;
  receipt_date: string;
  dispatch_id: string | null;
  notes: string | null;
  created_at: string;
  qty_accepted: number | null;
  qty_rejected: number | null;
  difference_type: string | null;
  incidence_notes: string | null;
  commercial_closed_at: string | null;
  commercial_closed_by: string | null;
  extra_total: number | null;
  real_total: number | null;
  unit_cost_real: number | null;
  cost_lines: ReceiptCostLine[];
};

export type PurchaseOrder = {
  id: string;
  supplier: Supplier | null;
  status: string;
  order_date: string;
  expected_date: string | null;
  notes: string | null;
  created_by: string;
  created_at: string;
  updated_at: string;
};

export type PurchaseOrderDetail = PurchaseOrder & {
  items: PurchaseItem[];
  receipts: PurchaseReceipt[];
};

export type PurchaseOrderPage = {
  items: PurchaseOrder[];
  total: number;
  limit: number;
  offset: number;
};

export type CreateSupplierPayload = {
  name: string;
  document_type_code?: string | null;
  document_number?: string | null;
  email?: string | null;
  phone?: string | null;
  notes?: string | null;
};

export type UpdateSupplierPayload = Partial<CreateSupplierPayload>;

export type OrderItemPayload = {
  product_id: string;
  quantity: number;
  unit_cost: number;
};

export type CreateOrderPayload = {
  supplier_id: string;
  expected_date?: string | null;
  notes?: string | null;
  items: OrderItemPayload[];
};

export type UpdateOrderPayload = Partial<CreateOrderPayload>;

export type ReceiveItemRequest = {
  purchase_item_id: string;
  quantity: number;
  qty_accepted?: number | null;
  qty_rejected?: number | null;
};

export type ReceiveCostLine = {
  cost_type: string;
  amount: number;
  currency?: string;
  notes?: string | null;
};

export type ReceiveOrderPayload = {
  warehouse_id: string;
  items: ReceiveItemRequest[];
  notes?: string | null;
  tank_id?: string | null;
  dispatch_id?: string | null;
  cost_lines?: ReceiveCostLine[] | null;
};

export type CommercialCloseLine = {
  purchase_item_id: string;
  qty_accepted: number;
  qty_rejected?: number;
};

export type CommercialClosePayload = {
  lines?: CommercialCloseLine[] | null;
  cost_lines?: ReceiveCostLine[] | null;
  incidence_notes?: string | null;
};

export type SupplierInvoiceLine = {
  id: string;
  invoice_id: string;
  order_item_id: string | null;
  product_id: string | null;
  qty: number;
  unit_price: number;
  line_total: number;
  notes: string | null;
};

export type SupplierInvoice = {
  id: string;
  supplier_id: string;
  order_id: string;
  invoice_number: string;
  invoice_date: string;
  currency: string;
  subtotal: number;
  tax: number;
  total: number;
  status: string;
  lines: SupplierInvoiceLine[];
};

export type ReconciliationItem = {
  order_item_id: string | null;
  ordered_qty: number;
  accepted_qty: number;
  invoiced_qty: number;
  ordered_cost: number;
  real_cost: number;
  invoiced_cost: number;
  status: string;
  reason: string | null;
};

export type ReconciliationTotals = {
  ordered: number;
  real: number;
  invoiced: number;
  status: string;
  reasons: string[];
};

export type Reconciliation = {
  by_item: ReconciliationItem[];
  totals: ReconciliationTotals;
  invoice_status: string | null;
};

export type CreateInvoicePayload = {
  invoice_number: string;
  invoice_date: string;
  currency?: string;
  tax?: number;
  lines: { order_item_id?: string | null; product_id?: string | null; qty: number; unit_price: number; notes?: string | null }[];
};

export type DispatchCylinder = {
  id: string;
  cylinder_id: string;
  serial: string | null;
  product_id: string | null;
  service_type: string;
  status: string;
  returned_at: string | null;
  notes: string | null;
};

export type Dispatch = {
  id: string;
  supplier_id: string;
  supplier_name: string | null;
  order_id: string | null;
  warehouse_id: string | null;
  dispatch_date: string;
  carrier: string | null;
  vehicle_plate: string | null;
  driver_name: string | null;
  status: string;
  notes: string | null;
  created_by: string;
  created_at: string;
  cylinders: DispatchCylinder[];
};

export type DispatchPage = {
  items: Dispatch[];
  total: number;
  limit: number;
  offset: number;
};

export type CustodyEntry = {
  dispatch_id: string;
  dispatch_date: string;
  cylinder_id: string;
  serial: string | null;
  product_id: string | null;
  service_type: string;
  days_out: number;
  order_id: string | null;
};

export type CustodySummaryRow = {
  supplier_id: string;
  supplier_name: string | null;
  total_cylinders: number;
  oldest_days_out: number;
};

export type SupplierClaimEvent = {
  id: string;
  from_status: string | null;
  to_status: string;
  reason: string | null;
  user_id: string | null;
  created_at: string;
};

export type SupplierClaim = {
  id: string;
  tenant_id: string;
  order_id: string;
  supplier_id: string;
  receipt_id: string | null;
  invoice_id: string | null;
  reason: string;
  description: string;
  status: string;
  source: string;
  opened_by: string;
  opened_at: string;
  resolved_by: string | null;
  resolved_at: string | null;
  resolution_notes: string | null;
};

export type SupplierClaimDetail = SupplierClaim & {
  events: SupplierClaimEvent[];
};

export type ClaimDerivationResult = {
  created: SupplierClaim[];
  skipped: number;
};

export type CreateClaimPayload = {
  reason: string;
  description: string;
  receipt_id?: string | null;
  invoice_id?: string | null;
};

export type ReceiptServiceLine = {
  id: string;
  receipt_id: string;
  cylinder_id: string;
  serial: string;
  service_type: string;
  cost: number | null;
  notes: string | null;
  test_date: string | null;
  next_test_date: string | null;
  result: string | null;
  document_ref: string | null;
  created_by: string;
  created_at: string;
};

export type CreateReceiptServiceLinePayload = {
  serial: string;
  service_type: string;
  cost?: number | null;
  notes?: string | null;
  test_date?: string | null;
  next_test_date?: string | null;
  result?: string | null;
  document_ref?: string | null;
};

export type CylinderHistoryDispatch = {
  dispatch_id: string;
  order_id: string | null;
  supplier_id: string;
  dispatch_date: string;
  service_type: string;
  status: string;
  returned_at: string | null;
};

export type CylinderHistoryReceipt = {
  receipt_id: string;
  order_id: string;
  receipt_date: string;
  qty_accepted: number | null;
  qty_rejected: number | null;
  difference_type: string | null;
};

export type CylinderHistoryService = {
  receipt_id: string;
  service_type: string;
  cost: number | null;
  notes: string | null;
  test_date: string | null;
  next_test_date: string | null;
  result: string | null;
  document_ref: string | null;
  created_at: string;
};

export type CylinderHistory = {
  cylinder_id: string;
  serial: string;
  dispatches: CylinderHistoryDispatch[];
  receipts: CylinderHistoryReceipt[];
  services: CylinderHistoryService[];
};
