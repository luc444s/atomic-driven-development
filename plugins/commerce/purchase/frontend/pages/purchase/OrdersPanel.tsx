import { useMutation, useQuery, useQueryClient } from "../../../../../../apps/web/src/lib/react-query";
import { FormEvent, useState } from "react";
import {
  closeOrder,
  confirmOrder,
  cancelOrder,
  createOrder,
  listOrders,
  listSuppliers,
} from "../../api";
import type { OrderItemPayload } from "../../types";
import type { ProductListItem } from "../../../../../productos/frontend/types";
import { Button } from "@systutor/shell/ui/button";
import { DataTable } from "@systutor/shell/ui/data-table";
import { Dialog } from "@systutor/shell/ui/dialog";
import { Input } from "@systutor/shell/ui/input";
import { Combobox } from "@systutor/shell/ui/combobox";
import { Badge } from "@systutor/shell/ui/badge";
import { Alert } from "@systutor/shell/ui/alert";
import { CommerceSection } from "../../../../frontend/components";
import { SuppliersCatalogModal } from "../../components/SuppliersCatalogModal";

const STATUS_BADGE: Record<string, string> = {
  DRAFT: "border-border bg-muted text-muted-foreground",
  ORDERED: "border-primary/30 bg-primary/10 text-primary",
  PARTIAL: "border-warning/30 bg-warning/10 text-warning",
  RECEIVED: "border-success/30 bg-success/10 text-success",
  CLOSED: "border-border bg-secondary text-secondary-foreground",
  CANCELLED: "border-destructive/30 bg-destructive/10 text-destructive",
};

const STATUS_LABEL: Record<string, string> = {
  DRAFT: "Borrador",
  ORDERED: "Ordenada",
  PARTIAL: "Parcial",
  RECEIVED: "Recibida",
  CLOSED: "Cerrada",
  CANCELLED: "Cancelada",
};

type OrdersPanelProps = {
  error: string | null;
  setError: (value: string | null) => void;
  products: ProductListItem[];
  onReceiveOrder: (orderId: string) => void;
  onInvoicesOrder: (orderId: string) => void;
  onClaimsOrder: (orderId: string) => void;
  onReturnsOrder: (orderId: string) => void;
};

