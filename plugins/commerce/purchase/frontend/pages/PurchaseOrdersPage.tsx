import { useMutation, useQuery, useQueryClient } from "../../../../../apps/web/src/lib/react-query";
import { FormEvent, useMemo, useState } from "react";
import {
  confirmOrder,
  cancelOrder,
  createOrder,
  getOrder,
  listOrders,
  listSuppliers,
  listTanks,
  receiveOrder,
} from "../api";
import type { OrderItemPayload, PurchaseOrder } from "../types";
import { Button } from "../../../../../apps/web/src/shared/ui/button";
import { DataTable } from "../../../../../apps/web/src/shared/ui/data-table";
import { Dialog } from "../../../../../apps/web/src/shared/ui/dialog";
import { Input } from "../../../../../apps/web/src/shared/ui/input";
import { Combobox } from "../../../../../apps/web/src/shared/ui/combobox";
import { Badge } from "../../../../../apps/web/src/shared/ui/badge";
import { Alert } from "../../../../../apps/web/src/shared/ui/alert";
import { CommerceSection } from "../../../frontend/components";
import { SupplierManagementDialog } from "../components/SupplierManagementDialog";
import { listAllProducts } from "../../../../productos/frontend/api";

const STATUS_BADGE: Record<string, string> = {
  DRAFT: "bg-muted text-muted-foreground",
  ORDERED: "bg-blue-100 text-blue-800",
  PARTIAL: "bg-yellow-100 text-yellow-800",
  RECEIVED: "bg-green-100 text-green-800",
  CANCELLED: "bg-red-100 text-red-800",
};

