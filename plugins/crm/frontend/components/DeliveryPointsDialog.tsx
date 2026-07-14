import { Dialog } from "../../../../apps/web/src/shared/ui/dialog";
import { DeliveryPointsSection } from "./DeliveryPointsSection";

type DeliveryPointsDialogProps = {
  open: boolean;
  onClose: () => void;
  deliveryPoints: Array<{ id: string; address: string; contact_name: string | null; phone: string | null; delivery_day: string | null; time_window: string | null; is_active: boolean }>;
  isLoading: boolean;
};

export function DeliveryPointsDialog({ open, onClose, deliveryPoints, isLoading }: DeliveryPointsDialogProps) {
  return (
    <Dialog
      open={open}
      title="Puntos de entrega"
      description="Vista operativa de los puntos de entrega gestionados por logistics para este cliente."
      onClose={onClose}
      maxWidthClassName="max-w-5xl"
    >
      <DeliveryPointsSection points={deliveryPoints} isLoading={isLoading} />
    </Dialog>
  );
}
