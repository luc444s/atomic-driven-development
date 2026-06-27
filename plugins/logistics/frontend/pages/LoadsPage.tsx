import { useMutation, useQuery, useQueryClient } from "../../../../apps/web/src/lib/react-query";
import { FormEvent, useState } from "react";

import { bulkCreateLoads, confirmLoads, listCylinders, listLoads, listRouteStops, listRoutes, logisticsKeys } from "../api";
import { LogisticsSection } from "../components/LogisticsSection";
import { CylinderStateBadge } from "../CylinderStateBadge";
import { Alert } from "../../../../apps/web/src/shared/ui/alert";
import { Button } from "../../../../apps/web/src/shared/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../../../apps/web/src/shared/ui/card";
import { DataTable } from "../../../../apps/web/src/shared/ui/data-table";

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
      setFormState((current) => ({ ...current, cylinder_ids: [] }));
      setError(null);
      await queryClient.invalidateQueries({ queryKey: logisticsKeys.loads(formState.route_id) });
    },
  });
  const confirmMutation = useMutation({
    mutationFn: () => confirmLoads(formState.route_id),
    onSuccess: async () => {
      setError(null);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: logisticsKeys.loads(formState.route_id) }),
        queryClient.invalidateQueries({ queryKey: logisticsKeys.cylinders.all() }),
      ]);
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
              <label className="block space-y-2 text-sm text-slate-300">
                <span>Ruta</span>
                <select
                  value={formState.route_id}
                  onChange={(event) => setFormState({ route_id: event.target.value, stop_id: "", cylinder_ids: [] })}
                  className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-200"
                >
                  <option value="">Selecciona una ruta</option>
                  {(routesQuery.data ?? []).map((route) => (
                    <option key={route.id} value={route.id}>
                      {route.route_date} · {route.status}
                    </option>
                  ))}
                </select>
              </label>
              <label className="block space-y-2 text-sm text-slate-300">
                <span>Parada</span>
                <select
                  value={formState.stop_id}
                  onChange={(event) => setFormState((current) => ({ ...current, stop_id: event.target.value }))}
                  className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-200"
                >
                  <option value="">Sin asignar</option>
                  {(stopsQuery.data ?? []).map((stop) => (
                    <option key={stop.id} value={stop.id}>
                      Parada {stop.stop_order}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
              {(cylindersQuery.data ?? []).map((cylinder) => {
                const checked = formState.cylinder_ids.includes(cylinder.id);
                return (
                  <label
                    key={cylinder.id}
                    className="flex items-center justify-between rounded-lg border border-slate-800 bg-slate-900/60 px-3 py-3 text-sm text-slate-300"
                  >
                    <div className="space-y-1">
                      <p className="font-medium text-white">{cylinder.serial}</p>
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
