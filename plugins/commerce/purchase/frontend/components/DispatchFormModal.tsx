import { useMutation, useQuery, useQueryClient } from "../../../../../apps/web/src/lib/react-query";
import { FormEvent, useState } from "react";
import { createDispatch, listSuppliers, listTanks } from "../api";
import { Button } from "@systutor/shell/ui/button";
import { Dialog } from "@systutor/shell/ui/dialog";
import { Input } from "@systutor/shell/ui/input";
import { Alert } from "@systutor/shell/ui/alert";

type Props = {
  open: boolean;
  onClose: () => void;
};

const SERVICE_TYPES = [
  "LLENADO", "PH", "RETIMBRADO", "INSPECCION", "REPARACION",
  "CAMBIO_VALVULA", "ACONDICIONAMIENTO", "CERTIFICACION", "MIXTO",
];

type CylRow = { cylinder_id: string; product_id: string; service_type: string };

export function DispatchFormModal({ open, onClose }: Props) {
  const queryClient = useQueryClient();
  const [error, setError] = useState<string | null>(null);
  const [supplierId, setSupplierId] = useState("");
  const [orderId, setOrderId] = useState("");
  const [cyls, setCyls] = useState<CylRow[]>([]);

  const suppliersQuery = useQuery({
    queryKey: ["compras", "suppliers"],
    queryFn: listSuppliers,
    enabled: open,
  });

  // Tanques criogénicos disponibles como candidatos (el input acepta el id
  // de cualquier cilindro; la validación real vive en el backend).
  void listTanks;

  const createMut = useMutation({
    mutationFn: () => createDispatch({
      supplier_id: supplierId,
      order_id: orderId || null,
      cylinders: cyls,
      dispatch_date: new Date().toISOString().slice(0, 10),
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["compras", "dispatches"] });
      onClose();
    },
    onError: (err) => setError(err instanceof Error ? err.message : "Error al crear despacho"),
  });

  function addCyl() { setCyls(p => [...p, { cylinder_id: "", product_id: "", service_type: "LLENADO" }]); }
  function updateCyl(i: number, field: keyof CylRow, value: string) {
    setCyls(p => p.map((row, j) => (j === i ? { ...row, [field]: value } : row)));
  }
  function removeCyl(i: number) { setCyls(p => p.filter((_, j) => j !== i)); }

  const supplierOptions = (suppliersQuery.data ?? []).map(s => ({ value: s.id, label: s.commercial_name ?? s.name }));
  const duplicates = cyls.some((c, i) => c.cylinder_id && cyls.findIndex(x => x.cylinder_id === c.cylinder_id) !== i);

  return (
    <Dialog
      open={open}
      title="Nuevo despacho a proveedor"
      description="Selecciona proveedor y lista los cilindros por serial. La custodia nace al confirmar el despacho."
      onClose={onClose}
      maxWidthClassName="max-w-3xl"
    >
      <div className="space-y-4">
        {error ? <Alert title="Error">{error}</Alert> : null}
        <form
          className="space-y-4"
          onSubmit={(e: FormEvent) => { e.preventDefault(); createMut.mutate(); }}
        >
          <label className="block space-y-2 text-sm text-foreground">
            <span>Proveedor *</span>
            <select
              className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm"
              value={supplierId}
              onChange={(e) => setSupplierId(e.target.value)}
              required
            >
              <option value="">Seleccionar proveedor</option>
              {supplierOptions.map(o => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          </label>
          <label className="block space-y-2 text-sm text-foreground">
            <span>Orden de compra asociada (opcional)</span>
            <Input value={orderId} onChange={(e) => setOrderId(e.target.value)} placeholder="ID de orden" />
          </label>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <p className="text-sm font-medium text-foreground">Cilindros ({cyls.length})</p>
              <Button type="button" variant="secondary" size="sm" onClick={addCyl}>Agregar serial</Button>
            </div>
            {duplicates ? (
              <Alert title="Seriales duplicados">Hay cilindros repetidos en la lista.</Alert>
            ) : null}
            {cyls.map((row, i) => (
              <div key={i} className="grid grid-cols-[1fr_140px_auto] gap-2">
                <Input
                  value={row.cylinder_id}
                  onChange={(e) => updateCyl(i, "cylinder_id", e.target.value)}
                  placeholder="ID del cilindro"
                  required
                />
                <select
                  className="rounded-md border border-border bg-surface px-2 py-2 text-sm"
                  value={row.service_type}
                  onChange={(e) => updateCyl(i, "service_type", e.target.value)}
                >
                  {SERVICE_TYPES.map(s => <option key={s} value={s}>{s}</option>)}
                </select>
                <Button type="button" variant="secondary" size="sm" onClick={() => removeCyl(i)}>x</Button>
              </div>
            ))}
          </div>

          <div className="flex justify-end gap-3">
            <Button type="button" variant="secondary" onClick={onClose}>Cancelar</Button>
            <Button
              type="submit"
              disabled={!supplierId || cyls.length === 0 || duplicates || createMut.isPending}
            >
              Crear despacho
            </Button>
          </div>
        </form>
      </div>
    </Dialog>
  );
}
