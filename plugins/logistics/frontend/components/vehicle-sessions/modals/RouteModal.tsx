import { Dialog } from "../../../../../../apps/web/src/shared/ui/dialog";
import { SessionRouteTab } from "../SessionRouteTab";

type Props = {
  open: boolean;
  onClose: () => void;
  sessionId: string;
  sessionStatus: string;
  routeId: string | null;
  routeDate: string | null;
  routeOriginLabel: string | null;
  routeDestinationLabel: string | null;
};

export function RouteModal({
  open,
  onClose,
  routeId,
  routeDate,
  routeOriginLabel,
  routeDestinationLabel,
  sessionId,
  sessionStatus,
}: Props) {
  return (
    <Dialog
      open={open}
      onClose={onClose}
      title="Contexto de ruta"
      description="Superficie base para operar la ruta sin salir del ciclo principal."
      maxWidthClassName="max-w-4xl"
    >
      <SessionRouteTab
        routeId={routeId}
        routeDate={routeDate}
        routeOriginLabel={routeOriginLabel}
        routeDestinationLabel={routeDestinationLabel}
        sessionId={sessionId}
        sessionStatus={sessionStatus}
        open={open}
      />
    </Dialog>
  );
}
