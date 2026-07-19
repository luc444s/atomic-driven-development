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
import { Input } from "../../../../../apps/web/src/shared/ui/input";
import { Select } from "../../../../../apps/web/src/shared/ui/select";
import { ProductSearchDialog } from "../../../../productos/frontend/components/ProductSearchDialog";
import {
  confirmRouteOperation,
  createRouteOperation,
  getCurrentComposition,
  getSessionWaybill,
  listRouteOperations,
  listRouteStops,
  listSessionWaybillHistory,
  logisticsKeys,
  regenerateSessionWaybill,
  type LogisticsRouteStop,
  type RouteOperation,
} from "../../api";

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
  const [draftItems, setDraftItems] = useState<Array<{ product_id: string; product_name: string; quantity: string; direction: "OUT" | "IN" }>>([]);

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
      const created = await createRouteOperation(sessionId, {
        route_stop_id: routeStopId || null,
        operation_type: operationType,
        notes: operationNotes || null,
        idempotency_key: `route-op:${sessionId}:${Date.now()}`,
        items: draftItems.map((item) => ({
          product_id: item.product_id,
          product_name: item.product_name,
          quantity: Number(item.quantity || "0"),
          direction: operationType === "DELIVERY" ? "OUT" : operationType === "PICKUP" ? "IN" : item.direction,
        })),
      });
      return confirmRouteOperation(sessionId, created.id);
    },
    onSuccess: async () => {
      setError(null);
      setOperationNotes("");
      setDraftItems([]);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: logisticsKeys.vehicleSessions.detail(sessionId) }),
        queryClient.invalidateQueries({ queryKey: logisticsKeys.vehicleSessions.routeOperations(sessionId) }),
        queryClient.invalidateQueries({ queryKey: logisticsKeys.vehicleSessions.composition(sessionId) }),
        queryClient.invalidateQueries({ queryKey: logisticsKeys.vehicleSessions.waybill(sessionId) }),
        queryClient.invalidateQueries({ queryKey: logisticsKeys.vehicleSessions.waybillHistory(sessionId) }),
      ]);
    },
    onError: (cause) => {
      setError(cause instanceof Error ? cause.message : "No se pudo confirmar la operación de ruta");
    },
  });
  const waybillState = waybillQuery.data;
  const active = waybillState?.active;
  const canRegenerate = waybillState?.can_regenerate && ["OUTBOUND", "RETURNING"].includes(sessionStatus);
  const canRegisterOperation = ["OUTBOUND", "RETURNING"].includes(sessionStatus);

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

  const stopOptions = (stopsQuery.data ?? []).map((stop: LogisticsRouteStop) => ({
    value: stop.id,
    label: `Parada ${stop.stop_order} · ${stop.status}`,
  }));

  const operationOptions = [
    { value: "DELIVERY", label: "Entrega" },
    { value: "PICKUP", label: "Recojo" },
    { value: "EXCHANGE", label: "Intercambio" },
  ];

  const directionOptions = [
    { value: "OUT", label: "Sale del camión" },
    { value: "IN", label: "Entra al camión" },
  ];

  return (
    <div className="space-y-4">
      {error ? <Alert title="No se pudo actualizar carta porte">{error}</Alert> : null}
      <Card>
        <CardHeader>
          <CardTitle>Ruta</CardTitle>
          <CardDescription>
            Esta superficie se ampliará luego con Deliver, Pickup y Exchange.
          </CardDescription>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          Ruta asignada: {routeId ?? "Sin ruta"}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Operación de ruta</CardTitle>
          <CardDescription>
            La calle se registra aquí. La composición vigente y la carta porte salen de estas operaciones confirmadas.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {!canRegisterOperation ? (
            <p className="text-sm text-muted-foreground">
              Las operaciones de ruta solo pueden registrarse cuando la jornada está en ruta o retorno.
            </p>
          ) : (
            <>
              <div className="grid gap-4 md:grid-cols-2">
                <label className="space-y-2 text-sm text-foreground">
                  <span>Tipo</span>
                  <Select value={operationType} onChange={setOperationType} options={operationOptions} />
                </label>
                <label className="space-y-2 text-sm text-foreground">
                  <span>Parada</span>
                  <Select value={routeStopId} onChange={setRouteStopId} options={stopOptions} placeholder="Sin parada" />
                </label>
              </div>

              <label className="space-y-2 text-sm text-foreground">
                <span>Notas</span>
                <Input value={operationNotes} onChange={(event) => setOperationNotes(event.target.value)} placeholder="Entrega parcial, recojo de vacíos..." />
              </label>

              <div className="space-y-2 rounded-xl border border-border p-3">
                <div className="flex flex-wrap items-center gap-2">
                  {operationType === "EXCHANGE" ? (
                    <div className="w-56">
                      <Select value={nextDirection} onChange={(value) => setNextDirection(value as "OUT" | "IN")} options={directionOptions} />
                    </div>
                  ) : null}
                  <Button type="button" variant="secondary" onClick={() => setShowProductSearch(true)}>
                    Agregar producto
                  </Button>
                </div>
                {draftItems.length ? (
                  <div className="space-y-2">
                    {draftItems.map((item, index) => (
                      <div key={`${item.product_id}-${index}`} className="grid gap-2 rounded-lg border border-border p-3 md:grid-cols-[1.4fr_0.8fr_0.8fr_auto]">
                        <div className="text-sm text-foreground">{item.product_name}</div>
                        <Select
                          value={operationType === "DELIVERY" ? "OUT" : operationType === "PICKUP" ? "IN" : item.direction}
                          onChange={(value) => updateDraftItem(index, { direction: value as "OUT" | "IN" })}
                          options={directionOptions}
                        />
                        <Input
                          type="number"
                          min="0"
                          step="0.001"
                          value={item.quantity}
                          onChange={(event) => updateDraftItem(index, { quantity: event.target.value })}
                        />
                        <Button type="button" variant="secondary" onClick={() => removeDraftItem(index)}>
                          Quitar
                        </Button>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">Sin líneas todavía.</p>
                )}
              </div>

              <div className="flex justify-end">
                <Button
                  disabled={createAndConfirmMutation.isPending || draftItems.length === 0}
                  onClick={() => createAndConfirmMutation.mutate()}
                >
                  {createAndConfirmMutation.isPending ? "Confirmando..." : "Confirmar operación"}
                </Button>
              </div>
            </>
          )}
        </CardContent>
      </Card>

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
          <CardTitle>Operaciones confirmadas</CardTitle>
          <CardDescription>
            Registro inmutable de lo que ya ocurrió en la calle.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-2">
          {routeOperationsQuery.data?.length ? (
            routeOperationsQuery.data.map((operation: RouteOperation) => (
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
