import { Button } from "../../../../../apps/web/src/shared/ui/button";
import { Dialog } from "../../../../../apps/web/src/shared/ui/dialog";
import { Select } from "../../../../../apps/web/src/shared/ui/select";
import { getRealWarehouses } from "../../api/warehouses";
import type { DriverOption, LogisticsRoute, LogisticsVehicle, LogisticsWarehouse } from "../../api";
import { formatRouteStatus } from "./jornada-labels";

export type JornadaCreateForm = {
  vehicle_id: string;
  driver_id: string;
  origin_warehouse_id: string;
  route_id: string;
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

  return (
    <Dialog
      open={open}
      title="Nueva jornada"
      description="Crea la jornada desde un solo flujo. Aquí mismo puedes seleccionar o crear vehículo y ruta."
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
        <label className="block space-y-2 text-sm text-foreground">
          <span>Ruta (opcional)</span>
          <div className="space-y-2">
            <Select
              value={form.route_id}
              onChange={(value) => setForm((current) => ({ ...current, route_id: value }))}
              placeholder="Sin ruta"
              options={routes.map((route) => ({ value: route.id, label: `${route.route_date} · ${formatRouteStatus(route.status)}` }))}
            />
            <Button type="button" variant="secondary" onClick={onOpenCreateRoute}>
              Crear ruta
            </Button>
          </div>
        </label>
        <div className="flex justify-end gap-3">
          <Button type="button" variant="secondary" onClick={onClose}>
            Cancelar
          </Button>
          <Button type="submit" disabled={isPending}>
            Crear jornada
          </Button>
        </div>
      </form>
    </Dialog>
  );
}
