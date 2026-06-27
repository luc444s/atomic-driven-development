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
    <div className="space-y-3 text-sm text-slate-300">
      <p className="text-slate-400">Vista rápida del movimiento de envases.</p>
      {topStates.length > 0 ? (
        <div className="grid gap-2">
          {topStates.map((item) => (
            <div
              key={item.state}
              className="flex items-center justify-between rounded-lg border border-slate-800 bg-slate-900/60 px-3 py-2.5"
            >
              <div>
                <CylinderStateBadge state={item.state} />
              </div>
              <span className="text-lg font-semibold text-white">{item.count}</span>
            </div>
          ))}
        </div>
      ) : (
        <p className="text-slate-400">Aún no hay registros para mostrar.</p>
      )}
    </div>
  );
}
