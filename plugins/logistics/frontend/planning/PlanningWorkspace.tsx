import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "../../../../apps/web/src/lib/react-query";
import { Alert } from "../../../../apps/web/src/shared/ui/alert";
import { getProduct, listAllProducts } from "../../../productos/frontend/api";
import { LogisticsSection } from "../components/LogisticsSection";
import {
  activatePlanningReservation,
  cancelPlanningReservation,
  createPlanningReservation,
  getRealWarehouses,
  listDriverOptions,
  listPlanningReservations,
  listRoutes,
  listVehicles,
  listWarehouses,
  logisticsKeys,
  planningKeys,
  type PlanningReservation,
  updatePlanningReservation,
} from "../api";
import { PlanningCalendarShell } from "./components/planning-calendar-shell";
import { PlanningStatusLegend } from "./components/planning-status-legend";
import { PlanningToolbar } from "./components/planning-toolbar";
import { CreatePlanningReservationDialog } from "./dialogs/create-planning-reservation-dialog";
import { EditPlanningReservationDialog } from "./dialogs/edit-planning-reservation-dialog";
import { ActivatePlanningReservationDialog } from "./dialogs/activate-planning-reservation-dialog";
import { usePlanningCalendarRange } from "./hooks/use-planning-calendar-range";
import { usePlanningFilters } from "./hooks/use-planning-filters";
import { usePlanningSelection } from "./hooks/use-planning-selection";
import type { PlanningProductCatalogItem } from "./dialogs/planning-product-lines-editor";
import { PlanningReservationDetailPanel } from "./panels/planning-reservation-detail-panel";
import { buildCalendarResources } from "./utils/planning-calendar-mappers";

