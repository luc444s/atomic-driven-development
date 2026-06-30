import { useQuery } from "../../../apps/web/src/lib/react-query";

import { listCylinderSummary, logisticsKeys } from "./api";
import { CylinderStateBadge, getCylinderStateLabel } from "./CylinderStateBadge";

export function LogisticsSummaryWidget() {
  const summaryQuery = useQuery({
    queryKey: logisticsKeys.cylinders.summary(),
    queryFn: listCylinderSummary,
  });

  const topStates = (summaryQuery.data ?? []).slice(0, 4);

  return (
    <div className="space-y-3 text-sm text-foreground">
      <p className="text-muted-foreground">Vista rápida del movimiento de envases.</p>
      {topStates.length > 0 ? (
        <div className="grid gap-2">
          {topStates.map((item) => (
            <div
              key={item.state}
              className="flex items-center justify-between rounded-lg border border-border bg-surface-alt/60 px-3 py-2.5"
            >
              <div>
                <CylinderStateBadge state={item.state} />
              </div>
              <span className="text-lg font-semibold text-foreground">{item.count}</span>
            </div>
          ))}
        </div>
      ) : (
        <p className="text-muted-foreground">Aún no hay registros para mostrar.</p>
      )}
    </div>
  );
}
