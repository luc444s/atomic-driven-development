import { apiRequest } from "../../../apps/web/src/shared/api/client";

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
  last_hydrotest_date: string | null;
  next_hydrotest_date: string | null;
  adr_category: string | null;
  adr_un_number: string | null;
  adr_label: string | null;
  adr_package_type: string | null;
  adr_weight_kg: number | null;
  adr_merchandise: string | null;
  adr_tunnel: string | null;
  adr_subline: string | null;
  adr_factor: number | null;
  adr_points: number | null;
  adr_unit_measure: string | null;
  location: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type LogisticsCylinderCondition = {
  code: string;
  name: string;
  is_active: boolean;
  created_at: string;
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

export type LogisticsWarehouse = {
  id: string;
  tenant_id: string;
  name: string;
  code: string;
  address: string | null;
  phone: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type LogisticsZone = {
  id: string;
  tenant_id: string;
  name: string;
  code: string;
  is_active: boolean;
  created_at: string;
};

export type LogisticsVehicle = {
  id: string;
  tenant_id: string;
  plate: string;
  vehicle_type: string | null;
  brand: string | null;
  model: string | null;
  capacity_weight: number | null;
  capacity_volume: number | null;
  useful_load: number | null;
  adr_class: string | null;
  status: string;
  warehouse_id: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type LogisticsDeliveryPoint = {
  id: string;
  tenant_id: string;
  customer_id: string;
  contact_name: string | null;
  contact_email: string | null;
  address: string;
  phone: string | null;
  zone_id: string | null;
  warehouse_id: string | null;
  address_id: string | null;
  is_primary: boolean;
  delivery_day: string | null;
  visit_day: string | null;
  time_window: string | null;
  instructions: string | null;
  service_time_min: number | null;
  demand_units: number | null;
  demand_weight_kg: number | null;
  agent_user_id: string | null;
  fiscal_operation_document: string | null;
  fiscal_operation_type: string | null;
  gps_link: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

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

export type LogisticsRoute = {
  id: string;
  tenant_id: string;
  branch_id: string | null;
  route_date: string;
  driver_id: string;
  vehicle_id: string | null;
  status: string;
  notes: string | null;
  created_by: string;
  created_at: string;
  updated_at: string;
};

export type LogisticsRouteStop = {
  id: string;
  route_id: string;
  delivery_point_id: string;
  stop_order: number;
  scheduled_time: string | null;
  status: string;
  arrival_time: string | null;
  departure_time: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
};

export type LogisticsLoad = {
  id: string;
  route_id: string;
  cylinder_id: string;
  stop_id: string | null;
  status: string;
  loaded_at: string | null;
  unloaded_at: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
};

export type LogisticsMovementType = {
  code: string;
  name: string;
  category: string;
  moves_cylinders: boolean;
  origin_state: string | null;
  target_state: string | null;
};

export type LogisticsMovement = {
  id: string;
  tenant_id: string;
  branch_id: string | null;
  movement_type: string;
  document_series: string | null;
  document_number: string | null;
  full_document: string | null;
  order_id: string | null;
  route_id: string | null;
  customer_id: string | null;
  customer_name: string | null;
  warehouse_id: string | null;
  driver_id: string | null;
  vehicle_id: string | null;
  total: number | null;
  tax: number | null;
  discount: number | null;
  currency: string;
  exchange_rate: number;
  status: string;
  payment_status: string | null;
  carrier: string | null;
  plate: string | null;
  destination_place: string | null;
  destination_address: string | null;
  notes: string | null;
  dispatched_at: string | null;
  parent_movement_id: string | null;
  created_by: string;
  created_at: string;
  updated_at: string;
};

export type LogisticsMovementItem = {
  id: string;
  movement_id: string;
  cylinder_id: string | null;
  product_id: string | null;
  product_name: string | null;
  quantity_in: number;
  quantity_out: number;
  quantity: number;
  quantity_planned: number;
  unit_price: number | null;
  total_item: number | null;
  discount: number;
  item_status: string;
  state_before: string | null;
  state_after: string | null;
  notes: string | null;
  created_at: string;
};

export type LogisticsMovementHistory = {
  id: string;
  movement_id: string;
  field_name: string;
  from_value: string | null;
  to_value: string;
  changed_by: string;
  notes: string | null;
  created_at: string;
};

export type LogisticsAgendaTaskType = {
  code: string;
  description: string;
};

export type LogisticsAgendaTask = {
  id: string;
  tenant_id: string;
  route_id: string | null;
  driver_id: string;
  customer_id: string;
  customer_name: string | null;
  delivery_point_id: string | null;
  task_type: string;
  description: string | null;
  scheduled_date: string;
  scheduled_time: string | null;
  status: string;
  priority: number;
  order_id: string | null;
  quantity_requested: number | null;
  quantity_served: number | null;
  cylinder_serial: string | null;
  customer_confirmed: boolean;
  requires_signature: boolean;
  evidence_url: string | null;
  delivery_location: string | null;
  gps_coordinates: Record<string, unknown>;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
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
  tenant_id: string;
  name: string;
  code: string;
  content_kg: number | null;
  unit: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type LogisticsBrand = {
  id: string;
  tenant_id: string;
  name: string;
  code: string;
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

export type CreateCylinderPayload = {
  serial: string;
  description?: string | null;
  barcode1?: string | null;
  barcode2?: string | null;
  gas_group_id?: string | null;
  content_kg?: number | null;
  volume_m3?: number | null;
  condition?: string | null;
  brand_id?: string | null;
  cost?: number | null;
  price?: number | null;
  country_code?: string | null;
  box_number?: string | null;
  is_service?: boolean;
  manufacturer_date?: string | null;
  manufacturer_code?: string | null;
  manufacture_year?: number | null;
  weight_origin?: number | null;
  weight_current?: number | null;
  last_hydrotest_date?: string | null;
  location?: string | null;
  next_hydrotest_date?: string | null;
  adr_category?: string | null;
  adr_un_number?: string | null;
  adr_label?: string | null;
  adr_package_type?: string | null;
  adr_weight_kg?: number | null;
  adr_merchandise?: string | null;
  adr_tunnel?: string | null;
  adr_subline?: string | null;
  adr_factor?: number | null;
  adr_points?: number | null;
  adr_unit_measure?: string | null;
};

export type UpdateCylinderPayload = Partial<CreateCylinderPayload> & {
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

const API_PREFIX = "/api/v1/plugins/logistics";

export const logisticsKeys = {
  all: ["logistics"] as const,
  cylinders: {
    all: () => [...logisticsKeys.all, "cylinders"] as const,
    list: (filters: Record<string, string | boolean | undefined>) =>
      [...logisticsKeys.cylinders.all(), "list", filters] as const,
    detail: (id: string) => [...logisticsKeys.cylinders.all(), id] as const,
    trace: (id: string) => [...logisticsKeys.cylinders.detail(id), "trace"] as const,
    retimbrados: (id: string) => [...logisticsKeys.cylinders.detail(id), "retimbrados"] as const,
    ownership: (id: string) => [...logisticsKeys.cylinders.detail(id), "ownership"] as const,
    labelData: (id: string) => [...logisticsKeys.cylinders.detail(id), "label-data"] as const,
    labelHistory: (id: string) => [...logisticsKeys.cylinders.detail(id), "label-history"] as const,
    services: (id: string) => [...logisticsKeys.cylinders.detail(id), "services"] as const,
    allowedTransitions: (id: string) =>
      [...logisticsKeys.cylinders.detail(id), "allowed-transitions"] as const,
    summary: () => [...logisticsKeys.cylinders.all(), "summary"] as const,
  },
  states: () => [...logisticsKeys.all, "states"] as const,
  conditions: () => [...logisticsKeys.all, "conditions"] as const,
  gasProducts: () => [...logisticsKeys.all, "gas-products"] as const,
  brands: () => [...logisticsKeys.all, "brands"] as const,
  serviceTypes: () => [...logisticsKeys.all, "service-types"] as const,
  warehouses: () => [...logisticsKeys.all, "warehouses"] as const,
  zones: () => [...logisticsKeys.all, "zones"] as const,
  vehicles: () => [...logisticsKeys.all, "vehicles"] as const,
  deliveryPoints: () => [...logisticsKeys.all, "delivery-points"] as const,
  orders: {
    all: () => [...logisticsKeys.all, "orders"] as const,
    list: (filters: Record<string, string | undefined>) =>
      [...logisticsKeys.orders.all(), "list", filters] as const,
    detail: (id: string) => [...logisticsKeys.orders.all(), id] as const,
    items: (id: string) => [...logisticsKeys.orders.detail(id), "items"] as const,
  },
  routes: {
    all: () => [...logisticsKeys.all, "routes"] as const,
    list: (filters: Record<string, string | undefined>) =>
      [...logisticsKeys.routes.all(), "list", filters] as const,
    detail: (id: string) => [...logisticsKeys.routes.all(), id] as const,
    stops: (id: string) => [...logisticsKeys.routes.detail(id), "stops"] as const,
  },
  loads: (routeId: string) => [...logisticsKeys.all, "loads", routeId] as const,
  movementTypes: () => [...logisticsKeys.all, "movement-types"] as const,
  movements: {
    all: () => [...logisticsKeys.all, "movements"] as const,
    list: (filters: Record<string, string | undefined>) =>
      [...logisticsKeys.movements.all(), "list", filters] as const,
    detail: (id: string) => [...logisticsKeys.movements.all(), id] as const,
    items: (id: string) => [...logisticsKeys.movements.detail(id), "items"] as const,
    history: (id: string) => [...logisticsKeys.movements.detail(id), "history"] as const,
  },
  taskTypes: () => [...logisticsKeys.all, "task-types"] as const,
  agenda: {
    all: () => [...logisticsKeys.all, "agenda"] as const,
    list: (filters: Record<string, string | undefined>) =>
      [...logisticsKeys.agenda.all(), "list", filters] as const,
    detail: (id: string) => [...logisticsKeys.agenda.all(), id] as const,
  },
  scans: {
    all: () => [...logisticsKeys.all, "scans"] as const,
    list: () => [...logisticsKeys.scans.all(), "list"] as const,
    byMovement: (movementId: string) => [...logisticsKeys.scans.all(), movementId] as const,
  },
};

function withQuery(path: string, params: Record<string, string | boolean | undefined>) {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === "") {
      continue;
    }
    search.set(key, String(value));
  }
  const query = search.toString();
  return query ? `${path}?${query}` : path;
}

export function listCylinderStates() {
  return apiRequest<LogisticsCylinderState[]>(`${API_PREFIX}/catalog/cylinder-states`);
}

export function listConditions() {
  return apiRequest<LogisticsCylinderCondition[]>(`${API_PREFIX}/catalog/conditions`);
}

export function listGasProducts() {
  return apiRequest<LogisticsGasProduct[]>(`${API_PREFIX}/catalog/gas-products`);
}

export function listBrands() {
  return apiRequest<LogisticsBrand[]>(`${API_PREFIX}/catalog/brands`);
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

export function listWarehouses() {
  return apiRequest<LogisticsWarehouse[]>(`${API_PREFIX}/warehouses`);
}

export function createWarehouse(payload: Record<string, unknown>) {
  return apiRequest<LogisticsWarehouse>(`${API_PREFIX}/warehouses`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateWarehouse(warehouseId: string, payload: Record<string, unknown>) {
  return apiRequest<LogisticsWarehouse>(`${API_PREFIX}/warehouses/${warehouseId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function listZones() {
  return apiRequest<LogisticsZone[]>(`${API_PREFIX}/zones`);
}

export function createZone(payload: Record<string, unknown>) {
  return apiRequest<LogisticsZone>(`${API_PREFIX}/zones`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function listVehicles() {
  return apiRequest<LogisticsVehicle[]>(`${API_PREFIX}/vehicles`);
}

export function createVehicle(payload: Record<string, unknown>) {
  return apiRequest<LogisticsVehicle>(`${API_PREFIX}/vehicles`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateVehicle(vehicleId: string, payload: Record<string, unknown>) {
  return apiRequest<LogisticsVehicle>(`${API_PREFIX}/vehicles/${vehicleId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function listDeliveryPoints() {
  return apiRequest<LogisticsDeliveryPoint[]>(`${API_PREFIX}/delivery-points`);
}

export function createDeliveryPoint(payload: Record<string, unknown>) {
  return apiRequest<LogisticsDeliveryPoint>(`${API_PREFIX}/delivery-points`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateDeliveryPoint(deliveryPointId: string, payload: Record<string, unknown>) {
  return apiRequest<LogisticsDeliveryPoint>(`${API_PREFIX}/delivery-points/${deliveryPointId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

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

export function listRoutes(filters: { date?: string; driver?: string; status?: string }) {
  return apiRequest<LogisticsRoute[]>(
    withQuery(`${API_PREFIX}/routes`, { date: filters.date, driver: filters.driver, status: filters.status })
  );
}

export function getRoute(routeId: string) {
  return apiRequest<LogisticsRoute>(`${API_PREFIX}/routes/${routeId}`);
}

export function listRouteStops(routeId: string) {
  return apiRequest<LogisticsRouteStop[]>(`${API_PREFIX}/routes/${routeId}/stops`);
}

export function createRoute(payload: Record<string, unknown>) {
  return apiRequest<LogisticsRoute>(`${API_PREFIX}/routes`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateRoute(routeId: string, payload: Record<string, unknown>) {
  return apiRequest<LogisticsRoute>(`${API_PREFIX}/routes/${routeId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function startRoute(routeId: string) {
  return apiRequest<LogisticsRoute>(`${API_PREFIX}/routes/${routeId}/start`, { method: "POST" });
}

export function completeRoute(routeId: string) {
  return apiRequest<LogisticsRoute>(`${API_PREFIX}/routes/${routeId}/complete`, { method: "POST" });
}

export function cancelRoute(routeId: string) {
  return apiRequest<LogisticsRoute>(`${API_PREFIX}/routes/${routeId}/cancel`, { method: "POST" });
}

export function createRouteStop(routeId: string, payload: Record<string, unknown>) {
  return apiRequest<LogisticsRouteStop>(`${API_PREFIX}/routes/${routeId}/stops`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateRouteStop(routeId: string, stopId: string, payload: Record<string, unknown>) {
  return apiRequest<LogisticsRouteStop>(`${API_PREFIX}/routes/${routeId}/stops/${stopId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function deleteRouteStop(routeId: string, stopId: string) {
  return apiRequest<void>(`${API_PREFIX}/routes/${routeId}/stops/${stopId}`, { method: "DELETE" });
}

export function deliverRouteStop(routeId: string, stopId: string) {
  return apiRequest<LogisticsRouteStop>(`${API_PREFIX}/routes/${routeId}/stops/${stopId}/deliver`, {
    method: "POST",
  });
}

export function createRouteAgendaTasks(routeId: string) {
  return apiRequest<LogisticsAgendaTask[]>(`${API_PREFIX}/routes/${routeId}/agenda-tasks`, {
    method: "POST",
  });
}

export function listLoads(routeId: string) {
  return apiRequest<LogisticsLoad[]>(withQuery(`${API_PREFIX}/loads`, { route_id: routeId }));
}

export function createLoad(payload: Record<string, unknown>) {
  return apiRequest<LogisticsLoad>(`${API_PREFIX}/loads`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function bulkCreateLoads(payload: Record<string, unknown>) {
  return apiRequest<LogisticsLoad[]>(`${API_PREFIX}/loads/bulk`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function deleteLoad(loadId: string) {
  return apiRequest<void>(`${API_PREFIX}/loads/${loadId}`, { method: "DELETE" });
}

export function confirmLoads(routeId: string) {
  return apiRequest<LogisticsLoad[]>(`${API_PREFIX}/loads/confirm`, {
    method: "POST",
    body: JSON.stringify({ route_id: routeId }),
  });
}

export function listMovementTypes() {
  return apiRequest<LogisticsMovementType[]>(`${API_PREFIX}/catalog/movement-types`);
}

export function listMovements(filters: { type?: string; status?: string; customer?: string }) {
  return apiRequest<LogisticsMovement[]>(
    withQuery(`${API_PREFIX}/movements`, {
      type: filters.type,
      status: filters.status,
      customer: filters.customer,
    })
  );
}

export function getMovement(movementId: string) {
  return apiRequest<LogisticsMovement>(`${API_PREFIX}/movements/${movementId}`);
}

export function listMovementItems(movementId: string) {
  return apiRequest<LogisticsMovementItem[]>(`${API_PREFIX}/movements/${movementId}/items`);
}

export function listMovementHistory(movementId: string) {
  return apiRequest<LogisticsMovementHistory[]>(`${API_PREFIX}/movements/${movementId}/history`);
}

export function createMovement(payload: Record<string, unknown>) {
  return apiRequest<LogisticsMovement>(`${API_PREFIX}/movements`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateMovement(movementId: string, payload: Record<string, unknown>) {
  return apiRequest<LogisticsMovement>(`${API_PREFIX}/movements/${movementId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function confirmMovement(movementId: string) {
  return apiRequest<LogisticsMovement>(`${API_PREFIX}/movements/${movementId}/confirm`, {
    method: "POST",
  });
}

export function cancelMovement(movementId: string, reason: string) {
  return apiRequest<LogisticsMovement>(`${API_PREFIX}/movements/${movementId}/cancel`, {
    method: "POST",
    body: JSON.stringify({ reason }),
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

export function listTaskTypes() {
  return apiRequest<LogisticsAgendaTaskType[]>(`${API_PREFIX}/catalog/task-types`);
}

export function listAgendaTasks(filters: {
  driver?: string;
  task_type?: string;
  status?: string;
  date?: string;
}) {
  return apiRequest<LogisticsAgendaTask[]>(
    withQuery(`${API_PREFIX}/agenda/tasks`, {
      driver: filters.driver,
      task_type: filters.task_type,
      status: filters.status,
      date: filters.date,
    })
  );
}

export function getAgendaTask(taskId: string) {
  return apiRequest<LogisticsAgendaTask>(`${API_PREFIX}/agenda/tasks/${taskId}`);
}

export function listAgendaTasksByDriver(driverId: string) {
  return apiRequest<LogisticsAgendaTask[]>(`${API_PREFIX}/agenda/tasks/by-driver/${driverId}`);
}

export function createAgendaTask(payload: Record<string, unknown>) {
  return apiRequest<LogisticsAgendaTask>(`${API_PREFIX}/agenda/tasks`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateAgendaTask(taskId: string, payload: Record<string, unknown>) {
  return apiRequest<LogisticsAgendaTask>(`${API_PREFIX}/agenda/tasks/${taskId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function completeAgendaTask(taskId: string) {
  return apiRequest<LogisticsAgendaTask>(`${API_PREFIX}/agenda/tasks/${taskId}/complete`, {
    method: "POST",
  });
}

export function cancelAgendaTask(taskId: string) {
  return apiRequest<LogisticsAgendaTask>(`${API_PREFIX}/agenda/tasks/${taskId}/cancel`, {
    method: "POST",
  });
}

// ── Planning ─────────────────────────────────────────────
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

export const planningKeys = {
  stock: (wh?: string) => [...logisticsKeys.all, "planning", "stock", wh] as const,
  stockSummary: () => [...logisticsKeys.all, "planning", "stock-summary"] as const,
  pendingOrders: () => [...logisticsKeys.all, "planning", "pending-orders"] as const,
  preloads: {
    all: () => [...logisticsKeys.all, "planning", "preloads"] as const,
    list: () => [...planningKeys.preloads.all(), "list"] as const,
    detail: (id: string) => [...planningKeys.preloads.all(), id] as const,
  },
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

export function listPlanningPendingOrders() {
  return apiRequest<PlanningPendingOrder[]>(`${API_PREFIX}/planning/pending-orders`);
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

export function listPreloads() {
  return apiRequest<PlanningPreload[]>(`${API_PREFIX}/planning/preloads`);
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

// ── Reception ────────────────────────────────────────────
export type ReceptionIncident = {
  id: string;
  tenant_id: string;
  movement_id: string;
  cylinder_id: string | null;
  reason_code: string;
  description: string | null;
  created_by: string;
  created_at: string;
};

export type ReceptionReceiveResult = {
  movement: LogisticsMovement;
  incidents: ReceptionIncident[];
  shortage_items: LogisticsMovementItem[];
};

export type IncidentReason = {
  code: string;
  description: string;
  target_state: string | null;
};

export const receptionKeys = {
  pending: () => [...logisticsKeys.all, "reception", "pending"] as const,
  detail: (id: string) => [...logisticsKeys.all, "reception", id] as const,
  incidentReasons: () => [...logisticsKeys.all, "reception", "incident-reasons"] as const,
};

export function listPendingReceptions(warehouse_id?: string) {
  return apiRequest<LogisticsMovement[]>(
    withQuery(`${API_PREFIX}/reception/pending`, { warehouse_id })
  );
}

export function getReceptionDetail(movementId: string) {
  return apiRequest<LogisticsMovement>(`${API_PREFIX}/reception/${movementId}`);
}

export function receiveMovement(movementId: string, payload: { items: { movement_item_id: string; quantity_received: number }[]; notes?: string }) {
  return apiRequest<ReceptionReceiveResult>(`${API_PREFIX}/reception/${movementId}/receive`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function createReceptionIncident(movementId: string, payload: { cylinder_id?: string; reason_code: string; description?: string }) {
  return apiRequest<ReceptionIncident>(`${API_PREFIX}/reception/${movementId}/incident`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function listIncidentReasons() {
  return apiRequest<IncidentReason[]>(`${API_PREFIX}/reception/incident-reasons`);
}

// ── Waybill / Carta Porte ────────────────────────────────
export type WaybillDetailItem = {
  product_id: string | null;
  product_name: string | null;
  quantity: number;
  unit_weight_kg: number | null;
  total_weight_kg: number | null;
  adr_points: number | null;
};

export type Waybill = {
  movement_id: string;
  movement_type: string;
  document: string | null;
  warehouse_id: string | null;
  warehouse_name: string | null;
  customer_id: string | null;
  customer_name: string | null;
  vehicle_id: string | null;
  vehicle_plate: string | null;
  driver_id: string | null;
  destination_place: string | null;
  destination_address: string | null;
  items: WaybillDetailItem[];
  total_packages: number;
  total_weight_kg: number;
  total_adr_points: number;
};

export type WaybillSummary = {
  movement_id: string;
  total_packages: number;
  total_weight_kg: number;
  total_adr_points: number;
};

export function getWaybill(movementId: string) {
  return apiRequest<Waybill>(`${API_PREFIX}/waybill/${movementId}`);
}

export function getWaybillSummary(movementId: string) {
  return apiRequest<WaybillSummary>(`${API_PREFIX}/waybill/${movementId}/summary`);
}

// ── Dispatch ─────────────────────────────────────────────
export function assignDispatchGuide(movementId: string, payload: { document_series: string }) {
  return apiRequest<LogisticsMovement>(`${API_PREFIX}/movements/${movementId}/guide`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function closeDispatch(movementId: string) {
  return apiRequest<LogisticsMovement>(`${API_PREFIX}/movements/${movementId}/close-dispatch`, {
    method: "POST",
  });
}

export function getDispatchReceipt(movementId: string) {
  return apiRequest<LogisticsMovement>(`${API_PREFIX}/movements/${movementId}/dispatch-receipt`);
}

export function vehicleReturn(movementId: string, payload: { cylinder_ids: string[]; notes?: string }) {
  return apiRequest<LogisticsMovement>(`${API_PREFIX}/movements/${movementId}/vehicle-return`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

// ── Reports ──────────────────────────────────────────────
export type RouteAgendaReportStop = {
  stop_id: string;
  stop_order: number;
  customer_name: string | null;
  address: string | null;
  scheduled_time: string | null;
  status: string;
};

export type RouteAgendaReport = {
  route_id: string;
  route_date: string;
  driver_id: string;
  vehicle_id: string | null;
  stops: RouteAgendaReportStop[];
};

export type DispatchTicket = Waybill;

export type TransferAlbaran = Waybill;

export type LoadSummaryItem = {
  cylinder_id: string;
  serial: string | null;
  state: string | null;
  weight_kg: number | null;
};

export type LoadSummaryReport = {
  route_id: string;
  driver_id: string;
  vehicle_id: string | null;
  total_weight_kg: number;
  items: LoadSummaryItem[];
};

export type AdrPointsItem = {
  product_id: string | null;
  product_name: string | null;
  quantity: number;
  adr_points_per_unit: number;
  total_adr_points: number;
};

export type AdrPointsSummary = {
  movement_id: string;
  total_adr_points: number;
  items: AdrPointsItem[];
};

export function getRouteAgendaReport(routeId: string) {
  return apiRequest<RouteAgendaReport>(`${API_PREFIX}/reports/route-agenda/${routeId}`);
}

export function getDispatchTicket(movementId: string) {
  return apiRequest<DispatchTicket>(`${API_PREFIX}/reports/dispatch-ticket/${movementId}`);
}

export function getTransferAlbaran(movementId: string) {
  return apiRequest<TransferAlbaran>(`${API_PREFIX}/reports/transfer-albaran/${movementId}`);
}

export function getLoadSummary(routeId: string) {
  return apiRequest<LoadSummaryReport>(`${API_PREFIX}/reports/load-summary/${routeId}`);
}

export function getAdrSummary(movementId: string) {
  return apiRequest<AdrPointsSummary>(`${API_PREFIX}/reports/adr-summary/${movementId}`);
}

// ── Equipment ────────────────────────────────────────────
export type Equipment = {
  id: string;
  tenant_id: string;
  name: string;
  equipment_type: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type MovementEquipment = {
  id: string;
  tenant_id: string;
  movement_id: string;
  equipment_id: string;
  assigned_at: string;
  returned_at: string | null;
  notes: string | null;
};

export const equipmentKeys = {
  all: () => [...logisticsKeys.all, "equipment"] as const,
  list: () => [...equipmentKeys.all(), "list"] as const,
  movementEquipment: (id: string) => [...logisticsKeys.all, "movements", id, "equipment"] as const,
};

export function listEquipment() {
  return apiRequest<Equipment[]>(`${API_PREFIX}/equipment`);
}

export function createEquipment(payload: { name: string; equipment_type?: string; is_active?: boolean }) {
  return apiRequest<Equipment>(`${API_PREFIX}/equipment`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function listMovementEquipment(movementId: string) {
  return apiRequest<MovementEquipment[]>(`${API_PREFIX}/movements/${movementId}/equipment`);
}

export function assignEquipmentToMovement(movementId: string, payload: { equipment_id: string; notes?: string }) {
  return apiRequest<MovementEquipment>(`${API_PREFIX}/movements/${movementId}/equipment`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function returnMovementEquipment(movementId: string, eqId: string, payload?: { notes?: string }) {
  return apiRequest<MovementEquipment>(
    `${API_PREFIX}/movements/${movementId}/equipment/${eqId}/return`,
    { method: "PATCH", body: payload ? JSON.stringify(payload) : undefined }
  );
}

// ── Route Restrictions ───────────────────────────────────
export type VehicleRouteRestriction = {
  id: string;
  tenant_id: string;
  vehicle_id: string;
  route_id: string;
  restriction_type: string;
  created_at: string;
};

export type VehicleEligibility = {
  vehicle_id: string;
  plate: string;
  adr_class: string | null;
  capacity_weight: number | null;
  eligible: boolean;
  reason: string | null;
};

export function listVehicleRouteRestrictions(vehicleId: string) {
  return apiRequest<VehicleRouteRestriction[]>(`${API_PREFIX}/vehicles/${vehicleId}/route-restrictions`);
}

export function replaceVehicleRouteRestrictions(vehicleId: string, payload: { restrictions: { route_id: string; restriction_type: string }[] }) {
  return apiRequest<VehicleRouteRestriction[]>(`${API_PREFIX}/vehicles/${vehicleId}/route-restrictions`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function listEligibleVehiclesForRoute(routeId: string) {
  return apiRequest<VehicleEligibility[]>(`${API_PREFIX}/routes/${routeId}/eligible-vehicles`);
}

// ── Driver Parameters ────────────────────────────────────
export type DriverParameter = {
  id: string;
  tenant_id: string;
  driver_id: string;
  param_key: string;
  param_value: string | null;
  updated_at: string;
};

export function listDriverParameters(driverId: string) {
  return apiRequest<DriverParameter[]>(`${API_PREFIX}/drivers/${driverId}/parameters`);
}

export function upsertDriverParameters(driverId: string, payload: { parameters: Record<string, string | null> }) {
  return apiRequest<DriverParameter[]>(`${API_PREFIX}/drivers/${driverId}/parameters`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

// ── Vehicle Delivery Points ──────────────────────────────
export type VehicleDeliveryPoint = {
  id: string;
  tenant_id: string;
  vehicle_id: string;
  delivery_point_id: string;
  created_at: string;
};

export function listVehicleDeliveryPoints(vehicleId: string) {
  return apiRequest<VehicleDeliveryPoint[]>(`${API_PREFIX}/vehicles/${vehicleId}/delivery-points`);
}

export function linkVehicleDeliveryPoint(vehicleId: string, payload: { delivery_point_id: string }) {
  return apiRequest<VehicleDeliveryPoint>(`${API_PREFIX}/vehicles/${vehicleId}/delivery-points`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function unlinkVehicleDeliveryPoint(vehicleId: string, dpId: string) {
  return apiRequest<void>(`${API_PREFIX}/vehicles/${vehicleId}/delivery-points/${dpId}`, {
    method: "DELETE",
  });
}

// ── Agenda Daily Summary ─────────────────────────────────
export type AgendaDailySummaryBucket = {
  driver_id: string;
  status: string;
  total: number;
};

export function getAgendaDailySummary(date?: string) {
  return apiRequest<AgendaDailySummaryBucket[]>(
    withQuery(`${API_PREFIX}/agenda/daily-summary`, { date })
  );
}

// ── Route Weekdays ───────────────────────────────────────
export type RouteWeekday = {
  id: string;
  tenant_id: string;
  route_id: string;
  weekday: number;
  created_at: string;
};

export function replaceRouteWeekdays(routeId: string, payload: { weekdays: number[] }) {
  return apiRequest<RouteWeekday[]>(`${API_PREFIX}/routes/${routeId}/weekly-schedule`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

// ── Weight Summary ───────────────────────────────────────
export type LoadWeightSummary = {
  route_id: string;
  weight_limit_kg: number;
  total_weight_kg: number;
  exceeds_limit: boolean;
};

export function getLoadWeightSummary(routeId: string) {
  return apiRequest<LoadWeightSummary>(`${API_PREFIX}/loads/weight-summary?route_id=${routeId}`);
}

// ── ADR ──────────────────────────────────────────────────
export type AdrProductConfig = {
  id: string;
  tenant_id: string;
  product_id: string;
  adr_class: string | null;
  adr_points: number | null;
  adr_tunnel: string | null;
  max_quantity: number | null;
  valid_from: string;
  valid_to: string | null;
  created_at: string;
  updated_at: string;
};

export type AdrIncompatibility = {
  id: string;
  tenant_id: string;
  product_id_1: string;
  product_id_2: string;
  created_at: string;
};

export function getAdrProductConfig(productId: string) {
  return apiRequest<AdrProductConfig | null>(`${API_PREFIX}/adr/product-config/${productId}`);
}

export function upsertAdrProductConfig(productId: string, payload: {
  adr_class?: string; adr_points?: number; adr_tunnel?: string;
  max_quantity?: number; valid_from: string; valid_to?: string;
}) {
  return apiRequest<AdrProductConfig>(`${API_PREFIX}/adr/product-config/${productId}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function listAdrIncompatibilities() {
  return apiRequest<AdrIncompatibility[]>(`${API_PREFIX}/adr/incompatibilities`);
}

export function createAdrIncompatibility(payload: { product_id_1: string; product_id_2: string }) {
  return apiRequest<AdrIncompatibility>(`${API_PREFIX}/adr/incompatibilities`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function deleteAdrIncompatibility(id: string) {
  return apiRequest<void>(`${API_PREFIX}/adr/incompatibilities/${id}`, { method: "DELETE" });
}

export function listEligibleVehiclesForMovement(movementId: string) {
  return apiRequest<VehicleEligibility[]>(`${API_PREFIX}/adr/eligible-vehicles/${movementId}`);
}

// ── GPS ──────────────────────────────────────────────────
export function updateRouteGpsStart(routeId: string, payload: { gps_coordinates: Record<string, unknown> }) {
  return apiRequest<void>(`${API_PREFIX}/routes/${routeId}/gps-start`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function updateRouteStopGps(routeId: string, stopId: string, payload: { gps_coordinates: Record<string, unknown> }) {
  return apiRequest<void>(`${API_PREFIX}/routes/${routeId}/stops/${stopId}/gps`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function updateAgendaTaskGps(taskId: string, payload: { gps_coordinates: Record<string, unknown> }) {
  return apiRequest<void>(`${API_PREFIX}/agenda/tasks/${taskId}/gps`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

// ── Cylinder Weight / Content ────────────────────────────
export type CylinderWeight = {
  cylinder_id: string;
  serial: string;
  product_id: string | null;
  product_name: string | null;
  tara_weight_kg: number | null;
  current_weight_kg: number | null;
  content_kg: number | null;
  total_weight_kg: number | null;
};

export type ProductContent = {
  product_id: string;
  product_name: string;
  content_kg: number | null;
};

export function listAvailableCylindersWithWeight(warehouse_id?: string) {
  return apiRequest<CylinderWeight[]>(
    withQuery(`${API_PREFIX}/cylinders/available-with-weight`, { warehouse_id })
  );
}

export function getCylinderWeight(cylinderId: string) {
  return apiRequest<CylinderWeight>(`${API_PREFIX}/cylinders/${cylinderId}/weight`);
}

export function getProductContent(productId: string) {
  return apiRequest<ProductContent>(`${API_PREFIX}/products/${productId}/content`);
}
