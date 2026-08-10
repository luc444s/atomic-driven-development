import type { CylinderEntryMode } from "../../api";

export type CylinderFormState = {
  serial: string;
  container_type: string;
  description: string;
  barcode2: string;
  gas_group_id: string;
  content_kg: string;
  volume_m3: string;
  condition: string;
  brand_id: string;
  cost: string;
  price: string;
  country_code: string;
  box_number: string;
  is_service: boolean;
  manufacturer_date: string;
  manufacturer_code: string;
  manufacture_year: string;
  weight_origin: string;
  weight_current: string;
  last_hydrotest_date: string;
  next_hydrotest_date: string;
  location: string;
  is_active: boolean;
  is_medical: boolean;
  medical_notes: string;
};

export type HydrotestFormState = {
  test_date: string;
  status: string;
  notes: string;
};

export type WarrantyFormState = {
  customer_id: string;
  customer_name: string;
  warranty_type: string;
  description: string;
};

export type RetimbradoFormState = {
  retimbrado_date: string;
  manufacture_code: string;
  manufacture_year: string;
  serial_number: string;
  weight_origin: string;
  weight_current: string;
  service_pressure: string;
  test_pressure: string;
  approval_number: string;
  danger_class: string;
  marking1: string;
  marking2: string;
  package_format: string;
  transport_code: string;
  adr_label: string;
  adr_tunnel: string;
  un_number: string;
  food_registry: string;
  notes: string;
};

export type ServiceFormState = {
  service_type_id: string;
  status: string;
  start_date: string;
  end_date: string;
  notes: string;
  purchase_price: string;
  sale_price: string;
  stock_in: string;
  stock_out: string;
  group_code: string;
  discount_pct: string;
  discount_amount: string;
  total_amount: string;
};

export type PrintLabelFormState = {
  origin: string;
  reason: string;
  printer_name: string;
  copies: string;
};

export type ScanFormState = {
  movement_id: string;
  barcode_serial: string;
  service_type: string;
  gps_lat: string;
  gps_lng: string;
};

export type CylinderCreateMetaState = {
  entry_mode: CylinderEntryMode;
  warehouse_id: string;
  customer_id: string;
  customer_name: string;
};

export const EMPTY_CYLINDER_FORM: CylinderFormState = {
  serial: "",
  container_type: "CYLINDER",
  description: "",
  barcode2: "",
  gas_group_id: "",
  content_kg: "",
  volume_m3: "",
  condition: "",
  brand_id: "",
  cost: "",
  price: "",
  country_code: "",
  box_number: "",
  is_service: false,
  manufacturer_date: "",
  manufacturer_code: "",
  manufacture_year: "",
  weight_origin: "",
  weight_current: "",
  last_hydrotest_date: "",
  next_hydrotest_date: "",
  location: "",
  is_active: true,
  is_medical: false,
  medical_notes: "",
};

export const EMPTY_HYDROTEST_FORM: HydrotestFormState = {
  test_date: "",
  status: "VIGENTE",
  notes: "",
};

export const EMPTY_WARRANTY_FORM: WarrantyFormState = {
  customer_id: "",
  customer_name: "",
  warranty_type: "CAMBIO",
  description: "",
};

export const EMPTY_RETIMBRADO_FORM: RetimbradoFormState = {
  retimbrado_date: "",
  manufacture_code: "",
  manufacture_year: "",
  serial_number: "",
  weight_origin: "",
  weight_current: "",
  service_pressure: "",
  test_pressure: "",
  approval_number: "",
  danger_class: "",
  marking1: "",
  marking2: "",
  package_format: "",
  transport_code: "",
  adr_label: "",
  adr_tunnel: "",
  un_number: "",
  food_registry: "",
  notes: "",
};

export const EMPTY_SERVICE_FORM: ServiceFormState = {
  service_type_id: "",
  status: "PENDIENTE",
  start_date: "",
  end_date: "",
  notes: "",
  purchase_price: "",
  sale_price: "",
  stock_in: "",
  stock_out: "",
  group_code: "",
  discount_pct: "",
  discount_amount: "",
  total_amount: "",
};

export const EMPTY_PRINT_LABEL_FORM: PrintLabelFormState = {
  origin: "ALTA",
  reason: "",
  printer_name: "",
  copies: "1",
};

export const EMPTY_SCAN_FORM: ScanFormState = {
  movement_id: "",
  barcode_serial: "",
  service_type: "VENTA",
  gps_lat: "",
  gps_lng: "",
};

export const EMPTY_CYLINDER_CREATE_META: CylinderCreateMetaState = {
  entry_mode: "EMPTY_FROM_WAREHOUSE",
  warehouse_id: "",
  customer_id: "",
  customer_name: "",
};
