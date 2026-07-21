import type { StockBalanceItem } from "../../../../stock/frontend/types";
import { Button } from "../../../../../apps/web/src/shared/ui/button";
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