export function PlanningWorkspace() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const range = usePlanningCalendarRange();
  const filters = usePlanningFilters();
  const selection = usePlanningSelection();
  const [activateDialogOpen, setActivateDialogOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const vehiclesQuery = useQuery({ queryKey: logisticsKeys.vehicles(), queryFn: listVehicles });
  const warehousesQuery = useQuery({ queryKey: logisticsKeys.warehouses(), queryFn: listWarehouses });
  const routesQuery = useQuery({ queryKey: logisticsKeys.routes.list({}), queryFn: () => listRoutes({}) });
  const driversQuery = useQuery({ queryKey: logisticsKeys.vehicleSessions.drivers(), queryFn: listDriverOptions });
  const productsQuery = useQuery({
    queryKey: ["productos", "products", "flat", "planning"],
    queryFn: () => listAllProducts({ is_active: true }),
  });
  const reservationsQuery = useQuery({
    queryKey: planningKeys.reservations.list({ start: range.rangeStart, end: range.rangeEnd, vehicle_id: filters.vehicleId || undefined }),
    queryFn: () => listPlanningReservations({ start: range.rangeStart, end: range.rangeEnd, vehicle_id: filters.vehicleId || undefined }),
  });

  const realWarehouses = getRealWarehouses(warehousesQuery.data ?? []);
  const vehicles = (vehiclesQuery.data ?? []).filter((vehicle) => !filters.warehouseId || vehicle.warehouse_id === filters.warehouseId);
  const reservations = reservationsQuery.data ?? [];
  const selectedReservation = reservations.find((reservation) => reservation.id === selection.selectedReservationId) ?? null;
  const editingReservation = reservations.find((reservation) => reservation.id === selection.editingReservationId) ?? null;
  const resources = buildCalendarResources(vehicles);
  const productCatalog: PlanningProductCatalogItem[] = (productsQuery.data ?? []).map((product) => ({
    id: product.id,
    name: product.name,
    sku: product.sku,
    brand_name: product.brand_name,
  }));

  async function resolvePlanningProduct(productId: string) {
    const product = await getProduct(productId);
    return {
      product_id: product.id,
      product_name: product.name,
      sku: product.sku,
      adr_required: product.adr_configs.length > 0,
      unit_weight_kg: product.weight_kg,
    };
  }

  async function refreshPlanningData() {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: planningKeys.reservations.all() }),
      queryClient.invalidateQueries({ queryKey: logisticsKeys.vehicleSessions.all() }),
    ]);
  }

  const createMutation = useMutation({
    mutationFn: createPlanningReservation,
    onSuccess: async (reservation) => {
      selection.setCreateDraft(null);
      selection.setSelectedReservationId(reservation.id);
      setError(null);
      await refreshPlanningData();
    },
    onError: (cause) => setError(cause instanceof Error ? cause.message : "No se pudo crear la planificación"),
  });

  const updateMutation = useMutation({
    mutationFn: ({ reservationId, payload }: { reservationId: string; payload: Parameters<typeof createPlanningReservation>[0] }) =>
      updatePlanningReservation(reservationId, payload),
    onSuccess: async (reservation) => {
      selection.setEditingReservationId(null);
      selection.setSelectedReservationId(reservation.id);
      setError(null);
      await refreshPlanningData();
    },
    onError: (cause) => setError(cause instanceof Error ? cause.message : "No se pudo actualizar la planificación"),
  });

  const activateMutation = useMutation({
    mutationFn: activatePlanningReservation,
    onSuccess: async (reservation) => {
      setActivateDialogOpen(false);
      setError(null);
      await refreshPlanningData();
      if (reservation.linked_session_id) {
        navigate(`/app/logistics/vehicle-sessions/${reservation.linked_session_id}`);
      }
    },
    onError: (cause) => setError(cause instanceof Error ? cause.message : "No se pudo materializar la jornada"),
  });

  const cancelMutation = useMutation({
    mutationFn: cancelPlanningReservation,
    onSuccess: async () => {
      selection.setSelectedReservationId(null);
      setError(null);
      await refreshPlanningData();
    },
    onError: (cause) => setError(cause instanceof Error ? cause.message : "No se pudo cancelar la planificación"),
  });

  return (
    <LogisticsSection
      title="Planificación"
      description="Calendario operacional de reservas de capacidad por vehículo, separado del runtime vivo de Jornadas."
    >
      {error ? <Alert title="Operación no completada">{error}</Alert> : null}

      <PlanningToolbar
        view={range.view}
        onViewChange={range.setView}
        focusDate={range.focusDate}
        onPrevious={range.goPrevious}
        onNext={range.goNext}
        onToday={range.goToday}
        vehicleId={filters.vehicleId}
        onVehicleChange={filters.setVehicleId}
        warehouseId={filters.warehouseId}
        onWarehouseChange={filters.setWarehouseId}
        vehicles={vehicles}
        warehouses={realWarehouses}
        onCreate={() => {
          const plannedStartAt = new Date();
          const plannedEndAt = new Date(plannedStartAt.getTime() + 60 * 60 * 1000);
          selection.setCreateDraft({
            vehicleId: filters.vehicleId,
            plannedStartAt: plannedStartAt.toISOString(),
            plannedEndAt: plannedEndAt.toISOString(),
          });
        }}
      />

      <PlanningStatusLegend />

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_340px]">
        <div>
          <PlanningCalendarShell
            view={range.view}
            focusDate={range.focusDate.toISOString()}
            rangeStart={range.rangeStart}
            rangeEnd={range.rangeEnd}
            resources={resources}
            reservations={reservations}
            onSlotSelect={(vehicleId, plannedStartAt, plannedEndAt) => {
              selection.setCreateDraft({ vehicleId, plannedStartAt, plannedEndAt });
            }}
            onReservationClick={(reservationId) => selection.setSelectedReservationId(reservationId)}
          />
        </div>

        <PlanningReservationDetailPanel
          reservation={selectedReservation}
          onEdit={() => selection.setEditingReservationId(selectedReservation?.id ?? null)}
          onActivate={() => setActivateDialogOpen(true)}
          onCancel={() => selectedReservation && cancelMutation.mutate(selectedReservation.id)}
          onOpenSession={(sessionId) => navigate(`/app/logistics/vehicle-sessions/${sessionId}`)}
          isActivating={activateMutation.isPending}
          isCancelling={cancelMutation.isPending}
        />
      </div>

      <CreatePlanningReservationDialog
        open={selection.createDraft != null}
        onClose={() => selection.setCreateDraft(null)}
        onSubmit={async (payload) => await createMutation.mutateAsync(payload)}
        isPending={createMutation.isPending}
        vehicles={vehiclesQuery.data ?? []}
        warehouses={realWarehouses}
        routes={routesQuery.data ?? []}
        drivers={driversQuery.data ?? []}
        products={productCatalog}
        resolveProduct={resolvePlanningProduct}
        initialDraft={selection.createDraft && { vehicleId: selection.createDraft.vehicleId, plannedStartAt: selection.createDraft.plannedStartAt, plannedEndAt: selection.createDraft.plannedEndAt }}
      />

      <EditPlanningReservationDialog
        open={editingReservation != null}
        onClose={() => selection.setEditingReservationId(null)}
        onSubmit={async (payload) => {
          if (!editingReservation) {
            return;
          }
          await updateMutation.mutateAsync({ reservationId: editingReservation.id, payload });
        }}
        isPending={updateMutation.isPending}
        reservation={editingReservation}
        vehicles={vehiclesQuery.data ?? []}
        warehouses={realWarehouses}
        routes={routesQuery.data ?? []}
        drivers={driversQuery.data ?? []}
        products={productCatalog}
        resolveProduct={resolvePlanningProduct}
      />

      <ActivatePlanningReservationDialog
        open={activateDialogOpen}
        reservation={selectedReservation}
        onClose={() => setActivateDialogOpen(false)}
        onConfirm={async () => {
          if (!selectedReservation) {
            return;
          }
          await activateMutation.mutateAsync(selectedReservation.id);
        }}
        isPending={activateMutation.isPending}
      />
    </LogisticsSection>
  );
}