export function PurchaseOrdersPage() {
  const queryClient = useQueryClient();
  const [statusFilter, setStatusFilter] = useState("");
  const [page, setPage] = useState(1);
  const [error, setError] = useState<string | null>(null);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isReceiveOpen, setIsReceiveOpen] = useState(false);
  const [isSuppliersOpen, setIsSuppliersOpen] = useState(false);
  const [selectedOrder, setSelectedOrder] = useState<PurchaseOrder | null>(null);

  const [createForm, setCreateForm] = useState<{
    supplier_id: string; items: OrderItemPayload[]; notes: string;
  }>({ supplier_id: "", items: [], notes: "" });

  const [receiveForm, setReceiveForm] = useState<{
    warehouse_id: string; items: { purchase_item_id: string; quantity: number }[]; notes: string; tank_id: string;
  }>({ warehouse_id: "", items: [], notes: "", tank_id: "" });

  const ordersQuery = useQuery({
    queryKey: ["compras", "orders", { status: statusFilter, page }],
    queryFn: () => listOrders({ status: statusFilter || undefined, limit: 20, offset: (page - 1) * 20 }),
  });
  const suppliersQuery = useQuery({
    queryKey: ["compras", "suppliers"],
    queryFn: () => listSuppliers(),
  });
  const productsQuery = useQuery({
    queryKey: ["productos", "all-active"],
    queryFn: () => listAllProducts({ is_active: true }),
  });

  const createMut = useMutation({
    mutationFn: () => createOrder({ supplier_id: createForm.supplier_id, items: createForm.items, notes: createForm.notes || null }),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["compras", "orders"] }); setIsCreateOpen(false); setCreateForm({ supplier_id: "", items: [], notes: "" }); setError(null); },
    onError: (err) => setError(err instanceof Error ? err.message : "Error al crear orden"),
  });
  const confirmMut = useMutation({ mutationFn: (id: string) => confirmOrder(id), onSuccess: () => queryClient.invalidateQueries({ queryKey: ["compras", "orders"] }) });
  const cancelMut = useMutation({ mutationFn: (id: string) => cancelOrder(id), onSuccess: () => queryClient.invalidateQueries({ queryKey: ["compras", "orders"] }) });
  const receiveMut = useMutation({
    mutationFn: () => selectedOrder ? receiveOrder(selectedOrder.id, { warehouse_id: receiveForm.warehouse_id, items: receiveForm.items, notes: receiveForm.notes || null, tank_id: receiveForm.tank_id || null }) : Promise.reject("No order"),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["compras", "orders"] }); setIsReceiveOpen(false); setSelectedOrder(null); setError(null); },
    onError: (err) => setError(err instanceof Error ? err.message : "Error al recepcionar"),
  });

  const receiveProductId = selectedOrder?.items?.[0]?.product_id;
  const tanksQuery = useQuery({
    queryKey: ["compras", "tanks", receiveProductId],
    queryFn: () => listTanks(receiveProductId),
    enabled: isReceiveOpen && Boolean(receiveProductId),
  });
  const tankOptions = (tanksQuery.data ?? []).map(t => ({ value: t.id, label: `${t.serial} · ${t.description} (${t.content_kg?.toFixed(1) ?? 0} kg)` }));

  function openReceiveDialog(orderId: string) {
    getOrder(orderId).then((detail) => {
      setSelectedOrder(detail);
      setReceiveForm({
        warehouse_id: "",
        items: detail.items.filter(i => i.received_qty < i.quantity).map(i => ({ purchase_item_id: i.id, quantity: i.quantity - i.received_qty })),
        notes: "",
        tank_id: "",
      });
      setIsReceiveOpen(true);
    });
  }

  function addItem() { setCreateForm(p => ({ ...p, items: [...p.items, { product_id: "", quantity: 1, unit_cost: 0 }] })); }
  function updateItem(i: number, f: string, v: string) { setCreateForm(p => { const items = [...p.items]; items[i] = { ...items[i], [f]: f === "product_id" ? v : Number(v) || 0 }; return { ...p, items }; }); }
  function removeItem(i: number) { setCreateForm(p => ({ ...p, items: p.items.filter((_, j) => j !== i) })); }

  const supplierOptions = (suppliersQuery.data ?? []).map(s => ({ value: s.id, label: s.name }));
  const productOptions = (productsQuery.data ?? []).map(p => ({ value: p.id, label: `${p.sku} · ${p.name}` }));
  const orders = ordersQuery.data?.items ?? [];
  const total = ordersQuery.data?.total ?? 0;
  const totalPages = Math.ceil(total / 20);

  return (
    <>
      <SupplierManagementDialog open={isSuppliersOpen} onClose={() => { setIsSuppliersOpen(false); setError(null); }} />
      <CommerceSection
        title="Órdenes de compra"
        description="Gestiona órdenes a proveedores, confirma pedidos y recepciona mercadería contra almacenes."
        actions={
          <div className="flex gap-2">
            <Button variant="secondary" onClick={() => setIsSuppliersOpen(true)}>Proveedores</Button>
            <Button onClick={() => { setCreateForm({ supplier_id: "", items: [], notes: "" }); setError(null); setIsCreateOpen(true); }}>Nueva orden</Button>
          </div>
        }
      >
        {error ? <Alert title="Error">{error}</Alert> : null}

        <div className="flex gap-2">
          <select className="rounded-md border border-border bg-surface px-3 py-2 text-sm" value={statusFilter} onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}>
            <option value="">Todos</option>
            <option value="DRAFT">Borrador</option><option value="ORDERED">Confirmada</option><option value="PARTIAL">Parcial</option><option value="RECEIVED">Recibida</option><option value="CANCELLED">Cancelada</option>
          </select>
        </div>

        <DataTable
          columns={[
            { key: "supplier", header: "Proveedor", render: (row) => row.supplier?.name ?? "-" },
            { key: "status", header: "Estado", render: (row) => <Badge className={STATUS_BADGE[row.status] ?? ""}>{row.status}</Badge> },
            { key: "date", header: "Fecha", render: (row) => row.order_date },
            { key: "actions", header: "Acciones", render: (row) => (
              <div className="flex gap-2">
                {row.status === "DRAFT" ? <Button variant="secondary" onClick={() => confirmMut.mutate(row.id)}>Confirmar</Button> : null}
                {(row.status === "ORDERED" || row.status === "PARTIAL") ? <Button variant="secondary" onClick={() => openReceiveDialog(row.id)}>Recepcionar</Button> : null}
                {(row.status === "DRAFT" || row.status === "ORDERED") ? <Button variant="secondary" onClick={() => cancelMut.mutate(row.id)}>Cancelar</Button> : null}
              </div>
            )},
          ]}
          rows={orders} rowKey={(row) => row.id} emptyMessage="No hay órdenes de compra."
        />

        {totalPages > 1 ? (
          <div className="flex justify-center gap-2">
            <Button variant="secondary" disabled={page <= 1} onClick={() => setPage(page - 1)}>Anterior</Button>
            <span className="px-3 py-2 text-sm">{page} / {totalPages}</span>
            <Button variant="secondary" disabled={page >= totalPages} onClick={() => setPage(page + 1)}>Siguiente</Button>
          </div>
        ) : null}

        <Dialog open={isCreateOpen} title="Nueva orden de compra" description="Selecciona proveedor y agrega productos." onClose={() => setIsCreateOpen(false)}>
          <form className="space-y-4" onSubmit={(e: FormEvent) => { e.preventDefault(); createMut.mutate(); }}>
            <label className="block space-y-2 text-sm text-foreground"><span>Proveedor</span>
              <Combobox value={createForm.supplier_id} onChange={(v) => setCreateForm(p => ({ ...p, supplier_id: v }))} options={supplierOptions} placeholder="Seleccionar proveedor" searchPlaceholder="Buscar proveedor" />
            </label>
            <div className="space-y-2">
              <div className="flex items-center justify-between"><span className="text-sm text-foreground">Productos</span><Button type="button" variant="secondary" onClick={addItem}>+ Agregar</Button></div>
              {createForm.items.map((item, i) => (
                <div key={i} className="grid grid-cols-[1fr_80px_100px_40px] gap-2">
                  <Combobox value={item.product_id} onChange={(v) => updateItem(i, "product_id", v)} options={productOptions} placeholder="Buscar producto" searchPlaceholder="SKU o nombre" />
                  <Input value={item.quantity || ""} onChange={(e) => updateItem(i, "quantity", e.target.value)} placeholder="Cant." />
                  <Input value={item.unit_cost || ""} onChange={(e) => updateItem(i, "unit_cost", e.target.value)} placeholder="Costo" />
                  <Button type="button" variant="secondary" onClick={() => removeItem(i)}>X</Button>
                </div>
              ))}
            </div>
            <label className="block space-y-2 text-sm text-foreground"><span>Notas</span><Input value={createForm.notes} onChange={(e) => setCreateForm(p => ({ ...p, notes: e.target.value }))} /></label>
            <div className="flex justify-end gap-3">
              <Button type="button" variant="secondary" onClick={() => setIsCreateOpen(false)}>Cancelar</Button>
              <Button type="submit" disabled={createMut.isPending}>{createMut.isPending ? "Creando..." : "Crear orden"}</Button>
            </div>
          </form>
        </Dialog>

        <Dialog open={isReceiveOpen} title="Recepcionar mercadería" description="Selecciona almacén y confirma cantidades." onClose={() => { setIsReceiveOpen(false); setSelectedOrder(null); }}>
          <form className="space-y-4" onSubmit={(e: FormEvent) => { e.preventDefault(); receiveMut.mutate(); }}>
            <label className="block space-y-2 text-sm text-foreground"><span>Almacén ID</span><Input value={receiveForm.warehouse_id} onChange={(e) => setReceiveForm(p => ({ ...p, warehouse_id: e.target.value }))} placeholder="ID del almacén" /></label>
            {tankOptions.length > 0 ? (
              <label className="block space-y-2 text-sm text-foreground">
                <span>Tanque criogénico destino</span>
                <Combobox value={receiveForm.tank_id} onChange={(v) => setReceiveForm(p => ({ ...p, tank_id: v }))}
                  options={tankOptions} placeholder="Seleccionar tanque (opcional)" searchPlaceholder="Buscar tanque" />
              </label>
            ) : null}
            <div className="space-y-2"><span className="text-sm text-foreground">Items a recibir</span>
              {receiveForm.items.map((item, i) => (
                <div key={i} className="flex items-center gap-2">
                  <span className="text-sm flex-1">Item {item.purchase_item_id.slice(0, 8)}...</span>
                  <Input className="w-24" value={item.quantity || ""} onChange={(e) => { const items = [...receiveForm.items]; items[i] = { ...items[i], quantity: Number(e.target.value) || 0 }; setReceiveForm(p => ({ ...p, items })); }} />
                </div>
              ))}
            </div>
            <label className="block space-y-2 text-sm text-foreground"><span>Notas</span><Input value={receiveForm.notes} onChange={(e) => setReceiveForm(p => ({ ...p, notes: e.target.value }))} /></label>
            <div className="flex justify-end gap-3">
              <Button type="button" variant="secondary" onClick={() => { setIsReceiveOpen(false); setSelectedOrder(null); }}>Cancelar</Button>
              <Button type="submit" disabled={receiveMut.isPending}>{receiveMut.isPending ? "Recepcionando..." : "Recepcionar"}</Button>
            </div>
          </form>
        </Dialog>
      </CommerceSection>
    </>
  );
}
