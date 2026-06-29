import { useQuery } from "../../../../apps/web/src/lib/react-query";
import { Link, useSearchParams } from "../../../../apps/web/src/lib/router";
import { useParams } from "../../../../apps/web/src/lib/router";

import { Alert } from "../../../../apps/web/src/shared/ui/alert";
import { Button } from "../../../../apps/web/src/shared/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../../../apps/web/src/shared/ui/card";
import { crmKeys, getCustomer } from "../api";
import { CrmSection } from "../components/CrmSection";
import { CustomerInfoCard } from "../components/CustomerInfoCard";
import { DeliveryPointsSection } from "../components/DeliveryPointsSection";

export function CustomerDetailPage() {
  const { customerId } = useParams();
  const [, setSearchParams] = useSearchParams();
  const detailQuery = useQuery({
    queryKey: crmKeys.customers.detail(customerId ?? ""),
    queryFn: () => getCustomer(customerId!),
    enabled: Boolean(customerId),
  });

  if (!customerId) {
    return null;
  }

  return (
    <CrmSection
      title="Detalle de cliente"
      description="Vista de solo lectura del cliente y sus datos fiscales principales."
      actions={
        <div className="flex gap-3">
          <Link to={`/app/crm/customers/${customerId}`}>
            <Button variant="secondary">Editar</Button>
          </Link>
          <Button
            variant="secondary"
            onClick={() => {
              setSearchParams({ customerId });
              window.location.href = "/app/logistics/movements";
            }}
          >
            Ver movimientos
          </Button>
        </div>
      }
    >
      {detailQuery.error ? <Alert title="No se pudo cargar el cliente">{detailQuery.error.message}</Alert> : null}
      {detailQuery.data ? (
        <div className="grid gap-6 xl:grid-cols-[1fr,1.1fr]">
          <CustomerInfoCard customer={detailQuery.data} />
          <Card>
            <CardHeader>
              <CardTitle>Direcciones y contactos</CardTitle>
              <CardDescription>Resumen del maestro de cliente.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4 text-sm text-slate-300">
              <div>
                <p className="font-medium text-slate-100">Direcciones</p>
                <p>{detailQuery.data.addresses.length}</p>
              </div>
              <div>
                <p className="font-medium text-slate-100">Contactos</p>
                <p>{detailQuery.data.contacts.length}</p>
              </div>
              <div>
                <p className="font-medium text-slate-100">Notas</p>
                <p>{detailQuery.data.notes ?? "-"}</p>
              </div>
            </CardContent>
          </Card>
          <div className="xl:col-span-2">
            <DeliveryPointsSection points={[]} />
          </div>
        </div>
      ) : null}
    </CrmSection>
  );
}
