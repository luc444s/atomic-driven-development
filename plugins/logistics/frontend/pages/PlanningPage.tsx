import { FormEvent, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "../../../../apps/web/src/lib/react-query";

import {
  acceptPreload,
  cancelPreload,
  generatePreload,
  getPlanningStock,
  listPlanningPendingOrders,
  listPreloads,
  listWarehouses,
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
import { Input } from "../../../../apps/web/src/shared/ui/input";

const controlClassName =
  "w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-50 outline-none transition focus:border-cyan-500";

const COVERAGE_COLORS: Record<string, string> = {
  verde: "text-emerald-400",
  amarillo: "text-amber-400",
  rojo: "text-rose-400",
};

function CoverageBadge({ status }: { status: string }) {
  return <Badge className={COVERAGE_COLORS[status] || "text-slate-400"}>{status}</Badge>;
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
  const stockQuery = useQuery({
    queryKey: planningKeys.stock(warehouseFilter),
    queryFn: () => getPlanningStock(warehouseFilter || undefined),
  });
  const pendingQuery = useQuery({
    queryKey: planningKeys.pendingOrders(),
    queryFn: listPlanningPendingOrders,
  });
  const preloadsQuery = useQuery({
    queryKey: planningKeys.preloads.list(),
    queryFn: listPreloads,
  });

  const planMutation = useMutation({
    mutationFn: (orderId: string) => postPlanOrder(orderId, { mode: planMode, permit_without_stock: permitNoStock }),
    onSuccess: async () => {
      setSelectedOrder(null);
      setError(null);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: planningKeys.stock(warehouseFilter) }),
        queryClient.invalidateQueries({ queryKey: planningKeys.pendingOrders() }),
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
      setIsPreloadOpen(false);
      setPreloadDate("");
      setError(null);
      queryClient.invalidateQueries({ queryKey: planningKeys.preloads.all() });
    },
  });

  const acceptMutation = useMutation({
    mutationFn: acceptPreload,
    onSuccess: () => {
      setSelectedPreload(null);
      queryClient.invalidateQueries({ queryKey: planningKeys.preloads.all() });
    },
  });

  const cancelPreloadMutation = useMutation({
    mutationFn: cancelPreload,
    onSuccess: () => {
      setSelectedPreload(null);
      queryClient.invalidateQueries({ queryKey: planningKeys.preloads.all() });
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

  const stockByProduct = new Map(
    (stockQuery.data ?? []).map((item) => [item.product_id, item])
  );

  return (
    <LogisticsSection
      title="Planificacion"
      description="Stock disponible, pedidos pendientes, planificacion y precargas."
      actions={
        <Button onClick={() => { setIsPreloadOpen(true); setPreloadDate(new Date().toISOString().split("T")[0]); }}>
          Generar precarga
        </Button>
      }
    >
      {error ? <Alert title="Operacion no completada">{error}</Alert> : null}

      <div className="flex flex-wrap gap-3">
        <select className={controlClassName} value={warehouseFilter} onChange={(e) => setWarehouseFilter(e.target.value)}>
          <option value="">Todos los almacenes</option>
          {(warehousesQuery.data ?? []).map((wh) => (
            <option key={wh.id} value={wh.id}>{wh.name}</option>
          ))}
        </select>
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
            rows={stockQuery.data ?? []}
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
                { key: "warehouse", header: "Almacen", render: (row) => row.warehouse_id || "-" },
                { key: "status", header: "Estado", render: (row) => row.status },
                { key: "coverage", header: "Cobertura", render: (row) => <CoverageBadge status={row.coverage_status} /> },
                {
                  key: "actions", header: "", className: "w-20",
                  render: (row) => (
                    <Button variant="secondary" onClick={() => setSelectedOrder(row)}>Planificar</Button>
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
                { key: "warehouse", header: "Almacen", render: (row) => row.warehouse_id },
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
              <label className="space-y-1 text-sm text-slate-300">
                <span>Modo</span>
                <select className={controlClassName} value={planMode} onChange={(e) => setPlanMode(e.target.value)}>
                  <option value="partial">Parcial</option>
                  <option value="full">Completos</option>
                  <option value="all">Todo</option>
                </select>
              </label>
              <label className="flex items-center gap-2 pt-5 text-sm text-slate-300">
                <input type="checkbox" checked={permitNoStock} onChange={(e) => setPermitNoStock(e.target.checked)} />
                Permitir sin stock
              </label>
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
          <label className="block space-y-2 text-sm text-slate-300">
            <span>Almacen</span>
            <select className={controlClassName} value={warehouseFilter} onChange={(e) => setWarehouseFilter(e.target.value)} required>
              <option value="">Selecciona almacen</option>
              {(warehousesQuery.data ?? []).map((wh) => (
                <option key={wh.id} value={wh.id}>{wh.name}</option>
              ))}
            </select>
          </label>
          <label className="block space-y-2 text-sm text-slate-300">
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
                { key: "product", header: "Producto", render: (row) => row.product_name || row.product_id },
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
