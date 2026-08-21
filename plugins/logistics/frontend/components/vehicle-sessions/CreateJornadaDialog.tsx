import { useEffect, useState } from "react";
import { Button } from "@systutor/shell/ui/button";
import { Dialog } from "@systutor/shell/ui/dialog";
import { Select } from "@systutor/shell/ui/select";
import { LocationMap } from "@systutor/shell/ui/location-map";
import { useQuery } from "../../../../../apps/web/src/lib/react-query";
import { CustomerSearchDialog } from "../../../../crm/frontend/components/CustomerSearchDialog";
import { listCustomerAddressesByCustomers } from "../../api/delivery-points";
import { getRealWarehouses } from "../../api/warehouses";
import type { DriverOption, LogisticsRoute, LogisticsVehicle, LogisticsWarehouse } from "../../api";
import { formatRouteLabel } from "../../lib/route-labels";
import { formatRouteStatus } from "./jornada-labels";
import { DEFAULT_MAP_CENTER } from "../route-builder/map-defaults";
export type JornadaCreateForm = {
  vehicle_id: string;
  driver_id: string;
  origin_warehouse_id: string;
  route_id: string;
  customer_ids: string[];
  address_ids: string[];
  customer_names: Record<string, string>;
};

type Props = {
  open: boolean;
  onClose: () => void;
  form: JornadaCreateForm;
  setForm: React.Dispatch<React.SetStateAction<JornadaCreateForm>>;
  vehicles: LogisticsVehicle[];
  drivers: DriverOption[];
  warehouses: LogisticsWarehouse[];
  routes: LogisticsRoute[];
  isPending: boolean;
  onSubmit: (event: React.FormEvent<HTMLFormElement>) => void;
  onOpenCreateVehicle: () => void;
  onOpenCreateRoute: () => void;
  setRouteVehicle: (vehicleId: string) => void;
  fixedVehicleId?: string | null;
};

