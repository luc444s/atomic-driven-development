import { useMutation, useQuery, useQueryClient } from "../../../../../../apps/web/src/lib/react-query";
import { FormEvent, useState } from "react";
import {
  closePhysicalCount,
  createPhysicalCount,
  getPhysicalCount,
  listPhysicalCounts,
  listSuppliers,
  resolvePhysicalCountItem,
} from "../../api";
import type {
  CreatePhysicalCountPayload,
  PhysicalCount,
  PhysicalCountDetail,
} from "../../types";
import { Button } from "@systutor/shell/ui/button";
import { Dialog } from "@systutor/shell/ui/dialog";
import { Input } from "@systutor/shell/ui/input";
import { Combobox } from "@systutor/shell/ui/combobox";
import { Alert } from "@systutor/shell/ui/alert";
import { Badge } from "@systutor/shell/ui/badge";

const COUNT_STATUS_BADGE: Record<string, string> = {
  EN_CURSO: "border-warning/30 bg-warning/10 text-warning",
  CERRADA: "border-primary/30 bg-primary/10 text-primary",
};

const DISCREPANCY_BADGE: Record<string, string> = {
  FALTANTE: "border-destructive/30 bg-destructive/10 text-destructive",
  NO_DECLARADO: "border-warning/30 bg-warning/10 text-warning",
  CONDICION: "border-border bg-muted text-muted-foreground",
};

const RESOLUTION_OPTIONS = [
  { value: "RECLAMADA", label: "Reclamada" },
  { value: "ACEPTADA", label: "Aceptada" },
  { value: "OBSERVADA", label: "Observada" },
];

// Línea por serial contado: "SERIAL" o "SERIAL | nota de condición".
function parseFoundLines(raw: string) {
  return raw
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      const [serial, ...rest] = line.split("|");
      const note = rest.join("|").trim();
      return { serial: serial.trim(), condition_note: note || null };
    });
}

type Props = {
  open: boolean;
  onClose: () => void;
};

