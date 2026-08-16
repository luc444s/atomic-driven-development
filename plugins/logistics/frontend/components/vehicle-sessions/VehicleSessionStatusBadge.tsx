import { Badge } from "@systutor/shell/ui/badge";
import { cn } from "@systutor/shell/ui/cn";
import { VEHICLE_SESSION_STATUS_LABELS } from "../../api";

const STATUS_BADGE_CLASSES: Record<string, string> = {
  DRAFT:
    "border-slate-500/30 bg-slate-500/10 text-slate-700 dark:text-slate-200",
  LOADING:
    "border-amber-500/30 bg-amber-500/10 text-amber-700 dark:text-amber-200",
  READY_TO_DEPART:
    "border-sky-500/30 bg-sky-500/10 text-sky-700 dark:text-sky-200",
  OUTBOUND:
    "border-emerald-500/30 bg-emerald-500/10 text-emerald-700 dark:text-emerald-200",
  RETURNING:
    "border-violet-500/30 bg-violet-500/10 text-violet-700 dark:text-violet-200",
  AWAITING_RECONCILIATION:
    "border-orange-500/30 bg-orange-500/10 text-orange-700 dark:text-orange-200",
  CLOSED:
    "border-emerald-500/30 bg-emerald-500/10 text-emerald-700 dark:text-emerald-200",
  CANCELLED:
    "border-rose-500/30 bg-rose-500/10 text-rose-700 dark:text-rose-200",
};

export function VehicleSessionStatusBadge({ status }: { status: string }) {
  return (
    <Badge className={cn(STATUS_BADGE_CLASSES[status] ?? STATUS_BADGE_CLASSES.DRAFT)}>
      {VEHICLE_SESSION_STATUS_LABELS[status] ?? status}
    </Badge>
  );
}
