import { Dialog } from "../../../../../apps/web/src/shared/ui/dialog";
import { Button } from "../../../../../apps/web/src/shared/ui/button";

type Props = {
  open: boolean;
  onClose: () => void;
};

export function OverridePlanningConflictDialog({ open, onClose }: Props) {
  return (
    <Dialog open={open} onClose={onClose} title="Override controlado" description="El override queda documentado en la propia planificación." actions={<Button variant="secondary" onClick={onClose}>Entendido</Button>}>
      <p className="text-sm text-muted-foreground">Usa el formulario de edición para habilitar override y registrar su motivo.</p>
    </Dialog>
  );
}
