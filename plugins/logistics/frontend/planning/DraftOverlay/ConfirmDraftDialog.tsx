import { Dialog } from "@systutor/shell/ui/dialog";
import { Button } from "@systutor/shell/ui/button";
import type { QuoteDraftDTO } from "../../../../../plugins/ventas/cotizacion/frontend/api";

interface ConfirmDraftDialogProps {
  open: boolean;
  draft: QuoteDraftDTO | null;
  onClose: () => void;
  onConfirm: () => void;
  isPending: boolean;
}

export function ConfirmDraftDialog({ open, draft, onClose, onConfirm, isPending }: ConfirmDraftDialogProps) {
  if (!draft) return null;

  return (
    <Dialog open={open} title="Confirmar cotización" onClose={onClose}>
      <div className="space-y-4 text-sm">
        <p>¿Confirmar <span className="font-mono text-primary/70">#{draft.id.slice(0, 4).toUpperCase()}</span> para planificación?</p>

        <div className="rounded-md border border-border p-3 space-y-2 text-xs">
          <div className="flex gap-2">
            <span className="text-muted-foreground">Cliente</span>
            <span>{draft.customer.name}</span>
          </div>
          <div className="flex gap-2">
            <span className="text-muted-foreground">Items</span>
            <span>{draft.items.map((i) => `${i.quantity} × ${i.product_name ?? i.product_id}`).join(", ")}</span>
          </div>
          <div className="flex gap-2">
            <span className="text-muted-foreground">Entrega</span>
            <span>
              {draft.delivery_date}
              {draft.delivery_time ? ` ${draft.delivery_time}` : ""}
            </span>
          </div>
          {draft.conditions && (
            <div className="flex gap-2">
              <span className="text-muted-foreground">Cond</span>
              <span>{draft.conditions}</span>
            </div>
          )}
          {draft.vehicle && (
            <div className="flex gap-2">
              <span className="text-muted-foreground">Vehículo</span>
              <span>{draft.vehicle.plate}</span>
            </div>
          )}
        </div>

        <p className="text-muted-foreground text-xs">
          Al confirmar, la cotización estará disponible para planificar. Ya no será un borrador.
        </p>

        <div className="flex justify-end gap-3 pt-2">
          <Button variant="secondary" onClick={onClose}>Cancelar</Button>
          <Button onClick={onConfirm} disabled={isPending}>
            {isPending ? "Confirmando..." : "Confirmar"}
          </Button>
        </div>
      </div>
    </Dialog>
  );
}
