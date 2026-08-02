// Auto-generado por split_api.py
import { BaseCylinderPayload } from "./_shared";
import { API_PREFIX, withQuery } from "./_shared";
import { apiRequest } from "../../../../apps/web/src/shared/api/client";
import { toNullable, toNumberOrNull, toIntegerOrNull } from "../cylinders/utils/formatters";
import type {
  HydrotestFormState,
  WarrantyFormState,
  RetimbradoFormState,
  ServiceFormState,
  PrintLabelFormState,
  ScanFormState,
} from "../cylinders/forms/cylinder-form-state";

export type LogisticsCylinder = {
  id: string;
  tenant_id: string;
  branch_id: string | null;
  serial: string;
  description: string | null;
  barcode1: string | null;
  barcode2: string | null;
  current_state: string;
  gas_group_id: string | null;
  product_id: string | null;
  content_kg: number | null;
  volume_m3: number | null;
  condition: string | null;
  brand_id: string | null;
  cost: number | null;
  price: number | null;
  country_code: string | null;
  box_number: string | null;
  is_service: boolean;
  manufacturer_date: string | null;
  manufacturer_code: string | null;
  manufacture_year: number | null;
  weight_origin: number | null;
  weight_current: number | null;
  average_weight_source: {
    weight_kg: number;
    matched_by: string[];
    source_id: string;
    brand_name: string | null;
    gas_name: string | null;
    condition_name: string | null;
  } | null;
  last_hydrotest_date: string | null;
  next_hydrotest_date: string | null;
  location: string | null;
  location_context: string | null;
  warehouse_id: string | null;
  warehouse_name: string | null;
  is_active: boolean;
  is_medical: boolean;
  medical_notes: string | null;
  created_at: string;
  updated_at: string;
};

export type LogisticsCylinderCondition = {
  code: string;
  name: string;
  description: string | null;
  is_active: boolean;
};

export type LogisticsCylinderState = {
  code: string;
  is_final: boolean;
  description: string | null;
};

export type LogisticsCylinderTransition = {
  id: string;
  from_state: string;
  to_state: string;
  requires_adr: boolean;
  requires_hydrotest: boolean;
  description: string | null;
};

export type LogisticsCylinderTrace = {
  id: number;
  tenant_id: string;
  cylinder_id: string;
  from_state: string | null;
  to_state: string;
  changed_by: string;
  movement_id: string | null;
  origin: string | null;
  reason_code: string | null;
  notes: string | null;
  metadata_json: Record<string, unknown>;
  created_at: string;
};

export type LogisticsCylinderSummaryItem = {
  state: string;
  count: number;
};

export type LogisticsHydrostaticTest = {
  id: string;
  cylinder_id: string;
  test_date: string;
  previous_test_date: string | null;
  status: string | null;
  movement_id: string | null;
  modified_by: string | null;
  notes: string | null;
  created_at: string;
};

export type LogisticsWarranty = {
  id: string;
  tenant_id: string;
  cylinder_id: string;
  customer_id: string;
  customer_name: string;
  warranty_type: string;
  status: string;
  description: string | null;
  return_date: string | null;
  created_by: string;
  created_at: string;
  updated_at: string;
};

