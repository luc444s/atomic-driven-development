import { FormEvent, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "../../../../apps/web/src/lib/react-query";

import {
  acceptPreload,
  cancelPreload,
  generatePreload,
  listPlanningPendingOrders,
  listPlanningStockBalances,
  listPreloads,
  listWarehouses,
  LogisticsWarehouse,
  logisticsKeys,
  planningKeys,
  PlanningPendingOrder,
  PlanningPreload,
  PlanningStockSummaryItem,
  postPlanOrder,
} from "../api";
import { LogisticsSection } from "../components/LogisticsSection";
import { Alert } from "../../../../apps/web/src/shared/ui/alert";
import { Badge } from "../../../../apps/web/src/shared/ui/badge";
import { Button } from "../../../../apps/web/src/shared/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../../../apps/web/src/shared/ui/card";
import { DataTable } from "../../../../apps/web/src/shared/ui/data-table";
import { Dialog } from "../../../../apps/web/src/shared/ui/dialog";
import { Input, Switch } from "../../../../apps/web/src/shared/ui/input";
import { Select } from "../../../../apps/web/src/shared/ui/select";
import { toast } from "../../../../apps/web/src/shared/ui/toast";

const COVERAGE_COLORS: Record<string, string> = {
  verde: "text-emerald-400",
  amarillo: "text-amber-400",
  rojo: "text-rose-400",
};

function getCoverageStatus(available: number): string {
  if (available >= 1) {
    return "verde";
  }
  if (available > 0) {
    return "amarillo";
  }
  return "rojo";
}

function resolveWarehouseName(
  warehousesById: Map<string, LogisticsWarehouse>,
  warehouseId: string | null,
): string {
  if (!warehouseId) {
    return "Sin asignar";
  }
  return warehousesById.get(warehouseId)?.name ?? "-";
}

function buildPlanningStockRows(
  warehouseId: string,
  balances: Array<{
    product_id: string;
    product_name: string;
    warehouse_id: string;
    quantity: number;
  }>,
  pendingOrders: PlanningPendingOrder[],
  preloads: PlanningPreload[],
): PlanningStockSummaryItem[] {
  const productNames = new Map<string, string>();
  const actualByProduct = new Map<string, number>();
  const committedByProduct = new Map<string, number>();
  const plannedByProduct = new Map<string, number>();

  for (const balance of balances) {
    productNames.set(balance.product_id, balance.product_name);
    actualByProduct.set(balance.product_id, (actualByProduct.get(balance.product_id) ?? 0) + balance.quantity);
  }

  for (const order of pendingOrders) {
    for (const item of order.items) {
      if (!item.product_id) {
        continue;
      }
      productNames.set(item.product_id, productNames.get(item.product_id) ?? item.product_name);
      committedByProduct.set(
        item.product_id,
        (committedByProduct.get(item.product_id) ?? 0) + item.quantity_planned,
      );
    }
  }

  for (const preload of preloads) {
    if (preload.status !== "PENDIENTE") {
      continue;
    }
    for (const item of preload.items) {
      productNames.set(item.product_id, productNames.get(item.product_id) ?? item.product_name ?? "-");
      plannedByProduct.set(
        item.product_id,
        (plannedByProduct.get(item.product_id) ?? 0) + item.quantity_planned,
      );
    }
  }

  const productIds = new Set<string>([
    ...actualByProduct.keys(),
    ...committedByProduct.keys(),
    ...plannedByProduct.keys(),
  ]);

  return Array.from(productIds)
    .map((productId) => {
      const stock_actual = actualByProduct.get(productId) ?? 0;
      const stock_comprometido = committedByProduct.get(productId) ?? 0;
      const stock_planificado = plannedByProduct.get(productId) ?? 0;
      const stock_disponible = stock_actual - stock_comprometido - stock_planificado;

      return {
        product_id: productId,
        product_name: productNames.get(productId) ?? "-",
        warehouse_id: warehouseId,
        stock_actual,
        stock_comprometido,
        stock_planificado,
        stock_disponible,
        coverage_status: getCoverageStatus(stock_disponible),
      };
    })
    .sort((left, right) => left.product_name.localeCompare(right.product_name));
}

function CoverageBadge({ status }: { status: string }) {
  return <Badge className={COVERAGE_COLORS[status] || "text-muted-foreground"}>{status}</Badge>;
}

export function PlanningPage() {
  const queryClient = useQueryClient();
  const [warehouseFilter, setWarehouseFilter] = useState("");
  const [selectedOrder, setSelectedOrder] = useState<PlanningPendingOrder | null>(null);
  const [planMode, setPlanMode] = useState("partial");
  const [permitNoStock, setPermitNoStock] = useState(false);
  const [isPreloadOpen, setIsPreloadOpen] = useState(false);
  const [preloadDate, setPreloadDate] = useState("");
  const [selectedPreload, setSelectedPreload] = useState<PlanningPreload | null>(null);
  const [error, setError] = useState<string | null>(null);

  const warehousesQuery = useQuery({ queryKey: logisticsKeys.warehouses(), queryFn: listWarehouses });
  const stockBalancesQuery = useQuery({
    queryKey: planningKeys.stock(warehouseFilter),
    queryFn: () => listPlanningStockBalances(warehouseFilter),
    enabled: Boolean(warehouseFilter),
  });
  const pendingQuery = useQuery({
    queryKey: planningKeys.pendingOrders(warehouseFilter),
    queryFn: () => listPlanningPendingOrders(warehouseFilter || undefined),
  });
  const preloadsQuery = useQuery({
    queryKey: planningKeys.preloads.list(warehouseFilter),
    queryFn: () => listPreloads(warehouseFilter || undefined),
  });

  const planMutation = useMutation({
    mutationFn: (orderId: string) => postPlanOrder(orderId, { mode: planMode, permit_without_stock: permitNoStock }),
    onSuccess: async () => {
      toast.success("Pedido planificado");
      setSelectedOrder(null);
      setError(null);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: planningKeys.stock(warehouseFilter) }),
        queryClient.invalidateQueries({ queryKey: planningKeys.pendingOrders(warehouseFilter) }),
        queryClient.invalidateQueries({ queryKey: logisticsKeys.orders.all() }),
      ]);
    },
  });

  const generateMutation = useMutation({
    mutationFn: () => generatePreload({
      warehouse_id: warehouseFilter || "",
      preload_date: preloadDate,
      notes: null,
    }),
    onSuccess: () => {
      toast.success("Precarga generada");
      setIsPreloadOpen(false);
      setPreloadDate("");
      setError(null);
      queryClient.invalidateQueries({ queryKey: planningKeys.preloads.all() });
      queryClient.invalidateQueries({ queryKey: planningKeys.stock(warehouseFilter) });
    },
  });

  const acceptMutation = useMutation({
    mutationFn: acceptPreload,
    onSuccess: () => {
      toast.success("Precarga aceptada");
      setSelectedPreload(null);
      queryClient.invalidateQueries({ queryKey: planningKeys.preloads.all() });
      queryClient.invalidateQueries({ queryKey: planningKeys.stock(warehouseFilter) });
    },
    onError: () => {
      toast.error("Error al aceptar precarga");
    },
  });

  const cancelPreloadMutation = useMutation({
    mutationFn: cancelPreload,
    onSuccess: () => {
      toast.success("Precarga cancelada");
      setSelectedPreload(null);
      queryClient.invalidateQueries({ queryKey: planningKeys.preloads.all() });
      queryClient.invalidateQueries({ queryKey: planningKeys.stock(warehouseFilter) });
    },
    onError: () => {
      toast.error("Error al cancelar precarga");
    },
  });

  async function handlePlanOrder(orderId: string) {
    setError(null);
    try {
      await planMutation.mutateAsync(orderId);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Error al planificar");
    }
  }

  async function handleGeneratePreload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    try {
      await generateMutation.mutateAsync();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Error al generar precarga");
    }
  }

  const warehousesById = new Map((warehousesQuery.data ?? []).map((warehouse) => [warehouse.id, warehouse]));
  const stockRows = warehouseFilter
    ? buildPlanningStockRows(
        warehouseFilter,
        stockBalancesQuery.data ?? [],
        pendingQuery.data ?? [],
        preloadsQuery.data ?? [],
      )
    : [];
  const stockByProduct = new Map(stockRows.map((item) => [item.product_id, item]));

  return (
    <LogisticsSection
      title="Planificacion (transicion)"
      description="Superficie auxiliar mientras el borrador de jornada absorbe la planificación operativa diaria."
      actions={
        <Button onClick={() => { setIsPreloadOpen(true); setPreloadDate(new Date().toISOString().split("T")[0]); }}>
          Generar precarga
        </Button>
      }
    >
      {error ? <Alert title="Operacion no completada">{error}</Alert> : null}

      <div className="flex flex-wrap gap-3">
        <Select value={warehouseFilter} onChange={(value) => setWarehouseFilter(value)}
          placeholder="Todos los almacenes"
          options={(warehousesQuery.data ?? []).map((wh) => ({ value: wh.id, label: wh.name }))} />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Stock disponible</CardTitle>
          <CardDescription>Resumen por producto con indicador de cobertura.</CardDescription>
        </CardHeader>
        <CardContent>
          <DataTable
            columns={[
              { key: "product", header: "Producto", render: (row) => row.product_name },
              { key: "actual", header: "Actual", render: (row) => String(row.stock_actual) },
              { key: "comprometido", header: "Comprometido", render: (row) => String(row.stock_comprometido) },
              { key: "planificado", header: "Planificado", render: (row) => String(row.stock_planificado) },
              { key: "disponible", header: "Disponible", render: (row) => String(row.stock_disponible) },
              { key: "coverage", header: "Cobertura", render: (row) => <CoverageBadge status={row.coverage_status} /> },
            ]}
            rows={stockRows}
            rowKey={(row) => `${row.product_id}-${row.warehouse_id}`}
            emptyMessage="Selecciona un almacen para ver stock."
          />
        </CardContent>
      </Card>

      <div className="grid gap-6 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Pedidos pendientes</CardTitle>
            <CardDescription>Selecciona un pedido para planificar.</CardDescription>
          </CardHeader>
          <CardContent>
            <DataTable
              columns={[
                { key: "customer", header: "Cliente", render: (row) => row.customer_name },
                {
                  key: "warehouse",
                  header: "Almacen",
                  render: (row) => resolveWarehouseName(warehousesById, row.warehouse_id),
                },
                { key: "status", header: "Estado", render: (row) => row.status },
                { key: "coverage", header: "Cobertura", render: (row) => <CoverageBadge status={row.coverage_status} /> },
                {
                  key: "actions", header: "", className: "w-20",
                  render: (row) => (
                    <Button
                      variant="secondary"
                      onClick={() => {
                        if (row.warehouse_id) {
                          setWarehouseFilter(row.warehouse_id);
                        }
                        setSelectedOrder(row);
                      }}
                    >
                      Planificar
                    </Button>
                  ),
                },
              ]}
              rows={pendingQuery.data ?? []}
              rowKey={(row) => row.order_id}
              emptyMessage="No hay pedidos pendientes."
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Precargas activas</CardTitle>
                <CardDescription>Precargas generadas, aceptadas o pendientes.</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <DataTable
              columns={[
                { key: "date", header: "Fecha", render: (row) => row.preload_date },
                {
                  key: "warehouse",
                  header: "Almacen",
                  render: (row) => resolveWarehouseName(warehousesById, row.warehouse_id),
                },
                { key: "status", header: "Estado", render: (row) => row.status },
                {
                  key: "actions", header: "", className: "w-32",
                  render: (row) => (
                    <div className="flex gap-2">
                      <Button variant="secondary" onClick={() => setSelectedPreload(row)}>Ver</Button>
                      {row.status === "PENDIENTE" ? (
                        <Button onClick={() => acceptMutation.mutate(row.id)}>Aceptar</Button>
                      ) : null}
                    </div>
                  ),
                },
              ]}
              rows={preloadsQuery.data ?? []}
              rowKey={(row) => row.id}
              emptyMessage="No hay precargas."
            />
          </CardContent>
        </Card>
      </div>

      <Dialog
        open={selectedOrder !== null}
        title={selectedOrder ? `Planificar: ${selectedOrder.customer_name}` : ""}
        description="Selecciona modo y ejecuta la planificacion."
        onClose={() => setSelectedOrder(null)}
      >
        {selectedOrder ? (
          <div className="space-y-4">
            <div className="flex flex-wrap gap-3">
              <label className="space-y-1 text-sm text-foreground">
                <span>Modo</span>
                <Select value={planMode} onChange={(value) => setPlanMode(value)}
                  options={[
                    { value: "partial", label: "Parcial" },
                    { value: "full", label: "Completos" },
                    { value: "all", label: "Todo" },
                  ]} />
              </label>
              <div className="flex items-center gap-2 pt-5 text-sm text-foreground">
                <Switch checked={permitNoStock} onChange={(e) => setPermitNoStock(e.target.checked)} />
                <span>Permitir sin stock</span>
              </div>
            </div>
            <DataTable
              columns={[
                { key: "product", header: "Producto", render: (row) => row.product_name },
                { key: "req", header: "Solicitado", render: (row) => String(row.quantity_requested) },
                { key: "planned", header: "Planificado", render: (row) => String(row.quantity_planned) },
                { key: "pending", header: "Pendiente", render: (row) => String(row.quantity_pending) },
                {
                  key: "stock", header: "Stock disp.",
                  render: (row) => {
                    const s = row.product_id ? stockByProduct.get(row.product_id) : null;
                    return s ? String(s.stock_disponible) : "-";
                  },
                },
                {
                  key: "coverage", header: "Cobertura",
                  render: (row) => <CoverageBadge status={row.coverage_status} />,
                },
              ]}
              rows={selectedOrder.items}
              rowKey={(row) => row.order_item_id}
              emptyMessage="Sin lineas"
            />
            <div className="flex justify-end gap-2">
              <Button variant="secondary" onClick={() => setSelectedOrder(null)}>Cancelar</Button>
              <Button onClick={() => handlePlanOrder(selectedOrder.order_id)} disabled={planMutation.isPending}>
                Ejecutar planificacion
              </Button>
            </div>
          </div>
        ) : null}
      </Dialog>

      <Dialog
        open={isPreloadOpen}
        title="Generar precarga"
        description="Crea una precarga para el almacen y fecha seleccionados."
        onClose={() => setIsPreloadOpen(false)}
      >
        <form className="space-y-4" onSubmit={handleGeneratePreload}>
          <label className="block space-y-2 text-sm text-foreground">
            <span>Almacen</span>
            <Select value={warehouseFilter} onChange={(value) => setWarehouseFilter(value)} required
              placeholder="Selecciona almacen"
              options={(warehousesQuery.data ?? []).map((wh) => ({ value: wh.id, label: wh.name }))} />
          </label>
          <label className="block space-y-2 text-sm text-foreground">
            <span>Fecha</span>
            <Input type="date" value={preloadDate} onChange={(e) => setPreloadDate(e.target.value)} required />
          </label>
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setIsPreloadOpen(false)}>Cancelar</Button>
            <Button type="submit" disabled={generateMutation.isPending}>Generar</Button>
          </div>
        </form>
      </Dialog>

      <Dialog
        open={selectedPreload !== null}
        title={selectedPreload ? `Precarga: ${selectedPreload.preload_date}` : ""}
        description={selectedPreload ? `Estado: ${selectedPreload.status} — ${selectedPreload.notes || ""}` : ""}
        onClose={() => setSelectedPreload(null)}
      >
        {selectedPreload ? (
          <div className="space-y-4">
            <DataTable
              columns={[
                { key: "product", header: "Producto", render: (row) => row.product_name || "-" },
                { key: "planned", header: "Planificado", render: (row) => String(row.quantity_planned) },
                { key: "loaded", header: "Cargado", render: (row) => String(row.quantity_loaded) },
              ]}
              rows={selectedPreload.items}
              rowKey={(row) => row.id}
              emptyMessage="Sin items"
            />
            <div className="flex justify-end gap-2">
              {selectedPreload.status === "PENDIENTE" ? (
                <>
                  <Button variant="secondary" onClick={() => cancelPreloadMutation.mutate(selectedPreload.id)}>
                    Cancelar precarga
                  </Button>
                  <Button onClick={() => acceptMutation.mutate(selectedPreload.id)}>
                    Aceptar precarga
                  </Button>
                </>
              ) : (
                <Button variant="secondary" onClick={() => setSelectedPreload(null)}>Cerrar</Button>
              )}
            </div>
          </div>
        ) : null}
      </Dialog>
    </LogisticsSection>
  );
}
