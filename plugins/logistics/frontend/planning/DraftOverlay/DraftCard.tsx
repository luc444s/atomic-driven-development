import { Button } from "@systutor/shell/ui/button";
import type { QuoteDraftListItem } from "../../../../../plugins/ventas/cotizacion/frontend/api";

interface DraftCardProps {
  draft: QuoteDraftListItem;
  onConfirm: (id: string) => void;
  onPlanificar: (id: string) => void;
}

export function DraftCard({ draft, onConfirm, onPlanificar }: DraftCardProps) {
  const isConfirmed = draft.status === "CONFIRMED";

  return (
    <div
      className={`rounded border-l-2 p-2 text-xs ${
        isConfirmed
          ? "border-l-emerald-500/40 bg-emerald-500/5"
          : "border-l-muted-foreground/30 bg-white/5"
      }`}
    >
      <div className="flex items-center justify-between gap-2">
        <div className="truncate min-w-0" title={`${draft.customer_name ?? "Sin cliente"} · ${draft.delivery_date}`}>
          <span className="text-primary/70 font-mono">
            #{draft.id.slice(0, 4).toUpperCase()}
          </span>
          <span className="ml-2 text-muted-foreground">{draft.customer_name ?? "—"}</span>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          {isConfirmed ? (
            <>
              <span className="text-emerald-400" title="Listo para planificar">⚡</span>
              <Button variant="primary" className="!text-[10px] !px-2 !py-0.5 h-5" onClick={() => onPlanificar(draft.id)}>
                Planificar
              </Button>
            </>
          ) : (
            <Button variant="secondary" className="!text-[10px] !px-2 !py-0.5 h-5" onClick={() => onConfirm(draft.id)}>
              Confirmar
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
