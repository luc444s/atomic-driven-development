import { useMutation, useQuery, useQueryClient } from "../../../../apps/web/src/lib/react-query";
import { FormEvent, useState } from "react";

import { bulkCreateLoads, confirmLoads, listCylinders, listLoads, listRouteStops, listRoutes, logisticsKeys } from "../api";
import { LogisticsSection } from "../components/LogisticsSection";
import { CylinderStateBadge } from "../CylinderStateBadge";
import { Alert } from "@systutor/shell/ui/alert";
import { Button } from "@systutor/shell/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@systutor/shell/ui/card";
import { DataTable } from "@systutor/shell/ui/data-table";
import { Select } from "@systutor/shell/ui/select";
import { toast } from "@systutor/shell/ui/toast";
import { formatRouteLabel } from "../lib/route-labels";

type LoadFormState = {
  route_id: string;
  stop_id: string;
  cylinder_ids: string[];
};

const EMPTY_FORM: LoadFormState = { route_id: "", stop_id: "", cylinder_ids: [] };

export function LoadsPage() {
  const queryClient = useQueryClient();
  const [formState, setFormState] = useState<LoadFormState>(EMPTY_FORM);
  const [error, setError] = useState<string | null>(null);

  const routesQuery = useQuery({ queryKey: logisticsKeys.routes.list({}), queryFn: () => listRoutes({}) });
  const cylindersQuery = useQuery({
    queryKey: logisticsKeys.cylinders.list({ state: "LLENADO_OK", active: true }),
    queryFn: () => listCylinders({ state: "LLENADO_OK", active: true }),
  });
  const stopsQuery = useQuery({
    queryKey: logisticsKeys.routes.stops(formState.route_id || ""),
    queryFn: () => listRouteStops(formState.route_id),
    enabled: Boolean(formState.route_id),
  });
  const loadsQuery = useQuery({
    queryKey: logisticsKeys.loads(formState.route_id || ""),
    queryFn: () => listLoads(formState.route_id),
    enabled: Boolean(formState.route_id),
  });

  const assignMutation = useMutation({
    mutationFn: () => bulkCreateLoads({ route_id: formState.route_id, stop_id: formState.stop_id || null, cylinder_ids: formState.cylinder_ids }),
    onSuccess: async () => {
      toast.success("Cargas asignadas");
      setFormState((current) => ({ ...current, cylinder_ids: [] }));
      setError(null);
      await queryClient.invalidateQueries({ queryKey: logisticsKeys.loads(formState.route_id) });
    },
  });
  const confirmMutation = useMutation({
    mutationFn: () => confirmLoads(formState.route_id),
    onSuccess: async () => {
      toast.success("Cargas confirmadas");
      setError(null);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: logisticsKeys.loads(formState.route_id) }),
        queryClient.invalidateQueries({ queryKey: logisticsKeys.cylinders.all() }),
      ]);
    },
    onError: () => {
      toast.error("Error al confirmar cargas");
    },
  });

  async function assignSelected(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!formState.route_id || formState.cylinder_ids.length === 0) {
      return;
    }
    setError(null);
    try {
      await assignMutation.mutateAsync();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "No se pudo asignar la carga.");
    }
  }

  return (
    <LogisticsSection
      title="Carga"
      description="Asigna envases listos a una ruta y confirma cuando estén sobre el vehículo."
    >
      {error ? <Alert title="No se pudo completar la acción">{error}</Alert> : null}

      <Card>
        <CardHeader>
          <CardTitle>Preparar carga</CardTitle>
          <CardDescription>Selecciona la ruta y elige los envases que saldrán hoy.</CardDescription>
        </CardHeader>
        <CardContent>
          <form className="space-y-4" onSubmit={assignSelected}>
            <div className="grid gap-4 md:grid-cols-2">
              <label className="block space-y-2 text-sm text-foreground">
                <span>Ruta</span>
                <Select
                  value={formState.route_id}
                  onChange={(value) => setFormState({ route_id: value, stop_id: "", cylinder_ids: [] })}
                  placeholder="Selecciona una ruta"
                  options={(routesQuery.data ?? []).map((route) => ({ value: route.id, label: formatRouteLabel(route) }))} />
               </label>
              <label className="block space-y-2 text-sm text-foreground">
                <span>Parada</span>
                <Select
                  value={formState.stop_id}
                  onChange={(value) => setFormState((current) => ({ ...current, stop_id: value }))}
                  placeholder="Sin asignar"
                  options={(stopsQuery.data ?? []).map((stop) => ({ value: stop.id, label: `Parada ${stop.stop_order}` }))} />
              </label>
            </div>
            <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
              {(cylindersQuery.data ?? []).map((cylinder) => {
                const checked = formState.cylinder_ids.includes(cylinder.id);
                return (
                  <label
                    key={cylinder.id}
                    className="flex items-center justify-between rounded-lg border border-border bg-surface-alt/60 px-3 py-3 text-sm text-foreground"
                  >
                    <div className="space-y-1">
                      <p className="font-medium text-foreground">{cylinder.serial}</p>
                      <CylinderStateBadge state={cylinder.current_state} />
                    </div>
                    <input
                      type="checkbox"
                      checked={checked}
                      onChange={(event) => {
                        setFormState((current) => ({
                          ...current,
                          cylinder_ids: event.target.checked
                            ? [...current.cylinder_ids, cylinder.id]
                            : current.cylinder_ids.filter((item) => item !== cylinder.id),
                        }));
                      }}
                    />
                  </label>
                );
              })}
            </div>
            <div className="flex justify-end gap-3">
              <Button type="submit" variant="secondary" disabled={assignMutation.isPending || !formState.route_id}>
                Asignar a ruta
              </Button>
              <Button type="button" onClick={() => confirmMutation.mutate()} disabled={confirmMutation.isPending || !formState.route_id}>
                Confirmar carga
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Carga actual</CardTitle>
          <CardDescription>Envases ya vinculados a la ruta seleccionada.</CardDescription>
        </CardHeader>
        <CardContent>
          <DataTable
            columns={[
              { key: "cylinder", header: "Envase", render: (row) => row.cylinder_id },
              { key: "stop", header: "Parada", render: (row) => row.stop_id ?? "-" },
              { key: "status", header: "Estado", render: (row) => row.status },
            ]}
            rows={loadsQuery.data ?? []}
            rowKey={(row) => row.id}
            emptyMessage={formState.route_id ? "Aún no hay envases asignados a esta ruta." : "Selecciona una ruta."}
          />
        </CardContent>
      </Card>
    </LogisticsSection>
  );
}
