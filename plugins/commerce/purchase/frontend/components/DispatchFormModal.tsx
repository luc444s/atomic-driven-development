import { useMutation, useQuery, useQueryClient } from "../../../../../apps/web/src/lib/react-query";
import { FormEvent, useState } from "react";
import { createDispatch, listSuppliers } from "../api";
import { listCylindersWithFilters } from "../../../../logistics/frontend/api/cylinder-list";
import { Button } from "@systutor/shell/ui/button";
import { Dialog } from "@systutor/shell/ui/dialog";
import { Input } from "@systutor/shell/ui/input";
import { Combobox } from "@systutor/shell/ui/combobox";
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
    queryFn: () => listSuppliers(),
    enabled: open,
  });

  // Cilindros reales de Logística para el selector por serial (§9: nunca IDs
  // manuales). La validación autoritativa sigue viviendo en el backend.
  const cylindersQuery = useQuery({
    queryKey: ["compras", "dispatch-cylinders"],
    queryFn: () => listCylindersWithFilters({ per_page: 200 }),
    enabled: open,
  });

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
  const cylinderOptions = (cylindersQuery.data?.items ?? []).map(c => ({
    value: c.id,
    label: `${c.serial}${c.description ? ` · ${c.description}` : ""}`,
  }));
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
            <Combobox
              value={supplierId}
              onChange={setSupplierId}
              options={supplierOptions}
              placeholder="Seleccionar proveedor"
              searchPlaceholder="Buscar proveedor"
            />
          </label>
          <label className="block space-y-2 text-sm text-foreground">
            <span>Orden de compra asociada (opcional)</span>
            <Input value={orderId} onChange={(e) => setOrderId(e.target.value)} placeholder="ID de orden" />
          </label>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <p className="text-sm font-medium text-foreground">Cilindros ({cyls.length})</p>
              <Button type="button" variant="secondary" size="sm" onClick={addCyl}>Agregar cilindro</Button>
            </div>
            {duplicates ? (
              <Alert title="Seriales duplicados">Hay cilindros repetidos en la lista.</Alert>
            ) : null}
            {cyls.length === 0 ? (
              <p className="text-xs text-muted-foreground">
                Agregá un cilindro y elegilo por serial desde el buscador.
              </p>
            ) : null}
            {cyls.map((row, i) => (
              <div key={i} className="grid grid-cols-[1fr_150px_auto] gap-2">
                <Combobox
                  value={row.cylinder_id}
                  onChange={(v) => {
                    const chosen = (cylindersQuery.data?.items ?? []).find(c => c.id === v);
                    updateCyl(i, "cylinder_id", v);
                    if (chosen?.product_id) updateCyl(i, "product_id", chosen.product_id);
                  }}
                  options={cylinderOptions}
                  placeholder="Buscar por serial..."
                  searchPlaceholder="Serial o descripción"
                />
                <Combobox
                  value={row.service_type}
                  onChange={(v) => updateCyl(i, "service_type", v)}
                  options={SERVICE_TYPES.map(s => ({ value: s, label: s }))}
                  placeholder="Servicio"
                />
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
