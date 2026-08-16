import { Alert } from "@systutor/shell/ui/alert";
import { Button } from "@systutor/shell/ui/button";
import { Dialog } from "@systutor/shell/ui/dialog";
import { Input } from "@systutor/shell/ui/input";
import { Select } from "@systutor/shell/ui/select";
import type { LogisticsVehicle } from "../../api";

export type JornadaRouteForm = {
  route_date: string;
  vehicle_id: string;
  notes: string;
};

type Props = {
  open: boolean;
  onClose: () => void;
  form: JornadaRouteForm;
  setForm: React.Dispatch<React.SetStateAction<JornadaRouteForm>>;
  vehicles: LogisticsVehicle[];
  error: string | null;
  isPending: boolean;
  onSubmit: (event: React.FormEvent<HTMLFormElement>) => void;
};

export function CreateRouteFromJornadaDialog({
  open,
  onClose,
  form,
  setForm,
  vehicles,
  error,
  isPending,
  onSubmit,
}: Props) {
  return (
    <Dialog
      open={open}
      title="Crear ruta desde jornada"
      description="Registra una ruta reusable sin abandonar el flujo principal."
      onClose={onClose}
    >
      <form className="space-y-4" onSubmit={onSubmit}>
        {error ? <Alert title="No se pudo crear la ruta">{error}</Alert> : null}
        <label className="block space-y-2 text-sm text-foreground">
          <span>Fecha</span>
          <Input type="date" value={form.route_date} onChange={(event) => setForm((current) => ({ ...current, route_date: event.target.value }))} />
        </label>
        <label className="block space-y-2 text-sm text-foreground">
          <span>Vehículo</span>
          <Select
            value={form.vehicle_id}
            onChange={(value) => setForm((current) => ({ ...current, vehicle_id: value }))}
            placeholder="Sin asignar"
            options={vehicles.map((vehicle) => ({ value: vehicle.id, label: vehicle.plate }))}
          />
        </label>
        <label className="block space-y-2 text-sm text-foreground">
          <span>Notas</span>
          <Input value={form.notes} onChange={(event) => setForm((current) => ({ ...current, notes: event.target.value }))} />
        </label>
        <div className="flex justify-end gap-3">
          <Button type="button" variant="secondary" onClick={onClose}>
            Cancelar
          </Button>
          <Button type="submit" disabled={isPending}>
            Guardar ruta
          </Button>
        </div>
      </form>
    </Dialog>
  );
}
