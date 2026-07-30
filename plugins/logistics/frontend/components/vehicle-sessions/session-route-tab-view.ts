import {
  type LogisticsRouteStop,
  type RouteIncident,
  type RouteOperation,
} from "../../api";
import {
  formatMovementDirection,
  formatRouteOperationStatus,
  formatRouteOperationType,
  formatStopStatus,
} from "./jornada-labels";
import {
  type RouteCorrectionContext,
  type RouteSelectOption,
} from "./RouteOperationForm";

type RouteEventCustomer = {
  id: string;
  commercial_name: string | null;
  legal_name: string | null;
  document_number: string | null;
};

export const operationOptions: RouteSelectOption[] = [
  { value: "DELIVERY", label: "Entrega" },
  { value: "PICKUP", label: "Recojo" },
  { value: "EXCHANGE", label: "Intercambio" },
];

export const incidentOptions: RouteSelectOption[] = [
  { value: "QUANTITY_MISMATCH", label: "Descuadre de cantidad" },
  { value: "WRONG_PRODUCT", label: "Producto incorrecto" },
  { value: "EXCESS_DELIVERY", label: "Exceso de entrega" },
  { value: "MISSING_PICKUP", label: "Recojo faltante" },
  { value: "CUSTOMER_ABSENT", label: "Cliente ausente" },
  { value: "FAILED_DELIVERY", label: "Entrega fallida" },
  { value: "UNPLANNED_RETURN", label: "Retorno no planificado" },
];

export const directionOptions: RouteSelectOption[] = [
  { value: "OUT", label: "Sale del camión" },
  { value: "IN", label: "Entra al camión" },
];

export function suggestCorrectionOperationType(incident: RouteIncident): string {
  switch (incident.type) {
    case "WRONG_PRODUCT":
      return "EXCHANGE";
    case "EXCESS_DELIVERY":
      return "DELIVERY";
    case "MISSING_PICKUP":
    case "QUANTITY_MISMATCH":
    default:
      return "PICKUP";
  }
}

export function buildStopOptions(stops: LogisticsRouteStop[]): RouteSelectOption[] {
  return stops.map((stop) => ({
    value: stop.id,
    label: `Parada ${stop.stop_order} · ${formatStopStatus(stop.status)}`,
  }));
}

export function buildCustomerOptions(customers: RouteEventCustomer[]): RouteSelectOption[] {
  return customers.map((customer) => ({
    value: customer.id,
    label: `${customer.commercial_name ?? customer.legal_name ?? customer.id} · ${customer.document_number ?? "Sin documento"}`,
  }));
}

export function buildRouteOperationOptions(operations: RouteOperation[]): RouteSelectOption[] {
  return operations.map((operation) => ({
    value: operation.id,
    label: `${formatRouteOperationType(operation.operation_type)} · ${formatRouteOperationStatus(operation.status)} · ${operation.items
      .map((item) => `${formatMovementDirection(item.direction)} ${item.product_name} ${item.quantity}`)
      .join(" · ")}`,
  }));
}

export function buildCorrectionContext(
  correctionIncident: RouteIncident | null,
  stopOptions: RouteSelectOption[],
  routeOperationOptions: RouteSelectOption[]
): RouteCorrectionContext | null {
  if (!correctionIncident) {
    return null;
  }

  return {
    incidentId: correctionIncident.id,
    incidentType: correctionIncident.type,
    stopLabel: correctionIncident.route_stop_id
      ? stopOptions.find((option) => option.value === correctionIncident.route_stop_id)?.label ?? correctionIncident.route_stop_id
      : "Sin parada",
    relatedOperationLabel: correctionIncident.related_operation_id
      ? routeOperationOptions.find((option) => option.value === correctionIncident.related_operation_id)?.label ?? correctionIncident.related_operation_id
      : null,
  };
}
