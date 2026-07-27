import { useMemo } from "react";
import { useQuery } from "../../../../../apps/web/src/lib/react-query";
import { listCotizaciones, type QuoteDraftListItem } from "../../../../../plugins/ventas/cotizacion/frontend/api";
import { DraftCard } from "./DraftCard";

interface DraftOverlayProps {
  dateFrom: string;
  dateTo: string;
  onConfirm: (id: string) => void;
  onPlanificar: (id: string) => void;
  onViewAll: () => void;
}

export const DRAFT_OVERLAY_KEY = ["planning", "draft-overlay"] as const;

export function DraftOverlay({ dateFrom, dateTo, onConfirm, onPlanificar, onViewAll }: DraftOverlayProps) {
  const { data: drafts = [], isError: draftsError } = useQuery({
    queryKey: [...DRAFT_OVERLAY_KEY, dateFrom, dateTo],
    queryFn: () =>
      listCotizaciones({
        status: "DRAFT",
        date_from: dateFrom,
        date_to: dateTo,
      }),
    refetchOnWindowFocus: true,
    staleTime: 15_000,
  });

  const { data: confirmed = [], isError: confirmedError } = useQuery({
    queryKey: [...DRAFT_OVERLAY_KEY, "confirmed", dateFrom, dateTo],
    queryFn: () =>
      listCotizaciones({
        status: "CONFIRMED",
        date_from: dateFrom,
        date_to: dateTo,
      }),
    refetchOnWindowFocus: true,
    staleTime: 15_000,
  });

  const allDrafts = useMemo(() => [...drafts, ...confirmed], [drafts, confirmed]);

  const grouped = useMemo(() => {
    const map = new Map<string, QuoteDraftListItem[]>();
    for (const d of allDrafts) {
      const date = d.delivery_date;
      if (!map.has(date)) map.set(date, []);
      map.get(date)!.push(d);
    }
    return map;
  }, [allDrafts]);

  if (draftsError || confirmedError) {
    return (
      <div className="border-t border-white/10 pt-2">
        <div className="text-[10px] uppercase tracking-[0.12em] text-muted-foreground mb-1 px-1">
          Demanda pendiente
        </div>
        <div className="text-xs text-red-400/70 px-1 py-1">
          Error al cargar. ¿Reiniciaste el backend?
        </div>
      </div>
    );
  }

  return (
    <div className="border-t border-white/10 pt-2">
      <div className="flex items-center justify-between mb-1 px-1">
        <span className="text-[10px] uppercase tracking-[0.12em] text-muted-foreground">
          Demanda pendiente
        </span>
        {allDrafts.length === 0 ? (
          <button
            type="button"
            onClick={onViewAll}
            className="text-[10px] text-muted-foreground/50 hover:text-primary transition"
          >
            Ver todos
          </button>
        ) : (
          <button
            type="button"
            onClick={onViewAll}
            className="text-[10px] text-primary hover:text-primary/80 transition"
          >
            Ver todos ({allDrafts.length})
          </button>
        )}
      </div>
      {allDrafts.length === 0 ? (
        <div className="text-xs text-muted-foreground/50 px-1 py-1">
          Sin demanda pendiente en este periodo
        </div>
      ) : (
      <div className="flex gap-3 overflow-x-auto pb-1">
        {Array.from(grouped.entries()).map(([date, dateDrafts]) => (
          <div key={date} className="shrink-0 min-w-[220px] space-y-1">
            <div className="text-[10px] text-muted-foreground/60 px-1">{date}</div>
            {dateDrafts.slice(0, 3).map((d) => (
              <DraftCard
                key={d.id}
                draft={d}
                onConfirm={onConfirm}
                onPlanificar={onPlanificar}
              />
            ))}
            {dateDrafts.length > 3 && (
              <div className="text-[10px] text-muted-foreground/50 px-1">
                +{dateDrafts.length - 3} más
              </div>
            )}
          </div>
        ))}
      </div>
      )}
    </div>
  );
}