export function PhysicalCountDialog({ open, onClose }: Props) {
  const queryClient = useQueryClient();
  const [error, setError] = useState<string | null>(null);
  const [supplierId, setSupplierId] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [foundRaw, setFoundRaw] = useState("");
  const [closeNotes, setCloseNotes] = useState("");
  const [resolveDraft, setResolveDraft] = useState<{ resolution: string; reason: string }>({
    resolution: "RECLAMADA",
    reason: "",
  });

  const suppliersQuery = useQuery({
    queryKey: ["compras", "suppliers"],
    queryFn: () => listSuppliers(),
    enabled: open,
  });
  const countsQuery = useQuery({
    queryKey: ["compras", "physical-counts"],
    queryFn: () => listPhysicalCounts(),
    enabled: open,
  });
  const detailQuery = useQuery({
    queryKey: ["compras", "physical-counts", selectedId],
    queryFn: () => getPhysicalCount(selectedId!),
    enabled: open && Boolean(selectedId),
  });

  function invalidate() {
    queryClient.invalidateQueries({ queryKey: ["compras", "physical-counts"] });
    setError(null);
  }

  const createMut = useMutation({
    mutationFn: (payload: CreatePhysicalCountPayload) => createPhysicalCount(payload),
    onSuccess: (created: PhysicalCount) => {
      setSupplierId("");
      setSelectedId(created.id);
      invalidate();
    },
    onError: (err) => setError(err instanceof Error ? err.message : "Error al crear conteo"),
  });
  const closeMut = useMutation({
    mutationFn: () =>
      selectedId
        ? closePhysicalCount(selectedId, {
            found: parseFoundLines(foundRaw),
            notes: closeNotes || null,
          })
        : Promise.reject("Sin conteo"),
    onSuccess: () => {
      setFoundRaw("");
      setCloseNotes("");
      invalidate();
    },
    onError: (err) => setError(err instanceof Error ? err.message : "Error al cerrar conteo"),
  });
  const resolveMut = useMutation({
    mutationFn: (itemId: string) =>
      selectedId
        ? resolvePhysicalCountItem(selectedId, itemId, resolveDraft.resolution, resolveDraft.reason)
        : Promise.reject("Sin conteo"),
    onSuccess: () => {
      setResolveDraft({ resolution: "RECLAMADA", reason: "" });
      invalidate();
    },
    onError: (err) => setError(err instanceof Error ? err.message : "Error al resolver"),
  });

  const counts = countsQuery.data ?? [];
  const detail: PhysicalCountDetail | undefined = detailQuery.data;
  const supplierName = (id: string) =>
    suppliersQuery.data?.find((s) => s.id === id)?.name ?? id.slice(0, 8);

  function submitCreate(e: FormEvent) {
    e.preventDefault();
    if (!supplierId) return;
    createMut.mutate({ supplier_id: supplierId });
  }

  return (
    <Dialog
      open={open}
      title="Conteo físico de custodia"
      description="Cotejo serial-by-serial del inventario en custodia del proveedor. Las diferencias se registran y resuelven con auditoría; la custodia nunca se ajusta en silencio."
      onClose={onClose}
      maxWidthClassName="max-w-3xl"
    >
      <div className="space-y-4">
        {error ? <Alert title="Error">{error}</Alert> : null}

        <form className="space-y-2 border-b border-border pb-3" onSubmit={submitCreate}>
          <span className="text-sm text-foreground">Nuevo conteo por proveedor</span>
          <div className="grid grid-cols-[1fr_auto] gap-2 items-center">
            <Combobox
              value={supplierId}
              onChange={setSupplierId}
              options={(suppliersQuery.data ?? []).map((s) => ({ value: s.id, label: s.name }))}
              placeholder="Seleccionar proveedor"
              searchPlaceholder="Buscar proveedor"
            />
            <Button type="submit" disabled={!supplierId || createMut.isPending}>
              Iniciar conteo
            </Button>
          </div>
        </form>

        <div className="space-y-1">
          <span className="text-sm text-foreground">Sesiones de conteo</span>
          {counts.length === 0 ? (
            <p className="text-xs text-muted-foreground">Sin conteos registrados.</p>
          ) : (
            counts.map((c) => (
              <button
                key={c.id}
                type="button"
                onClick={() => setSelectedId(c.id)}
                className={`w-full rounded-md border px-3 py-2 text-left text-sm ${selectedId === c.id ? "border-primary bg-primary/5" : "border-border"}`}
              >
                <span className="flex items-center justify-between gap-2">
                  <span className="font-medium text-foreground">{supplierName(c.supplier_id)}</span>
                  <Badge className={COUNT_STATUS_BADGE[c.status] ?? ""}>{c.status}</Badge>
                </span>
                <span className="text-xs text-muted-foreground">
                  esperados {c.expected_total} · encontrados {c.found_total} · cotejados {c.match_count}
                </span>
              </button>
            ))
          )}
        </div>

        {detail ? (
          <div className="space-y-3 border-t border-border pt-3">
            <div className="flex items-center justify-between gap-2">
              <span className="text-sm font-medium text-foreground">
                {supplierName(detail.supplier_id)} · {detail.status}
              </span>
              <span className="text-xs text-muted-foreground">
                esperados {detail.expected_total} · encontrados {detail.found_total} · cotejados {detail.match_count}
              </span>
            </div>

            <div className="space-y-1">
              <span className="text-xs text-muted-foreground">Snapshot al iniciar (custodia declarada)</span>
              <div className="flex flex-wrap gap-1">
                {detail.expected_serials.map((s) => (
                  <Badge key={s.id} className="border-border bg-muted text-muted-foreground">{s.serial}</Badge>
                ))}
              </div>
            </div>

            {detail.status === "EN_CURSO" ? (
              <form
                className="space-y-2"
                onSubmit={(e: FormEvent) => {
                  e.preventDefault();
                  closeMut.mutate();
                }}
              >
                <span className="text-sm text-foreground">Cerrar conteo</span>
                <textarea
                  className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm"
                  rows={4}
                  value={foundRaw}
                  onChange={(e) => setFoundRaw(e.target.value)}
                  placeholder={"Seriales contados, uno por línea:\nABC-001\nABC-002 | válvula gastada"}
                />
                <Input
                  value={closeNotes}
                  onChange={(e) => setCloseNotes(e.target.value)}
                  placeholder="Notas del cierre (opcional)"
                />
                <div className="flex justify-end">
                  <Button type="submit" disabled={closeMut.isPending}>
                    Cerrar y calcular diferencias
                  </Button>
                </div>
              </form>
            ) : null}

            {detail.items.length > 0 ? (
              <div className="space-y-1">
                <span className="text-sm text-foreground">Discrepancias</span>
                {detail.items.map((item) => (
                  <div key={item.id} className="rounded-md border border-border p-2 text-sm space-y-1">
                    <div className="flex items-center justify-between gap-2">
                      <span className="flex items-center gap-2">
                        <Badge className={DISCREPANCY_BADGE[item.discrepancy_type] ?? ""}>
                          {item.discrepancy_type}
                        </Badge>
                        <span className="font-medium text-foreground">{item.serial}</span>
                      </span>
                      {item.resolution ? (
                        <Badge className="border-success/30 bg-success/10 text-success">{item.resolution}</Badge>
                      ) : null}
                    </div>
                    {item.notes ? <p className="text-xs text-muted-foreground">{item.notes}</p> : null}
                    {detail.status === "CERRADA" && !item.resolution ? (
                      <div className="grid grid-cols-[140px_1fr_auto] gap-2 items-center">
                        <Combobox
                          value={resolveDraft.resolution}
                          onChange={(v) => setResolveDraft((p) => ({ ...p, resolution: v }))}
                          options={RESOLUTION_OPTIONS}
                          placeholder="Resolución"
                        />
                        <Input
                          value={resolveDraft.reason}
                          onChange={(e) => setResolveDraft((p) => ({ ...p, reason: e.target.value }))}
                          placeholder="Motivo de la resolución *"
                        />
                        <Button
                          type="button"
                          variant="secondary"
                          disabled={!resolveDraft.reason.trim() || resolveMut.isPending}
                          onClick={() => resolveMut.mutate(item.id)}
                        >
                          Resolver
                        </Button>
                      </div>
                    ) : null}
                  </div>
                ))}
              </div>
            ) : detail.status === "CERRADA" ? (
              <p className="text-xs text-muted-foreground">Sin discrepancias: el conteo coincidió con la custodia.</p>
            ) : null}

            <div className="space-y-1">
              <span className="text-sm text-foreground">Historial</span>
              <ol className="text-xs space-y-1">
                {detail.events.map((ev) => (
                  <li key={ev.id}>
                    {ev.from_status ? `${ev.from_status} → ` : ""}
                    <Badge className={COUNT_STATUS_BADGE[ev.to_status] ?? ""}>{ev.to_status}</Badge>
                    {ev.reason ? ` · ${ev.reason}` : ""}
                  </li>
                ))}
              </ol>
            </div>
          </div>
        ) : null}
      </div>
    </Dialog>
  );
}
