import { memo } from "react";

import { Badge } from "@systutor/shell/ui/badge";
import { Card } from "@systutor/shell/ui/card";
import { cn } from "@systutor/shell/ui/cn";
import { VEHICLE_SESSION_STATUS_LABELS } from "../../api";
import { VehicleSessionStatusBadge } from "./VehicleSessionStatusBadge";
import type { VehicleProjectionCard } from "./vehicle-jornadas-projection";

type Props = {
  card: VehicleProjectionCard;
  onOpenVehicle: (vehicleId: string) => void;
};

export const VehicleJornadaCard = memo(function VehicleJornadaCard({
  card,
  onOpenVehicle,
}: Props) {
  const semanticStatus = card.active_session?.status ?? card.latest_session_status;
  const activeLabel = semanticStatus
    ? VEHICLE_SESSION_STATUS_LABELS[semanticStatus] ?? semanticStatus
    : "Sin activa";
  const totalAdr = card.active_session?.current_stock?.total_adr_points ?? 0;
  const cardToneClass =
    semanticStatus === "LOADING"
      ? "border-warning/30 bg-warning/5 hover:bg-warning/10"
      : semanticStatus === "READY_TO_DEPART"
        ? "border-primary/30 bg-primary/5 hover:bg-primary/10"
        : semanticStatus === "OUTBOUND"
          ? "border-success/30 bg-success/5 hover:bg-success/10"
          : semanticStatus === "RETURNING"
            ? "border-accent/30 bg-accent/5 hover:bg-accent/10"
            : semanticStatus === "AWAITING_RECONCILIATION"
              ? "border-warning/30 bg-warning/5 hover:bg-warning/10"
              : semanticStatus === "CLOSED"
                ? "border-success/20 bg-success/5 hover:bg-success/10"
                : semanticStatus === "CANCELLED"
                  ? "border-destructive/30 bg-destructive/5 hover:bg-destructive/10"
                  : semanticStatus === "DRAFT"
                    ? "border-muted bg-muted/5 hover:bg-muted/10"
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
            <Badge className="border-border bg-muted text-muted-foreground">
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
        {totalAdr > 0 ? (
          <div className="rounded-md border border-destructive/30 bg-destructive/10 px-2 py-1">
            <p className="text-[11px] font-semibold uppercase tracking-wider text-destructive">
              ADR {totalAdr} pts
            </p>
          </div>
        ) : null}
      </div>
    </Card>
  );
});
