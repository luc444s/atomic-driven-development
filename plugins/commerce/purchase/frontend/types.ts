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

export type PurchaseReceipt = {
  id: string;
  warehouse_id: string;
  receipt_date: string;
  notes: string | null;
  created_at: string;
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
};

export type ReceiveOrderPayload = {
  warehouse_id: string;
  items: ReceiveItemRequest[];
  notes?: string | null;
  tank_id?: string | null;
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
