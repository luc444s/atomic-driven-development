import { useMutation, useQuery, useQueryClient } from "../../../../../apps/web/src/lib/react-query";
import { FormEvent, useMemo, useState } from "react";
import {
  annulClaim,
  closeOrder,
  confirmOrder,
  cancelOrder,
  cancelInvoice,
  commercialCloseReceipt,
  createClaim,
  createInvoice,
  createOrder,
  getClaim,
  getOrder,
  getReconciliation,
  listClaims,
  listDispatches,
  listInvoices,
  listOrders,
  listSuppliers,
  listTanks,
  receiveOrder,
  resolveClaim,
  startClaim,
} from "../api";
import { SuppliersCatalogModal } from "../components/SuppliersCatalogModal";
import { listWarehouses, getRealWarehouses } from "../../../../logistics/frontend/api/warehouses";
import type {
  CommercialClosePayload,
  CreateClaimPayload,
  CreateInvoicePayload,
  OrderItemPayload,
  PurchaseOrder,
  ReceiveCostLine,
  Reconciliation,
  SupplierClaim,
  SupplierClaimDetail,
  SupplierInvoice,
} from "../types";
import { Button } from "@systutor/shell/ui/button";
import { DataTable } from "@systutor/shell/ui/data-table";
import { Dialog } from "@systutor/shell/ui/dialog";
import { Input } from "@systutor/shell/ui/input";
import { Combobox } from "@systutor/shell/ui/combobox";
import { Badge } from "@systutor/shell/ui/badge";
import { Alert } from "@systutor/shell/ui/alert";
import { CommerceSection } from "../../../frontend/components";
import { listAllProducts } from "../../../../productos/frontend/api";

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

const CLAIM_REASON_LABEL: Record<string, string> = {
  FALTANTE: "Faltante", PRODUCTO_INCORRECTO: "Producto incorrecto",
  MALA_CALIDAD: "Mala calidad", CILINDRO_DANADO: "Cilindro dañado",
  SERVICIO_INCOMPLETO: "Servicio incompleto", SERVICIO_DEFECTUOSO: "Servicio defectuoso",
  PRECIO_INCORRECTO: "Precio incorrecto", DOCUMENTO_INCORRECTO: "Documento incorrecto",
  DEMORA: "Demora", PERDIDA_ENVASE: "Pérdida de envase", DANO_EN_CUSTODIA: "Daño en custodia",
};

const CLAIM_REASON_OPTIONS = Object.entries(CLAIM_REASON_LABEL).map(([value, label]) => ({ value, label }));const CLAIM_STATUS_BADGE: Record<string, string> = {
  ABIERTA: "border-warning/30 bg-warning/10 text-warning",
  EN_GESTION: "border-primary/30 bg-primary/10 text-primary",
  RESUELTA: "border-success/30 bg-success/10 text-success",
  ANULADA: "border-border bg-muted text-muted-foreground",
};