export function CreateJornadaDialog({
  open,
  onClose,
  form,
  setForm,
  vehicles,
  drivers,
  warehouses,
  routes,
  isPending,
  onSubmit,
  onOpenCreateVehicle,
  onOpenCreateRoute,
  setRouteVehicle,
  fixedVehicleId,
}: Props) {
  const originWarehouses = getRealWarehouses(warehouses);
  const fixedVehicle = fixedVehicleId
    ? vehicles.find((vehicle) => vehicle.id === fixedVehicleId) ?? null
    : null;

  const [isCustomerSearchOpen, setIsCustomerSearchOpen] = useState(false);
  const [customerNames, setCustomerNames] = useState<Record<string, string>>({});
  const [addressesQuery, setAddressesQuery] = useState<
    { id: string; customer_id: string; line1: string; latitude: number | null; longitude: number | null }[]
  >([]);

  const addressesByCustomers = useQuery({
    queryKey: ["logistics", "jornada-addresses", form.customer_ids],
    queryFn: () => listCustomerAddressesByCustomers(form.customer_ids.join(",")),
    enabled: form.customer_ids.length > 0,
  });

  useEffect(() => {
    setAddressesQuery(addressesByCustomers.data ?? []);
  }, [addressesByCustomers.data]);

  function toggleCustomer(customer: { id: string; display_name: string }) {
    if (form.customer_ids.includes(customer.id)) {
      setForm((current) => ({
        ...current,
        customer_ids: current.customer_ids.filter((id) => id !== customer.id),
        delivery_point_ids: current.delivery_point_ids,
      }));
    } else {
      setForm((current) => ({
        ...current,
        customer_ids: [...current.customer_ids, customer.id],
        customer_names: { ...current.customer_names, [customer.id]: customer.display_name },
      }));
      setCustomerNames((current) => ({ ...current, [customer.id]: customer.display_name }));
    }
  }

  function toggleAddress(addressId: string) {
    setForm((current) => ({
      ...current,
      address_ids: current.address_ids.includes(addressId)
        ? current.address_ids.filter((id) => id !== addressId)
        : [...current.address_ids, addressId],
    }));
  }

  const gpsMarkers = addressesQuery
    .filter((address) => address.latitude != null && address.longitude != null)
    .map((address) => ({
      id: address.id,
      position: { lat: address.latitude!, lng: address.longitude! },
      label: `${customerNames[address.customer_id] ?? ""} — ${address.line1}`,
    }));

  const originWarehouse = form.origin_warehouse_id
    ? originWarehouses.find((warehouse) => warehouse.id === form.origin_warehouse_id) ?? null
    : null;
  const hasOriginPoint =
    originWarehouse?.latitude != null && originWarehouse?.longitude != null;
  const mapMarkers = [
    ...(hasOriginPoint
      ? [
          {
            id: "origin",
            position: { lat: originWarehouse!.latitude!, lng: originWarehouse!.longitude! },
            label: "Inicio",
            labelVisible: true,
            color: "origin" as const,
          },
        ]
      : []),
    ...gpsMarkers,
  ];

  return (
    <Dialog
      open={open}
      title="Nueva jornada"
      description="Crea la jornada en un solo flujo. Si usas direcciones, el sistema debe generar la ruta asignada antes de crear la jornada."
      onClose={onClose}
    >
      <form className="space-y-4" onSubmit={onSubmit}>
        {fixedVehicle ? (
          <div className="rounded-md border border-border p-4">
            <p className="mb-3 text-sm font-medium text-foreground">Vehículo</p>
            <p className="text-sm text-foreground">{fixedVehicle.plate}</p>
          </div>
        ) : (
          <label className="block space-y-2 text-sm text-foreground">
            <span>Vehículo</span>
            <div className="space-y-2">
              <Select
                value={form.vehicle_id}
                onChange={(value) => {
                  setForm((current) => ({ ...current, vehicle_id: value }));
                  setRouteVehicle(value);
                }}
                options={vehicles.map((vehicle) => ({ value: vehicle.id, label: vehicle.plate }))}
              />
              <Button type="button" variant="secondary" onClick={onOpenCreateVehicle}>
                Crear vehículo
              </Button>
            </div>
          </label>
        )}
        <label className="block space-y-2 text-sm text-foreground">
          <span>Conductor</span>
          <Select
            value={form.driver_id}
            onChange={(value) => setForm((current) => ({ ...current, driver_id: value }))}
            options={drivers.map((driver) => ({ value: driver.id, label: driver.full_name }))}
          />
        </label>
        <label className="block space-y-2 text-sm text-foreground">
          <span>Almacén origen</span>
          <Select
            value={form.origin_warehouse_id}
            onChange={(value) => setForm((current) => ({ ...current, origin_warehouse_id: value }))}
            options={originWarehouses.map((warehouse) => ({ value: warehouse.id, label: `${warehouse.code} · ${warehouse.name}` }))}
          />
        </label>

        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-foreground">Clientes de la jornada</span>
            <Button type="button" variant="secondary" onClick={() => setIsCustomerSearchOpen(true)}>
              Agregar cliente
            </Button>
          </div>
          {form.customer_ids.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {form.customer_ids.map((customerId) => (
                <span
                  key={customerId}
                  className="inline-flex items-center gap-2 rounded-full border border-border bg-surface px-3 py-1 text-xs text-foreground"
                >
                  {customerNames[customerId] ?? customerId}
                  <button
                    type="button"
                    onClick={() => setForm((current) => ({ ...current, customer_ids: current.customer_ids.filter((id) => id !== customerId) }))}
                    className="text-muted-foreground hover:text-foreground"
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          ) : (
            <p className="text-xs text-muted-foreground">
              Agrega los clientes a visitar. Sus puntos de entrega aparecerán en el mapa.
            </p>
          )}
          <CustomerSearchDialog
            open={isCustomerSearchOpen}
            onOpenChange={setIsCustomerSearchOpen}
            onSelect={toggleCustomer}
          />
        </div>

        {addressesQuery.length > 0 ? (
          <div className="space-y-2">
            <span className="block text-sm font-medium text-foreground">Direcciones del cliente (clic para incluir)</span>
            <LocationMap
              center={mapMarkers[0]?.position ?? DEFAULT_MAP_CENTER}
              height={240}
              autoFit
              markers={mapMarkers.map((marker) => {
                if (marker.id === "origin") {
                  return marker;
                }
                const assigned = form.address_ids.includes(marker.id);
                return {
                  ...marker,
                  label: assigned ? "Punto asignado" : `${marker.label}${assigned ? " ✓" : ""}`,
                  labelVisible: assigned,
                  color: (assigned ? "assigned" : "default") as const,
                };
              })}
              onMarkerClick={(id) => {
                if (id !== "origin") {
                  toggleAddress(id);
                }
              }}
            />
            <div className="grid gap-1">
              {addressesQuery.map((address) => {
                const selected = form.address_ids.includes(address.id);
                return (
                  <button
                    key={address.id}
                    type="button"
                    onClick={() => toggleAddress(address.id)}
                    className={`flex items-center justify-between gap-2 rounded-md border px-3 py-2 text-left text-xs transition ${
                      selected ? "border-primary bg-primary/10 text-foreground" : "border-border bg-surface text-foreground"
                    }`}
                  >
                    <span className="truncate">
                      {customerNames[address.customer_id] ?? ""} — {address.line1}
                    </span>
                    <span className="text-muted-foreground">
                      {address.latitude != null && address.longitude != null ? "📍" : "sin GPS"}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>
        ) : null}
        {form.address_ids.length > 0 ? (
          <div className="rounded-lg border border-dashed border-border p-4 text-center">
            <p className="text-sm text-foreground">
              La ruta se creará automáticamente con el inicio del almacén y las {form.address_ids.length} dirección(es) seleccionada(s).
            </p>
          </div>
        ) : (
          <label className="block space-y-2 text-sm text-foreground">
            <span>Ruta</span>
            {routes.length > 0 ? (
              <div className="space-y-2">
                <Select
                  value={form.route_id}
                  onChange={(value) => setForm((current) => ({ ...current, route_id: value }))}
                  placeholder="Seleccionar ruta"
                  options={routes.map((route) => ({
                    value: route.id,
                    label:
                      formatRouteLabel(route) === route.route_date
                        ? `${route.route_date} · ${formatRouteStatus(route.status)}`
                        : formatRouteLabel(route),
                  }))}
                />
                <Button type="button" variant="secondary" onClick={onOpenCreateRoute}>
                  Crear ruta
                </Button>
              </div>
            ) : (
              <div className="rounded-lg border border-dashed border-border p-4 text-center">
                <p className="text-sm text-muted-foreground">No hay rutas disponibles.</p>
                <p className="mt-1 text-xs text-muted-foreground">
                  Agrega clientes y selecciona sus puntos en el mapa para generar la ruta automáticamente.
                </p>
                <div className="mt-2">
                  <Button type="button" variant="secondary" onClick={onOpenCreateRoute}>
                    Crear ruta manual
                  </Button>
                </div>
              </div>
            )}
          </label>
        )}
        <div className="flex justify-end gap-3">
          <Button type="button" variant="secondary" onClick={onClose}>
            Cancelar
          </Button>
          <Button type="submit" disabled={isPending}>
            {isPending ? "Creando jornada..." : "Crear jornada"}
          </Button>
        </div>
      </form>
    </Dialog>
  );
}
