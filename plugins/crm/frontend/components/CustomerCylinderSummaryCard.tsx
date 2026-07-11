import { useState } from "react";

import { useAuthStore } from "../../../../apps/web/src/features/auth/store";
import { useQuery } from "../../../../apps/web/src/lib/react-query";
import { Alert } from "../../../../apps/web/src/shared/ui/alert";
import { Button } from "../../../../apps/web/src/shared/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../../../../apps/web/src/shared/ui/card";
import {
  getCustomerCylinderSummary,
  logisticsKeys,
} from "../../../logistics/frontend/api";
import { CustomerCylinderSummaryDialog } from "./CustomerCylinderSummaryDialog";

type CustomerCylinderSummaryCardProps = {
  customerId: string;
};

function MetricBox({
  label,
  value,
  tone = "text-foreground",
}: {
  label: string;
  value: number;
  tone?: string;
}) {
  return (
    <div>
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className={`text-2xl font-semibold ${tone}`}>{value}</p>
    </div>
  );
}

export function CustomerCylinderSummaryCard({ customerId }: CustomerCylinderSummaryCardProps) {
  const permissions = useAuthStore((state) => state.permissions);
  const [open, setOpen] = useState(false);
  const canRead = permissions.includes("logistics.cylinder.read");

  const summaryQuery = useQuery({
    queryKey: logisticsKeys.customerCylinderSummary(customerId),
    queryFn: () => getCustomerCylinderSummary(customerId),
    enabled: canRead,
  });

  if (!canRead) {
    return null;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Envases en posesión</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4 text-sm text-foreground">
        {summaryQuery.isLoading ? <p className="text-muted-foreground">Cargando...</p> : null}
        {summaryQuery.error ? (
          <Alert title="No se pudo cargar el summary de envases">
            {summaryQuery.error.message}
          </Alert>
        ) : null}

        {summaryQuery.data ? (
          <>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <MetricBox label="Contrato" value={summaryQuery.data.summary.contracted} />
              <MetricBox label="Asignados" value={summaryQuery.data.summary.assigned} />
              <MetricBox label="En cliente" value={summaryQuery.data.summary.at_customer} />
              <MetricBox
                label="Desviación"
                value={summaryQuery.data.summary.deviation}
                tone={summaryQuery.data.summary.deviation !== 0 ? "text-amber-600" : "text-foreground"}
              />
            </div>

            <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-muted-foreground">
              <span>
                Pipeline: <strong className="text-foreground">{summaryQuery.data.summary.pipeline}</strong>
              </span>
              <span>
                Sin ownership:{" "}
                <strong className="text-foreground">{summaryQuery.data.summary.at_customer_unknown}</strong>
              </span>
              <span>
                Lost: <strong className="text-foreground">{summaryQuery.data.summary.lost}</strong>
              </span>
              <span>
                Contratos activos:{" "}
                <strong className="text-foreground">{summaryQuery.data.contract.active_contract_count}</strong>
              </span>
            </div>

            <div>
              <Button variant="secondary" onClick={() => setOpen(true)}>
                Ver detalle de envases
              </Button>
            </div>

            <CustomerCylinderSummaryDialog
              open={open}
              onClose={() => setOpen(false)}
              summary={summaryQuery.data}
            />
          </>
        ) : null}
      </CardContent>
    </Card>
  );
}
