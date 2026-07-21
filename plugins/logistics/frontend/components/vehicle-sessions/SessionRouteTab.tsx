import { useState } from "react";

import { useMutation, useQuery, useQueryClient } from "../../../../../apps/web/src/lib/react-query";
import { Alert } from "../../../../../apps/web/src/shared/ui/alert";
import { Button } from "../../../../../apps/web/src/shared/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "../../../../../apps/web/src/shared/ui/card";
import { ProductSearchDialog } from "../../../../productos/frontend/components/ProductSearchDialog";
import {
  correctRouteIncident,
  confirmRouteOperation,
  createExchangeRouteOperation,
  createRouteIncident,
  createRouteOperation,
  getCurrentComposition,
  getRouteStopProgress,
  getSessionWaybill,
  listRouteIncidents,
  listRouteOperations,
  listRouteStopResults,
  listRouteStops,
  listSessionWaybillHistory,
  logisticsKeys,
  regenerateSessionWaybill,
  type LogisticsRouteStop,
  type RouteIncident,
  type RouteOperation,
  resolveRouteIncident,
  upsertRouteStopResult,
} from "../../api";
import { RouteIncidentsPanel } from "./RouteIncidentsPanel";
import { RouteCompositionCard } from "./RouteCompositionCard";
import { RouteOperationsCard } from "./RouteOperationsCard";
import {
  RouteOperationForm,
  type RouteCorrectionContext,
  type RouteDraftItem,
} from "./RouteOperationForm";
import { RouteStopProgressCard } from "./RouteStopProgressCard";
import { RouteStopResultsPanel } from "./RouteStopResultsPanel";
import { SessionWaybillCard } from "./SessionWaybillCard";
import {
  formatMovementDirection,
  formatRouteOperationStatus,
  formatRouteOperationType,
  formatStopStatus,
} from "./jornada-labels";

type Props = {
  open: boolean;
  routeId: string | null;
  sessionId: string;
  sessionStatus: string;
};

