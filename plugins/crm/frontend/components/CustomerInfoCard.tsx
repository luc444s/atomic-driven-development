import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@systutor/shell/ui/card";

import type { Customer } from "../types";

type CustomerInfoCardProps = {
  customer: Customer;
};

export function CustomerInfoCard({ customer }: CustomerInfoCardProps) {
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
      <CardContent className="space-y-4 text-sm text-foreground">
        <div className="grid gap-x-8 gap-y-2 sm:grid-cols-2 lg:grid-cols-3">
          {identityItems.map((item) => (
            <div key={item.label}>
              <p className="text-xs text-muted-foreground">{item.label}</p>
              <p className="font-medium">{item.value}</p>
            </div>
          ))}
        </div>

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
      </CardContent>
    </Card>
  );
}
