import { Dialog } from "../../../../../../apps/web/src/shared/ui/dialog";
import { SessionRouteTab } from "../SessionRouteTab";

type Props = {
  open: boolean;
  onClose: () => void;
  sessionId: string;
  sessionStatus: string;
  routeId: string | null;
};

export function RouteModal({ open, onClose, routeId, sessionId, sessionStatus }: Props) {
  return (
    <Dialog
      open={open}
      onClose={onClose}
      title="Contexto de ruta"
      description="Superficie base para operar la ruta sin salir del ciclo principal."
      maxWidthClassName="max-w-4xl"
    >
      <SessionRouteTab routeId={routeId} sessionId={sessionId} sessionStatus={sessionStatus} open={open} />
    </Dialog>
  );
}