export function SessionRouteTab({ open, routeId, sessionId, sessionStatus }: Props) {
  const queryClient = useQueryClient();
  const [error, setError] = useState<string | null>(null);
  const [operationType, setOperationType] = useState("DELIVERY");
  const [routeStopId, setRouteStopId] = useState("");
  const [operationNotes, setOperationNotes] = useState("");
  const [showProductSearch, setShowProductSearch] = useState(false);
  const [nextDirection, setNextDirection] = useState<"OUT" | "IN">("OUT");
  const [draftItems, setDraftItems] = useState<RouteDraftItem[]>([]);
  const [incidentStopId, setIncidentStopId] = useState("");
  const [incidentRelatedOperationId, setIncidentRelatedOperationId] = useState("");
  const [incidentType, setIncidentType] = useState("QUANTITY_MISMATCH");
  const [incidentNotes, setIncidentNotes] = useState("");
  const [resolveIncidentId, setResolveIncidentId] = useState<string | null>(null);
  const [resolveNotes, setResolveNotes] = useState("");
  const [correctionIncidentId, setCorrectionIncidentId] = useState<string | null>(null);

  const stopsQuery = useQuery({
    queryKey: routeId ? logisticsKeys.routes.stops(routeId) : ["logistics", "routes", "none", "stops"],
    queryFn: () => listRouteStops(routeId!),
    enabled: open && Boolean(routeId),
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
  const createAndConfirmMutation = useMutation({
    mutationFn: async () => {
      const operationItems = draftItems.map((item) => ({
        product_id: item.product_id,
        product_name: item.product_name,
        quantity: Number(item.quantity || "0"),
        direction:
          operationType === "DELIVERY"
            ? "OUT"
            : operationType === "PICKUP"
              ? "IN"
              : item.direction,
      }));
      const correctionIncident = (routeIncidentsQuery.data ?? []).find((incident) => incident.id === correctionIncidentId);
      if (correctionIncidentId && !correctionIncident) {
        throw new Error("La incidencia a corregir ya no está disponible");
      }
      if (correctionIncidentId && correctionIncident) {
        return correctRouteIncident(sessionId, correctionIncidentId, {
          route_stop_id: routeStopId || correctionIncident.route_stop_id || null,
          operation_type: operationType,
          notes: operationNotes || null,
          idempotency_key: `route-op-correction:${sessionId}:${correctionIncidentId}:${Date.now()}`,
          items: operationItems,
        });
      }
      const created =
        operationType === "EXCHANGE"
          ? await createExchangeRouteOperation(sessionId, {
              route_stop_id: routeStopId || null,
              notes: operationNotes || null,
              idempotency_key: `route-op:${sessionId}:${Date.now()}`,
              delivered_lines: draftItems
                .filter((item) => item.direction === "OUT")
                .map((item) => ({
                  product_id: item.product_id,
                  product_name: item.product_name,
                  quantity: Number(item.quantity || "0"),
                })),
              picked_up_lines: draftItems
                .filter((item) => item.direction === "IN")
                .map((item) => ({
                  product_id: item.product_id,
                  product_name: item.product_name,
                  quantity: Number(item.quantity || "0"),
                })),
            })
          : await createRouteOperation(sessionId, {
              route_stop_id: routeStopId || null,
              operation_type: operationType,
              notes: operationNotes || null,
              idempotency_key: `route-op:${sessionId}:${Date.now()}`,
              items: operationItems,
            });
      return confirmRouteOperation(sessionId, created.id);
    },
    onSuccess: async () => {
      setError(null);
      setOperationNotes("");
      setDraftItems([]);
      setCorrectionIncidentId(null);
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
          : correctionIncidentId
            ? "No se pudo confirmar la corrección operativa"
            : "No se pudo confirmar la operación de ruta"
      );
    },
  });
  const createIncidentMutation = useMutation({
    mutationFn: () =>
      createRouteIncident(sessionId, {
        route_stop_id: incidentStopId || null,
        related_operation_id: incidentRelatedOperationId || null,
        type: incidentType,
        notes: incidentNotes || null,
      }),
    onSuccess: async () => {
      setError(null);
      setIncidentNotes("");
      setIncidentRelatedOperationId("");
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: logisticsKeys.vehicleSessions.routeIncidents(sessionId) }),
        queryClient.invalidateQueries({ queryKey: logisticsKeys.vehicleSessions.routeStopProgress(sessionId) }),
      ]);
    },
    onError: (cause) => {
      setError(cause instanceof Error ? cause.message : "No se pudo registrar la incidencia");
    },
  });
  const resolveIncidentMutation = useMutation({
    mutationFn: ({ incidentId, notes }: { incidentId: string; notes: string }) =>
      resolveRouteIncident(sessionId, incidentId, { notes: notes || null }),
    onSuccess: async () => {
      setError(null);
      setResolveIncidentId(null);
      setResolveNotes("");
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: logisticsKeys.vehicleSessions.routeIncidents(sessionId) }),
        queryClient.invalidateQueries({ queryKey: logisticsKeys.vehicleSessions.routeStopProgress(sessionId) }),
      ]);
    },
    onError: (cause) => {
      setError(cause instanceof Error ? cause.message : "No se pudo resolver la incidencia");
    },
  });
  const upsertStopResultMutation = useMutation({
    mutationFn: ({
      routeStopId,
      payload,
    }: {
      routeStopId: string;
      payload: {
        status: string;
        completion_percent: number;
        outcome_type: string;
        driver_note?: string | null;
      };
    }) => upsertRouteStopResult(sessionId, routeStopId, payload),
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
  const canRegenerate = waybillState?.can_regenerate && ["OUTBOUND", "RETURNING"].includes(sessionStatus);
  const canRegisterOperation = ["OUTBOUND", "RETURNING"].includes(sessionStatus);

  const routeOperations = routeOperationsQuery.data ?? [];
  const routeIncidents = routeIncidentsQuery.data ?? [];

  function addDraftProduct(product: { id: string; sku: string; name: string }) {
    setDraftItems((current) => [
      ...current,
      {
        product_id: product.id,
        product_name: `${product.sku} · ${product.name}`,
        quantity: "1",
        direction: operationType === "DELIVERY" ? "OUT" : operationType === "PICKUP" ? "IN" : nextDirection,
      },
    ]);
  }

  function updateDraftItem(index: number, patch: Partial<(typeof draftItems)[number]>) {
    setDraftItems((current) => current.map((item, itemIndex) => (itemIndex === index ? { ...item, ...patch } : item)));
  }

  function removeDraftItem(index: number) {
    setDraftItems((current) => current.filter((_, itemIndex) => itemIndex !== index));
  }

  function handleOpenProductSearch(direction?: "OUT" | "IN") {
    if (direction) {
      setNextDirection(direction);
    }
    setShowProductSearch(true);
  }

  function startResolveIncident(incidentId: string) {
    setCorrectionIncidentId(null);
    setResolveIncidentId(incidentId);
    setResolveNotes("");
  }

  function cancelResolveIncident() {
    setResolveIncidentId(null);
    setResolveNotes("");
  }

  function suggestCorrectionOperationType(incident: RouteIncident): string {
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

  function startCorrection(incident: RouteIncident) {
    setResolveIncidentId(null);
    setResolveNotes("");
    setCorrectionIncidentId(incident.id);
    setOperationType(suggestCorrectionOperationType(incident));
    setRouteStopId(incident.route_stop_id ?? "");
    setOperationNotes(`Reconciliación de incidencia ${incident.id}`);
    setDraftItems([]);
  }

  function cancelCorrection() {
    setCorrectionIncidentId(null);
    setDraftItems([]);
    setOperationNotes("");
  }

  const stopOptions = (stopsQuery.data ?? []).map((stop: LogisticsRouteStop) => ({
    value: stop.id,
    label: `Parada ${stop.stop_order} · ${formatStopStatus(stop.status)}`,
  }));
  const routeOperationOptions = routeOperations.map((operation: RouteOperation) => ({
    value: operation.id,
    label: `${formatRouteOperationType(operation.operation_type)} · ${formatRouteOperationStatus(operation.status)} · ${operation.items
      .map((item) => `${formatMovementDirection(item.direction)} ${item.product_name} ${item.quantity}`)
      .join(" · ")}`,
  }));

  const operationOptions = [
    { value: "DELIVERY", label: "Entrega" },
    { value: "PICKUP", label: "Recojo" },
    { value: "EXCHANGE", label: "Intercambio" },
  ];

  const incidentOptions = [
    { value: "QUANTITY_MISMATCH", label: "Descuadre de cantidad" },
    { value: "WRONG_PRODUCT", label: "Producto incorrecto" },
    { value: "EXCESS_DELIVERY", label: "Exceso de entrega" },
    { value: "MISSING_PICKUP", label: "Recojo faltante" },
    { value: "CUSTOMER_ABSENT", label: "Cliente ausente" },
    { value: "FAILED_DELIVERY", label: "Entrega fallida" },
    { value: "UNPLANNED_RETURN", label: "Retorno no planificado" },
  ];

  const directionOptions = [
    { value: "OUT", label: "Sale del camión" },
    { value: "IN", label: "Entra al camión" },
  ];
  const correctionIncident = routeIncidents.find((incident) => incident.id === correctionIncidentId) ?? null;
  const correctionContext: RouteCorrectionContext | null = correctionIncident
    ? {
        incidentId: correctionIncident.id,
        incidentType: correctionIncident.type,
        stopLabel:
          correctionIncident.route_stop_id
            ? stopOptions.find((option) => option.value === correctionIncident.route_stop_id)?.label ?? correctionIncident.route_stop_id
            : "Sin parada",
        relatedOperationLabel:
          correctionIncident.related_operation_id
            ? routeOperationOptions.find((option) => option.value === correctionIncident.related_operation_id)?.label ?? correctionIncident.related_operation_id
            : null,
      }
    : null;

  return (
    <div className="space-y-4">
      {error ? <Alert title="No se pudo actualizar la jornada en ruta">{error}</Alert> : null}
      <Card>
        <CardHeader>
          <CardTitle>Ruta</CardTitle>
          <CardDescription>
            Espacio operativo real de la jornada en calle.
          </CardDescription>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          Ruta asignada: {routeId ?? "Sin ruta"}
        </CardContent>
      </Card>

      <RouteOperationForm
        canRegisterOperation={canRegisterOperation}
        operationType={operationType}
        routeStopId={routeStopId}
        operationNotes={operationNotes}
        draftItems={draftItems}
        stopOptions={stopOptions}
        operationOptions={operationOptions}
        directionOptions={directionOptions}
        correctionContext={correctionContext}
        isPending={createAndConfirmMutation.isPending}
        onOperationTypeChange={setOperationType}
        onRouteStopChange={setRouteStopId}
        onOperationNotesChange={setOperationNotes}
        onOpenProductSearch={handleOpenProductSearch}
        onUpdateDraftItem={updateDraftItem}
        onRemoveDraftItem={removeDraftItem}
        onCancelCorrection={cancelCorrection}
        onSubmit={() => createAndConfirmMutation.mutate()}
      />

      <RouteCompositionCard composition={compositionQuery.data} />

      <RouteStopProgressCard stopOptions={stopOptions} progress={routeStopProgressQuery.data ?? []} />

      <RouteStopResultsPanel
        canManage={["OUTBOUND", "RETURNING"].includes(sessionStatus)}
        stopOptions={stopOptions}
        results={routeStopResultsQuery.data ?? []}
        isPending={upsertStopResultMutation.isPending}
        onSave={(routeStopId, payload) => upsertStopResultMutation.mutate({ routeStopId, payload })}
      />

      <RouteIncidentsPanel
        incidentStopId={incidentStopId}
        incidentRelatedOperationId={incidentRelatedOperationId}
        incidentType={incidentType}
        incidentNotes={incidentNotes}
        stopOptions={stopOptions}
        incidentOptions={incidentOptions}
        relatedOperationOptions={routeOperationOptions}
        incidents={routeIncidents}
        resolveIncidentId={resolveIncidentId}
        resolveNotes={resolveNotes}
        isCreatePending={createIncidentMutation.isPending}
        isResolvePending={resolveIncidentMutation.isPending}
        correctionIncidentId={correctionIncidentId}
        onIncidentStopChange={setIncidentStopId}
        onIncidentRelatedOperationChange={setIncidentRelatedOperationId}
        onIncidentTypeChange={setIncidentType}
        onIncidentNotesChange={setIncidentNotes}
        onCreateIncident={() => createIncidentMutation.mutate()}
        onStartResolve={startResolveIncident}
        onResolveNotesChange={setResolveNotes}
        onCancelResolve={cancelResolveIncident}
        onConfirmResolve={(incidentId) =>
          resolveIncidentMutation.mutate({ incidentId, notes: resolveNotes })
        }
        onStartCorrection={startCorrection}
      />

      <RouteOperationsCard operations={routeOperations} />

      <SessionWaybillCard
        waybillState={waybillState}
        history={historyQuery.data ?? []}
        isLoading={waybillQuery.isLoading}
        canRegenerate={Boolean(canRegenerate)}
        isRegenerating={regenerateMutation.isPending}
        onRegenerate={() => regenerateMutation.mutate()}
      />

      <ProductSearchDialog
        open={showProductSearch}
        onOpenChange={setShowProductSearch}
        onSelect={(product) => {
          addDraftProduct(product);
          setShowProductSearch(false);
        }}
      />
    </div>
  );
}
