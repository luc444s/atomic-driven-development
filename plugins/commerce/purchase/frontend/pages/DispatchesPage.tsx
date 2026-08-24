import { useMutation, useQuery, useQueryClient } from "../../../../../apps/web/src/lib/react-query";
import { useState } from "react";
import {
  cancelDispatch,
  confirmDispatch,
  listDispatches,
} from "../api";
import { Button } from "@systutor/shell/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@systutor/shell/ui/card";
import { DataTable } from "@systutor/shell/ui/data-table";
import { Alert } from "@systutor/shell/ui/alert";
import { Badge } from "@systutor/shell/ui/badge";
import { Combobox } from "@systutor/shell/ui/combobox";
import { DispatchFormModal } from "../components/DispatchFormModal";

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
    </div>
  );
}
