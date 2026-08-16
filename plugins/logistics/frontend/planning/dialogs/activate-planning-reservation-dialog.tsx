import { Dialog } from "@systutor/shell/ui/dialog";
import { Button } from "@systutor/shell/ui/button";
import type { PlanningReservation } from "../../api";

type Props = {
  open: boolean;
  reservation: PlanningReservation | null;
  onClose: () => void;
  onConfirm: () => Promise<void>;
  isPending: boolean;
};

export function ActivatePlanningReservationDialog({ open, reservation, onClose, onConfirm, isPending }: Props) {
  if (!open || !reservation) {
    return null;
  }

  return (
    <Dialog
      open={open}
      onClose={onClose}
      title="Materializar jornada"
      description="Esto crea una jornada en DRAFT o la deja en cola para el vehículo."
      actions={<Button onClick={() => void onConfirm()}>{isPending ? "Materializando..." : "Confirmar"}</Button>}
    >
      <p className="text-sm text-muted-foreground">
        Vehículo {reservation.vehicle_plate} · {reservation.expected_load_summary.total_units} unidades.
      </p>
    </Dialog>
  );
}
