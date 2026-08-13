import { useState } from "react";

import { useMutation, useQuery, useQueryClient } from "../../../../../apps/web/src/lib/react-query";
import { listCustomers } from "../../../../crm/frontend/api";
import {
  confirmRouteEvent,
  createRouteIncident,
  emitSessionWaybill,
  getCurrentComposition,
  getCustomerCylinderSummary,
  getRealWarehouses,
  openSessionWaybillDocument,
  getRouteStopProgress,
  getSessionWaybill,
  listRouteIncidents,
  listRouteOperations,
  listRouteStopResults,
  listRouteStops,
  listSessionWaybillHistory,
  listWarehouses,
  logisticsKeys,
  regenerateSessionWaybill,
  resolveRouteIncident,
  selectLoadSerial,
  upsertRouteStopResult,
} from "../../api";
import { buildCorrectionContext, buildCustomerOptions, buildRouteOperationOptions, buildStopOptions, directionOptions, incidentOptions, operationOptions } from "./session-route-tab-view";
import { useSessionRouteTabUiState } from "./useSessionRouteTabUiState";

type Props = {
  open: boolean;
  routeId: string | null;
  sessionId: string;
  sessionStatus: string;
};

export function useSessionRouteTabController({ open, routeId, sessionId, sessionStatus }: Props) {
  const queryClient = useQueryClient();
  const [error, setError] = useState<string | null>(null);
  const [fastSerialError, setFastSerialError] = useState<string | null>(null);

  const stopsQuery = useQuery({
    queryKey: routeId ? logisticsKeys.routes.stops(routeId) : ["logistics", "routes", "none", "stops"],
    queryFn: () => listRouteStops(routeId!),
    enabled: open && Boolean(routeId),
  });
  const customersQuery = useQuery({
    queryKey: ["crm", "customers", "route-event-context"],
    queryFn: () => listCustomers({ limit: 200, offset: 0 }),
    enabled: open,
  });
  const warehousesQuery = useQuery({
    queryKey: ["logistics", "warehouses", "route-event-context"],
    queryFn: () => listWarehouses(),
    enabled: open,
  });
  const routeOperationsQuery = useQuery({
    queryKey: logisticsKeys.vehicleSessions.routeOperations(sessionId),
    queryFn: () => listRouteOperations(sessionId),
    enabled: open,
  });
  const compositionQuery = useQuery({
    queryKey: logisticsKeys.vehicleSessions.composition(sessionId),
    queryFn: () => getCurrentComposition(sessionId),
    enabled: open,
  });
  const waybillQuery = useQuery({
    queryKey: logisticsKeys.vehicleSessions.waybill(sessionId),
    queryFn: () => getSessionWaybill(sessionId),
    enabled: open,
  });
  const historyQuery = useQuery({
    queryKey: logisticsKeys.vehicleSessions.waybillHistory(sessionId),
    queryFn: () => listSessionWaybillHistory(sessionId),
    enabled: open,
  });
  const routeIncidentsQuery = useQuery({
    queryKey: logisticsKeys.vehicleSessions.routeIncidents(sessionId),
    queryFn: () => listRouteIncidents(sessionId),
    enabled: open,
  });
  const routeStopProgressQuery = useQuery({
    queryKey: logisticsKeys.vehicleSessions.routeStopProgress(sessionId),
    queryFn: () => getRouteStopProgress(sessionId),
    enabled: open,
  });
  const routeStopResultsQuery = useQuery({
    queryKey: logisticsKeys.vehicleSessions.routeStopResults(sessionId),
    queryFn: () => listRouteStopResults(sessionId),
    enabled: open,
  });

  const uiState = useSessionRouteTabUiState();

  const stops = stopsQuery.data ?? [];
  const resolvedCustomerId = uiState.routeStopId
    ? stops.find((s) => s.id === uiState.routeStopId)?.customer_id ?? null
    : uiState.contextType === "CUSTOMER" ? uiState.contextCustomerId || null : null;
  const customerCylindersQuery = useQuery({
    queryKey: logisticsKeys.customerCylinderSummary(resolvedCustomerId ?? "none"),
    queryFn: () => getCustomerCylinderSummary(resolvedCustomerId!),
    enabled: open && Boolean(resolvedCustomerId) && uiState.operationType === "PICKUP",
  });

  const regenerateMutation = useMutation({
    mutationFn: () =>
      regenerateSessionWaybill(sessionId, {
        reason: "Regeneración manual desde la jornada",
        event: "MOVEMENT_CHANGED",
        idempotency_key: `session-waybill:${sessionId}:${Date.now()}`,
      }),
    onSuccess: async () => {
      setError(null);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: logisticsKeys.vehicleSessions.detail(sessionId) }),
        queryClient.invalidateQueries({ queryKey: logisticsKeys.vehicleSessions.composition(sessionId) }),
        queryClient.invalidateQueries({ queryKey: logisticsKeys.vehicleSessions.waybill(sessionId) }),
        queryClient.invalidateQueries({ queryKey: logisticsKeys.vehicleSessions.waybillHistory(sessionId) }),
      ]);
    },
    onError: (cause) => {
      setError(cause instanceof Error ? cause.message : "No se pudo regenerar la carta porte");
    },
  });

  const emitMutation = useMutation({
    mutationFn: () =>
      emitSessionWaybill(sessionId, {
        reason: "Emision oficial desde la jornada",
        idempotency_key: `session-waybill-issue:${sessionId}:${Date.now()}`,
      }),
    onSuccess: async () => {
      setError(null);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: logisticsKeys.vehicleSessions.detail(sessionId) }),
        queryClient.invalidateQueries({ queryKey: logisticsKeys.vehicleSessions.waybill(sessionId) }),
        queryClient.invalidateQueries({ queryKey: logisticsKeys.vehicleSessions.waybillHistory(sessionId) }),
      ]);
    },
    onError: (cause) => {
      setError(cause instanceof Error ? cause.message : "No se pudo emitir la carta porte oficial");
    },
  });

  const createAndConfirmMutation = useMutation({
    mutationFn: async () => {
      const operationItems = uiState.draftItems.map((item) => ({
        product_id: item.product_id,
        product_name: item.product_name,
        quantity: Number(item.quantity || "0"),
        direction:
          uiState.operationType === "DELIVERY"
            ? "OUT"
            : uiState.operationType === "PICKUP"
              ? "IN"
              : item.direction,
      }));
      const correctionIncident = (routeIncidentsQuery.data ?? []).find((incident) => incident.id === uiState.correctionIncidentId);
      if (uiState.correctionIncidentId && !correctionIncident) {
        throw new Error("La incidencia a corregir ya no está disponible");
      }

      const selectedStopId = uiState.routeStopId || correctionIncident?.route_stop_id || null;
      const resolvedContextType = selectedStopId ? "STOP" : uiState.contextType;
      const correctionTarget = correctionIncident ?? null;
      const incidentMode = correctionTarget ? "CORRECT_EXISTING" : "NONE";
      const idempotencyKey = correctionTarget
        ? `route-event-correction:${sessionId}:${correctionTarget.id}:${Date.now()}`
        : `route-event:${sessionId}:${Date.now()}`;

      return confirmRouteEvent(sessionId, {
        route_stop_id: selectedStopId,
        context_type: resolvedContextType,
        customer_id: resolvedContextType === "CUSTOMER" ? uiState.contextCustomerId || null : null,
        warehouse_id: resolvedContextType === "WAREHOUSE" ? uiState.contextWarehouseId || null : null,
        operation_type: uiState.operationType,
        notes: uiState.operationNotes || null,
        idempotency_key: idempotencyKey,
        items: operationItems,
        incident_mode: incidentMode,
        type: null,
        related_operation_id: correctionTarget?.related_operation_id ?? null,
        target_incident_id: correctionTarget?.id ?? null,
        incident_notes: correctionTarget ? uiState.operationNotes || null : null,
      });
    },
    onSuccess: async () => {
      setError(null);
      uiState.resetAfterRouteEventSuccess();
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: logisticsKeys.vehicleSessions.detail(sessionId) }),
        queryClient.invalidateQueries({ queryKey: logisticsKeys.vehicleSessions.routeOperations(sessionId) }),
        queryClient.invalidateQueries({ queryKey: logisticsKeys.vehicleSessions.composition(sessionId) }),
        queryClient.invalidateQueries({ queryKey: logisticsKeys.vehicleSessions.routeIncidents(sessionId) }),
        queryClient.invalidateQueries({ queryKey: logisticsKeys.vehicleSessions.routeStopProgress(sessionId) }),
        queryClient.invalidateQueries({ queryKey: logisticsKeys.vehicleSessions.waybill(sessionId) }),
        queryClient.invalidateQueries({ queryKey: logisticsKeys.vehicleSessions.waybillHistory(sessionId) }),
      ]);
    },
    onError: (cause) => {
      setError(
        cause instanceof Error
          ? cause.message
          : uiState.correctionIncidentId
            ? "No se pudo confirmar la corrección operativa"
            : "No se pudo confirmar el evento de ruta"
      );
    },
  });

  const resolveIncidentMutation = useMutation({
    mutationFn: ({ incidentId, notes }: { incidentId: string; notes: string }) =>
      resolveRouteIncident(sessionId, incidentId, { notes: notes || null }),
    onSuccess: async () => {
      setError(null);
      uiState.resetAfterIncidentResolved();
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: logisticsKeys.vehicleSessions.routeIncidents(sessionId) }),
        queryClient.invalidateQueries({ queryKey: logisticsKeys.vehicleSessions.routeStopProgress(sessionId) }),
      ]);
    },
    onError: (cause) => {
      setError(cause instanceof Error ? cause.message : "No se pudo resolver la incidencia");
    },
  });

  const createIncidentMutation = useMutation({
    mutationFn: () =>
      createRouteIncident(sessionId, {
        route_stop_id: uiState.incidentStopId || null,
        related_operation_id: uiState.incidentRelatedOperationId || null,
        type: uiState.incidentType,
        notes: uiState.incidentNotes || null,
      }),
    onSuccess: async () => {
      setError(null);
      uiState.resetAfterIncidentCreated();
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: logisticsKeys.vehicleSessions.routeIncidents(sessionId) }),
        queryClient.invalidateQueries({ queryKey: logisticsKeys.vehicleSessions.routeStopProgress(sessionId) }),
      ]);
    },
    onError: (cause) => {
      setError(cause instanceof Error ? cause.message : "No se pudo registrar la incidencia");
    },
  });

  const upsertStopResultMutation = useMutation({
    mutationFn: ({
      routeStopId: selectedRouteStopId,
      payload,
    }: {
      routeStopId: string;
      payload: {
        status: string;
        completion_percent: number;
        outcome_type: string;
        driver_note?: string | null;
      };
    }) => upsertRouteStopResult(sessionId, selectedRouteStopId, payload),
    onSuccess: async () => {
      setError(null);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: logisticsKeys.vehicleSessions.routeStopResults(sessionId) }),
        queryClient.invalidateQueries({ queryKey: logisticsKeys.vehicleSessions.routeStopProgress(sessionId) }),
        queryClient.invalidateQueries({ queryKey: logisticsKeys.vehicleSessions.operationalSummary(sessionId) }),
      ]);
    },
    onError: (cause) => {
      setError(cause instanceof Error ? cause.message : "No se pudo guardar el resultado de parada");
    },
  });

  const waybillState = waybillQuery.data;
  const canManageRouteContext = ["OUTBOUND", "RETURNING"].includes(sessionStatus);
  const canRegenerate = Boolean(waybillState?.can_regenerate) && canManageRouteContext;
  const routeOperations = routeOperationsQuery.data ?? [];
  const routeIncidents = routeIncidentsQuery.data ?? [];
  const routeStopResults = routeStopResultsQuery.data ?? [];
  const routeStopProgress = routeStopProgressQuery.data ?? [];
  const waybillHistory = historyQuery.data ?? [];

  function submitRouteEvent() {
    createAndConfirmMutation.mutate();
  }

  function createIncident() {
    createIncidentMutation.mutate();
  }

  function confirmResolveIncident(incidentId: string) {
    resolveIncidentMutation.mutate({ incidentId, notes: uiState.resolveNotes });
  }

  function closeEventModal() {
    if (createAndConfirmMutation.isPending) {
      return;
    }
    uiState.closeEventModal();
  }

  function closeIncidentsModal() {
    if (resolveIncidentMutation.isPending) {
      return;
    }
    uiState.closeIncidentsModal();
  }

  function closeStopResultsModal() {
    if (upsertStopResultMutation.isPending) {
      return;
    }
    uiState.closeStopResultsModal();
  }

  function saveStopResult(
    selectedRouteStopId: string,
    payload: {
      status: string;
      completion_percent: number;
      outcome_type: string;
      driver_note?: string | null;
    }
  ) {
    upsertStopResultMutation.mutate({ routeStopId: selectedRouteStopId, payload });
  }

  function regenerateWaybill() {
    regenerateMutation.mutate();
  }

  async function openWaybillDocument() {
    const issuedVersionId = waybillState?.issued?.id;
    if (!issuedVersionId) {
      setError("No existe documento oficial emitido para esta jornada");
      return;
    }
    try {
      // Open uses authenticated fetch + blob because browser navigation cannot attach bearer token.
      await openSessionWaybillDocument(sessionId, issuedVersionId);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "No se pudo abrir la carta porte oficial");
    }
  }

  const stopOptions = buildStopOptions(stopsQuery.data ?? []);
  const customerOptions = buildCustomerOptions(customersQuery.data?.items ?? []);
  const warehouseOptions = getRealWarehouses(warehousesQuery.data ?? []).map((warehouse) => ({
    value: warehouse.id,
    label: `${warehouse.code} · ${warehouse.name}`,
  }));
  const routeOperationOptions = buildRouteOperationOptions(routeOperations);

  const correctionIncident = routeIncidents.find((incident) => incident.id === uiState.correctionIncidentId) ?? null;
  const correctionContext = buildCorrectionContext(correctionIncident, stopOptions, routeOperationOptions);

  async function submitFastSerial() {
    const serial = uiState.fastSerialInput.trim();
    if (!serial) return;

    const isPickup = uiState.operationType === "PICKUP";
    const productLines = isPickup
      ? (customerCylindersQuery.data?.by_product ?? []).map((p) => ({ product_id: p.product_id, product_name: p.product_name, quantity: p.at_customer }))
      : compositionQuery.data?.product_lines ?? [];
    const contextProductId = productLines[0]?.product_id ?? "";
    const selectionContext = isPickup ? "ROUTE_PICKUP" : "ROUTE_DELIVERY";

    setFastSerialError(null);
    try {
      const result = await selectLoadSerial(sessionId, {
        product_id: contextProductId,
        source_warehouse_id: null,
        selection_context: selectionContext,
        serial,
      });
      if (result) {
        uiState.resetFastSerialInput();
        const matchingLine = productLines.find((l) => l.product_id === result.product_id);
        if (isPickup) {
          uiState.addPickupProduct({
            product_id: result.product_id,
            product_name: matchingLine?.product_name ?? result.cylinder_serial,
            available: (matchingLine as any)?.quantity ?? 99,
            serial: result.cylinder_serial,
          });
        } else {
          uiState.addDeliveryProduct({
            product_id: result.product_id,
            product_name: matchingLine?.product_name ?? result.cylinder_serial,
            available: matchingLine?.quantity ?? 99,
            serial: result.cylinder_serial,
          });
        }
      }
    } catch (cause) {
      setFastSerialError(cause instanceof Error ? cause.message : "No se pudo agregar el serial");
    }
  }

  return {
    sessionId,
    error,
    waybillState,
    waybillHistory,
    isWaybillLoading: waybillQuery.isLoading,
    canRegenerate,
    canEmitWaybill: Boolean(waybillState?.can_emit) && canManageRouteContext,
    canRegisterOperation: canManageRouteContext,
    isRegeneratingWaybill: regenerateMutation.isPending,
    isEmittingWaybill: emitMutation.isPending,
    routeOperations,
    routeIncidents,
    routeStopResults,
    routeStopProgress,
    composition: compositionQuery.data,
    customerCylinders: (customerCylindersQuery.data?.by_product ?? [])
      .filter((p) => p.at_customer > 0)
      .map((p) => ({
        product_id: p.product_id ?? "",
        product_name: p.product_name,
        quantity: p.at_customer,
      })),
    correctionContext,
    stopOptions,
    customerOptions,
    warehouseOptions,
    routeOperationOptions,
    operationOptions,
    incidentOptions,
    directionOptions,
    isSubmittingRouteEvent: createAndConfirmMutation.isPending,
    isCreatingIncident: createIncidentMutation.isPending,
    isResolvingIncident: resolveIncidentMutation.isPending,
    isSavingStopResult: upsertStopResultMutation.isPending,
    fastSerialError,
    ...uiState,
    openEventModal: () => {
      const defaultStopId = stopOptions[0]?.value ?? "";
      uiState.openEventModal(defaultStopId || undefined);
    },
    submitRouteEvent,
    submitFastSerial,
    createIncident,
    confirmResolveIncident,
    closeEventModal,
    closeIncidentsModal,
    closeStopResultsModal,
    saveStopResult,
    regenerateWaybill,
    emitWaybill: () => emitMutation.mutate(),
    openWaybillDocument,
  };
}