const CLAIM_STATUS_LABEL: Record<string, string> = {
  ABIERTA: "Abierta",
  EN_GESTION: "En gestión",
  RESUELTA: "Resuelta",
  ANULADA: "Anulada",
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
    warehouse_id: string; items: { purchase_item_id: string; quantity: number; qty_accepted?: number; qty_rejected?: number }[]; notes: string; tank_id: string; dispatch_id: string; cost_lines: ReceiveCostLine[];
  }>({ warehouse_id: "", items: [], notes: "", tank_id: "", dispatch_id: "", cost_lines: [] });

  const [isInvoicesOpen, setIsInvoicesOpen] = useState(false);
  const [invoiceOrder, setInvoiceOrder] = useState<PurchaseOrder | null>(null);
  const [invoiceForm, setInvoiceForm] = useState<CreateInvoicePayload>({ invoice_number: "", invoice_date: "", tax: 0, lines: [] });
  const [reconciliation, setReconciliation] = useState<Reconciliation | null>(null);

  const [isClaimsOpen, setIsClaimsOpen] = useState(false);
  const [claimsOrder, setClaimsOrder] = useState<PurchaseOrderDetail | null>(null);
  const [claimForm, setClaimForm] = useState<CreateClaimPayload>({ reason: "", description: "" });
  const [expandedClaimId, setExpandedClaimId] = useState<string | null>(null);
  const [claimTimeline, setClaimTimeline] = useState<Record<string, SupplierClaimDetail>>({});
  const [resolveNotes, setResolveNotes] = useState("");
  const [annulReason, setAnnulReason] = useState("");

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
  const confirmMut = useMutation({ mutationFn: (id: string) => confirmOrder(id), onSuccess: () => queryClient.invalidateQueries({ queryKey: ["compras", "orders"] }), onError: (err) => setError(err instanceof Error ? err.message : "Error al confirmar") });
  const cancelMut = useMutation({ mutationFn: (id: string) => cancelOrder(id), onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["compras", "orders"] }); setError(null); }, onError: (err) => setError(err instanceof Error ? err.message : "Error al cancelar") });
  const [closeOrderId, setCloseOrderId] = useState<string | null>(null);
  const [closeReason, setCloseReason] = useState("");
  const closeMut = useMutation({
    mutationFn: () => closeOrderId ? closeOrder(closeOrderId, closeReason) : Promise.reject("No order"),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["compras", "orders"] }); setCloseOrderId(null); setCloseReason(""); setError(null); },
    onError: (err) => setError(err instanceof Error ? err.message : "Error al cerrar"),
  });
  const receiveMut = useMutation({
    mutationFn: () => selectedOrder ? receiveOrder(selectedOrder.id, { warehouse_id: receiveForm.warehouse_id, items: receiveForm.items, notes: receiveForm.notes || null, tank_id: receiveForm.tank_id || null, dispatch_id: receiveForm.dispatch_id || null, cost_lines: receiveForm.cost_lines.length ? receiveForm.cost_lines : null }) : Promise.reject("No order"),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["compras", "orders"] }); setIsReceiveOpen(false); setSelectedOrder(null); setError(null); },
    onError: (err) => setError(err instanceof Error ? err.message : "Error al recepcionar"),
  });

  const invoiceCreateMut = useMutation({
    mutationFn: () => invoiceOrder ? createInvoice(invoiceOrder.id, invoiceForm) : Promise.reject("No order"),
    onSuccess: () => { setInvoiceForm({ invoice_number: "", invoice_date: "", tax: 0, lines: [] }); setReconciliation(null); queryClient.invalidateQueries({ queryKey: ["compras", "orders"] }); },
    onError: (err) => setError(err instanceof Error ? err.message : "Error al registrar factura"),
  });
  const invoiceCancelMut = useMutation({
    mutationFn: (id: string) => cancelInvoice(id),
    onSuccess: () => { setReconciliation(null); queryClient.invalidateQueries({ queryKey: ["compras", "orders"] }); },
    onError: (err) => setError(err instanceof Error ? err.message : "Error al anular factura"),
  });

  const invoicesQuery = useQuery({
    queryKey: ["compras", "invoices", invoiceOrder?.id],
    queryFn: () => listInvoices(invoiceOrder!.id),
    enabled: isInvoicesOpen && Boolean(invoiceOrder),
  });

  function openInvoicesDialog(orderId: string) {
    getOrder(orderId).then((detail) => {
      setInvoiceOrder(detail);
      setInvoiceForm({
        invoice_number: "",
        invoice_date: new Date().toISOString().slice(0, 10),
        tax: 0,
        lines: detail.items.map((i) => ({
          order_item_id: i.id,
          qty: Math.max(0, Number((i.quantity - i.received_qty).toFixed(2))),
          unit_price: i.unit_cost,
        })),
      });
      setReconciliation(null);
      setIsInvoicesOpen(true);
    });
  }

  function runReconcile() {
    if (!invoiceOrder) return;
    getReconciliation(invoiceOrder.id)
      .then(setReconciliation)
      .catch((err) => setError(err instanceof Error ? err.message : "Error al conciliar"));
  }

  function updateInvoiceLine(i: number, f: string, v: string) {
    setInvoiceForm((p) => {
      const lines = [...p.lines];
      lines[i] = { ...lines[i], [f]: f === "order_item_id" ? v : Number(v) || 0 };
      return { ...p, lines };
    });
  }

  const claimsQuery = useQuery({
    queryKey: ["compras", "claims", claimsOrder?.id],
    queryFn: () => listClaims(claimsOrder!.id),
    enabled: isClaimsOpen && Boolean(claimsOrder),
  });
  const claimInvoicesQuery = useQuery({
    queryKey: ["compras", "invoices", claimsOrder?.id],
    queryFn: () => listInvoices(claimsOrder!.id),
    enabled: isClaimsOpen && Boolean(claimsOrder),
  });

  function invalidateClaims() { queryClient.invalidateQueries({ queryKey: ["compras", "claims"] }); setError(null); }
  function refreshClaimDetail(claimId: string) {
    if (!claimsOrder) return;
    getClaim(claimsOrder.id, claimId).then((d) => setClaimTimeline(p => ({ ...p, [claimId]: d })));
  }
  function toggleClaimTimeline(claimId: string) { if (expandedClaimId === claimId) setExpandedClaimId(null); else { setExpandedClaimId(claimId); refreshClaimDetail(claimId); } }

  function openClaimsDialog(orderId: string) {
    getOrder(orderId).then((detail) => {
      setClaimsOrder(detail);
      setExpandedClaimId(null); setClaimTimeline({}); setResolveNotes(""); setAnnulReason("");
      setIsClaimsOpen(true);
    });
  }

  const claimCreateMut = useMutation({
    mutationFn: () => claimsOrder ? createClaim(claimsOrder.id, { reason: claimForm.reason, description: claimForm.description, receipt_id: claimForm.receipt_id || null, invoice_id: claimForm.invoice_id || null }) : Promise.reject("No order"),
    onSuccess: () => { setClaimForm({ reason: "", description: "" }); invalidateClaims(); },
    onError: (err) => setError(err instanceof Error ? err.message : "Error al registrar reclamación"),
  });
  const claimStartMut = useMutation({
    mutationFn: (id: string) => startClaim(claimsOrder!.id, id),
    onSuccess: (_d, id) => { invalidateClaims(); refreshClaimDetail(id); },
    onError: (err) => setError(err instanceof Error ? err.message : "Error al iniciar reclamación"),
  });
  const claimResolveMut = useMutation({
    mutationFn: (id: string) => resolveClaim(claimsOrder!.id, id, resolveNotes),
    onSuccess: (_d, id) => { setResolveNotes(""); invalidateClaims(); refreshClaimDetail(id); },
    onError: (err) => setError(err instanceof Error ? err.message : "Error al resolver reclamación"),
  });
  const claimAnnulMut = useMutation({
    mutationFn: (id: string) => annulClaim(claimsOrder!.id, id, annulReason),
    onSuccess: (_d, id) => { setAnnulReason(""); invalidateClaims(); refreshClaimDetail(id); },
    onError: (err) => setError(err instanceof Error ? err.message : "Error al anular reclamación"),
  });

  const receiveProductId = selectedOrder?.items?.[0]?.product_id;
  const tanksQuery = useQuery({
    queryKey: ["compras", "tanks", receiveProductId],
    queryFn: () => listTanks(receiveProductId),
    enabled: isReceiveOpen && Boolean(receiveProductId),
  });
  const tankOptions = (tanksQuery.data ?? []).map(t => ({ value: t.id, label: `${t.serial} · ${t.description} (${t.content_kg?.toFixed(1) ?? 0} kg)` }));

  const warehousesQuery = useQuery({
    queryKey: ["logistics", "warehouses"],
    queryFn: listWarehouses,
  });
  const warehouseOptions = getRealWarehouses(warehousesQuery.data ?? []).map(w => ({
    value: w.id,
    label: `${w.code} · ${w.name}`,
  }));

  const orderDispatchesQuery = useQuery({
    queryKey: ["compras", "dispatches", { order_id: selectedOrder?.id }],
    queryFn: () => listDispatches({ order_id: selectedOrder!.id, limit: 50 }),
    enabled: isReceiveOpen && Boolean(selectedOrder),
  });
  const orderDispatchOptions = (orderDispatchesQuery.data?.items ?? []).map(d => ({
    value: d.id,
    label: `${d.dispatch_date} · ${d.status}${d.carrier ? ` · ${d.carrier}` : ""}`,
  }));

  const claimReceiptOptions = (claimsOrder?.receipts ?? []).map((r) => ({
    value: r.id,
    label: `${r.receipt_date}${r.difference_type ? ` · ${r.difference_type}` : ""}`,
  }));
  const claimInvoiceOptions = (claimInvoicesQuery.data ?? []).map((iv) => ({
    value: iv.id,
    label: `${iv.invoice_number} · ${iv.invoice_date}`,
  }));

  function openReceiveDialog(orderId: string) {
    getOrder(orderId).then((detail) => {
      setSelectedOrder(detail);
      setReceiveForm({
        warehouse_id: "",
        items: detail.items.filter(i => i.received_qty < i.quantity).map(i => {
          const pending = i.quantity - i.received_qty;
          return { purchase_item_id: i.id, quantity: pending, qty_accepted: pending, qty_rejected: 0 };
        }),
        notes: "",
        tank_id: "",
        dispatch_id: "",
        cost_lines: [],
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
                {(row.status === "ORDERED" || row.status === "PARTIAL") ? <Button variant="secondary" onClick={() => openReceiveDialog(row.id)}>Recepcionar</Button> : null}
                {(row.status === "RECEIVED" || row.status === "PARTIAL") ? <Button variant="secondary" onClick={() => { setCloseOrderId(row.id); setCloseReason(""); }}>Cerrar</Button> : null}
                {(row.status === "DRAFT" || row.status === "ORDERED" || row.status === "PARTIAL") ? <Button variant="secondary" onClick={() => cancelMut.mutate(row.id)}>Cancelar</Button> : null}
                {(row.status === "RECEIVED" || row.status === "PARTIAL" || row.status === "CLOSED") ? <Button variant="secondary" onClick={() => openInvoicesDialog(row.id)}>Facturas</Button> : null}
                <Button variant="secondary" onClick={() => openClaimsDialog(row.id)}>Reclamaciones</Button>
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
            <label className="block space-y-2 text-sm text-foreground"><span>Almacén destino *</span><Combobox value={receiveForm.warehouse_id} onChange={(v) => setReceiveForm(p => ({ ...p, warehouse_id: v }))} options={warehouseOptions} placeholder="Seleccionar almacén" searchPlaceholder="Buscar almacén" /></label>
            {tankOptions.length > 0 ? (
              <label className="block space-y-2 text-sm text-foreground">
                <span>Tanque criogénico destino</span>
                <Combobox value={receiveForm.tank_id} onChange={(v) => setReceiveForm(p => ({ ...p, tank_id: v }))}
                  options={tankOptions} placeholder="Seleccionar tanque (opcional)" searchPlaceholder="Buscar tanque" />
              </label>
            ) : null}
            {orderDispatchOptions.length > 0 ? (
              <label className="block space-y-2 text-sm text-foreground">
                <span>Despacho asociado</span>
                <Combobox value={receiveForm.dispatch_id} onChange={(v) => setReceiveForm(p => ({ ...p, dispatch_id: v }))}
                  options={orderDispatchOptions} placeholder="Sin despacho (opcional)" searchPlaceholder="Buscar despacho" />
              </label>
            ) : null}
            <div className="space-y-2"><span className="text-sm text-foreground">Items a recibir</span>
              {receiveForm.items.map((item, i) => {
                const orderItem = selectedOrder?.items.find(oi => oi.id === item.purchase_item_id);
                const product = productsQuery.data?.find(p => p.id === orderItem?.product_id);
                const accepted = item.qty_accepted ?? item.quantity;
                const rejected = item.qty_rejected ?? 0;
                const sum = Number(accepted) + Number(rejected);
                const sumOk = sum === Number(item.quantity);
                return (
                  <div key={i} className="grid grid-cols-[1fr_70px_70px_70px] gap-2 items-center">
                    <span className="text-sm flex-1">{product ? `${product.sku} · ${product.name}` : `Producto ${orderItem?.product_id?.slice(0, 8) ?? "desconocido"}`}</span>
                    <Input className="w-20" value={item.quantity || ""} onChange={(e) => { const items = [...receiveForm.items]; items[i] = { ...items[i], quantity: Number(e.target.value) || 0 }; setReceiveForm(p => ({ ...p, items })); }} title="Recibidas" />
                    <Input className="w-20" value={accepted} onChange={(e) => { const items = [...receiveForm.items]; items[i] = { ...items[i], qty_accepted: Number(e.target.value) || 0 }; setReceiveForm(p => ({ ...p, items })); }} title="Aceptadas" />
                    <Input className="w-20" value={rejected} onChange={(e) => { const items = [...receiveForm.items]; items[i] = { ...items[i], qty_rejected: Number(e.target.value) || 0 }; setReceiveForm(p => ({ ...p, items })); }} title="Rechazadas" />
                    {!sumOk ? <span className="text-xs text-destructive">acep+rech≠recib</span> : null}
                  </div>
                );
              })}
              <p className="text-xs text-muted-foreground">Columnas: Recibidas · Aceptadas · Rechazadas</p>
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between"><span className="text-sm text-foreground">Costos adicionales</span><Button type="button" variant="secondary" onClick={() => setReceiveForm(p => ({ ...p, cost_lines: [...p.cost_lines, { cost_type: "FLETE", amount: 0 }] }))}>+ Agregar</Button></div>
              {receiveForm.cost_lines.map((cl, i) => (
                <div key={i} className="grid grid-cols-[120px_100px_1fr_40px] gap-2">
                  <Input value={cl.cost_type} onChange={(e) => { const cs = [...receiveForm.cost_lines]; cs[i] = { ...cs[i], cost_type: e.target.value }; setReceiveForm(p => ({ ...p, cost_lines: cs })); }} placeholder="FLETE" />
                  <Input value={cl.amount || ""} onChange={(e) => { const cs = [...receiveForm.cost_lines]; cs[i] = { ...cs[i], amount: Number(e.target.value) || 0 }; setReceiveForm(p => ({ ...p, cost_lines: cs })); }} placeholder="Monto" />
                  <Input value={cl.notes ?? ""} onChange={(e) => { const cs = [...receiveForm.cost_lines]; cs[i] = { ...cs[i], notes: e.target.value }; setReceiveForm(p => ({ ...p, cost_lines: cs })); }} placeholder="Notas" />
                  <Button type="button" variant="secondary" onClick={() => setReceiveForm(p => ({ ...p, cost_lines: p.cost_lines.filter((_, j) => j !== i) }))}>X</Button>
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
        <Dialog open={isInvoicesOpen} title="Facturas de proveedor y conciliación" description="Registra la factura del proveedor y concilia orden ↔ recibido ↔ facturado." onClose={() => { setIsInvoicesOpen(false); setInvoiceOrder(null); setReconciliation(null); }}>
          <div className="space-y-4">
            <Button variant="secondary" onClick={runReconcile}>Conciliar</Button>
            {reconciliation ? (
              <div className="space-y-2 rounded-md border border-border p-3">
                <div className="text-sm font-medium">Tres vías: <Badge className={reconciliation.totals.status === "MATCH" ? "border-success/30 bg-success/10 text-success" : "border-destructive/30 bg-destructive/10 text-destructive"}>{reconciliation.totals.status}</Badge> {reconciliation.invoice_status ? <span className="ml-2 text-success">Factura {reconciliation.invoice_status}</span> : null}</div>
                <div className="text-xs text-muted-foreground">Pedido {reconciliation.totals.ordered.toFixed(2)} · Real {reconciliation.totals.real.toFixed(2)} · Facturado {reconciliation.totals.invoiced.toFixed(2)}</div>
                {reconciliation.by_item.map((it, idx) => (
                  <div key={idx} className="text-xs flex gap-2">
                    <span className="w-16"><Badge className={it.status === "MATCH" ? "border-success/30 bg-success/10 text-success" : "border-destructive/30 bg-destructive/10 text-destructive"}>{it.status}</Badge></span>
                    <span>Ped {it.ordered_qty} · Acep {it.accepted_qty} · Fact {it.invoiced_qty} · Real {it.real_cost.toFixed(2)} · Fact {it.invoiced_cost.toFixed(2)}</span>
                  </div>
                ))}
              </div>
            ) : null}

            <div className="space-y-2">
              <span className="text-sm text-foreground">Facturas registradas</span>
              {(invoicesQuery.data ?? []).map((inv: SupplierInvoice) => (
                <div key={inv.id} className="flex items-center justify-between rounded-md border border-border p-2 text-sm">
                  <span>{inv.invoice_number} · {inv.invoice_date} · {inv.total.toFixed(2)} {inv.currency} <Badge className="ml-2">{inv.status}</Badge></span>
                  {inv.status !== "ANULADA" ? <Button variant="secondary" onClick={() => invoiceCancelMut.mutate(inv.id)}>Anular</Button> : null}
                </div>
              ))}
              {!(invoicesQuery.data ?? []).length ? <p className="text-xs text-muted-foreground">Sin facturas.</p> : null}
            </div>

            <form className="space-y-2 border-t border-border pt-3" onSubmit={(e: FormEvent) => { e.preventDefault(); invoiceCreateMut.mutate(); }}>
              <span className="text-sm text-foreground">Nueva factura</span>
              <div className="grid grid-cols-[1fr_140px_100px] gap-2">
                <Input value={invoiceForm.invoice_number} onChange={(e) => setInvoiceForm(p => ({ ...p, invoice_number: e.target.value }))} placeholder="Folio *" />
                <Input value={invoiceForm.invoice_date} onChange={(e) => setInvoiceForm(p => ({ ...p, invoice_date: e.target.value }))} placeholder="Fecha" />
                <Input value={invoiceForm.tax || ""} onChange={(e) => setInvoiceForm(p => ({ ...p, tax: Number(e.target.value) || 0 }))} placeholder="Impuesto" />
              </div>
              {invoiceForm.lines.map((ln, i) => {
                const orderItem = invoiceOrder?.items.find(oi => oi.id === ln.order_item_id);
                const product = productsQuery.data?.find(p => p.id === orderItem?.product_id);
                return (
                  <div key={i} className="grid grid-cols-[1fr_80px_100px] gap-2 items-center">
                    <span className="text-xs flex-1">{product ? `${product.sku} · ${product.name}` : "Item"}</span>
                    <Input value={ln.qty || ""} onChange={(e) => updateInvoiceLine(i, "qty", e.target.value)} placeholder="Cant" />
                    <Input value={ln.unit_price || ""} onChange={(e) => updateInvoiceLine(i, "unit_price", e.target.value)} placeholder="P.Unit" />
                  </div>
                );
              })}
              <div className="flex justify-end gap-3">
                <Button type="submit" disabled={invoiceCreateMut.isPending || !invoiceForm.invoice_number}>{invoiceCreateMut.isPending ? "Guardando..." : "Registrar factura"}</Button>
              </div>
            </form>
          </div>
        </Dialog>

        <Dialog open={isClaimsOpen} title="Reclamaciones al proveedor" description={`Orden ${claimsOrder ? claimsOrder.id.slice(0, 8) : ""} · Seguimiento hasta su resolución.`} onClose={() => { setIsClaimsOpen(false); setClaimsOrder(null); setExpandedClaimId(null); }}>
          <div className="space-y-4">
            <div className="space-y-2">
              <span className="text-sm text-foreground">Reclamaciones registradas</span>
              {(claimsQuery.data ?? []).map((cl: SupplierClaim) => (
                <div key={cl.id} className="rounded-md border border-border p-2 text-sm space-y-1">
                  <div className="flex items-center justify-between gap-2">
                    <span className="flex items-center gap-2">
                      <Badge className={CLAIM_STATUS_BADGE[cl.status] ?? ""}>{CLAIM_STATUS_LABEL[cl.status] ?? cl.status}</Badge>
                      <span>{CLAIM_REASON_LABEL[cl.reason] ?? cl.reason}</span>
                    </span>
                    <div className="flex gap-2">
                      {cl.status === "ABIERTA" ? <Button variant="secondary" onClick={() => claimStartMut.mutate(cl.id)}>Iniciar</Button> : null}
                      <Button variant="secondary" onClick={() => toggleClaimTimeline(cl.id)}>{expandedClaimId === cl.id ? "Cerrar" : "Historial"}</Button>
                    </div>
                  </div>
                  <p className="text-xs text-muted-foreground">{cl.description}{cl.receipt_id ? ` · Recepción ${cl.receipt_id.slice(0, 8)}` : ""}{cl.invoice_id ? ` · Factura ${cl.invoice_id.slice(0, 8)}` : ""}</p>
                  {expandedClaimId === cl.id ? (
                    <div className="border-t border-border pt-2 space-y-2">
                      <ol className="text-xs space-y-1">
                        {(claimTimeline[cl.id]?.events ?? []).map((ev) => (
                          <li key={ev.id}>{ev.from_status ?? "Alta"} → <Badge className={CLAIM_STATUS_BADGE[ev.to_status] ?? ""}>{CLAIM_STATUS_LABEL[ev.to_status] ?? ev.to_status}</Badge>{ev.reason ? ` · ${ev.reason}` : ""}</li>
                        ))}
                        {!claimTimeline[cl.id] ? <li className="text-muted-foreground">Cargando…</li> : null}
                      </ol>
                      {cl.status === "RESUELTA" && cl.resolution_notes ? <p className="text-xs">Resolución: {cl.resolution_notes}</p> : null}
                      {(cl.status === "ABIERTA" || cl.status === "EN_GESTION") ? (
                        <div className="grid grid-cols-[1fr_140px_auto_auto] gap-2 items-center">
                          <Input value={resolveNotes} onChange={(e) => setResolveNotes(e.target.value)} placeholder="Notas de resolución *" />
                          <Input value={annulReason} onChange={(e) => setAnnulReason(e.target.value)} placeholder="Motivo anulación" />
                          <Button type="button" variant="secondary" disabled={!resolveNotes.trim() || claimResolveMut.isPending} onClick={() => claimResolveMut.mutate(cl.id)}>Resolver</Button>
                          <Button type="button" variant="secondary" disabled={!annulReason.trim() || claimAnnulMut.isPending} onClick={() => claimAnnulMut.mutate(cl.id)}>Anular</Button>
                        </div>
                      ) : null}
                    </div>
                  ) : null}
                </div>
              ))}
              {!(claimsQuery.data ?? []).length ? <p className="text-xs text-muted-foreground">Sin reclamaciones.</p> : null}
            </div>

            <form className="space-y-3 border-t border-border pt-3" onSubmit={(e: FormEvent) => { e.preventDefault(); claimCreateMut.mutate(); }}>
              <span className="text-sm text-foreground">Nueva reclamación</span>
              <label className="block space-y-2 text-sm text-foreground"><span>Motivo *</span><Combobox value={claimForm.reason} onChange={(v) => setClaimForm(p => ({ ...p, reason: v }))} options={CLAIM_REASON_OPTIONS} placeholder="Seleccionar motivo" searchPlaceholder="Buscar motivo" /></label>
              <label className="block space-y-1 text-sm text-foreground"><span>Descripción *</span>
                <textarea
                  className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm"
                  rows={3}
                  value={claimForm.description}
                  onChange={(e) => setClaimForm(p => ({ ...p, description: e.target.value }))}
                  placeholder="Detalle de la reclamación"
                  required
                />
              </label>
              <div className="grid grid-cols-2 gap-3">
                <label className="block space-y-2 text-sm text-foreground"><span>Recepción vinculada (opcional)</span><Combobox value={claimForm.receipt_id ?? ""} onChange={(v) => setClaimForm(p => ({ ...p, receipt_id: v }))} options={claimReceiptOptions} placeholder="Sin recepción" searchPlaceholder="Buscar recepción" /></label>
                <label className="block space-y-2 text-sm text-foreground"><span>Factura vinculada (opcional)</span><Combobox value={claimForm.invoice_id ?? ""} onChange={(v) => setClaimForm(p => ({ ...p, invoice_id: v }))} options={claimInvoiceOptions} placeholder="Sin factura" searchPlaceholder="Buscar factura" /></label>
              </div>
              <div className="flex justify-end gap-3">
                <Button type="submit" disabled={claimCreateMut.isPending || !claimForm.reason || !claimForm.description.trim()}>{claimCreateMut.isPending ? "Registrando..." : "Registrar reclamación"}</Button>
              </div>
            </form>
          </div>
        </Dialog>
      </CommerceSection>

      <SuppliersCatalogModal open={isSuppliersOpen} onClose={() => setIsSuppliersOpen(false)} />
    </>
  );
}
