import { useMutation, useQuery, useQueryClient } from "../../../../apps/web/src/lib/react-query";
import { FormEvent, useState } from "react";

import {
  createRoute,
  createRouteAgendaTasks,
  createRouteStop,
  deliverRouteStop,
  getRoute,
  listDeliveryPoints,
  listRouteStops,
  listRoutes,
  listVehicles,
  logisticsKeys,
  startRoute,
} from "../api";
import { LogisticsSection } from "../components/LogisticsSection";
import { Alert } from "../../../../apps/web/src/shared/ui/alert";
import { Button } from "../../../../apps/web/src/shared/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../../../apps/web/src/shared/ui/card";
import { DataTable } from "../../../../apps/web/src/shared/ui/data-table";
import { Dialog } from "../../../../apps/web/src/shared/ui/dialog";
import { Input } from "../../../../apps/web/src/shared/ui/input";

type RouteFormState = { route_date: string; vehicle_id: string; notes: string };
type StopFormState = { delivery_point_id: string; stop_order: string };

const EMPTY_ROUTE: RouteFormState = { route_date: "", vehicle_id: "", notes: "" };
const EMPTY_STOP: StopFormState = { delivery_point_id: "", stop_order: "1" };

export function RoutesPage() {
  const queryClient = useQueryClient();
  const [routeForm, setRouteForm] = useState<RouteFormState>(EMPTY_ROUTE);
  const [stopForm, setStopForm] = useState<StopFormState>(EMPTY_STOP);
  const [selectedRouteId, setSelectedRouteId] = useState<string | null>(null);
  const [isRouteOpen, setIsRouteOpen] = useState(false);
  const [isStopOpen, setIsStopOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const routesQuery = useQuery({ queryKey: logisticsKeys.routes.list({}), queryFn: () => listRoutes({}) });
  const vehiclesQuery = useQuery({ queryKey: logisticsKeys.vehicles(), queryFn: listVehicles });
  const deliveryPointsQuery = useQuery({ queryKey: logisticsKeys.deliveryPoints(), queryFn: listDeliveryPoints });
  const routeQuery = useQuery({
    queryKey: logisticsKeys.routes.detail(selectedRouteId ?? ""),
    queryFn: () => getRoute(selectedRouteId!),
    enabled: selectedRouteId !== null,
  });
  const stopsQuery = useQuery({
    queryKey: logisticsKeys.routes.stops(selectedRouteId ?? ""),
    queryFn: () => listRouteStops(selectedRouteId!),
    enabled: selectedRouteId !== null,
  });

  const createRouteMutation = useMutation({
    mutationFn: createRoute,
    onSuccess: async (route) => {
      setSelectedRouteId(route.id);
      setIsRouteOpen(false);
      setRouteForm(EMPTY_ROUTE);
      setError(null);
      await queryClient.invalidateQueries({ queryKey: logisticsKeys.routes.all() });
    },
  });
  const createStopMutation = useMutation({
    mutationFn: async (payload: StopFormState) =>
      createRouteStop(selectedRouteId!, {
        delivery_point_id: payload.delivery_point_id,
        stop_order: Number(payload.stop_order),
      }),
    onSuccess: async () => {
      setIsStopOpen(false);
      setStopForm(EMPTY_STOP);
      setError(null);
      await queryClient.invalidateQueries({ queryKey: logisticsKeys.routes.stops(selectedRouteId!) });
    },
  });

  const startMutation = useMutation({
    mutationFn: startRoute,
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: logisticsKeys.routes.all() }),
        queryClient.invalidateQueries({ queryKey: logisticsKeys.routes.detail(selectedRouteId!) }),
      ]);
    },
  });
  const deliverMutation = useMutation({
    mutationFn: async (stopId: string) => deliverRouteStop(selectedRouteId!, stopId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: logisticsKeys.routes.stops(selectedRouteId!) });
    },
  });
  const agendaMutation = useMutation({
    mutationFn: createRouteAgendaTasks,
    onSuccess: async () => {
      setError(null);
    },
  });

  async function submitRoute(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    try {
      await createRouteMutation.mutateAsync({
        route_date: routeForm.route_date,
        vehicle_id: routeForm.vehicle_id || null,
        notes: routeForm.notes || null,
      });
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "No se pudo crear la ruta.");
    }
  }

  async function submitStop(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedRouteId) {
      return;
    }
    setError(null);
    try {
      await createStopMutation.mutateAsync(stopForm);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "No se pudo agregar la parada.");
    }
  }

  return (
    <LogisticsSection
      title="Rutas"
      description="Planifica salidas simples, asigna paradas y dispara la agenda del día."
      actions={<Button onClick={() => setIsRouteOpen(true)}>Nueva ruta</Button>}
    >
      {error ? <Alert title="No se pudo completar la acción">{error}</Alert> : null}

      <div className="grid gap-6 xl:grid-cols-[1.2fr,1fr]">
        <Card>
          <CardHeader>
            <CardTitle>Rutas registradas</CardTitle>
            <CardDescription>Vista rápida por fecha, vehículo y estado.</CardDescription>
          </CardHeader>
          <CardContent>
            <DataTable
              columns={[
                { key: "date", header: "Fecha", render: (row) => row.route_date },
                {
                  key: "vehicle",
                  header: "Vehículo",
                  render: (row) => vehiclesQuery.data?.find((item) => item.id === row.vehicle_id)?.plate ?? "-",
                },
                { key: "status", header: "Estado", render: (row) => row.status },
                {
                  key: "actions",
                  header: "Detalle",
                  className: "w-32",
                  render: (row) => (
                    <Button variant="secondary" onClick={() => setSelectedRouteId(row.id)}>
                      Ver
                    </Button>
                  ),
                },
              ]}
              rows={routesQuery.data ?? []}
              rowKey={(row) => row.id}
              emptyMessage="Aún no hay rutas creadas."
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center justify-between gap-3">
              <div>
                <CardTitle>Detalle de ruta</CardTitle>
                <CardDescription>Paradas y acciones del recorrido actual.</CardDescription>
              </div>
              {selectedRouteId ? (
                <div className="flex gap-2">
                  <Button variant="secondary" onClick={() => setIsStopOpen(true)}>
                    Parada
                  </Button>
                  <Button variant="secondary" onClick={() => agendaMutation.mutate(selectedRouteId!)}>
                    Agenda
                  </Button>
                  <Button onClick={() => startMutation.mutate(selectedRouteId!)}>Iniciar</Button>
                </div>
              ) : null}
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {routeQuery.data ? (
              <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-4 text-sm text-slate-300">
                <p className="font-medium text-white">{routeQuery.data.route_date}</p>
                <p className="mt-1 text-slate-400">Estado: {routeQuery.data.status}</p>
                <p className="text-slate-500">{routeQuery.data.notes ?? "Sin notas"}</p>
              </div>
            ) : (
              <p className="text-sm text-slate-400">Selecciona una ruta.</p>
            )}

            <DataTable
              columns={[
                { key: "order", header: "#", render: (row) => String(row.stop_order) },
                {
                  key: "point",
                  header: "Punto",
                  render: (row) =>
                    deliveryPointsQuery.data?.find((item) => item.id === row.delivery_point_id)?.customer_name ?? "-",
                },
                { key: "status", header: "Estado", render: (row) => row.status },
                {
                  key: "actions",
                  header: "Entrega",
                  className: "w-28",
                  render: (row) => (
                    <Button variant="secondary" onClick={() => deliverMutation.mutate(row.id)}>
                      Entregar
                    </Button>
                  ),
                },
              ]}
              rows={stopsQuery.data ?? []}
              rowKey={(row) => row.id}
              emptyMessage={selectedRouteId ? "Aún no hay paradas." : "Selecciona una ruta."}
            />
          </CardContent>
        </Card>
      </div>

      <Dialog
        open={isRouteOpen}
        title="Nueva ruta"
        description="Crea una salida base y luego agrega sus paradas."
        onClose={() => setIsRouteOpen(false)}
      >
        <form className="space-y-4" onSubmit={submitRoute}>
          <label className="block space-y-2 text-sm text-slate-300">
            <span>Fecha</span>
            <Input type="date" value={routeForm.route_date} onChange={(event) => setRouteForm((current) => ({ ...current, route_date: event.target.value }))} />
          </label>
          <label className="block space-y-2 text-sm text-slate-300">
            <span>Vehículo</span>
            <select
              value={routeForm.vehicle_id}
              onChange={(event) => setRouteForm((current) => ({ ...current, vehicle_id: event.target.value }))}
              className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-200"
            >
              <option value="">Sin asignar</option>
              {(vehiclesQuery.data ?? []).map((vehicle) => (
                <option key={vehicle.id} value={vehicle.id}>
                  {vehicle.plate}
                </option>
              ))}
            </select>
          </label>
          <label className="block space-y-2 text-sm text-slate-300">
            <span>Notas</span>
            <Input value={routeForm.notes} onChange={(event) => setRouteForm((current) => ({ ...current, notes: event.target.value }))} />
          </label>
          <div className="flex justify-end gap-3">
            <Button type="button" variant="secondary" onClick={() => setIsRouteOpen(false)}>
              Cancelar
            </Button>
            <Button type="submit" disabled={createRouteMutation.isPending}>
              Guardar
            </Button>
          </div>
        </form>
      </Dialog>

      <Dialog
        open={isStopOpen}
        title="Agregar parada"
        description="Relaciona un punto de entrega con el orden de visita."
        onClose={() => setIsStopOpen(false)}
      >
        <form className="space-y-4" onSubmit={submitStop}>
          <label className="block space-y-2 text-sm text-slate-300">
            <span>Punto</span>
            <select
              value={stopForm.delivery_point_id}
              onChange={(event) => setStopForm((current) => ({ ...current, delivery_point_id: event.target.value }))}
              className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-200"
            >
              <option value="">Selecciona</option>
              {(deliveryPointsQuery.data ?? []).map((point) => (
                <option key={point.id} value={point.id}>
                  {point.customer_name} - {point.address}
                </option>
              ))}
            </select>
          </label>
          <label className="block space-y-2 text-sm text-slate-300">
            <span>Orden</span>
            <Input value={stopForm.stop_order} onChange={(event) => setStopForm((current) => ({ ...current, stop_order: event.target.value }))} />
          </label>
          <div className="flex justify-end gap-3">
            <Button type="button" variant="secondary" onClick={() => setIsStopOpen(false)}>
              Cancelar
            </Button>
            <Button type="submit" disabled={createStopMutation.isPending}>
              Guardar
            </Button>
          </div>
        </form>
      </Dialog>
    </LogisticsSection>
  );
}
