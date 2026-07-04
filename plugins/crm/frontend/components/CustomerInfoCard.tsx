import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../../../apps/web/src/shared/ui/card";

import type { Customer } from "../types";

type CustomerInfoCardProps = {
  customer: Customer;
};

export function CustomerInfoCard({ customer }: CustomerInfoCardProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{customer.commercial_name || customer.legal_name}</CardTitle>
        <CardDescription>{customer.document_type_code} {customer.document_number}</CardDescription>
      </CardHeader>
      <CardContent className="grid gap-2 text-sm text-foreground">
        <p>Nombre fiscal: {customer.legal_name}</p>
        <p>Nombre comercial: {customer.commercial_name ?? "-"}</p>
        <p>Código cliente: {customer.external_code ?? "-"}</p>
        <p>País: {customer.country_code}</p>
        <p>Email: {customer.email ?? "-"}</p>
        <p>Teléfono: {customer.phone ?? "-"}</p>
        <p>Código contable: {customer.accounting_code ?? "-"}</p>
        <p>Forma de pago: {customer.payment_term_code ?? "-"}</p>
        <p>Facturación: {customer.billing_type ?? "-"}</p>
        <p>Exento: {customer.is_exempt ? "Sí" : "No"}</p>
        <p>Activo: {customer.is_active ? "Sí" : "No"}</p>

        <div className="mt-3 rounded-md border border-border p-3">
          <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">Fiscal</p>
          <p>Intracomunitario: {customer.is_intracommunity ? "Sí" : "No"}</p>
          <p>Recargo equivalencia: {customer.equivalence_surcharge_applicable ? "Sí" : "No"}</p>
          <p>Criterio de caja: {customer.cash_criterion_applicable ? "Sí" : "No"}</p>
          <p>Clave operación fiscal: {customer.fiscal_operation_key ?? "-"}</p>
          <p>Régimen fiscal: {customer.tax_regime_code ?? "-"}</p>
        </div>
      </CardContent>
    </Card>
  );
}
