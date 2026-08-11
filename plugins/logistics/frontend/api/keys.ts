// Auto-generado por split_api.py
import { apiRequest } from "../../../../apps/web/src/shared/api/client";

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
  customerCylinderSummary: (id: string) => [...logisticsKeys.all, "customers", id, "cylinders", "summary"] as const,
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
    assigned: (id: string) => [...logisticsKeys.routes.detail(id), "assigned-route"] as const,
    optimize: (id: string) => [...logisticsKeys.routes.detail(id), "optimize-preview"] as const,
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
  vehicleSessions: {
    all: () => [...logisticsKeys.all, "vehicle-sessions"] as const,
    list: (filters: Record<string, string | undefined>) =>
      [...logisticsKeys.vehicleSessions.all(), "list", filters] as const,
    active: () => [...logisticsKeys.vehicleSessions.all(), "active"] as const,
    detail: (id: string) => [...logisticsKeys.vehicleSessions.all(), id] as const,
    history: (id: string) => [...logisticsKeys.vehicleSessions.detail(id), "history"] as const,
    operationalSummary: (id: string) =>
      [...logisticsKeys.vehicleSessions.detail(id), "operational-summary"] as const,
    drivers: () => [...logisticsKeys.vehicleSessions.all(), "drivers"] as const,
    waybill: (id: string) => [...logisticsKeys.vehicleSessions.detail(id), "carta-porte"] as const,
    waybillHistory: (id: string) =>
      [...logisticsKeys.vehicleSessions.detail(id), "carta-porte", "history"] as const,
    routeOperations: (id: string) =>
      [...logisticsKeys.vehicleSessions.detail(id), "route-operations"] as const,
    composition: (id: string) =>
      [...logisticsKeys.vehicleSessions.detail(id), "composition", "current"] as const,
    routeIncidents: (id: string) =>
      [...logisticsKeys.vehicleSessions.detail(id), "route-incidents"] as const,
    routeStopResults: (id: string) =>
      [...logisticsKeys.vehicleSessions.detail(id), "route-stop-results"] as const,
    routeStopProgress: (id: string) =>
      [...logisticsKeys.vehicleSessions.detail(id), "route-stop-progress"] as const,
    routeControlState: (id: string) =>
      [...logisticsKeys.vehicleSessions.detail(id), "route-control-state"] as const,
    locationHistory: (id: string, filters: Record<string, string | undefined>) =>
      [...logisticsKeys.vehicleSessions.detail(id), "location-history", filters] as const,
  },
  loadPlans: {
    detail: (sessionId: string) => [...logisticsKeys.vehicleSessions.detail(sessionId), "load-plan"] as const,
  },
  loadSerials: {
    selected: (sessionId: string, productId: string, selectionContext = "LOAD_PLAN") =>
      [...logisticsKeys.vehicleSessions.detail(sessionId), "load-serials", selectionContext, productId, "selected"] as const,
    search: (sessionId: string, productId: string, query: string, selectionContext = "LOAD_PLAN") =>
      [...logisticsKeys.vehicleSessions.detail(sessionId), "load-serials", selectionContext, productId, "search", query] as const,
  },
  reconciliation: {
    detail: (sessionId: string) => [...logisticsKeys.vehicleSessions.detail(sessionId), "reconciliation"] as const,
  },
};

export function getCylinderQueryKeys(cylinderId?: string) {
  const keys: (readonly (string | number)[])[] = [
    logisticsKeys.cylinders.all(),
    logisticsKeys.cylinders.summary(),
  ];
  if (cylinderId) {
    keys.push(
      logisticsKeys.cylinders.detail(cylinderId),
      logisticsKeys.cylinders.trace(cylinderId),
      logisticsKeys.cylinders.allowedTransitions(cylinderId),
      logisticsKeys.cylinders.retimbrados(cylinderId),
      logisticsKeys.cylinders.ownership(cylinderId),
      logisticsKeys.cylinders.labelData(cylinderId),
      logisticsKeys.cylinders.labelHistory(cylinderId),
      logisticsKeys.cylinders.services(cylinderId),
    );
  }
  return keys;
}

export const planningKeys = {
  stock: (wh?: string) => [...logisticsKeys.all, "planning", "stock", wh] as const,
  stockSummary: () => [...logisticsKeys.all, "planning", "stock-summary"] as const,
  pendingOrders: (wh?: string) => [...logisticsKeys.all, "planning", "pending-orders", wh] as const,
  preloads: {
    all: () => [...logisticsKeys.all, "planning", "preloads"] as const,
    list: (wh?: string) => [...planningKeys.preloads.all(), "list", wh] as const,
    detail: (id: string) => [...planningKeys.preloads.all(), id] as const,
  },
  reservations: {
    all: () => [...logisticsKeys.all, "planning", "reservations"] as const,
    list: (filters: Record<string, string | undefined>) =>
      [...planningKeys.reservations.all(), "list", filters] as const,
    detail: (id: string) => [...planningKeys.reservations.all(), id] as const,
  },
};

export const receptionKeys = {
  pending: () => [...logisticsKeys.all, "reception", "pending"] as const,
  detail: (id: string) => [...logisticsKeys.all, "reception", id] as const,
  incidentReasons: () => [...logisticsKeys.all, "reception", "incident-reasons"] as const,
};

export const equipmentKeys = {
  all: () => [...logisticsKeys.all, "equipment"] as const,
  list: () => [...equipmentKeys.all(), "list"] as const,
  movementEquipment: (id: string) => [...logisticsKeys.all, "movements", id, "equipment"] as const,
};
