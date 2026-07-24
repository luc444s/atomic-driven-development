import { Button } from "../../../../../apps/web/src/shared/ui/button";
import { Select } from "../../../../../apps/web/src/shared/ui/select";
import type { LogisticsVehicle, LogisticsWarehouse } from "../../api";
import type { CalendarView } from "../../../../../apps/web/src/shared/ui/resource-calendar/resource-calendar";

type Props = {
  view: CalendarView;
  onViewChange: (value: CalendarView) => void;
  focusDate: Date;
  onPrevious: () => void;
  onNext: () => void;
  onToday: () => void;
  vehicleId: string;
  onVehicleChange: (value: string) => void;
  warehouseId: string;
  onWarehouseChange: (value: string) => void;
  vehicles: LogisticsVehicle[];
  warehouses: LogisticsWarehouse[];
  onCreate: () => void;
};

export function PlanningToolbar({
  view,
  onViewChange,
  focusDate,
  onPrevious,
  onNext,
  onToday,
  vehicleId,
  onVehicleChange,
  warehouseId,
  onWarehouseChange,
  vehicles,
  warehouses,
  onCreate,
}: Props) {
  const focusLabel = focusDate.toLocaleDateString(undefined, {
    month: "long",
    year: "numeric",
  });

  return (
    <div className="flex flex-col gap-3 rounded-2xl border border-border bg-card p-4 lg:flex-row lg:items-center lg:justify-between">
      <div className="flex flex-wrap items-center gap-2">
        <Button variant="secondary" onClick={onPrevious}>Anterior</Button>
        <Button variant="secondary" onClick={onToday}>Hoy</Button>
        <Button variant="secondary" onClick={onNext}>Siguiente</Button>
        <span className="ml-1 text-sm font-medium capitalize text-foreground">{focusLabel}</span>
      </div>

      <div className="grid gap-3 md:grid-cols-3 lg:min-w-[680px]">
        <Select
          value={view}
          onChange={(value) => onViewChange(value as CalendarView)}
          options={[
            { value: "month", label: "Mes" },
            { value: "week", label: "Semana" },
            { value: "day", label: "Dia" },
          ]}
        />
        <Select
          value={warehouseId}
          onChange={onWarehouseChange}
          placeholder="Todos los almacenes"
          options={[{ value: "", label: "Todos los almacenes" }, ...warehouses.map((warehouse) => ({ value: warehouse.id, label: warehouse.name }))]}
        />
        <Select
          value={vehicleId}
          onChange={onVehicleChange}
          placeholder="Todos los vehículos"
          options={[{ value: "", label: "Todos los vehículos" }, ...vehicles.map((vehicle) => ({ value: vehicle.id, label: vehicle.plate }))]}
        />
      </div>

      <Button onClick={onCreate}>Nueva planificación</Button>
    </div>
  );
}
