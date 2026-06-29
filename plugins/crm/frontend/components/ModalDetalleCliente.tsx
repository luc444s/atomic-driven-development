import { useQuery } from "../../../../apps/web/src/lib/react-query";
import { Alert } from "../../../../apps/web/src/shared/ui/alert";
import { Button } from "../../../../apps/web/src/shared/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../../../apps/web/src/shared/ui/card";
import { Dialog } from "../../../../apps/web/src/shared/ui/dialog";
import { crmKeys, getCustomer } from "../api";
import { CustomerInfoCard } from "./CustomerInfoCard";
import { DeliveryPointsSection } from "./DeliveryPointsSection";

export type ModalDetalleClienteProps = {
  open: boolean;
  customerId: string;
  onClose: () => void;
  onEditCustomer?: (customerId: string) => void;
  asPage?: boolean;
};

export function ModalDetalleCliente({ open, customerId, onClose, onEditCustomer, asPage }: ModalDetalleClienteProps) {
  const detailQuery = useQuery({
    queryKey: crmKeys.customers.detail(customerId),
    queryFn: () => getCustomer(customerId),
    enabled: open,
  });

  const content = (
    <div className="space-y-6">
      {detailQuery.error ? <Alert title="No se pudo cargar el cliente">{detailQuery.error.message}</Alert> : null}

      {detailQuery.data ? (
        <>
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => onEditCustomer?.(customerId)}>Editar</Button>
            <Button
              variant="secondary"
              onClick={() => {
                window.location.href = `/app/logistics/movements?customerId=${customerId}`;
              }}
            >
              Ver movimientos
            </Button>
          </div>

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
        </>
      ) : null}
    </div>
  );

  if (asPage) {
    return <div className="p-6">{content}</div>;
  }

  return (
    <Dialog
      open={open}
      title="Detalle de cliente"
      description="Vista de solo lectura del cliente y sus datos fiscales principales."
      onClose={onClose}
      maxWidthClassName="max-w-4xl"
    >
      <div className="max-h-[85vh] overflow-y-auto">{content}</div>
    </Dialog>
  );
}
