import { useMutation, useQuery, useQueryClient } from "../../../../apps/web/src/lib/react-query";
import { useState } from "react";

import {
  createRoute,
  createRouteStop,
  getRoute,
  listActiveVehicleSessions,
  listDeliveryPoints,
  listRouteStops,
  listRoutes,
  listVehicles,
  logisticsKeys,
} from "../api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../../../apps/web/src/shared/ui/card";

export function RoutesPage() {
  const queryClient = useQueryClient();
  const [selectedRouteId, setSelectedRouteId] = useState<string | null>(null);

  const routesQuery = useQuery({ queryKey: logisticsKeys.routes.list({}), queryFn: () => listRoutes({}) });
  const vehiclesQuery = useQuery({ queryKey: logisticsKeys.vehicles(), queryFn: listVehicles });
  const deliveryPointsQuery = useQuery({ queryKey: logisticsKeys.deliveryPoints(), queryFn: listDeliveryPoints });
  const activeSessionsQuery = useQuery({
    queryKey: logisticsKeys.vehicleSessions.list({ status: "active" }),
    queryFn: () => listActiveVehicleSessions(),
  });
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
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: logisticsKeys.routes.all() });
    },
  });

  const createStopMutation = useMutation({
    mutationFn: async (args: { delivery_point_id: string; stop_order?: number }) =>
      createRouteStop(selectedRouteId!, args),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: logisticsKeys.routes.stops(selectedRouteId!) });
    },
  });

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Rutas</CardTitle>
          <CardDescription>Gestión central de rutas: creación, paradas y asignación a jornadas activas.</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Panel en construcción. Los datos de rutas ({routesQuery.data?.length ?? 0}), vehículos ({vehiclesQuery.data?.length ?? 0}), puntos de entrega ({deliveryPointsQuery.data?.length ?? 0}) y sesiones activas ({activeSessionsQuery.data?.length ?? 0}) están disponibles.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
