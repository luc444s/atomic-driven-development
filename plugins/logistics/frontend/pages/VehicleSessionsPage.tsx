import { FormEvent, useMemo, useState } from "react";

import { useMutation, useQuery, useQueryClient } from "../../../../apps/web/src/lib/react-query";
import { Alert } from "../../../../apps/web/src/shared/ui/alert";
import { Button } from "../../../../apps/web/src/shared/ui/button";
import { Card, CardContent } from "../../../../apps/web/src/shared/ui/card";
import { Dialog } from "../../../../apps/web/src/shared/ui/dialog";
import {
  createRoute,
  createVehicle,
  createVehicleSession,
  listPlanningReservations,
  listDriverOptions,
  listRoutes,
  listVehicleSessions,
  listVehicles,
  listWarehouses,
  logisticsKeys,
  planningKeys,
} from "../api";
import { CreateJornadaDialog, type JornadaCreateForm } from "../components/vehicle-sessions/CreateJornadaDialog";
import {
  CreateRouteFromJornadaDialog,
  type JornadaRouteForm,
} from "../components/vehicle-sessions/CreateRouteFromJornadaDialog";
import {
  CreateVehicleFromJornadaDialog,
  type JornadaVehicleForm,
} from "../components/vehicle-sessions/CreateVehicleFromJornadaDialog";
import { VehicleJornadaCard } from "../components/vehicle-sessions/VehicleJornadaCard";
import { VehicleJornadasDialog } from "../components/vehicle-sessions/VehicleJornadasDialog";
import {
  buildVehicleProjectionCards,
  type VehicleProjectionCard,
} from "../components/vehicle-sessions/vehicle-jornadas-projection";
import { LogisticsSection } from "../components/LogisticsSection";
import { RoutesPage } from "./RoutesPage";
import { VehicleSessionDetailPage } from "./VehicleSessionDetailPage";
import { WarehousesPage } from "./WarehousesPage";

const EMPTY_FORM: JornadaCreateForm = {
  vehicle_id: "",
  driver_id: "",
  origin_warehouse_id: "",
  route_id: "",
};

const EMPTY_VEHICLE_FORM: JornadaVehicleForm = {
  plate: "",
  vehicle_type: "",
  brand: "",
  model: "",
  capacity_weight: "",
  warehouse_id: "",
};

const EMPTY_ROUTE_FORM: JornadaRouteForm = {
  route_date: "",
  vehicle_id: "",
  notes: "",
};

