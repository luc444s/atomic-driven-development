import { Badge } from "../../../../../apps/web/src/shared/ui/badge";
import { Card } from "../../../../../apps/web/src/shared/ui/card";
import { cn } from "../../../../../apps/web/src/shared/ui/cn";
import { VEHICLE_SESSION_STATUS_LABELS } from "../../api";
import { VehicleSessionStatusBadge } from "./VehicleSessionStatusBadge";
import type { VehicleProjectionCard } from "./vehicle-jornadas-projection";

type Props = {
  card: VehicleProjectionCard;
  onOpenVehicle: (vehicleId: string) => void;
};

export function VehicleJornadaCard({ card, onOpenVehicle }: Props) {
  const semanticStatus = card.active_session?.status ?? card.latest_session_status;
  const activeLabel = semanticStatus
    ? VEHICLE_SESSION_STATUS_LABELS[semanticStatus] ?? semanticStatus
    : "Sin activa";
  const cardToneClass =
    semanticStatus === "LOADING"
      ? "border-amber-500/30 bg-amber-500/5 hover:bg-amber-500/10"
      : semanticStatus === "READY_TO_DEPART"
        ? "border-sky-500/30 bg-sky-500/5 hover:bg-sky-500/10"
        : semanticStatus === "OUTBOUND"
          ? "border-emerald-500/30 bg-emerald-500/5 hover:bg-emerald-500/10"
          : semanticStatus === "RETURNING"
            ? "border-violet-500/30 bg-violet-500/5 hover:bg-violet-500/10"
            : semanticStatus === "AWAITING_RECONCILIATION"
              ? "border-orange-500/30 bg-orange-500/5 hover:bg-orange-500/10"
              : semanticStatus === "CLOSED"
                ? "border-emerald-500/20 bg-emerald-500/5 hover:bg-emerald-500/10"
                : semanticStatus === "CANCELLED"
                  ? "border-rose-500/30 bg-rose-500/5 hover:bg-rose-500/10"
                  : semanticStatus === "DRAFT"
                    ? "border-slate-500/30 bg-slate-500/5 hover:bg-slate-500/10"
                    : "border-border bg-card hover:border-border/80 hover:bg-accent/20";

  return (
    <Card
      className={cn("cursor-pointer rounded-2xl p-3 transition", cardToneClass)}
      onDoubleClick={() => onOpenVehicle(card.vehicle_id)}
    >
      <div className="space-y-2 text-sm">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <p className="truncate text-base font-semibold leading-none text-foreground">
              {card.vehicle_plate}
            </p>
          </div>
          {card.active_session ? (
            <VehicleSessionStatusBadge status={card.active_session.status} />
          ) : (
            <Badge className="border-slate-500/30 bg-slate-500/10 text-slate-700 dark:text-slate-200">
              Sin activa
            </Badge>
          )}
        </div>
        <p className="truncate font-medium text-foreground">
          {card.active_session ? "Activa" : "Sin jornada activa"}
        </p>
        <p className="truncate text-xs text-muted-foreground">
          Pend {card.pending_sessions.length} · Hist {card.historical_sessions.length}
        </p>
        <p className="truncate text-[11px] text-muted-foreground">{activeLabel}</p>
      </div>
    </Card>
  );
}
