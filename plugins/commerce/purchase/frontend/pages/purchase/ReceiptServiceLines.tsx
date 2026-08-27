import { useMutation, useQuery, useQueryClient } from "../../../../../../apps/web/src/lib/react-query";
import { FormEvent, forwardRef, useImperativeHandle, useState } from "react";
import {
  createReceiptServiceLine,
  deleteReceiptServiceLine,
  listReceiptServiceLines,
} from "../../api";
import type { ReceiptServiceLine } from "../../types";
import { Button } from "@systutor/shell/ui/button";
import { Dialog } from "@systutor/shell/ui/dialog";
import { Input } from "@systutor/shell/ui/input";
import { Combobox } from "@systutor/shell/ui/combobox";

const SERVICE_TYPES = [
  "LLENADO",
  "PRUEBA_HIDROSTATICA",
  "RETIMBRADO",
  "INSPECCION",
  "REPARACION",
  "MANTENIMIENTO",
  "CAMBIO_VALVULA",
  "PINTURA",
  "ACONDICIONAMIENTO",
  "CERTIFICACION",
];

const SERVICE_TYPE_LABEL: Record<string, string> = {
  LLENADO: "Llenado",
  PRUEBA_HIDROSTATICA: "Prueba hidrostática",
  RETIMBRADO: "Retimbrado",
  INSPECCION: "Inspección",
  REPARACION: "Reparación",
  MANTENIMIENTO: "Mantenimiento",
  CAMBIO_VALVULA: "Cambio de válvula",
  PINTURA: "Pintura",
  ACONDICIONAMIENTO: "Acondicionamiento",
  CERTIFICACION: "Certificación",
};

export type ReceiptServiceLinesHandle = {
  openServiceLinesDialog: (receiptId: string) => void;
};

type ReceiptServiceLinesProps = {
  setError: (value: string | null) => void;
};

export const ReceiptServiceLines = forwardRef<ReceiptServiceLinesHandle, ReceiptServiceLinesProps>(function ReceiptServiceLines({ setError }, ref) {
  const queryClient = useQueryClient();
  const [isServiceLinesOpen, setIsServiceLinesOpen] = useState(false);
  const [serviceReceiptId, setServiceReceiptId] = useState<string | null>(null);
  const [lineForm, setLineForm] = useState<{ serial: string; service_type: string; cost: string; notes: string }>({
    serial: "",
    service_type: "",
    cost: "",
    notes: "",
  });

  const linesQuery = useQuery({
    queryKey: ["compras", "service-lines", serviceReceiptId],
    queryFn: () => listReceiptServiceLines(serviceReceiptId!),
    enabled: isServiceLinesOpen && Boolean(serviceReceiptId),
  });
  const lines = linesQuery.data ?? [];

  const createMut = useMutation({
    mutationFn: () => serviceReceiptId
      ? createReceiptServiceLine(serviceReceiptId, {
          serial: lineForm.serial,
          service_type: lineForm.service_type,
          cost: lineForm.cost === "" ? null : Number(lineForm.cost),
          notes: lineForm.notes || null,
        })
      : Promise.reject("No receipt"),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["compras", "service-lines", serviceReceiptId] });
      setLineForm({ serial: "", service_type: "", cost: "", notes: "" });
      setError(null);
    },
    onError: (err) => setError(err instanceof Error ? err.message : "Error al registrar servicio"),
  });

  const deleteMut = useMutation({
    mutationFn: (lineId: string) => {
      if (!serviceReceiptId) return Promise.reject("No receipt");
      return deleteReceiptServiceLine(serviceReceiptId, lineId);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["compras", "service-lines", serviceReceiptId] });
      setError(null);
    },
    onError: (err) => setError(err instanceof Error ? err.message : "Error al borrar servicio"),
  });

  function openServiceLinesDialog(receiptId: string) {
    setServiceReceiptId(receiptId);
    setLineForm({ serial: "", service_type: "", cost: "", notes: "" });
    setIsServiceLinesOpen(true);
  }

  useImperativeHandle(ref, () => ({ openServiceLinesDialog }));

  return (
    <Dialog open={isServiceLinesOpen} title="Servicios realizados por el proveedor" description="Registra por serial el servicio realizado en el paso por el proveedor." onClose={() => { setIsServiceLinesOpen(false); setServiceReceiptId(null); }}>
      <div className="space-y-4">
        <div className="space-y-2">
          <span className="text-sm text-foreground">Servicios registrados</span>
          {lines.map((line: ReceiptServiceLine) => (
            <div key={line.id} className="flex items-center justify-between rounded-md border border-border p-2 text-sm">
              <span>{line.serial} · {SERVICE_TYPE_LABEL[line.service_type] ?? line.service_type}{line.cost !== null ? ` · ${line.cost.toFixed(2)}` : ""}{line.notes ? ` · ${line.notes}` : ""}</span>
              <Button variant="secondary" onClick={() => deleteMut.mutate(line.id)}>X</Button>
            </div>
          ))}
          {!lines.length ? <p className="text-xs text-muted-foreground">Sin servicios registrados.</p> : null}
        </div>

        <form className="space-y-2 border-t border-border pt-3" onSubmit={(e: FormEvent) => { e.preventDefault(); if (lineForm.serial.trim() && lineForm.service_type) createMut.mutate(); }}>
          <span className="text-sm text-foreground">Nuevo servicio</span>
          <div className="grid grid-cols-[1fr_1fr] gap-2">
            <Input value={lineForm.serial} onChange={(e) => setLineForm(p => ({ ...p, serial: e.target.value }))} placeholder="Serial del cilindro *" />
            <Combobox value={lineForm.service_type} onChange={(v) => setLineForm(p => ({ ...p, service_type: v }))} options={SERVICE_TYPES.map(t => ({ value: t, label: SERVICE_TYPE_LABEL[t] ?? t }))} placeholder="Tipo de servicio *" searchPlaceholder="Buscar servicio" />
          </div>
          <div className="grid grid-cols-[120px_1fr] gap-2">
            <Input value={lineForm.cost} onChange={(e) => setLineForm(p => ({ ...p, cost: e.target.value }))} placeholder="Costo" />
            <Input value={lineForm.notes} onChange={(e) => setLineForm(p => ({ ...p, notes: e.target.value }))} placeholder="Notas" />
          </div>
          <div className="flex justify-end gap-3">
            <Button type="submit" disabled={!lineForm.serial.trim() || !lineForm.service_type || createMut.isPending}>{createMut.isPending ? "Guardando..." : "Registrar servicio"}</Button>
          </div>
        </form>
      </div>
    </Dialog>
  );
});
