import { Badge } from "../../../../../apps/web/src/shared/ui/badge";

const ITEMS = [
  ["PLANNED", "Planificada"],
  ["READY", "Lista"],
  ["IN_PROGRESS", "En curso"],
  ["CONFLICT", "Conflicto"],
  ["COMPLETED", "Completada"],
];

export function PlanningStatusLegend() {
  return (
    <div className="flex flex-wrap gap-2">
      {ITEMS.map(([value, label]) => (
        <Badge key={value} className="bg-muted text-muted-foreground">
          {label}
        </Badge>
      ))}
    </div>
  );
}
