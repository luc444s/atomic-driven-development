import { useMutation, useQuery, useQueryClient } from "../../../../apps/web/src/lib/react-query";
import { FormEvent, useState } from "react";

import {
  createDeliveryPoint,
  listDeliveryPoints,
  listZones,
  logisticsKeys,
  updateDeliveryPoint,
} from "../api";
import { LogisticsSection } from "../components/LogisticsSection";
import { Alert } from "../../../../apps/web/src/shared/ui/alert";
import { Button } from "../../../../apps/web/src/shared/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../../../apps/web/src/shared/ui/card";
import { DataTable } from "../../../../apps/web/src/shared/ui/data-table";
import { Dialog } from "../../../../apps/web/src/shared/ui/dialog";
import { Input } from "../../../../apps/web/src/shared/ui/input";

type DeliveryPointFormState = {
  id?: string;
  customer_name: string;
  contact_name: string;
  address: string;
  phone: string;
  zone_id: string;
  delivery_day: string;
};

const EMPTY_FORM: DeliveryPointFormState = {
  customer_name: "",
  contact_name: "",
  address: "",
  phone: "",
  zone_id: "",
  delivery_day: "",
};

export function DeliveryPointsPage() {
  const queryClient = useQueryClient();
  const [formState, setFormState] = useState<DeliveryPointFormState>(EMPTY_FORM);
  const [isOpen, setIsOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const deliveryPointsQuery = useQuery({
    queryKey: logisticsKeys.deliveryPoints(),
    queryFn: listDeliveryPoints,
  });
  const zonesQuery = useQuery({ queryKey: logisticsKeys.zones(), queryFn: listZones });

  const saveMutation = useMutation({
    mutationFn: async (payload: DeliveryPointFormState) => {
      const normalized = {
        customer_name: payload.customer_name,
        contact_name: payload.contact_name || null,
        address: payload.address,
        phone: payload.phone || null,
        zone_id: payload.zone_id || null,
        delivery_day: payload.delivery_day || null,
      };
      if (payload.id) {
        return updateDeliveryPoint(payload.id, normalized);
      }
      return createDeliveryPoint(normalized);
    },
    onSuccess: async () => {
      setIsOpen(false);
      setFormState(EMPTY_FORM);
      setError(null);
      await queryClient.invalidateQueries({ queryKey: logisticsKeys.deliveryPoints() });
    },
  });

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    try {
      await saveMutation.mutateAsync(formState);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "No se pudo guardar el punto de entrega.");
    }
  }

  return (
    <LogisticsSection
      title="Puntos de entrega"
      description="Direcciones frecuentes para organizar la salida y el reparto."
      actions={<Button onClick={() => setIsOpen(true)}>Nuevo punto</Button>}
    >
      {error ? <Alert title="No se pudo completar la acción">{error}</Alert> : null}

      <Card>
        <CardHeader>
          <CardTitle>Direcciones activas</CardTitle>
          <CardDescription>Listado simple por cliente, zona y contacto principal.</CardDescription>
        </CardHeader>
        <CardContent>
          <DataTable
            columns={[
              { key: "customer", header: "Cliente", render: (row) => row.customer_name },
              { key: "address", header: "Dirección", render: (row) => row.address },
              { key: "contact", header: "Contacto", render: (row) => row.contact_name ?? "-" },
              {
                key: "zone",
                header: "Zona",
                render: (row) => zonesQuery.data?.find((zone) => zone.id === row.zone_id)?.name ?? "-",
              },
              {
                key: "actions",
                header: "Editar",
                className: "w-32",
                render: (row) => (
                  <Button
                    variant="secondary"
                    onClick={() => {
                      setFormState({
                        id: row.id,
                        customer_name: row.customer_name,
                        contact_name: row.contact_name ?? "",
                        address: row.address,
                        phone: row.phone ?? "",
                        zone_id: row.zone_id ?? "",
                        delivery_day: row.delivery_day ?? "",
                      });
                      setIsOpen(true);
                    }}
                  >
                    Abrir
                  </Button>
                ),
              },
            ]}
            rows={deliveryPointsQuery.data ?? []}
            rowKey={(row) => row.id}
            emptyMessage="Todavía no hay puntos de entrega cargados."
          />
        </CardContent>
      </Card>

      <Dialog
        open={isOpen}
        title={formState.id ? "Editar punto de entrega" : "Nuevo punto de entrega"}
        description="Guarda una dirección útil para rutas y pedidos."
        onClose={() => {
          setIsOpen(false);
          setFormState(EMPTY_FORM);
        }}
      >
        <form className="space-y-4" onSubmit={onSubmit}>
          <label className="block space-y-2 text-sm text-slate-300">
            <span>Cliente</span>
            <Input value={formState.customer_name} onChange={(event) => setFormState((current) => ({ ...current, customer_name: event.target.value }))} />
          </label>
          <label className="block space-y-2 text-sm text-slate-300">
            <span>Contacto</span>
            <Input value={formState.contact_name} onChange={(event) => setFormState((current) => ({ ...current, contact_name: event.target.value }))} />
          </label>
          <label className="block space-y-2 text-sm text-slate-300">
            <span>Dirección</span>
            <Input value={formState.address} onChange={(event) => setFormState((current) => ({ ...current, address: event.target.value }))} />
          </label>
          <div className="grid gap-4 md:grid-cols-2">
            <label className="block space-y-2 text-sm text-slate-300">
              <span>Teléfono</span>
              <Input value={formState.phone} onChange={(event) => setFormState((current) => ({ ...current, phone: event.target.value }))} />
            </label>
            <label className="block space-y-2 text-sm text-slate-300">
              <span>Día sugerido</span>
              <Input value={formState.delivery_day} onChange={(event) => setFormState((current) => ({ ...current, delivery_day: event.target.value }))} />
            </label>
          </div>
          <label className="block space-y-2 text-sm text-slate-300">
            <span>Zona</span>
            <select
              value={formState.zone_id}
              onChange={(event) => setFormState((current) => ({ ...current, zone_id: event.target.value }))}
              className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-200"
            >
              <option value="">Sin zona</option>
              {(zonesQuery.data ?? []).map((zone) => (
                <option key={zone.id} value={zone.id}>
                  {zone.name}
                </option>
              ))}
            </select>
          </label>
          <div className="flex justify-end gap-3">
            <Button type="button" variant="secondary" onClick={() => setIsOpen(false)}>
              Cancelar
            </Button>
            <Button type="submit" disabled={saveMutation.isPending}>
              Guardar
            </Button>
          </div>
        </form>
      </Dialog>
    </LogisticsSection>
  );
}
