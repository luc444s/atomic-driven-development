import { useMutation, useQuery, useQueryClient } from "../../../../../../apps/web/src/lib/react-query";
import { FormEvent, forwardRef, useImperativeHandle, useState } from "react";
import {
  cancelInvoice,
  createInvoice,
  getOrder,
  getReconciliation,
  listInvoices,
} from "../../api";
import type {
  CreateInvoicePayload,
  PurchaseOrderDetail,
  Reconciliation,
  SupplierInvoice,
} from "../../types";
import type { ProductListItem } from "../../../../../productos/frontend/types";
import { ClaimDerivationPanel } from "./ClaimDerivationPanel";
import { Button } from "@systutor/shell/ui/button";
import { Dialog } from "@systutor/shell/ui/dialog";
import { Input } from "@systutor/shell/ui/input";
import { Badge } from "@systutor/shell/ui/badge";

export type InvoicePanelHandle = {
  openInvoicesDialog: (orderId: string) => void;
};

type InvoicePanelProps = {
  setError: (value: string | null) => void;
  products: ProductListItem[];
};

export const InvoicePanel = forwardRef<InvoicePanelHandle, InvoicePanelProps>(function InvoicePanel({ setError, products }, ref) {
  const queryClient = useQueryClient();
  const [isInvoicesOpen, setIsInvoicesOpen] = useState(false);
  const [invoiceOrder, setInvoiceOrder] = useState<PurchaseOrderDetail | null>(null);
  const [invoiceForm, setInvoiceForm] = useState<CreateInvoicePayload>({ invoice_number: "", invoice_date: "", tax: 0, lines: [] });
  const [reconciliation, setReconciliation] = useState<Reconciliation | null>(null);

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

  useImperativeHandle(ref, () => ({ openInvoicesDialog }));

  return (
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

        <ClaimDerivationPanel orderId={invoiceOrder?.id ?? null} setError={setError} />

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
            const product = products.find(p => p.id === orderItem?.product_id);
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
  );
});
