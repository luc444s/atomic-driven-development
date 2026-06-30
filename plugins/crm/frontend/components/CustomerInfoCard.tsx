import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../../../apps/web/src/shared/ui/card";

import type { Customer } from "../types";

type CustomerInfoCardProps = {
  customer: Customer;
};

export function CustomerInfoCard({ customer }: CustomerInfoCardProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{customer.legal_name}</CardTitle>
        <CardDescription>
          {customer.document_type_code} {customer.document_number}
        </CardDescription>
      </CardHeader>
      <CardContent className="grid gap-2 text-sm text-foreground">
        <p>País: {customer.country_code}</p>
        <p>Email: {customer.email ?? "-"}</p>
        <p>Teléfono: {customer.phone ?? "-"}</p>
        <p>Facturación: {customer.billing_type ?? "-"}</p>
        <p>Activo: {customer.is_active ? "Sí" : "No"}</p>
      </CardContent>
    </Card>
  );
}
