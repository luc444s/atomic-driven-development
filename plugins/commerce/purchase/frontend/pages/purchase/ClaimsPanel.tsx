import { useMutation, useQuery, useQueryClient } from "../../../../../../apps/web/src/lib/react-query";
import { FormEvent, forwardRef, useImperativeHandle, useState } from "react";
import {
  annulClaim,
  createClaim,
  getClaim,
  getOrder,
  listClaims,
  listInvoices,
  resolveClaim,
  startClaim,
} from "../../api";
import type {
  CreateClaimPayload,
  PurchaseOrderDetail,
  SupplierClaim,
  SupplierClaimDetail,
} from "../../types";
import { Button } from "@systutor/shell/ui/button";
import { Dialog } from "@systutor/shell/ui/dialog";
import { Input } from "@systutor/shell/ui/input";
import { Combobox } from "@systutor/shell/ui/combobox";
import { Badge } from "@systutor/shell/ui/badge";

const CLAIM_REASON_LABEL: Record<string, string> = {
  FALTANTE: "Faltante", PRODUCTO_INCORRECTO: "Producto incorrecto",
  MALA_CALIDAD: "Mala calidad", CILINDRO_DANADO: "Cilindro dañado",
  SERVICIO_INCOMPLETO: "Servicio incompleto", SERVICIO_DEFECTUOSO: "Servicio defectuoso",
  PRECIO_INCORRECTO: "Precio incorrecto", DOCUMENTO_INCORRECTO: "Documento incorrecto",
  DEMORA: "Demora", PERDIDA_ENVASE: "Pérdida de envase", DANO_EN_CUSTODIA: "Daño en custodia",
};

const CLAIM_REASON_OPTIONS = Object.entries(CLAIM_REASON_LABEL).map(([value, label]) => ({ value, label }));

const CLAIM_STATUS_BADGE: Record<string, string> = {
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

export type ClaimsPanelHandle = {
  openClaimsDialog: (orderId: string) => void;
};

type ClaimsPanelProps = {
  setError: (value: string | null) => void;
};

export const ClaimsPanel = forwardRef<ClaimsPanelHandle, ClaimsPanelProps>(function ClaimsPanel({ setError }, ref) {
  const queryClient = useQueryClient();
  const [isClaimsOpen, setIsClaimsOpen] = useState(false);
  const [claimsOrder, setClaimsOrder] = useState<PurchaseOrderDetail | null>(null);
  const [claimForm, setClaimForm] = useState<CreateClaimPayload>({ reason: "", description: "" });
  const [expandedClaimId, setExpandedClaimId] = useState<string | null>(null);
  const [claimTimeline, setClaimTimeline] = useState<Record<string, SupplierClaimDetail>>({});
  const [resolveNotes, setResolveNotes] = useState("");
  const [annulReason, setAnnulReason] = useState("");

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

  const claimReceiptOptions = (claimsOrder?.receipts ?? []).map((r) => ({
    value: r.id,
    label: `${r.receipt_date}${r.difference_type ? ` · ${r.difference_type}` : ""}`,
  }));
  const claimInvoiceOptions = (claimInvoicesQuery.data ?? []).map((iv) => ({
    value: iv.id,
    label: `${iv.invoice_number} · ${iv.invoice_date}`,
  }));

  useImperativeHandle(ref, () => ({ openClaimsDialog }));

  return (
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
  );
});
