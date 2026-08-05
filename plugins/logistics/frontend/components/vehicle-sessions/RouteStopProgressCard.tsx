import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "../../../../../apps/web/src/shared/ui/card";
import type { RouteStopProgress } from "../../api";
import { formatStopOutcomeType, formatStopStatus, STOP_STATUS_BORDER_COLORS } from "./jornada-labels";
import type { RouteSelectOption } from "./RouteOperationForm";

type Props = {
  stopOptions: RouteSelectOption[];
  progress: RouteStopProgress[];
};

export function RouteStopProgressCard({ stopOptions, progress }: Props) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Progreso real de paradas</CardTitle>
        <CardDescription>
          Estado derivado desde operaciones confirmadas e incidencias abiertas.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-2">
        {progress.length ? (
          progress.map((entry) => {
            const stopLabel = stopOptions.find((option) => option.value === entry.route_stop_id)?.label ?? entry.route_stop_id;
            return (
              <div key={entry.route_stop_id} className={`rounded-lg border-r border-t border-b border-l-4 border-border ${STOP_STATUS_BORDER_COLORS[entry.progress_status] ?? "border-l-gray-400"} px-3 py-2 text-sm text-foreground`}>
                <div className="font-medium">{stopLabel}</div>
                <div className="text-muted-foreground">
                  {formatStopStatus(entry.progress_status)} · Incidencias abiertas: {entry.open_incidents}
                  {entry.completion_percent != null ? ` · ${entry.completion_percent}%` : ""}
                  {entry.outcome_type ? ` · ${formatStopOutcomeType(entry.outcome_type)}` : ""}
                </div>
                {entry.driver_note ? <div className="mt-1 text-muted-foreground">{entry.driver_note}</div> : null}
              </div>
            );
          })
        ) : (
          <p className="text-sm text-muted-foreground">Sin paradas progresadas todavía.</p>
        )}
      </CardContent>
    </Card>
  );
}
