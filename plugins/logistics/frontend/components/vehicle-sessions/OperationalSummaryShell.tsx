import { useState } from "react";

import { Button } from "@systutor/shell/ui/button";
import type { SessionOperationalSummary, VehicleSessionDetail } from "../../api";
import { OperationalSummaryDetailDialog } from "./OperationalSummaryDetailDialog";
import { OperationalSummaryInline } from "./OperationalSummaryInline";

type Props = {
  session: VehicleSessionDetail;
  summary: SessionOperationalSummary | null;
  isLoading: boolean;
};

export function OperationalSummaryShell({ session, summary, isLoading }: Props) {
  const [detailOpen, setDetailOpen] = useState(false);

  return (
    <div className="space-y-3">
      <OperationalSummaryInline session={session} summary={summary} isLoading={isLoading} />
      <div className="flex justify-end">
        <Button type="button" variant="secondary" disabled={!summary} onClick={() => setDetailOpen(true)}>
          Ver detalle
        </Button>
      </div>
      <OperationalSummaryDetailDialog open={detailOpen} summary={summary} onClose={() => setDetailOpen(false)} />
    </div>
  );
}