export type LogisticsGasProduct = {
  id: string;
  name: string;
  code: string;
  content_kg: number | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type LogisticsBrand = {
  id: string;
  tenant_id: string;
  name: string;
  code: string;
  description: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type LogisticsServiceType = {
  id: string;
  tenant_id: string;
  code: string;
  name: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type LogisticsRetimbrado = {
  id: string;
  cylinder_id: string;
  retimbrado_date: string;
  manufacture_code: string | null;
  manufacture_year: number | null;
  serial_number: string | null;
  weight_origin: number | null;
  weight_current: number | null;
  service_pressure: number | null;
  test_pressure: number | null;
  approval_number: string | null;
  danger_class: string | null;
  marking1: string | null;
  marking2: string | null;
  package_format: string | null;
  transport_code: number | null;
  adr_label: string | null;
  adr_tunnel: string | null;
  un_number: string | null;
  food_registry: string | null;
  movement_id: string | null;
  notes: string | null;
  created_by: string;
  created_at: string;
  updated_at: string;
};

export type LogisticsOwnership = {
  id: string;
  cylinder_id: string;
  customer_id: string | null;
  customer_name: string | null;
  movement_id: string | null;
  change_date: string;
  condition: string | null;
  notes: string | null;
  created_by: string;
  created_at: string;
};

export type LogisticsLabelHistory = {
  id: string;
  cylinder_id: string;
  origin: string;
  reason: string | null;
  printer_name: string | null;
  copies: number;
  printed_by: string;
  printed_at: string;
  created_at: string;
};

export type LogisticsLabelData = {
  cylinder_id: string;
  serial: string;
  barcode2: string | null;
  description: string | null;
  brand_name: string | null;
  gas_product_name: string | null;
  manufacturer_code: string | null;
  manufacture_year: number | null;
  approval_number: string | null;
  danger_class: string | null;
  un_number: string | null;
  last_hydrotest_date: string | null;
  next_hydrotest_date: string | null;
  adr_label: string | null;
  adr_un_number: string | null;
  label_origin: string | null;
};

export type LogisticsScanLog = {
  id: string;
  tenant_id: string;
  movement_id: string;
  cylinder_id: string | null;
  barcode_scanned: string;
  service_type: string;
  user_id: string;
  gps_lat: number | null;
  gps_lng: number | null;
  result: string;
  error_reason: string | null;
  adr_validated: boolean;
  hydrotest_validated: boolean;
  scanned_at: string;
  created_at: string;
};

export type LogisticsCylinderService = {
  id: string;
  cylinder_id: string;
  order_id: string | null;
  order_item_id: string | null;
  movement_id: string | null;
  service_type_id: string;
  status: string;
  start_date: string | null;
  end_date: string | null;
  notes: string | null;
  purchase_price: number | null;
  sale_price: number | null;
  stock_in: number | null;
  stock_out: number | null;
  group_code: string | null;
  discount_pct: number | null;
  discount_amount: number | null;
  total_amount: number | null;
  created_by: string;
  created_at: string;
  updated_at: string;
};

export type CylinderEntryMode = "EMPTY_FROM_CUSTOMER" | "FULL_FROM_SUPPLIER";

export type CreateCylinderPayload = BaseCylinderPayload & {
  entry_mode?: CylinderEntryMode | null;
  minimal_route_create?: boolean;
  document_type?: string | null;
  document_number?: string | null;
  customer_id?: string | null;
};

export type UpdateCylinderPayload = Partial<BaseCylinderPayload> & {
  is_active?: boolean | null;
  branch_id?: string | null;
};

export type TransitionCylinderPayload = {
  to_state: string;
  movement_id?: string | null;
  origin?: string | null;
  reason_code?: string | null;
  notes?: string | null;
  metadata_json?: Record<string, unknown>;
};

export function createHydrotestFromForm(cylinderId: string, form: HydrotestFormState) {
  return createHydrotest(cylinderId, {
    test_date: form.test_date,
    status: form.status,
    notes: toNullable(form.notes),
  });
}

export function createWarrantyFromForm(cylinderId: string, form: WarrantyFormState) {
  return createWarranty(cylinderId, {
    customer_id: form.customer_id,
    warranty_type: form.warranty_type,
    description: toNullable(form.description),
  });
}

export function createRetimbradoFromForm(cylinderId: string, form: RetimbradoFormState) {
  return createRetimbrado(cylinderId, {
    retimbrado_date: form.retimbrado_date,
    manufacture_code: toNullable(form.manufacture_code),
    manufacture_year: toIntegerOrNull(form.manufacture_year),
    serial_number: toNullable(form.serial_number),
    weight_origin: toNumberOrNull(form.weight_origin),
    weight_current: toNumberOrNull(form.weight_current),
    service_pressure: toNumberOrNull(form.service_pressure),
    test_pressure: toNumberOrNull(form.test_pressure),
    approval_number: toNullable(form.approval_number),
    danger_class: toNullable(form.danger_class),
    marking1: toNullable(form.marking1),
    marking2: toNullable(form.marking2),
    package_format: toNullable(form.package_format),
    transport_code: toIntegerOrNull(form.transport_code),
    adr_label: toNullable(form.adr_label),
    adr_tunnel: toNullable(form.adr_tunnel),
    un_number: toNullable(form.un_number),
    food_registry: toNullable(form.food_registry),
    notes: toNullable(form.notes),
  });
}

export function createCylinderServiceFromForm(cylinderId: string, form: ServiceFormState) {
  return createCylinderService(cylinderId, {
    service_type_id: form.service_type_id,
    status: form.status,
    start_date: toNullable(form.start_date),
    end_date: toNullable(form.end_date),
    notes: toNullable(form.notes),
    purchase_price: toNumberOrNull(form.purchase_price),
    sale_price: toNumberOrNull(form.sale_price),
    stock_in: toNumberOrNull(form.stock_in),
    stock_out: toNumberOrNull(form.stock_out),
    group_code: toNullable(form.group_code),
    discount_pct: toNumberOrNull(form.discount_pct),
    discount_amount: toNumberOrNull(form.discount_amount),
    total_amount: toNumberOrNull(form.total_amount),
  });
}

export function printLabelFromForm(cylinderId: string, form: PrintLabelFormState) {
  return printLabel(cylinderId, {
    origin: form.origin,
    reason: toNullable(form.reason),
    printer_name: toNullable(form.printer_name),
    copies: Number(form.copies || "1"),
  });
}

export function processScanFromForm(form: ScanFormState) {
  return processScan({
    movement_id: form.movement_id,
    barcode_serial: form.barcode_serial,
    service_type: form.service_type,
    gps_lat: toNumberOrNull(form.gps_lat),
    gps_lng: toNumberOrNull(form.gps_lng),
  });
}

export function listCylinderStates() {
  return apiRequest<LogisticsCylinderState[]>(`${API_PREFIX}/catalog/cylinder-states`);
}

const PRODUCTOS_PREFIX = "/api/v1/plugins/productos";

export function listConditions() {
  return apiRequest<LogisticsCylinderCondition[]>(`${PRODUCTOS_PREFIX}/catalog/conditions`);
}

export function listGasProducts() {
  return apiRequest<LogisticsGasProduct[]>(`${PRODUCTOS_PREFIX}/catalog/gas-products`);
}

export function listBrands() {
  return apiRequest<LogisticsBrand[]>(`${PRODUCTOS_PREFIX}/catalog/brands`);
}

export function listServiceTypes() {
  return apiRequest<LogisticsServiceType[]>(`${API_PREFIX}/catalog/service-types`);
}

export function listCylinders(filters: {
  search?: string;
  state?: string;
  active?: boolean;
}) {
  return apiRequest<LogisticsCylinder[]>(
    withQuery(`${API_PREFIX}/cylinders`, {
      search: filters.search,
      state: filters.state,
      active: filters.active,
    })
  );
}

export function listCylinderSummary() {
  return apiRequest<LogisticsCylinderSummaryItem[]>(`${API_PREFIX}/cylinders/summary`);
}

export function getCylinder(cylinderId: string) {
  return apiRequest<LogisticsCylinder>(`${API_PREFIX}/cylinders/${cylinderId}`);
}

export function getCylinderBySerial(serial: string) {
  return apiRequest<LogisticsCylinder>(`${API_PREFIX}/cylinders/by-serial/${serial}`);
}

export function createCylinder(payload: CreateCylinderPayload) {
  return apiRequest<LogisticsCylinder>(`${API_PREFIX}/cylinders`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateCylinder(cylinderId: string, payload: UpdateCylinderPayload) {
  return apiRequest<LogisticsCylinder>(`${API_PREFIX}/cylinders/${cylinderId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function getAllowedTransitions(cylinderId: string) {
  return apiRequest<LogisticsCylinderTransition[]>(
    `${API_PREFIX}/cylinders/allowed-transitions/${cylinderId}`
  );
}

export function listCylinderTrace(cylinderId: string) {
  return apiRequest<LogisticsCylinderTrace[]>(`${API_PREFIX}/cylinders/${cylinderId}/trace`);
}

export function getCylinderLabelData(cylinderId: string) {
  return apiRequest<LogisticsLabelData>(`${API_PREFIX}/cylinders/${cylinderId}/label-data`);
}

export function listRetimbrados(cylinderId: string) {
  return apiRequest<LogisticsRetimbrado[]>(`${API_PREFIX}/cylinders/${cylinderId}/retimbrados`);
}

export function createRetimbrado(cylinderId: string, payload: Record<string, unknown>) {
  return apiRequest<LogisticsRetimbrado>(`${API_PREFIX}/cylinders/${cylinderId}/retimbrados`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function listOwnership(cylinderId: string) {
  return apiRequest<LogisticsOwnership[]>(`${API_PREFIX}/cylinders/${cylinderId}/ownership`);
}

export function listLabelHistory(cylinderId: string) {
  return apiRequest<LogisticsLabelHistory[]>(`${API_PREFIX}/cylinders/${cylinderId}/label-history`);
}

export function printLabel(cylinderId: string, payload: Record<string, unknown>) {
  return apiRequest<LogisticsLabelHistory>(`${API_PREFIX}/cylinders/${cylinderId}/print-label`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function listCylinderServices(cylinderId: string) {
  return apiRequest<LogisticsCylinderService[]>(`${API_PREFIX}/cylinders/${cylinderId}/services`);
}

export function createCylinderService(cylinderId: string, payload: Record<string, unknown>) {
  return apiRequest<LogisticsCylinderService>(`${API_PREFIX}/cylinders/${cylinderId}/services`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateCylinderService(
  cylinderId: string,
  serviceId: string,
  payload: Record<string, unknown>
) {
  return apiRequest<LogisticsCylinderService>(
    `${API_PREFIX}/cylinders/${cylinderId}/services/${serviceId}`,
    {
      method: "PATCH",
      body: JSON.stringify(payload),
    }
  );
}

export function deleteCylinderService(cylinderId: string, serviceId: string) {
  return apiRequest<void>(`${API_PREFIX}/cylinders/${cylinderId}/services/${serviceId}`, {
    method: "DELETE",
  });
}

export function transitionCylinder(cylinderId: string, payload: TransitionCylinderPayload) {
  return apiRequest<LogisticsCylinder>(`${API_PREFIX}/cylinders/${cylinderId}/transition`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function listHydrotests(cylinderId: string) {
  return apiRequest<LogisticsHydrostaticTest[]>(`${API_PREFIX}/cylinders/${cylinderId}/hydrotests`);
}

export function createHydrotest(cylinderId: string, payload: Record<string, unknown>) {
  return apiRequest<LogisticsHydrostaticTest>(`${API_PREFIX}/cylinders/${cylinderId}/hydrotests`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function listWarranties(cylinderId: string) {
  return apiRequest<LogisticsWarranty[]>(`${API_PREFIX}/cylinders/${cylinderId}/warranties`);
}

export function createWarranty(cylinderId: string, payload: Record<string, unknown>) {
  return apiRequest<LogisticsWarranty>(`${API_PREFIX}/cylinders/${cylinderId}/warranties`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function processScan(payload: Record<string, unknown>) {
  return apiRequest<LogisticsScanLog>(`${API_PREFIX}/scan`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function listScanLogs() {
  return apiRequest<LogisticsScanLog[]>(`${API_PREFIX}/scan/log`);
}

export function listScanLogsByMovement(movementId: string) {
  return apiRequest<LogisticsScanLog[]>(`${API_PREFIX}/scan/log/${movementId}`);
}
