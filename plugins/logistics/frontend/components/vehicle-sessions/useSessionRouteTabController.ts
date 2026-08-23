import { useState } from "react";

import { useMutation, useQuery, useQueryClient } from "../../../../../apps/web/src/lib/react-query";
import {
  confirmRouteEvent,
  createRouteIncident,
  emitSessionWaybill,
  getCustomerCylinderSummary,
  getRouteControlState,
  getSessionRouteContext,
  getVehicleLocationHistory,
  listDeliveryPoints,
  openSessionWaybillDocument,
  postRouteStopArrive,
  postRouteStopDepart,
  logisticsKeys,
  regenerateSessionWaybill,
  resolveRouteIncident,
  selectLoadSerial,
  upsertRouteStopResult,
} from "../../api";
import { buildCorrectionContext, directionOptions, incidentOptions, operationOptions } from "./session-route-tab-view";
import { buildRouteContextView } from "./route-context-view";
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

  const routeContextQuery = useQuery({
    queryKey: logisticsKeys.vehicleSessions.routeContext(sessionId),
    queryFn: () => getSessionRouteContext(sessionId),
    enabled: open,
    staleTime: 30 * 1000,
  });

  const hasAssignedRoute = open && Boolean(routeId);
  const isOperativeStatus = ["READY_TO_DEPART", "OUTBOUND", "RETURNING"].includes(sessionStatus);
  const telemetryEnabled = hasAssignedRoute && isOperativeStatus;

  const controlStateQuery = useQuery({
    queryKey: logisticsKeys.vehicleSessions.routeControlState(sessionId),
    queryFn: () => getRouteControlState(sessionId),
    enabled: telemetryEnabled,
    refetchInterval: 10_000,
  });

  const locationHistoryQuery = useQuery({
    queryKey: logisticsKeys.vehicleSessions.locationHistory(sessionId, {}),
    queryFn: () => getVehicleLocationHistory(sessionId, { limit: 200 }),
    enabled: telemetryEnabled,
    refetchInterval: 10_000,
  });

  const deliveryPointsQuery = useQuery({
    queryKey: logisticsKeys.all.concat("delivery-points"),
    queryFn: listDeliveryPoints,
    enabled: open,
    staleTime: 60 * 1000,
  });

  const uiState = useSessionRouteTabUiState();

  const view = buildRouteContextView(routeContextQuery.data);
  const stops = view.stops;
  const resolvedCustomerId = uiState.routeStopId
    ? stops.find((s) => s.id === uiState.routeStopId)?.customer_id ?? null
    : uiState.contextType === "CUSTOMER" ? uiState.contextCustomerId || null : null;
  const customerCylindersQuery = useQuery({
    queryKey: logisticsKeys.customerCylinderSummary(resolvedCustomerId ?? "none"),
    queryFn: () => getCustomerCylinderSummary(resolvedCustomerId!),
    enabled: open && Boolean(resolvedCustomerId) && uiState.operationType === "PICKUP",
  });

  function invalidateRouteContext() {
    return queryClient.invalidateQueries({
      queryKey: logisticsKeys.vehicleSessions.routeContext(sessionId),
    });
  }

  const regenerateMutation = useMutation({
    mutationFn: () =>
      regenerateSessionWaybill(sessionId, {
        reason: "Regeneración manual desde la jornada",
        event: "MOVEMENT_CHANGED",
        idempotency_key: `session-waybill:${sessionId}:${Date.now()}`,
      }),
    onSuccess: async () => {
      setError(null);
      await invalidateRouteContext();
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
      await invalidateRouteContext();
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
      const routeIncidents = view.routeIncidents;
      const correctionIncident = routeIncidents.find((incident) => incident.id === uiState.correctionIncidentId);
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
        invalidateRouteContext(),
        queryClient.invalidateQueries({ queryKey: logisticsKeys.vehicleSessions.detail(sessionId) }),
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
      await invalidateRouteContext();
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
      await invalidateRouteContext();
    },
    onError: (cause) => {
      setError(cause instanceof Error ? cause.message : "No se pudo registrar la incidencia");
    },
  });

  const arriveMutation = useMutation({
    mutationFn: (stopId: string) => postRouteStopArrive(sessionId, stopId),
    onSuccess: async () => {
      setError(null);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: logisticsKeys.vehicleSessions.routeControlState(sessionId) }),
        queryClient.invalidateQueries({ queryKey: logisticsKeys.vehicleSessions.routeContext(sessionId) }),
      ]);
    },
    onError: (cause) => {
      setError(cause instanceof Error ? cause.message : "No se pudo marcar la llegada");
    },
  });

  const departMutation = useMutation({
    mutationFn: (stopId: string) => postRouteStopDepart(sessionId, stopId),
    onSuccess: async () => {
      setError(null);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: logisticsKeys.vehicleSessions.routeControlState(sessionId) }),
        queryClient.invalidateQueries({ queryKey: logisticsKeys.vehicleSessions.routeContext(sessionId) }),
      ]);
    },
    onError: (cause) => {
      setError(cause instanceof Error ? cause.message : "No se pudo marcar la salida");
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
        invalidateRouteContext(),
        queryClient.invalidateQueries({ queryKey: logisticsKeys.vehicleSessions.operationalSummary(sessionId) }),
      ]);
    },
    onError: (cause) => {
      setError(cause instanceof Error ? cause.message : "No se pudo guardar el resultado de parada");
    },
  });

  const waybillState = view.waybill;
  const canManageRouteContext = ["OUTBOUND", "RETURNING"].includes(sessionStatus);
  const canRegenerate = Boolean(waybillState?.can_regenerate) && canManageRouteContext;
  const routeOperations = view.routeOperations;
  const routeIncidents = view.routeIncidents;
  const routeStopResults = view.routeStopResults;
  const routeStopProgress = view.routeStopProgress;
  const waybillHistory = view.waybillHistory;

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

  const stopOptions = view.stopOptions;
  const customerOptions = view.customerOptions;
  const warehouseOptions = view.warehouseOptions;
  const routeOperationOptions = view.routeOperationOptions;

  const correctionIncident = routeIncidents.find((incident) => incident.id === uiState.correctionIncidentId) ?? null;
  const correctionContext = buildCorrectionContext(correctionIncident, stopOptions, routeOperationOptions);

  const selectedStop = stops.find((s) => s.id === uiState.routeStopId) ?? null;
  const stopAddressLabel = selectedStop?.delivery_point_id
    ? (deliveryPointsQuery.data ?? []).find((dp) => dp.id === selectedStop.delivery_point_id)?.address ?? null
    : null;

  async function submitFastSerial() {
    const serial = uiState.fastSerialInput.trim();
    if (!serial) return;

    const isPickup = uiState.operationType === "PICKUP";
    const productLines = isPickup
      ? (customerCylindersQuery.data?.by_product ?? []).map((p) => ({ product_id: p.product_id, product_name: p.product_name, quantity: p.at_customer }))
      : view.composition?.product_lines ?? [];
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
    routeId,
    stops,
    controlState: controlStateQuery.data ?? null,
    locationHistory: locationHistoryQuery.data ?? [],
    deliveryPoints: deliveryPointsQuery.data ?? [],
    isControlPending: arriveMutation.isPending || departMutation.isPending,
    onArrive: (stopId: string) => arriveMutation.mutate(stopId),
    onDepart: (stopId: string) => departMutation.mutate(stopId),
    routeDetail: routeContextQuery.data?.route_detail ?? null,
    assignedRoute: routeContextQuery.data?.assigned_route ?? null,
    waybillState,
    waybillHistory,
    isWaybillLoading: routeContextQuery.isLoading,
    canRegenerate,
    canEmitWaybill: Boolean(waybillState?.can_emit) && canManageRouteContext,
    canRegisterOperation: canManageRouteContext,
    isRegeneratingWaybill: regenerateMutation.isPending,
    isEmittingWaybill: emitMutation.isPending,
    routeOperations,
    routeIncidents,
    routeStopResults,
    routeStopProgress,
    composition: view.composition,
    customerCylinders: (customerCylindersQuery.data?.by_product ?? [])
      .filter((p) => p.at_customer > 0)
      .map((p) => ({
        product_id: p.product_id ?? "",
        product_name: p.product_name,
        quantity: p.at_customer,
        address_label: p.address_label ?? null,
      })),
    correctionContext,
    stopOptions,
    customerOptions,
    warehouseOptions,
    routeOperationOptions,
    operationOptions,
    incidentOptions,
    directionOptions,
    stopAddressLabel,
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
