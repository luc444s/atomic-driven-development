import type { StockBalanceItem } from "../../../../stock/frontend/types";
import { Button } from "@systutor/shell/ui/button";
import type { SessionOperationalSummary, VehicleSessionDetail } from "../../api";
import { MobileStockInline } from "./MobileStockInline";
import { OperationalSummaryShell } from "./OperationalSummaryShell";
import { SessionStepper } from "./SessionStepper";
import type { SessionContextKey } from "./session-ui-map";

type Props = {
  session: VehicleSessionDetail;
  mobileRows: StockBalanceItem[];
  operationalSummary: SessionOperationalSummary | null;
  operationalSummaryLoading: boolean;
  cancellation: {
    canCancel: boolean;
    isPending: boolean;
    onOpenConfirm: () => void;
  };
  stepper: {
    nextTransitionAllowed: boolean;
    nextTransitionBlocker: string | null;
    closedAt: string | null;
    isPending: boolean;
    error: { type: "technical" | "business"; message: string } | null;
    onNext: () => void;
    onOpenContext: (context: SessionContextKey) => void;
  };
};

export function VehicleSessionConsole({
  session,
  mobileRows,
  operationalSummary,
  operationalSummaryLoading,
  cancellation,
  stepper,
}: Props) {
  const totalAdr = operationalSummary?.composition?.total_adr_points ?? 0;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-3">
        <div className="space-y-1">
          <p className="text-xs font-semibold uppercase tracking-[0.24em] text-muted-foreground">
            Jornada operativa
          </p>
        </div>
        {cancellation.canCancel ? (
          <Button
            type="button"
            variant="secondary"
            disabled={cancellation.isPending}
            className="border-destructive/30 bg-destructive/10 text-destructive hover:bg-destructive/15"
            onClick={cancellation.onOpenConfirm}
          >
            {cancellation.isPending ? "Cancelando..." : "Cancelar jornada"}
          </Button>
        ) : null}
      </div>

      {totalAdr > 0 ? (
        <div className="rounded-lg border-2 border-rose-500/40 bg-rose-500/10 px-4 py-3">
          <p className="text-sm font-bold uppercase tracking-wider text-rose-600 dark:text-rose-400">
            PELIGRO: VEHÍCULO CON MERCANCÍA PELIGROSA
          </p>
          <p className="mt-1 text-xs text-rose-600/80 dark:text-rose-400/80">
            Puntos ADR totales: {totalAdr}. Consulte la carta porte para el detalle de la carga.
          </p>
        </div>
      ) : null}

      <SessionStepper
        status={session.status}
        nextTransitionAllowed={stepper.nextTransitionAllowed}
        nextTransitionBlocker={stepper.nextTransitionBlocker}
        closedAt={stepper.closedAt}
        isPending={stepper.isPending}
        error={stepper.error}
        onNext={stepper.onNext}
        onOpenContext={stepper.onOpenContext}
      />

      <div className="grid gap-4 xl:grid-cols-[1.4fr_0.9fr] xl:items-stretch">
        <OperationalSummaryShell
          session={session}
          summary={operationalSummary}
          isLoading={operationalSummaryLoading}
        />
        <MobileStockInline mobileRows={mobileRows} />
      </div>
    </div>
  );
}
