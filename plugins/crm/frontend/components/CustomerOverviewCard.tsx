import { useState } from "react";

import { useAuthStore } from "../../../../apps/web/src/features/auth/store";
import { useQuery } from "../../../../apps/web/src/lib/react-query";
import { Alert } from "../../../../apps/web/src/shared/ui/alert";
import { Button } from "../../../../apps/web/src/shared/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../../../apps/web/src/shared/ui/card";
import {
  getCustomerCylinderSummary,
  logisticsKeys,
} from "../../../logistics/frontend/api";
import type { Customer } from "../types";
import { CustomerCylinderAlertsDialog } from "./CustomerCylinderAlertsDialog";
import { CustomerCylinderSummaryDialog } from "./CustomerCylinderSummaryDialog";

type CustomerOverviewCardProps = {
  customer: Customer;
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

export function CustomerOverviewCard({ customer }: CustomerOverviewCardProps) {
  const permissions = useAuthStore((state) => state.permissions);
  const [open, setOpen] = useState(false);
  const [alertsOpen, setAlertsOpen] = useState(false);
  const canReadCylinder = permissions.includes("logistics.cylinder.read");

  const summaryQuery = useQuery({
    queryKey: logisticsKeys.customerCylinderSummary(customer.id),
    queryFn: () => getCustomerCylinderSummary(customer.id),
    enabled: canReadCylinder,
  });

  const identityItems = [
    { label: "Nombre fiscal", value: customer.legal_name },
    { label: "Nombre comercial", value: customer.commercial_name ?? "-" },
    { label: "Código cliente", value: customer.external_code ?? "-" },
    { label: "País", value: customer.country_code },
    { label: "Email", value: customer.email ?? "-" },
    { label: "Teléfono", value: customer.phone ?? "-" },
    { label: "Activo", value: customer.is_active ? "Sí" : "No" },
  ];

  const fiscalItems = [
    { label: "Exento", value: customer.is_exempt ? "Sí" : "No" },
    { label: "Intracomunitario", value: customer.is_intracommunity ? "Sí" : "No" },
    {
      label: "Recargo equivalencia",
      value: customer.equivalence_surcharge_applicable ? "Sí" : "No",
    },
    {
      label: "Criterio de caja",
      value: customer.cash_criterion_applicable ? "Sí" : "No",
    },
    { label: "Clave operación fiscal", value: customer.fiscal_operation_key ?? "-" },
    { label: "Régimen fiscal", value: customer.tax_regime_code ?? "-" },
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle>{customer.commercial_name || customer.legal_name}</CardTitle>
        <CardDescription>
          {customer.document_type_code} {customer.document_number}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6 text-sm text-foreground">
        <div className="grid gap-8 lg:grid-cols-[1fr,auto]">
          <div className="grid gap-x-8 gap-y-2 sm:grid-cols-2 xl:grid-cols-3">
            {identityItems.map((item) => (
              <div key={item.label}>
                <p className="text-xs text-muted-foreground">{item.label}</p>
                <p className="font-medium">{item.value}</p>
              </div>
            ))}
          </div>

          {canReadCylinder && summaryQuery.data ? (
            <div className="lg:border-l lg:border-border lg:pl-8">
              <p className="mb-3 text-xs font-semibold text-muted-foreground">Envases en posesión</p>
              <div className="grid gap-x-6 gap-y-3 sm:grid-cols-2">
                <MetricBox label="Contrato" value={summaryQuery.data.summary.contracted} />
                <MetricBox label="Asignados" value={summaryQuery.data.summary.assigned} />
                <MetricBox label="En cliente" value={summaryQuery.data.summary.at_customer} />
                <MetricBox
                  label="Desviación"
                  value={summaryQuery.data.summary.deviation}
                  tone={summaryQuery.data.summary.deviation !== 0 ? "text-amber-600" : "text-foreground"}
                />
              </div>
              <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-muted-foreground">
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
              <div className="mt-3 flex flex-wrap items-center gap-2">
                <Button variant="secondary" onClick={() => setOpen(true)}>
                  Ver detalle de envases
                </Button>
                {summaryQuery.data.alerts.length > 0 ? (
                  <Button
                    variant="secondary"
                    onClick={() => setAlertsOpen(true)}
                    className="border-amber-400 bg-amber-50 text-amber-800 hover:bg-amber-100 dark:border-amber-600 dark:bg-amber-500/10 dark:text-amber-200 dark:hover:bg-amber-500/20"
                  >
                    ⚠ {summaryQuery.data.alerts.length} advertencia{summaryQuery.data.alerts.length > 1 ? "s" : ""}
                  </Button>
                ) : null}
              </div>
            </div>
          ) : null}
        </div>

        {canReadCylinder && summaryQuery.isLoading ? (
          <p className="text-xs text-muted-foreground">Cargando envases...</p>
        ) : null}

        {canReadCylinder && summaryQuery.error ? (
          <Alert title="No se pudo cargar el summary de envases">
            {summaryQuery.error.message}
          </Alert>
        ) : null}

        <details className="group rounded-lg border border-border">
          <summary className="flex cursor-pointer items-center gap-2 px-4 py-2 text-xs font-semibold text-muted-foreground hover:text-foreground">
            Información fiscal
            <span className="ml-auto transition-transform group-open:rotate-180">▾</span>
          </summary>
          <div className="grid gap-x-8 gap-y-2 border-t border-border px-4 py-3 sm:grid-cols-2 lg:grid-cols-3">
            {fiscalItems.map((item) => (
              <div key={item.label}>
                <p className="text-xs text-muted-foreground">{item.label}</p>
                <p className="font-medium">{item.value}</p>
              </div>
            ))}
          </div>
        </details>

        {summaryQuery.data ? (
          <>
            <CustomerCylinderSummaryDialog
              open={open}
              onClose={() => setOpen(false)}
              summary={summaryQuery.data}
            />
            <CustomerCylinderAlertsDialog
              open={alertsOpen}
              onClose={() => setAlertsOpen(false)}
              alerts={summaryQuery.data.alerts}
            />
          </>
        ) : null}
      </CardContent>
    </Card>
  );
}
