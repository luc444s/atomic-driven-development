import { useMutation, useQuery, useQueryClient } from "../../../../apps/web/src/lib/react-query";
import { useEffect, useState } from "react";

import {
  assignRouteToSession,
  listActiveVehicleSessions,
  listRoutes,
  listVehicles,
  logisticsKeys,
} from "../api";
import { RouteBuilderMap } from "../components/route-builder/RouteBuilderMap";
import { RouteBuilderPanel } from "../components/route-builder/RouteBuilderPanel";
import { RouteListSidebar } from "../components/route-builder/RouteListSidebar";
import { useRouteBuilder } from "../components/route-builder/useRouteBuilder";
import { Alert } from "@systutor/shell/ui/alert";

type Props = {
  autoStart?: boolean;
  onRouteCreated?: (routeId: string) => void;
};

export function RoutesPage({ autoStart = false, onRouteCreated }: Props) {
  const queryClient = useQueryClient();
  const [selectedRouteId, setSelectedRouteId] = useState<string | null>(null);
  const [selectedSessionId, setSelectedSessionId] = useState("");
  const [error, setError] = useState<string | null>(null);

  const routesQuery = useQuery({ queryKey: logisticsKeys.routes.list({}), queryFn: () => listRoutes({}) });
  const vehiclesQuery = useQuery({ queryKey: logisticsKeys.vehicles(), queryFn: listVehicles });
  const activeSessionsQuery = useQuery({
    queryKey: logisticsKeys.vehicleSessions.list({ status: "active" }),
    queryFn: () => listActiveVehicleSessions(),
  });

  const builder = useRouteBuilder({ onError: (msg) => setError(msg), onRouteCreated });

  useEffect(() => {
    if (autoStart && builder.phase === "idle") {
      builder.startNew();
    }
  }, [autoStart]);

  const assignRouteMutation = useMutation({
    mutationFn: (routeId: string) => assignRouteToSession(selectedSessionId, routeId),
    onSuccess: async () => {
      setSelectedSessionId("");
      setError(null);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: logisticsKeys.vehicleSessions.all() }),
        queryClient.invalidateQueries({ queryKey: logisticsKeys.routes.all() }),
      ]);
    },
    onError: (cause) => {
      setError(cause instanceof Error ? cause.message : "No se pudo asignar la ruta");
    },
  });

  const isBuilding = builder.phase !== "idle";

  return (
    <div className="flex h-full gap-0">
      {!isBuilding ? (
        <div className="w-[320px] shrink-0 overflow-y-auto border-r border-border p-4">
          <RouteListSidebar
            routes={routesQuery.data ?? []}
            selectedRouteId={selectedRouteId}
            onSelectRoute={setSelectedRouteId}
            onEditRoute={(routeId) => builder.startEditing(routeId)}
            onNewRoute={builder.startNew}
          />
        </div>
      ) : (
        <div className="w-[340px] shrink-0 overflow-y-auto border-r border-border p-4">
          <RouteBuilderPanel
            phase={builder.phase}
            startPoint={builder.startPoint}
            endPoint={builder.endPoint}
            stops={builder.stops}
            routeDate={builder.routeDate}
            vehicleId={builder.vehicleId}
            customName={builder.customName}
            isSaving={builder.isSaving}
            isCalculating={builder.isCalculating}
            vehicles={vehiclesQuery.data ?? []}
            sessions={activeSessionsQuery.data ?? []}
            selectedSessionId={selectedSessionId}
            preview={builder.preview}
            onRemoveStart={builder.removeStart}
            onRemoveEnd={builder.removeEnd}
            onRemoveStop={builder.removeStop}
            onReorderStop={builder.reorderStop}
            onRouteDateChange={builder.setRouteDate}
            onVehicleChange={builder.setVehicleId}
            onCustomNameChange={builder.setCustomName}
            onSessionChange={setSelectedSessionId}
            onAssignSession={() => {
              if (builder.editingRouteId || selectedRouteId) {
                assignRouteMutation.mutate(builder.editingRouteId ?? selectedRouteId!);
              }
            }}
            onCalculate={builder.calculatePreview}
            onClearPreview={builder.clearPreview}
            onCancel={builder.cancelBuilder}
            onSave={builder.save}
            onSearchSelect={(lat, lng) => builder.handleMapClick(lat, lng)}
            onAddStopManual={builder.addStopManual}
            compact={autoStart}
          />
        </div>
      )}

      <div className="min-w-0 flex-1 p-4">
        {error ? (
          <div className="mb-4">
            <Alert title="Error">{error}</Alert>
          </div>
        ) : null}
          <RouteBuilderMap
            phase={builder.phase}
            startPoint={builder.startPoint}
            endPoint={builder.endPoint}
            stops={builder.stops}
            preview={builder.preview}
            onClickMap={(lat, lng) => builder.handleMapClick(lat, lng)}
            onDragMarker={(id, lat, lng) => builder.handleMarkerDrag(id, lat, lng)}
          />
      </div>
    </div>
  );
}
