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

/** Alta rápida de seriales al estilo jornadas: buscar, elegir, queda agregado
 * y el modal sigue abierto para cargar el siguiente. */
function QuickAddSerialDialog({ open, onClose, onAdded }: QuickAddProps) {
  const [search, setSearch] = useState("");
  const [lastAdded, setLastAdded] = useState<string | null>(null);
  const [dupError, setDupError] = useState<string | null>(null);

  const searchQuery = useQuery({
    queryKey: ["compras", "dispatch-cylinders", search],
    queryFn: () => listCylindersWithFilters({ search, per_page: 20 }),
    enabled: open && search.trim().length >= 2,
  });

  const resultados = (searchQuery.data?.items ?? []).map(c => ({
    id: c.id,
    serial: c.serial,
    descripcion: c.description ?? "",
    product_id: c.product_id,
  }));

  function agregar(r: (typeof resultados)[number]) {
    onAdded({ cylinder_id: r.id, serial: r.serial, product_id: r.product_id ?? "", service_type: "LLENADO" });
    setLastAdded(r.serial);
    setDupError(null);
    setSearch("");
  }

  return (
    <Dialog
      open={open}
      title="Agregar seriales"
      description="Buscá por serial o descripción y elegí el cilindro. Queda agregado y podés seguir cargando."
      onClose={onClose}
      maxWidthClassName="max-w-xl"
    >
      <div className="space-y-3">
        <Input
          autoFocus
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Buscar por serial o descripción..."
        />

        {dupError ? <Alert title="Duplicado">{dupError}</Alert> : null}
        {lastAdded ? (
          <p className="text-xs font-medium text-success">✓ {lastAdded} agregado — seguí cargando el siguiente.</p>
        ) : null}

        {search.trim().length >= 2 ? (
          <div className="max-h-72 space-y-1 overflow-y-auto">
            {resultados.map(r => (
              <button
                key={r.id}
                type="button"
                onClick={() => agregar(r)}
                className="w-full rounded-md border border-border bg-surface px-3 py-2 text-left transition hover:border-ring hover:bg-surface-alt"
              >
                <p className="font-medium text-foreground">{r.serial}</p>
                {r.descripcion ? <p className="text-xs text-muted-foreground">{r.descripcion}</p> : null}
              </button>
            ))}
            {resultados.length === 0 && !searchQuery.isFetching ? (
              <p className="py-2 text-sm text-muted-foreground">Sin resultados.</p>
            ) : null}
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">Escribí al menos 2 caracteres para buscar.</p>
        )}

        <div className="flex justify-end">
          <Button type="button" variant="secondary" onClick={onClose}>Listo</Button>
        </div>
      </div>
    </Dialog>
  );
}
