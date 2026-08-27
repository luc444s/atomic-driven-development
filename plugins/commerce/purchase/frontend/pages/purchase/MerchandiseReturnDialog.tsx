import { useMutation, useQuery, useQueryClient } from "../../../../../../apps/web/src/lib/react-query";
import { FormEvent, forwardRef, useImperativeHandle, useState } from "react";
import {
  annulMerchandiseReturn,
  completeMerchandiseReturn,
  createMerchandiseReturn,
  getMerchandiseReturn,
  getOrder,
  listClaims,
  listDispatches,
  listMerchandiseReturns,
} from "../../api";
import type {
  CreateMerchandiseReturnPayload,
  MerchandiseReturn,
  MerchandiseReturnDetail,
  PurchaseOrderDetail,
} from "../../types";
import type { ProductListItem } from "../../../../../productos/frontend/types";
import { Alert } from "@systutor/shell/ui/alert";
import { Badge } from "@systutor/shell/ui/badge";
import { Button } from "@systutor/shell/ui/button";
import { Combobox } from "@systutor/shell/ui/combobox";
import { Dialog } from "@systutor/shell/ui/dialog";
import { Input, Textarea } from "@systutor/shell/ui/input";

const RETURN_STATUS_BADGE: Record<string, string> = {
  REGISTRADA: "border-warning/30 bg-warning/10 text-warning",
  CONCRETADA: "border-success/30 bg-success/10 text-success",
  ANULADA: "border-border bg-muted text-muted-foreground",
};

const RETURN_STATUS_LABEL: Record<string, string> = {
  REGISTRADA: "Registrada",
  CONCRETADA: "Concretada",
  ANULADA: "Anulada",
};

type ReturnLineDraft = {
  order_item_id: string;
  cylinder_id: string;
  qty: string;
  unit_cost: string;
  notes: string;
};

type ReturnForm = {
  receipt_id: string;
  claim_id: string;
  return_date: string;
  notes: string;
  lines: ReturnLineDraft[];
};

export type MerchandiseReturnDialogHandle = {
  openReturnsDialog: (orderId: string) => void;
};

type MerchandiseReturnDialogProps = {
  products: ProductListItem[];
};

function today() {
  return new Date().toISOString().slice(0, 10);
}

function emptyForm(): ReturnForm {
  return {
    receipt_id: "",
    claim_id: "",
    return_date: today(),
    notes: "",
    lines: [{ order_item_id: "", cylinder_id: "", qty: "1", unit_cost: "", notes: "" }],
  };
}

export const MerchandiseReturnDialog = forwardRef<
  MerchandiseReturnDialogHandle,
  MerchandiseReturnDialogProps
