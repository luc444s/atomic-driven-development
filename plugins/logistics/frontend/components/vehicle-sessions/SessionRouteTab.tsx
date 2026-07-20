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
  listRouteStops,
  listSessionWaybillHistory,
  logisticsKeys,
  regenerateSessionWaybill,
  type LogisticsRouteStop,
  type RouteIncident,
  type RouteOperation,
  resolveRouteIncident,
} from "../../api";
import { RouteIncidentsPanel } from "./RouteIncidentsPanel";
import {
  RouteOperationForm,
  type RouteCorrectionContext,
  type RouteDraftItem,
} from "./RouteOperationForm";

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
  const waybillState = waybillQuery.data;
  const active = waybillState?.active;
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
    label: `Parada ${stop.stop_order} · ${stop.status}`,
  }));
  const routeOperationOptions = routeOperations.map((operation: RouteOperation) => ({
    value: operation.id,
    label: `${operation.operation_type} · ${operation.status} · ${operation.items
      .map((item) => `${item.direction} ${item.product_name} ${item.quantity}`)
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
            Workspace operativo real de la jornada en calle.
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

      <Card>
        <CardHeader>
          <CardTitle>Composición vigente</CardTitle>
          <CardDescription>
            Proyección derivada de lo que el vehículo transporta ahora mismo.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {compositionQuery.data?.product_lines.length ? (
            <>
              <div className="space-y-2">
                {compositionQuery.data.product_lines.map((line) => (
                  <div key={line.product_id} className="rounded-lg border border-border px-3 py-2 text-sm text-foreground">
                    <div className="font-medium">{line.product_name}</div>
                    <div className="text-muted-foreground">
                      Cantidad: {line.quantity} · Peso: {line.weight_kg ?? "-"} kg · ADR: {line.adr_points ?? "-"}
                    </div>
                  </div>
                ))}
              </div>
              <div className="grid gap-3 border-t border-border pt-3 text-sm text-muted-foreground md:grid-cols-3">
                <div>Total bultos: {compositionQuery.data.totals.total_packages}</div>
                <div>Peso total: {compositionQuery.data.totals.total_weight_kg} kg</div>
                <div>ADR total: {compositionQuery.data.totals.total_adr_points}</div>
              </div>
            </>
          ) : (
            <p className="text-sm text-muted-foreground">Sin composición transportada vigente.</p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Progreso real de paradas</CardTitle>
          <CardDescription>
            Estado derivado desde operaciones confirmadas e incidencias abiertas.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-2">
          {routeStopProgressQuery.data?.length ? (
            routeStopProgressQuery.data.map((progress) => {
              const stopLabel = stopOptions.find((option) => option.value === progress.route_stop_id)?.label ?? progress.route_stop_id;
              return (
                <div key={progress.route_stop_id} className="rounded-lg border border-border px-3 py-2 text-sm text-foreground">
                  <div className="font-medium">{stopLabel}</div>
                  <div className="text-muted-foreground">
                    {progress.progress_status} · Incidencias abiertas: {progress.open_incidents}
                  </div>
                </div>
              );
            })
          ) : (
            <p className="text-sm text-muted-foreground">Sin paradas progresadas todavía.</p>
          )}
        </CardContent>
      </Card>

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

      <Card>
        <CardHeader>
          <CardTitle>Operaciones confirmadas</CardTitle>
          <CardDescription>
            Registro inmutable de lo que ya ocurrió en la calle.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-2">
          {routeOperationsQuery.data?.length ? (
            routeOperations.map((operation: RouteOperation) => (
              <div key={operation.id} className="rounded-lg border border-border px-3 py-2 text-sm text-foreground">
                <div className="font-medium">
                  {operation.operation_type} · {operation.status}
                </div>
                <div className="text-muted-foreground">
                  {operation.items.map((item) => `${item.direction} ${item.product_name} ${item.quantity}`).join(" · ")}
                </div>
              </div>
            ))
          ) : (
            <p className="text-sm text-muted-foreground">Sin operaciones registradas todavía.</p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <div className="flex items-start justify-between gap-4">
            <div>
              <CardTitle>Carta Porte</CardTitle>
              <CardDescription>
                Contexto documental vivo de la jornada mientras el vehículo está en ruta.
              </CardDescription>
            </div>
            <Button
              variant={waybillState?.sync_status === "OUTDATED" ? "default" : "secondary"}
              disabled={!canRegenerate || regenerateMutation.isPending}
              onClick={() => regenerateMutation.mutate()}
            >
              {regenerateMutation.isPending ? "Regenerando..." : active ? "Regenerar" : "Generar"}
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {waybillQuery.isLoading ? (
            <p className="text-sm text-muted-foreground">Cargando carta porte...</p>
          ) : null}

          {!waybillQuery.isLoading && !active ? (
            <div className="rounded-xl border border-dashed border-border p-4 text-sm text-muted-foreground">
              Todavía no existe una carta porte activa para esta jornada.
            </div>
          ) : null}

          {active ? (
            <>
              {waybillState?.sync_status === "OUTDATED" ? (
                <Alert title="Carta porte desactualizada">
                  La composición documental vigente ya no coincide con el estado operativo actual.
                </Alert>
              ) : null}
              <div className="grid gap-3 md:grid-cols-2 text-sm text-foreground">
                <div><span className="text-muted-foreground">Versión:</span> v{active.version}</div>
                <div><span className="text-muted-foreground">Generada:</span> {new Date(active.generated_at).toLocaleString()}</div>
                <div><span className="text-muted-foreground">Vehículo:</span> {active.snapshot.vehicle.plate}</div>
                <div><span className="text-muted-foreground">Conductor:</span> {active.snapshot.driver.name}</div>
                <div><span className="text-muted-foreground">Destino:</span> {active.snapshot.destination.name ?? "Sin destino"}</div>
                <div><span className="text-muted-foreground">Dirección:</span> {active.snapshot.destination.address ?? "Sin dirección"}</div>
              </div>

              <div className="space-y-2">
                <p className="text-sm font-medium text-foreground">Items transportados</p>
                <div className="space-y-2">
                  {active.snapshot.transported_items.map((item) => (
                    <div key={`${item.product_id}-${item.product_name}`} className="rounded-lg border border-border px-3 py-2 text-sm">
                      <div className="font-medium text-foreground">{item.product_name}</div>
                      <div className="text-muted-foreground">
                        Cantidad: {item.quantity} · Peso: {item.weight_kg ?? "-"} kg · ADR: {item.adr_points ?? "-"}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="grid gap-3 border-t border-border pt-3 text-sm text-muted-foreground md:grid-cols-3">
                <div>Total bultos: {active.snapshot.totals.total_packages ?? "-"}</div>
                <div>Peso total: {active.snapshot.totals.total_weight_kg ?? "-"} kg</div>
                <div>ADR total: {active.snapshot.totals.total_adr_points ?? "-"}</div>
              </div>
            </>
          ) : null}

          <div className="space-y-2 border-t border-border pt-3">
            <p className="text-sm font-medium text-foreground">Historial</p>
            {historyQuery.data?.length ? (
              <div className="space-y-2">
                {historyQuery.data.map((version) => (
                  <div key={version.id} className="rounded-lg border border-border px-3 py-2 text-sm text-foreground">
                    <div className="font-medium">v{version.version} · {version.status}</div>
                    <div className="text-muted-foreground">
                      {version.change_event} · {version.change_reason}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">Sin versiones registradas.</p>
            )}
          </div>
        </CardContent>
      </Card>

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