export function OrdersPanel({ error, setError, products, onReceiveOrder, onInvoicesOrder, onClaimsOrder, onReturnsOrder }: OrdersPanelProps) {
  const queryClient = useQueryClient();
  const [statusFilter, setStatusFilter] = useState("");
  const [page, setPage] = useState(1);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isSuppliersOpen, setIsSuppliersOpen] = useState(false);

  const [createForm, setCreateForm] = useState<{
    supplier_id: string; items: OrderItemPayload[]; notes: string;
  }>({ supplier_id: "", items: [], notes: "" });

  const ordersQuery = useQuery({
    queryKey: ["compras", "orders", { status: statusFilter, page }],
    queryFn: () => listOrders({ status: statusFilter || undefined, limit: 20, offset: (page - 1) * 20 }),
  });
  const suppliersQuery = useQuery({
    queryKey: ["compras", "suppliers"],
    queryFn: () => listSuppliers(),
  });

  const createMut = useMutation({
    mutationFn: () => createOrder({ supplier_id: createForm.supplier_id, items: createForm.items, notes: createForm.notes || null }),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["compras", "orders"] }); setIsCreateOpen(false); setCreateForm({ supplier_id: "", items: [], notes: "" }); setError(null); },
    onError: (err) => setError(err instanceof Error ? err.message : "Error al crear orden"),
  });
  const confirmMut = useMutation({ mutationFn: (id: string) => confirmOrder(id), onSuccess: () => queryClient.invalidateQueries({ queryKey: ["compras", "orders"] }), onError: (err) => setError(err instanceof Error ? err.message : "Error al confirmar") });
  const cancelMut = useMutation({ mutationFn: (id: string) => cancelOrder(id), onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["compras", "orders"] }); setError(null); }, onError: (err) => setError(err instanceof Error ? err.message : "Error al cancelar") });
  const [closeOrderId, setCloseOrderId] = useState<string | null>(null);
  const [closeReason, setCloseReason] = useState("");
  const closeMut = useMutation({
    mutationFn: () => closeOrderId ? closeOrder(closeOrderId, closeReason) : Promise.reject("No order"),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["compras", "orders"] }); setCloseOrderId(null); setCloseReason(""); setError(null); },
    onError: (err) => setError(err instanceof Error ? err.message : "Error al cerrar"),
  });

  function addItem() { setCreateForm(p => ({ ...p, items: [...p.items, { product_id: "", quantity: 1, unit_cost: 0 }] })); }
  function updateItem(i: number, f: string, v: string) { setCreateForm(p => { const items = [...p.items]; items[i] = { ...items[i], [f]: f === "product_id" ? v : Number(v) || 0 }; return { ...p, items }; }); }
  function removeItem(i: number) { setCreateForm(p => ({ ...p, items: p.items.filter((_, j) => j !== i) })); }

  const supplierOptions = (suppliersQuery.data ?? []).map(s => ({ value: s.id, label: s.name }));
  const productOptions = products.map(p => ({ value: p.id, label: `${p.sku} · ${p.name}` }));
  const orders = ordersQuery.data?.items ?? [];
  const total = ordersQuery.data?.total ?? 0;
  const totalPages = Math.ceil(total / 20);

  return (
    <>
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
          <div className="max-w-xs">
            <Combobox
              value={statusFilter}
              onChange={(v) => { setStatusFilter(v); setPage(1); }}
              options={[
                { value: "", label: "Todos" },
                { value: "DRAFT", label: "Borrador" },
                { value: "ORDERED", label: "Confirmada" },
                { value: "PARTIAL", label: "Parcial" },
                { value: "RECEIVED", label: "Recibida" },
                { value: "CANCELLED", label: "Cancelada" },
              ]}
              placeholder="Filtrar por estado"
            />
          </div>
        </div>

        <DataTable
          columns={[
            { key: "supplier", header: "Proveedor", render: (row) => row.supplier?.name ?? "-" },
            { key: "status", header: "Estado", render: (row) => <Badge className={STATUS_BADGE[row.status] ?? ""}>{STATUS_LABEL[row.status] ?? row.status}</Badge> },
            { key: "date", header: "Fecha", render: (row) => row.order_date },
            { key: "actions", header: "Acciones", render: (row) => (
              <div className="flex gap-2">
                {row.status === "DRAFT" ? <Button variant="secondary" onClick={() => confirmMut.mutate(row.id)}>Confirmar</Button> : null}
                {(row.status === "ORDERED" || row.status === "PARTIAL") ? <Button variant="secondary" onClick={() => onReceiveOrder(row.id)}>Recepcionar</Button> : null}
                {(row.status === "RECEIVED" || row.status === "PARTIAL") ? <Button variant="secondary" onClick={() => { setCloseOrderId(row.id); setCloseReason(""); }}>Cerrar</Button> : null}
                {(row.status === "DRAFT" || row.status === "ORDERED" || row.status === "PARTIAL") ? <Button variant="secondary" onClick={() => cancelMut.mutate(row.id)}>Cancelar</Button> : null}
                 {(row.status === "RECEIVED" || row.status === "PARTIAL" || row.status === "CLOSED") ? <Button variant="secondary" onClick={() => onInvoicesOrder(row.id)}>Facturas</Button> : null}
                 <Button variant="secondary" onClick={() => onClaimsOrder(row.id)}>Reclamaciones</Button>
                 {(row.status === "RECEIVED" || row.status === "PARTIAL" || row.status === "CLOSED") ? <Button variant="secondary" onClick={() => onReturnsOrder(row.id)}>Devoluciones</Button> : null}
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

        <Dialog open={closeOrderId !== null} title="Cerrar orden administrativamente" description="El cierre registra diferencias aceptadas. Requiere motivo y es irreversible." onClose={() => { setCloseOrderId(null); setCloseReason(""); }}>
          <form onSubmit={(e) => { e.preventDefault(); if (closeReason.trim()) closeMut.mutate(); }}>
            <div className="space-y-3">
              <label className="block space-y-1 text-sm">
                <span className="text-muted-foreground">Motivo del cierre *</span>
                <textarea
                  className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm"
                  rows={3}
                  value={closeReason}
                  onChange={(e) => setCloseReason(e.target.value)}
                  placeholder="Ej: saldo pendiente aceptado por proveedor incumplido"
                  required
                />
              </label>
              <div className="flex justify-end gap-2">
                <Button type="button" variant="secondary" onClick={() => { setCloseOrderId(null); setCloseReason(""); }}>Cancelar</Button>
                <Button type="submit" disabled={!closeReason.trim() || closeMut.isPending}>Cerrar orden</Button>
              </div>
            </div>
          </form>
        </Dialog>
      </CommerceSection>

      <SuppliersCatalogModal open={isSuppliersOpen} onClose={() => setIsSuppliersOpen(false)} />
    </>
  );
}
