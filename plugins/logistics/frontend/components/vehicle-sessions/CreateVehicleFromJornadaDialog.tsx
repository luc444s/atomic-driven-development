import { Alert } from "@systutor/shell/ui/alert";
import { Button } from "@systutor/shell/ui/button";
import { Dialog } from "@systutor/shell/ui/dialog";
import { Input } from "@systutor/shell/ui/input";
import { Select } from "@systutor/shell/ui/select";
import { getRealWarehouses } from "../../api/warehouses";
import type { LogisticsWarehouse } from "../../api";

export type JornadaVehicleForm = {
  plate: string;
  vehicle_type: string;
  brand: string;
  model: string;
  capacity_weight: string;
  warehouse_id: string;
};

type Props = {
  open: boolean;
  onClose: () => void;
  form: JornadaVehicleForm;
  setForm: React.Dispatch<React.SetStateAction<JornadaVehicleForm>>;
  warehouses: LogisticsWarehouse[];
  error: string | null;
  isPending: boolean;
  onSubmit: (event: React.FormEvent<HTMLFormElement>) => void;
};

export function CreateVehicleFromJornadaDialog({
  open,
  onClose,
  form,
  setForm,
  warehouses,
  error,
  isPending,
  onSubmit,
}: Props) {
  const realWarehouses = getRealWarehouses(warehouses);

  return (
    <Dialog
      open={open}
      title="Crear vehículo desde jornada"
      description="Registra una unidad nueva sin salir del flujo principal de la jornada."
      onClose={onClose}
    >
      <form className="space-y-4" onSubmit={onSubmit}>
        {error ? <Alert title="No se pudo crear el vehículo">{error}</Alert> : null}
        <label className="block space-y-2 text-sm text-foreground">
          <span>Placa</span>
          <Input value={form.plate} onChange={(event) => setForm((current) => ({ ...current, plate: event.target.value }))} />
        </label>
        <div className="grid gap-4 md:grid-cols-2">
          <label className="block space-y-2 text-sm text-foreground">
            <span>Tipo</span>
            <Input value={form.vehicle_type} onChange={(event) => setForm((current) => ({ ...current, vehicle_type: event.target.value }))} />
          </label>
          <label className="block space-y-2 text-sm text-foreground">
            <span>Marca</span>
            <Input value={form.brand} onChange={(event) => setForm((current) => ({ ...current, brand: event.target.value }))} />
          </label>
        </div>
        <div className="grid gap-4 md:grid-cols-2">
          <label className="block space-y-2 text-sm text-foreground">
            <span>Modelo</span>
            <Input value={form.model} onChange={(event) => setForm((current) => ({ ...current, model: event.target.value }))} />
          </label>
          <label className="block space-y-2 text-sm text-foreground">
            <span>Capacidad</span>
            <Input value={form.capacity_weight} onChange={(event) => setForm((current) => ({ ...current, capacity_weight: event.target.value }))} />
          </label>
        </div>
        <label className="block space-y-2 text-sm text-foreground">
          <span>Almacén base</span>
          <Select
            value={form.warehouse_id}
            onChange={(value) => setForm((current) => ({ ...current, warehouse_id: value }))}
            placeholder="Sin asignar"
            options={realWarehouses.map((warehouse) => ({ value: warehouse.id, label: `${warehouse.code} · ${warehouse.name}` }))}
          />
        </label>
        <div className="flex justify-end gap-3">
          <Button type="submit" disabled={isPending}>
            Guardar vehículo
          </Button>
        </div>
      </form>
    </Dialog>
  );
}
