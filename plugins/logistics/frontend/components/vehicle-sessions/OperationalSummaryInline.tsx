import { Badge } from "../../../../../apps/web/src/shared/ui/badge";

import { VEHICLE_SESSION_STATUS_LABELS, type VehicleSessionDetail } from "../../api";

type Props = {
  session: VehicleSessionDetail;
};

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

export function OperationalSummaryInline({ session }: Props) {
  const items = [
    { label: "Jornada", value: session.vehicle_plate },
    { label: "Conductor", value: session.driver_name },
    { label: "Origen", value: session.origin_warehouse_name },
    { label: "Almacén móvil", value: `${session.mobile_warehouse_code} · ${session.mobile_warehouse_name}` },
    { label: "Ruta", value: session.route_id ?? "Sin ruta" },
    { label: "Apertura", value: new Date(session.opened_at).toLocaleString() },
    { label: "Peso planificado", value: `${session.planned_weight_kg ?? 0} kg` },
    { label: "Peso confirmado", value: `${session.loaded_weight_kg ?? 0} kg` },
    {
      label: "Stock móvil",
      value: `${session.current_stock.total_products} prod · ${session.current_stock.total_units} und`,
    },
    { label: "Última actividad", value: session.last_activity ?? "Sin actividad aún" },
  ];

  return (
    <div className="space-y-3 rounded-2xl bg-muted/35 px-4 py-4 sm:px-5">
      <div className="flex flex-wrap items-center gap-3">
        <p className="text-lg font-semibold tracking-tight text-foreground">{session.vehicle_plate}</p>
        <SessionStatusBadge status={session.status} />
      </div>
      <div className="grid gap-x-6 gap-y-3 text-sm sm:grid-cols-2 xl:grid-cols-5">
        {items.map((item) => (
          <div key={item.label} className="min-w-0">
            <p className="text-[11px] uppercase tracking-wide text-muted-foreground">{item.label}</p>
            <p className="truncate font-medium text-foreground">{item.value}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
