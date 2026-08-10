import type { OrderItemPayload } from "../types";

export type SupplierFormState = {
  id?: string;
  name: string;
  commercial_name: string;
  document_type_code: string;
  document_number: string;
  country_code: string;
  email: string;
  phone: string;
  mobile: string;
  payment_term_code: string;
  billing_type: string;
  accounting_code: string;
  fiscal_operation_key: string;
  tax_regime_code: string;
  notes: string;
};

export const EMPTY_SUPPLIER_FORM: SupplierFormState = {
  name: "",
  commercial_name: "",
  document_type_code: "",
  document_number: "",
  country_code: "PE",
  email: "",
  phone: "",
  mobile: "",
  payment_term_code: "",
  billing_type: "",
  accounting_code: "",
  fiscal_operation_key: "",
  tax_regime_code: "",
  notes: "",
};

export type OrderFormState = {
  id?: string;
  supplier_id: string;
  expected_date: string;
  notes: string;
  items: OrderItemPayload[];
};

export const EMPTY_ORDER_FORM: OrderFormState = {
  supplier_id: "",
  expected_date: "",
  notes: "",
  items: [],
};

export type ReceiveFormState = {
  warehouse_id: string;
  items: { purchase_item_id: string; quantity: number }[];
  notes: string;
};
