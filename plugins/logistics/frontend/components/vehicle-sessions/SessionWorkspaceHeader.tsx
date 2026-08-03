import { Badge } from "../../../../../apps/web/src/shared/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "../../../../../apps/web/src/shared/ui/card";

import { VEHICLE_SESSION_STATUS_LABELS, type VehicleSessionDetail } from "../../api";
import { formatRouteLabel } from "../../lib/route-labels";

function SessionStatusBadge({ status }: { status: string }) {
  const variant =
    status === "OUTBOUND"
      ? "success"
      : status === "RETURNING"
        ? "warning"
        : status === "CLOSED"
          ? "outline"
          : "secondary";

  return (
    <Badge
      variant={
        variant as
          | "default"
          | "secondary"
          | "destructive"
          | "outline"
          | "success"
          | "warning"
      }
    >
      {VEHICLE_SESSION_STATUS_LABELS[status] ?? status}
    </Badge>
  );
}

type Props = {
  session: VehicleSessionDetail;
};

export function SessionWorkspaceHeader({ session }: Props) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-3">
          <span>{session.vehicle_plate}</span>
          <SessionStatusBadge status={session.status} />
        </CardTitle>
        <CardDescription>
          {session.driver_name} · {session.origin_warehouse_name} · {session.mobile_warehouse_code}
        </CardDescription>
      </CardHeader>
      <CardContent className="grid gap-3 text-sm md:grid-cols-2 xl:grid-cols-4">
        <div>
          <span className="font-medium">Apertura:</span> {new Date(session.opened_at).toLocaleString()}
        </div>
        <div>
          <span className="font-medium">Ruta:</span>{" "}
          {formatRouteLabel({
            route_date: session.route_date,
            route_id: session.route_id,
            origin_label: session.route_origin_label,
            destination_label: session.route_destination_label,
          })}
        </div>
        <div>
          <span className="font-medium">Peso planificado:</span> {session.planned_weight_kg ?? 0} kg
        </div>
        <div>
          <span className="font-medium">Peso confirmado:</span> {session.loaded_weight_kg ?? 0} kg
        </div>
      </CardContent>
    </Card>
  );
}
