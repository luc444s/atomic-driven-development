import type { StockBalanceItem } from "../../../../stock/frontend/types";
import type { VehicleSessionDetail } from "../../api";
import { MobileStockInline } from "./MobileStockInline";
import { OperationalSummaryInline } from "./OperationalSummaryInline";
import { SessionStepper } from "./SessionStepper";
import type { SessionContextKey } from "./session-ui-map";

type Props = {
  session: VehicleSessionDetail;
  mobileRows: StockBalanceItem[];
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

export function VehicleSessionConsole({ session, mobileRows, stepper }: Props) {
  return (
    <div className="space-y-6">
      <div className="space-y-1">
        <p className="text-xs font-semibold uppercase tracking-[0.24em] text-muted-foreground">
          Jornada operativa
        </p>
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
        <OperationalSummaryInline session={session} />
        <MobileStockInline mobileRows={mobileRows} />
      </div>
    </div>
  );
}
