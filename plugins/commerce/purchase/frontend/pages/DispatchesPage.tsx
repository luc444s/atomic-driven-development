import { useMutation, useQuery, useQueryClient } from "../../../../../apps/web/src/lib/react-query";
import { useState } from "react";
import {
  cancelDispatch,
  confirmDispatch,
  getDispatch,
  listDispatches,
  registerDispatchReturn,
} from "../api";
import { Button } from "@systutor/shell/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@systutor/shell/ui/card";
import { DataTable } from "@systutor/shell/ui/data-table";
import { Alert } from "@systutor/shell/ui/alert";
import { Badge } from "@systutor/shell/ui/badge";
import { Combobox } from "@systutor/shell/ui/combobox";
import { Dialog } from "@systutor/shell/ui/dialog";
import { DispatchFormModal } from "../components/DispatchFormModal";
import { PhysicalCountDialog } from "./purchase/PhysicalCountDialog";

const STATUS_BADGE: Record<string, string> = {
  PREPARADO: "border-warning/30 bg-warning/10 text-warning",
  DESPACHADO: "border-primary/30 bg-primary/10 text-primary",
  CANCELADO: "border-destructive/30 bg-destructive/10 text-destructive",
};

export function DispatchesPage() {
  const queryClient = useQueryClient();
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState("");
  const [formOpen, setFormOpen] = useState(false);
  const [countOpen, setCountOpen] = useState(false);

  const dispatchesQuery = useQuery({
    queryKey: ["compras", "dispatches", { status: statusFilter }],
    queryFn: () => listDispatches({ status: statusFilter || undefined }),
  });

  function invalidate() {
    queryClient.invalidateQueries({ queryKey: ["compras", "dispatches"] });
    setError(null);
  }

  const confirmMut = useMutation({
    mutationFn: (id: string) => confirmDispatch(id),
    onSuccess: invalidate,
    onError: (err) => setError(err instanceof Error ? err.message : "Error al confirmar"),
  });
  const cancelMut = useMutation({
    mutationFn: (id: string) => cancelDispatch(id),
    onSuccess: invalidate,
    onError: (err) => setError(err instanceof Error ? err.message : "Error al cancelar"),
  });

  const [retornoOpenId, setRetornoOpenId] = useState<string | null>(null);
  const [retornoItems, setRetornoItems] = useState<{ id: string; serial: string | null }[]>([]);
  const [retornoSel, setRetornoSel] = useState<Set<string>>(new Set());
  async function openRetorno(id: string) {
    const detail = await getDispatch(id);
    const enCustodia = detail.cylinders.filter(c => c.status === "EN_CUSTODIA");
    setRetornoItems(enCustodia.map(c => ({ id: c.cylinder_id, serial: c.serial })));
    setRetornoSel(new Set());
    setRetornoOpenId(id);
  }
  function toggleRetorno(id: string) {
    setRetornoSel(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }
  const retornoMut = useMutation({
    mutationFn: () =>
      retornoOpenId
        ? registerDispatchReturn(retornoOpenId, [...retornoSel])
        : Promise.reject("Sin despacho"),
    onSuccess: () => { invalidate(); setRetornoOpenId(null); },
    onError: (err) => setError(err instanceof Error ? err.message : "Error al registrar retorno"),
  });

  const dispatches = dispatchesQuery.data?.items ?? [];

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="gap-3">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <CardTitle>Despachos a proveedor</CardTitle>
              <CardDescription>
                Envíos de cilindros propios por serial. La custodia nace al confirmar el despacho.
              </CardDescription>
            </div>
            <Button onClick={() => setFormOpen(true)}>Nuevo despacho</Button>
            <Button variant="secondary" onClick={() => setCountOpen(true)}>Conteo físico</Button>
          </div>
          <div className="max-w-xs">
            <Combobox
              value={statusFilter}
              onChange={setStatusFilter}
              options={[
                { value: "", label: "Todos los estados" },
                { value: "PREPARADO", label: "Preparado" },
                { value: "DESPACHADO", label: "Despachado" },
                { value: "CANCELADO", label: "Cancelado" },
              ]}
              placeholder="Filtrar por estado"
            />
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          {error ? <Alert title="Error">{error}</Alert> : null}
          <DataTable
            columns={[
              {
                key: "supplier",
                header: "Proveedor",
                render: (row) => row.supplier_name ?? row.supplier_id,
              },
              { key: "date", header: "Fecha", render: (row) => row.dispatch_date },
              {
                key: "cyls",
                header: "Cilindros",
                render: (row) => `${row.cylinders.length} seriales`,
              },
              { key: "order", header: "Orden", render: (row) => row.order_id ? row.order_id.slice(0, 8) : "-" },
              {
                key: "status",
                header: "Estado",
                render: (row) => (
                  <Badge className={STATUS_BADGE[row.status] ?? ""}>
                    {row.status === "DESPACHADO" ? "Despachado" : row.status === "PREPARADO" ? "Preparado" : "Cancelado"}
                  </Badge>
                ),
              },
              {
                key: "actions",
                header: "",
                render: (row) => (
                  <div className="flex flex-wrap gap-1">
                    {row.status === "PREPARADO" ? (
                      <>
                        <Button variant="secondary" size="sm" onClick={() => confirmMut.mutate(row.id)}>Confirmar salida</Button>
                        <Button variant="secondary" size="sm" onClick={() => cancelMut.mutate(row.id)}>Cancelar</Button>
                      </>
                    ) : null}
                    {row.status === "DESPACHADO" ? (
                      <Button variant="secondary" size="sm" onClick={() => { setError(null); void openRetorno(row.id); }}>Registrar retorno</Button>
                    ) : null}
                  </div>
                ),
              },
            ]}
            rows={dispatches}
            rowKey={(row) => row.id}
            emptyMessage="No hay despachos registrados."
          />
        </CardContent>
      </Card>

      <DispatchFormModal
        open={formOpen}
        onClose={() => { setFormOpen(false); setError(null); }}
      />

      <PhysicalCountDialog
        open={countOpen}
        onClose={() => { setCountOpen(false); setError(null); }}
      />

      <Dialog
        open={retornoOpenId !== null}
        title="Registrar retorno de cilindros"
        description="Marca los seriales que efectivamente regresaron. Los no marcados siguen en custodia del proveedor."
        onClose={() => setRetornoOpenId(null)}
        maxWidthClassName="max-w-lg"
      >
        <div className="space-y-3">
          {retornoItems.length === 0 ? (
            <p className="text-sm text-muted-foreground">Sin cilindros en custodia.</p>
          ) : (
            retornoItems.map(item => (
              <label key={item.id} className="flex items-center gap-3 rounded-md border border-border px-3 py-2 text-sm">
                <input
                  type="checkbox"
                  checked={retornoSel.has(item.id)}
                  onChange={() => toggleRetorno(item.id)}
                />
                <span className="font-medium text-foreground">{item.serial ?? item.id}</span>
              </label>
            ))
          )}
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setRetornoOpenId(null)}>Cancelar</Button>
            <Button
              disabled={retornoSel.size === 0 || retornoMut.isPending}
              onClick={() => retornoMut.mutate()}
            >
              Registrar retorno ({retornoSel.size})
            </Button>
          </div>
        </div>
      </Dialog>
    </div>
  );
}
