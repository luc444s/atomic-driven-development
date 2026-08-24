import { useMutation, useQuery, useQueryClient } from "../../../../../apps/web/src/lib/react-query";
import { FormEvent, useState } from "react";
import { createDispatch, listSuppliers } from "../api";
import { listCylindersWithFilters } from "../../../../logistics/frontend/api/cylinder-list";
import { Button } from "@systutor/shell/ui/button";
import { Dialog } from "@systutor/shell/ui/dialog";
import { Input } from "@systutor/shell/ui/input";
import { Badge } from "@systutor/shell/ui/badge";
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

type CylRow = { cylinder_id: string; serial: string; product_id: string; service_type: string };

export function DispatchFormModal({ open, onClose }: Props) {
  const queryClient = useQueryClient();
  const [error, setError] = useState<string | null>(null);
  const [supplierId, setSupplierId] = useState("");
  const [orderId, setOrderId] = useState("");
  const [cyls, setCyls] = useState<CylRow[]>([]);
  const [quickAddOpen, setQuickAddOpen] = useState(false);

  const suppliersQuery = useQuery({
    queryKey: ["compras", "suppliers"],
    queryFn: () => listSuppliers(),
    enabled: open,
  });

  const createMut = useMutation({
    mutationFn: () => createDispatch({
      supplier_id: supplierId,
      order_id: orderId || null,
      cylinders: cyls.map(c => ({ cylinder_id: c.cylinder_id, product_id: c.product_id || null, service_type: c.service_type })),
      dispatch_date: new Date().toISOString().slice(0, 10),
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["compras", "dispatches"] });
      onClose();
    },
    onError: (err) => setError(err instanceof Error ? err.message : "Error al crear despacho"),
  });

  function addCyl(row: CylRow) {
    if (cyls.some(c => c.cylinder_id === row.cylinder_id)) {
      setError(`El serial ${row.serial} ya está en la lista`);
      return;
    }
    setError(null);
    setCyls(p => [...p, row]);
  }
  function updateService(i: number, value: string) {
    setCyls(p => p.map((row, j) => (j === i ? { ...row, service_type: value } : row)));
  }
  function removeCyl(i: number) { setCyls(p => p.filter((_, j) => j !== i)); }

  const supplierOptions = (suppliersQuery.data ?? []).map(s => ({ value: s.id, label: s.commercial_name ?? s.name }));

  return (
    <>
      <Dialog
        open={open}
        title="Nuevo despacho a proveedor"
        description="Selecciona proveedor y agrega los cilindros por serial. La custodia nace al confirmar el despacho."
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
                <Button type="button" variant="secondary" size="sm" onClick={() => setQuickAddOpen(true)}>
                  Agregar serial
                </Button>
              </div>
              {cyls.length === 0 ? (
                <p className="text-xs text-muted-foreground">
                  Todavía no agregaste seriales. Toca "Agregar serial" y buscálos uno por uno.
                </p>
              ) : null}
              {cyls.map((row, i) => (
                <div key={row.cylinder_id} className="flex items-center gap-2 rounded-md border border-border px-3 py-2 text-sm">
                  <Badge variant="secondary">{i + 1}</Badge>
                  <span className="flex-1 font-medium text-foreground">{row.serial}</span>
                  <div className="w-44">
                    <Combobox
                      value={row.service_type}
                      onChange={(v) => updateService(i, v)}
                      options={SERVICE_TYPES.map(s => ({ value: s, label: s }))}
                      placeholder="Servicio"
                    />
                  </div>
                  <Button type="button" variant="secondary" size="sm" onClick={() => removeCyl(i)}>x</Button>
                </div>
              ))}
            </div>

            <div className="flex justify-end gap-3">
              <Button type="button" variant="secondary" onClick={onClose}>Cancelar</Button>
              <Button
                type="submit"
                disabled={!supplierId || cyls.length === 0 || createMut.isPending}
              >
                Crear despacho
              </Button>
            </div>
          </form>
        </div>
      </Dialog>

      <QuickAddSerialDialog
        open={quickAddOpen}
        onClose={() => setQuickAddOpen(false)}
        onAdded={(row) => addCyl(row)}
      />
    </>
  );
}

type QuickAddProps = {
  open: boolean;
  onClose: () => void;
  onAdded: (row: CylRow) => void;
};

/** Alta rápida de seriales al estilo jornadas: combobox de texto clásico,
 * elegís el cilindro y queda agregado sin cerrar para cargar el siguiente. */
function QuickAddSerialDialog({ open, onClose, onAdded }: QuickAddProps) {
  const [lastAdded, setLastAdded] = useState<string | null>(null);
  const [dupError, setDupError] = useState<string | null>(null);

  const cylindersQuery = useQuery({
    queryKey: ["compras", "dispatch-cylinders"],
    queryFn: () => listCylindersWithFilters({ per_page: 200 }),
    enabled: open,
  });

  const opciones = (cylindersQuery.data?.items ?? []).map(c => ({
    value: c.id,
    label: `${c.serial}${c.description ? ` · ${c.description}` : ""}`,
  }));

  function elegir(value: string) {
    if (!value) return;
    const c = (cylindersQuery.data?.items ?? []).find(x => x.id === value);
    if (!c) return;
    onAdded({
      cylinder_id: c.id,
      serial: c.serial,
      product_id: c.product_id ?? "",
      service_type: "LLENADO",
    });
    setLastAdded(c.serial);
    setDupError(null);
  }

  return (
    <Dialog
      open={open}
      title="Agregar seriales"
      description="Elegí un cilindro del buscador. Queda agregado y podés seguir cargando."
      onClose={onClose}
      maxWidthClassName="max-w-xl"
    >
      <div className="space-y-3">
        {dupError ? <Alert title="Duplicado">{dupError}</Alert> : null}
        {lastAdded ? (
          <p className="text-xs font-medium text-success">✓ {lastAdded} agregado — seguí cargando el siguiente.</p>
        ) : null}

        <Combobox
          key={lastAdded ?? "vacio"}
          value=""
          onChange={elegir}
          options={opciones}
          placeholder="Seleccionar cilindro..."
          searchPlaceholder="Buscar por serial o descripción..."
        />

        {cylindersQuery.data ? (
          <p className="text-xs text-muted-foreground">{opciones.length} cilindros disponibles</p>
        ) : null}

        <div className="flex justify-end">
          <Button type="button" variant="secondary" onClick={onClose}>Listo</Button>
        </div>
      </div>
    </Dialog>
  );
}