>(function MerchandiseReturnDialog({ products }, ref) {
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [returnsOrder, setReturnsOrder] = useState<PurchaseOrderDetail | null>(null);
  const [form, setForm] = useState<ReturnForm>(emptyForm());
  const [expandedReturnId, setExpandedReturnId] = useState<string | null>(null);
  const [returnTimeline, setReturnTimeline] = useState<Record<string, MerchandiseReturnDetail>>({});
  const [resolutionNotes, setResolutionNotes] = useState("");
  const [annulReason, setAnnulReason] = useState("");

  const returnsQuery = useQuery({
    queryKey: ["compras", "merchandise-returns", returnsOrder?.id],
    queryFn: () => listMerchandiseReturns(returnsOrder!.id),
    enabled: open && Boolean(returnsOrder),
  });
  const claimsQuery = useQuery({
    queryKey: ["compras", "claims", returnsOrder?.id],
    queryFn: () => listClaims(returnsOrder!.id),
    enabled: open && Boolean(returnsOrder),
  });
  const dispatchesQuery = useQuery({
    queryKey: ["compras", "dispatches", "returns", returnsOrder?.id],
    queryFn: () => listDispatches({ order_id: returnsOrder!.id, limit: 100 }),
    enabled: open && Boolean(returnsOrder),
  });

  function invalidate() {
    queryClient.invalidateQueries({ queryKey: ["compras", "merchandise-returns"] });
    setError(null);
  }

  function refreshReturnDetail(returnId: string) {
    if (!returnsOrder) return;
    getMerchandiseReturn(returnsOrder.id, returnId)
      .then((detail) => setReturnTimeline((current) => ({ ...current, [returnId]: detail })))
      .catch((err) => setError(err instanceof Error ? err.message : "Error al cargar devolución"));
  }

  function toggleReturnTimeline(returnId: string) {
    if (expandedReturnId === returnId) {
      setExpandedReturnId(null);
      return;
    }
    setExpandedReturnId(returnId);
    refreshReturnDetail(returnId);
  }

  function openReturnsDialog(orderId: string) {
    getOrder(orderId)
      .then((detail) => {
        setReturnsOrder(detail);
        setForm(emptyForm());
        setExpandedReturnId(null);
        setReturnTimeline({});
        setResolutionNotes("");
        setAnnulReason("");
        setError(null);
        setOpen(true);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Error al cargar orden"));
  }

  const createMut = useMutation({
    mutationFn: (payload: CreateMerchandiseReturnPayload) =>
      returnsOrder ? createMerchandiseReturn(returnsOrder.id, payload) : Promise.reject("Sin orden"),
    onSuccess: () => {
      setForm(emptyForm());
      invalidate();
    },
    onError: (err) => setError(err instanceof Error ? err.message : "Error al registrar devolución"),
  });
  const completeMut = useMutation({
    mutationFn: (returnId: string) =>
      returnsOrder
        ? completeMerchandiseReturn(returnsOrder.id, returnId, resolutionNotes)
        : Promise.reject("Sin orden"),
    onSuccess: (_data, returnId) => {
      setResolutionNotes("");
      invalidate();
      refreshReturnDetail(returnId);
    },
    onError: (err) => setError(err instanceof Error ? err.message : "Error al concretar devolución"),
  });
  const annulMut = useMutation({
    mutationFn: (returnId: string) =>
      returnsOrder
        ? annulMerchandiseReturn(returnsOrder.id, returnId, annulReason)
        : Promise.reject("Sin orden"),
    onSuccess: (_data, returnId) => {
      setAnnulReason("");
      invalidate();
      refreshReturnDetail(returnId);
    },
    onError: (err) => setError(err instanceof Error ? err.message : "Error al anular devolución"),
  });

  const productLabel = new Map(products.map((product) => [product.id, `${product.sku} · ${product.name}`]));
  const receiptOptions = (returnsOrder?.receipts ?? []).map((receipt) => ({
    value: receipt.id,
    label: `${receipt.receipt_date}${receipt.difference_type ? ` · ${receipt.difference_type}` : ""}`,
  }));
  const claimOptions = (claimsQuery.data ?? []).map((claim) => ({
    value: claim.id,
    label: `${claim.reason} · ${claim.status}`,
  }));
  const dispatchCylinderOptions = Array.from(
    new Map(
      (dispatchesQuery.data?.items ?? []).flatMap((dispatch) =>
        dispatch.cylinders.map((cylinder) => [
          cylinder.cylinder_id,
          {
            value: cylinder.cylinder_id,
            label: `${cylinder.serial ?? cylinder.cylinder_id.slice(0, 8)} · ${dispatch.dispatch_date}`,
          },
        ])
      )
    ).values()
  );
  const orderItemOptions = (returnsOrder?.items ?? []).map((item) => ({
    value: item.id,
    label: productLabel.get(item.product_id) ?? item.product_id,
  }));

  function updateLine(index: number, patch: Partial<ReturnLineDraft>) {
    setForm((current) => ({
      ...current,
      lines: current.lines.map((line, lineIndex) =>
        lineIndex === index ? { ...line, ...patch } : line
      ),
    }));
  }

  function addLine() {
    setForm((current) => ({
      ...current,
      lines: [...current.lines, { order_item_id: "", cylinder_id: "", qty: "1", unit_cost: "", notes: "" }],
    }));
  }

  function removeLine(index: number) {
    setForm((current) => ({
      ...current,
      lines: current.lines.filter((_, lineIndex) => lineIndex !== index),
    }));
  }

  function buildPayload(): CreateMerchandiseReturnPayload | null {
    if (!returnsOrder || !form.receipt_id || !form.return_date || form.lines.length === 0) {
      return null;
    }
    const lines = form.lines.map((line) => {
      const orderItem = returnsOrder.items.find((item) => item.id === line.order_item_id);
      return {
        order_item_id: line.order_item_id || null,
        product_id: orderItem?.product_id ?? null,
        cylinder_id: line.cylinder_id || null,
        qty: Number(line.qty),
        unit_cost: line.unit_cost.trim() ? Number(line.unit_cost) : null,
        notes: line.notes.trim() ? line.notes.trim() : null,
      };
    });
    if (lines.some((line) => !line.order_item_id || !(line.qty > 0))) {
      return null;
    }
    return {
      receipt_id: form.receipt_id,
      claim_id: form.claim_id || null,
      return_date: form.return_date,
      notes: form.notes.trim() ? form.notes.trim() : null,
      lines,
    };
  }

  const payload = buildPayload();

  useImperativeHandle(ref, () => ({ openReturnsDialog }));

  return (
    <Dialog
      open={open}
      title="Devolución de mercadería"
      description={`Orden ${returnsOrder ? returnsOrder.id.slice(0, 8) : ""} · Registro, resolución y auditoría de la devolución al proveedor.`}
      onClose={() => {
        setOpen(false);
        setReturnsOrder(null);
        setExpandedReturnId(null);
        setError(null);
      }}
      maxWidthClassName="max-w-4xl"
    >
      <div className="space-y-6">
        {error ? <Alert title="Error">{error}</Alert> : null}

        <div className="space-y-2">
          <div className="flex items-center justify-between gap-2">
            <span className="text-sm text-foreground">Devoluciones registradas</span>
            <span className="text-xs text-muted-foreground">
              {(returnsQuery.data ?? []).length} registradas
            </span>
          </div>
          {(returnsQuery.data ?? []).map((item: MerchandiseReturn) => (
            <div key={item.id} className="space-y-2 rounded-md border border-border p-3 text-sm">
              <div className="flex items-center justify-between gap-2">
                <span className="flex items-center gap-2">
                  <Badge className={RETURN_STATUS_BADGE[item.status] ?? ""}>
                    {RETURN_STATUS_LABEL[item.status] ?? item.status}
                  </Badge>
                  <span>Recepción {item.receipt_id.slice(0, 8)}</span>
                </span>
                <div className="flex gap-2">
                  <Button variant="secondary" onClick={() => toggleReturnTimeline(item.id)}>
                    {expandedReturnId === item.id ? "Cerrar" : "Historial"}
                  </Button>
                </div>
              </div>
              <p className="text-xs text-muted-foreground">
                {item.return_date}
                {item.claim_id ? ` · Claim ${item.claim_id.slice(0, 8)}` : ""}
                {item.notes ? ` · ${item.notes}` : ""}
              </p>

              {expandedReturnId === item.id ? (
                <div className="space-y-3 border-t border-border pt-3">
                  <div className="space-y-2">
                    <span className="text-sm text-foreground">Líneas</span>
                    {(returnTimeline[item.id]?.lines ?? []).map((line) => (
                      <div key={line.id} className="rounded-md border border-border p-2 text-xs text-muted-foreground">
                        <span className="text-foreground">
                          {line.product_id ? productLabel.get(line.product_id) ?? line.product_id : "Sin producto"}
                        </span>
                        {` · qty ${line.qty}`}
                        {line.serial ? ` · serial ${line.serial}` : ""}
                        {line.unit_cost != null ? ` · costo ${line.unit_cost}` : ""}
                        {line.notes ? ` · ${line.notes}` : ""}
                      </div>
                    ))}
                    {!returnTimeline[item.id] ? (
                      <p className="text-xs text-muted-foreground">Cargando…</p>
                    ) : null}
                  </div>

                  <div className="space-y-1">
                    <span className="text-sm text-foreground">Timeline</span>
                    <ol className="space-y-1 text-xs">
                      {(returnTimeline[item.id]?.events ?? []).map((event) => (
                        <li key={event.id}>
                          {event.from_status ?? "Alta"} -&gt; {RETURN_STATUS_LABEL[event.to_status] ?? event.to_status}
                          {event.reason ? ` · ${event.reason}` : ""}
                        </li>
                      ))}
                    </ol>
                    {item.resolution_notes ? (
                      <p className="text-xs text-muted-foreground">Resolución: {item.resolution_notes}</p>
                    ) : null}
                  </div>

                  {item.status === "REGISTRADA" ? (
                    <div className="grid gap-3 md:grid-cols-[1fr_1fr_auto_auto] md:items-center">
                      <Input
                        value={resolutionNotes}
                        onChange={(event) => setResolutionNotes(event.target.value)}
                        placeholder="Notas de concretación"
                      />
                      <Input
                        value={annulReason}
                        onChange={(event) => setAnnulReason(event.target.value)}
                        placeholder="Motivo de anulación"
                      />
                      <Button
                        type="button"
                        variant="secondary"
                        disabled={!resolutionNotes.trim() || completeMut.isPending}
                        onClick={() => completeMut.mutate(item.id)}
                      >
                        Concretar
                      </Button>
                      <Button
                        type="button"
                        variant="secondary"
                        disabled={!annulReason.trim() || annulMut.isPending}
                        onClick={() => annulMut.mutate(item.id)}
                      >
                        Anular
                      </Button>
                    </div>
                  ) : null}
                </div>
              ) : null}
            </div>
          ))}
          {!(returnsQuery.data ?? []).length ? (
            <p className="text-xs text-muted-foreground">Sin devoluciones registradas.</p>
          ) : null}
        </div>

        <form
          className="space-y-6 border-t border-border pt-4"
          onSubmit={(event: FormEvent) => {
            event.preventDefault();
            if (payload) createMut.mutate(payload);
          }}
        >
          <div className="space-y-2">
            <span className="text-sm text-foreground">Nueva devolución</span>
            <div className="grid gap-3 md:grid-cols-2">
              <label className="block space-y-2 text-sm text-foreground">
                <span>Recepción de origen</span>
                <Combobox
                  value={form.receipt_id}
                  onChange={(value) => setForm((current) => ({ ...current, receipt_id: value }))}
                  options={receiptOptions}
                  placeholder="Seleccionar recepción"
                  searchPlaceholder="Buscar recepción"
                />
              </label>
              <label className="block space-y-2 text-sm text-foreground">
                <span>Reclamación vinculada</span>
                <Combobox
                  value={form.claim_id}
                  onChange={(value) => setForm((current) => ({ ...current, claim_id: value }))}
                  options={claimOptions}
                  placeholder="Sin reclamación"
                  searchPlaceholder="Buscar reclamación"
                />
              </label>
            </div>
            <div className="grid gap-3 md:grid-cols-2">
              <label className="block space-y-2 text-sm text-foreground">
                <span>Fecha de devolución</span>
                <Input
                  type="date"
                  value={form.return_date}
                  onChange={(event) => setForm((current) => ({ ...current, return_date: event.target.value }))}
                />
              </label>
              <label className="block space-y-2 text-sm text-foreground">
                <span>Notas</span>
                <Textarea
                  rows={3}
                  value={form.notes}
                  onChange={(event) => setForm((current) => ({ ...current, notes: event.target.value }))}
                  placeholder="Detalle del motivo o acuerdo con el proveedor"
                />
              </label>
            </div>
          </div>

          <div className="space-y-3 rounded-md border border-border p-4">
            <div className="flex items-center justify-between gap-2">
              <p className="text-sm font-medium text-foreground">Líneas devueltas</p>
              <Button type="button" variant="secondary" onClick={addLine}>
                Agregar línea
              </Button>
            </div>
            {form.lines.map((line, index) => (
              <div key={index} className="space-y-3 rounded-md border border-border p-3">
                <div className="grid gap-3 md:grid-cols-2">
                  <label className="block space-y-2 text-sm text-foreground">
                    <span>Item de la orden</span>
                    <Combobox
                      value={line.order_item_id}
                      onChange={(value) => updateLine(index, { order_item_id: value })}
                      options={orderItemOptions}
                      placeholder="Seleccionar item"
                      searchPlaceholder="Buscar producto"
                    />
                  </label>
                  <label className="block space-y-2 text-sm text-foreground">
                    <span>Serial</span>
                    <Combobox
                      value={line.cylinder_id}
                      onChange={(value) => updateLine(index, { cylinder_id: value })}
                      options={dispatchCylinderOptions}
                      placeholder="Sin serial"
                      searchPlaceholder="Buscar serial"
                    />
                  </label>
                </div>
                <div className="grid gap-3 md:grid-cols-[120px_160px_1fr_auto] md:items-end">
                  <label className="block space-y-2 text-sm text-foreground">
                    <span>Cantidad</span>
                    <Input
                      value={line.qty}
                      onChange={(event) => updateLine(index, { qty: event.target.value })}
                      placeholder="0"
                    />
                  </label>
                  <label className="block space-y-2 text-sm text-foreground">
                    <span>Costo unitario</span>
                    <Input
                      value={line.unit_cost}
                      onChange={(event) => updateLine(index, { unit_cost: event.target.value })}
                      placeholder="Opcional"
                    />
                  </label>
                  <label className="block space-y-2 text-sm text-foreground">
                    <span>Notas de línea</span>
                    <Input
                      value={line.notes}
                      onChange={(event) => updateLine(index, { notes: event.target.value })}
                      placeholder="Observación de la línea"
                    />
                  </label>
                  <Button
                    type="button"
                    variant="secondary"
                    onClick={() => removeLine(index)}
                    disabled={form.lines.length === 1}
                  >
                    Quitar
                  </Button>
                </div>
              </div>
            ))}
          </div>

          <div className="flex justify-end gap-3">
            <Button
              type="button"
              variant="secondary"
              onClick={() => {
                setForm(emptyForm());
                setError(null);
              }}
            >
              Limpiar
            </Button>
            <Button type="submit" disabled={!payload || createMut.isPending}>
              {createMut.isPending ? "Registrando..." : "Registrar devolución"}
            </Button>
          </div>
        </form>
      </div>
    </Dialog>
  );
});