export function VehicleSessionsPage() {
  const queryClient = useQueryClient();
  const [isOpen, setIsOpen] = useState(false);
  const [isVehicleOpen, setIsVehicleOpen] = useState(false);
  const [isRouteOpen, setIsRouteOpen] = useState(false);
  const [isRoutesLibraryOpen, setIsRoutesLibraryOpen] = useState(false);
  const [routesAutoStart, setRoutesAutoStart] = useState(false);
  const [isWarehousesOpen, setIsWarehousesOpen] = useState(false);
  const [openSessionId, setOpenSessionId] = useState<string | null>(null);
  const [openVehicleId, setOpenVehicleId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [vehicleError, setVehicleError] = useState<string | null>(null);
  const [routeError, setRouteError] = useState<string | null>(null);
  const [formState, setFormState] = useState(EMPTY_FORM);
  const [vehicleForm, setVehicleForm] = useState(EMPTY_VEHICLE_FORM);
  const [routeForm, setRouteForm] = useState(EMPTY_ROUTE_FORM);
  const [fixedVehicleId, setFixedVehicleId] = useState<string | null>(null);

  const sessionsQuery = useQuery({
    queryKey: logisticsKeys.vehicleSessions.list({}),
    queryFn: () => listVehicleSessions({}),
  });
  const vehiclesQuery = useQuery({ queryKey: logisticsKeys.vehicles(), queryFn: listVehicles });
  const driversQuery = useQuery({
    queryKey: logisticsKeys.vehicleSessions.drivers(),
    queryFn: listDriverOptions,
  });
  const warehousesQuery = useQuery({
    queryKey: logisticsKeys.warehouses(),
    queryFn: listWarehouses,
  });
  const routesQuery = useQuery({
    queryKey: logisticsKeys.routes.list({}),
    queryFn: () => listRoutes({}),
  });
  const plannedReservationsQuery = useQuery({
    queryKey: planningKeys.reservations.list({ start: "now" }),
    queryFn: () => listPlanningReservations({ start: new Date().toISOString() }),
  });

  const createMutation = useMutation({
    mutationFn: () =>
      createVehicleSession({
        vehicle_id: formState.vehicle_id,
        driver_id: formState.driver_id,
        origin_warehouse_id: formState.origin_warehouse_id || null,
        route_id: formState.route_id,
      }),
    onSuccess: async (session) => {
      setIsOpen(false);
      setFormState(EMPTY_FORM);
      setError(null);
      await queryClient.invalidateQueries({ queryKey: logisticsKeys.vehicleSessions.all() });
      setOpenSessionId(session.id);
    },
  });

  const createVehicleMutation = useMutation({
    mutationFn: () =>
      createVehicle({
        plate: vehicleForm.plate,
        vehicle_type: vehicleForm.vehicle_type || null,
        brand: vehicleForm.brand || null,
        model: vehicleForm.model || null,
        capacity_weight: vehicleForm.capacity_weight ? Number(vehicleForm.capacity_weight) : null,
        warehouse_id: vehicleForm.warehouse_id || null,
      }),
    onSuccess: async (vehicle) => {
      setIsVehicleOpen(false);
      setVehicleForm(EMPTY_VEHICLE_FORM);
      setVehicleError(null);
      setFormState((current) => ({
        ...current,
        vehicle_id: vehicle.id,
        origin_warehouse_id: current.origin_warehouse_id || vehicle.warehouse_id || "",
      }));
      setRouteForm((current) => ({ ...current, vehicle_id: vehicle.id }));
      await queryClient.invalidateQueries({ queryKey: logisticsKeys.vehicles() });
    },
  });

  const createRouteMutation = useMutation({
    mutationFn: () =>
      createRoute({
        route_date: routeForm.route_date,
        vehicle_id: routeForm.vehicle_id || null,
        notes: routeForm.notes || null,
      }),
    onSuccess: async (route) => {
      setIsRouteOpen(false);
      setRouteForm(EMPTY_ROUTE_FORM);
      setRouteError(null);
      setFormState((current) => ({ ...current, route_id: route.id }));
      await queryClient.invalidateQueries({ queryKey: logisticsKeys.routes.all() });
    },
  });

  const routeMap = useMemo(
    () => new Map((routesQuery.data ?? []).map((route) => [route.id, route])),
    [routesQuery.data]
  );

  const vehicleCards = useMemo(
    () => buildVehicleProjectionCards(vehiclesQuery.data ?? [], sessionsQuery.data ?? []),
    [sessionsQuery.data, vehiclesQuery.data]
  );

  const selectedVehicleCard: VehicleProjectionCard | null =
    vehicleCards.find((card) => card.vehicle_id === openVehicleId) ?? null;
  const selectedVehicleReservations = (plannedReservationsQuery.data ?? []).filter(
    (reservation) =>
      reservation.vehicle_id === selectedVehicleCard?.vehicle_id &&
      reservation.linked_session_id == null &&
      !["COMPLETED", "CANCELLED", "EXPIRED"].includes(reservation.status)
  );

  const cardsLayoutClass = useMemo(() => {
    if (vehicleCards.length <= 1) {
      return "grid max-w-[260px] grid-cols-1 gap-3";
    }
    if (vehicleCards.length === 2) {
      return "grid max-w-[540px] grid-cols-1 gap-3 md:grid-cols-2";
    }
    if (vehicleCards.length === 3) {
      return "grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-3";
    }
    return "grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-4 2xl:grid-cols-5";
  }, [vehicleCards.length]);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!formState.route_id) {
      setError("Selecciona una ruta antes de crear la jornada.");
      return;
    }
    setError(null);
    try {
      await createMutation.mutateAsync();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "No se pudo crear la jornada.");
    }
  }

  async function onSubmitVehicle(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setVehicleError(null);
    try {
      await createVehicleMutation.mutateAsync();
    } catch (cause) {
      setVehicleError(cause instanceof Error ? cause.message : "No se pudo crear el vehículo.");
    }
  }

  async function onSubmitRoute(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setRouteError(null);
    try {
      await createRouteMutation.mutateAsync();
    } catch (cause) {
      setRouteError(cause instanceof Error ? cause.message : "No se pudo crear la ruta.");
    }
  }

  function openCreateJornadaFromVehicle(vehicleId: string) {
    setOpenVehicleId(null);
    window.setTimeout(() => {
      openCreateJornada(vehicleId);
    }, 0);
  }

  function openSession(sessionId: string) {
    setOpenVehicleId(null);
    window.setTimeout(() => {
      setOpenSessionId(sessionId);
    }, 0);
  }

  function openCreateJornada(vehicleId?: string) {
    setError(null);
    setFixedVehicleId(vehicleId ?? null);
    setFormState((current) => ({
      ...EMPTY_FORM,
      vehicle_id: vehicleId ?? current.vehicle_id,
      origin_warehouse_id:
        vehicleId != null
          ? (vehiclesQuery.data?.find((vehicle) => vehicle.id === vehicleId)?.warehouse_id ?? "")
          : "",
    }));
    setRouteForm((current) => ({
      ...EMPTY_ROUTE_FORM,
      vehicle_id: vehicleId ?? current.vehicle_id,
    }));
    setIsOpen(true);
  }

  return (
    <LogisticsSection
      title="Jornadas"
      description="Centro operativo del reparto: cada jornada concentra vehículo, ruta, carga, salida, retorno y conciliación."
      actions={
        <div className="flex flex-wrap justify-end gap-2">
          <Button
            onClick={() => setIsVehicleOpen(true)}
          >
            Nuevo vehículo
          </Button>
          <Button
            variant="secondary"
            className="border-transparent bg-transparent text-muted-foreground hover:border-border hover:bg-accent/40 hover:text-foreground"
            onClick={() => setIsRoutesLibraryOpen(true)}
          >
            Rutas
          </Button>
          <Button
            variant="secondary"
            className="border-transparent bg-transparent text-muted-foreground hover:border-border hover:bg-accent/40 hover:text-foreground"
            onClick={() => setIsWarehousesOpen(true)}
          >
            Almacenes
          </Button>
        </div>
      }
    >
      {error ? <Alert title="No se pudo completar la acción">{error}</Alert> : null}

      <div className={cardsLayoutClass}>
        {vehicleCards.map((card) => (
          <VehicleJornadaCard
            key={card.vehicle_id}
            card={card}
            onOpenVehicle={setOpenVehicleId}
          />
        ))}
      </div>

      {!vehicleCards.length ? (
        <Card>
          <CardContent className="py-10 text-center text-sm text-muted-foreground">
            No hay vehículos ni jornadas todavía.
          </CardContent>
        </Card>
      ) : null}

      <CreateJornadaDialog
        open={isOpen}
        onClose={() => {
          setIsOpen(false);
          setFormState(EMPTY_FORM);
          setFixedVehicleId(null);
        }}
        form={formState}
        setForm={setFormState}
        vehicles={vehiclesQuery.data ?? []}
        drivers={driversQuery.data ?? []}
        warehouses={warehousesQuery.data ?? []}
        routes={routesQuery.data ?? []}
        isPending={createMutation.isPending}
        onSubmit={onSubmit}
        onOpenCreateVehicle={() => setIsVehicleOpen(true)}
        onOpenCreateRoute={() => {
          setRoutesAutoStart(true);
          setIsRoutesLibraryOpen(true);
        }}
        fixedVehicleId={fixedVehicleId}
        setRouteVehicle={(vehicleId) =>
          setRouteForm((current) => ({ ...current, vehicle_id: vehicleId }))
        }
      />

      <CreateVehicleFromJornadaDialog
        open={isVehicleOpen}
        onClose={() => {
          setIsVehicleOpen(false);
          setVehicleForm(EMPTY_VEHICLE_FORM);
        }}
        form={vehicleForm}
        setForm={setVehicleForm}
        warehouses={warehousesQuery.data ?? []}
        error={vehicleError}
        isPending={createVehicleMutation.isPending}
        onSubmit={onSubmitVehicle}
      />

      <CreateRouteFromJornadaDialog
        open={isRouteOpen}
        onClose={() => {
          setIsRouteOpen(false);
          setRouteForm(EMPTY_ROUTE_FORM);
        }}
        form={routeForm}
        setForm={setRouteForm}
        vehicles={vehiclesQuery.data ?? []}
        error={routeError}
        isPending={createRouteMutation.isPending}
        onSubmit={onSubmitRoute}
      />

      <Dialog
        open={Boolean(openSessionId)}
        title="Panel de la jornada"
        description="Panel completo de carga, ruta, conciliación e historial de la jornada activa."
        onClose={() => setOpenSessionId(null)}
        maxWidthClassName="max-w-[1600px]"
        zIndexClassName="z-[70]"
      >
        {openSessionId ? (
          <div className="h-[60vh] overflow-y-auto">
            <VehicleSessionDetailPage
              sessionIdOverride={openSessionId}
              embedded
              onClose={() => setOpenSessionId(null)}
            />
          </div>
        ) : null}
      </Dialog>

      <VehicleJornadasDialog
        open={Boolean(openVehicleId && selectedVehicleCard)}
        card={selectedVehicleCard}
        onClose={() => setOpenVehicleId(null)}
        onOpenSession={openSession}
        onCreateJornada={openCreateJornadaFromVehicle}
        plannedReservations={selectedVehicleReservations}
      />

      <Dialog
        open={isRoutesLibraryOpen}
        onClose={() => {
          setIsRoutesLibraryOpen(false);
          setRoutesAutoStart(false);
        }}
        maxWidthClassName="max-w-[1500px]"
      >
        <RoutesPage
          autoStart={routesAutoStart}
          onRouteCreated={(routeId) => {
            setFormState((current) => ({ ...current, route_id: routeId }));
            setIsRoutesLibraryOpen(false);
            setRoutesAutoStart(false);
          }}
        />
      </Dialog>

      <Dialog
        open={isWarehousesOpen}
        title="Almacenes"
        description="Superficie secundaria de almacenes y zonas accesible desde Jornadas."
        onClose={() => setIsWarehousesOpen(false)}
        maxWidthClassName="max-w-[1500px]"
      >
        <div className="h-[70vh] overflow-y-auto">
          <WarehousesPage />
        </div>
      </Dialog>
    </LogisticsSection>
  );
}
