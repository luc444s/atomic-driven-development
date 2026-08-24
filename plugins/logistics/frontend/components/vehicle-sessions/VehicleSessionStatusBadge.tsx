import { Badge } from "@systutor/shell/ui/badge";
import { cn } from "@systutor/shell/ui/cn";
import { VEHICLE_SESSION_STATUS_LABELS } from "../../api";

const STATUS_BADGE_CLASSES: Record<string, string> = {
  DRAFT:
    "border-border bg-muted text-muted-foreground",
  LOADING:
    "border-warning/30 bg-warning/10 text-warning",
  READY_TO_DEPART:
    "border-primary/30 bg-primary/10 text-primary",
  OUTBOUND:
    "border-success/30 bg-success/10 text-success",
  RETURNING:
    "border-accent/30 bg-accent/10 text-accent-foreground",
  AWAITING_RECONCILIATION:
    "border-warning/30 bg-warning/10 text-warning",
  CLOSED:
    "border-success/30 bg-success/10 text-success",
  CANCELLED:
    "border-destructive/30 bg-destructive/10 text-destructive",
};

export function VehicleSessionStatusBadge({ status }: { status: string }) {
  return (
    <Badge className={cn(STATUS_BADGE_CLASSES[status] ?? STATUS_BADGE_CLASSES.DRAFT)}>
      {VEHICLE_SESSION_STATUS_LABELS[status] ?? status}
    </Badge>
  );
}
