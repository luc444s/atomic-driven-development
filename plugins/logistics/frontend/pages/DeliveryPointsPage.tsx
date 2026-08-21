import { useMutation, useQuery, useQueryClient } from "../../../../apps/web/src/lib/react-query";
import { FormEvent, useState } from "react";
import type { CustomerBrief } from "../../../crm/frontend/types";

import {
  createDeliveryPoint,
  listDeliveryPoints,
  logisticsKeys,
  updateDeliveryPoint,
} from "../api";
import { listCustomers } from "../../../crm/frontend/api";
import { CustomerSearchDialog } from "../../../crm/frontend/components/CustomerSearchDialog";
import { LogisticsSection } from "../components/LogisticsSection";
import { Alert } from "@systutor/shell/ui/alert";
import { Button } from "@systutor/shell/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@systutor/shell/ui/card";
import { DataTable } from "@systutor/shell/ui/data-table";
import { Dialog } from "@systutor/shell/ui/dialog";
import { Input } from "@systutor/shell/ui/input";
import { LocationPicker } from "@systutor/shell/ui/location-picker";
import { DEFAULT_MAP_CENTER } from "../components/route-builder/map-defaults";
import { Select } from "@systutor/shell/ui/select";

type DeliveryPointFormState = {
  id?: string;
  customer_id: string;
  customer_name: string;
  contact_name: string;
  contact_email: string;
  address: string;
  phone: string;
  warehouse_id: string;
  delivery_day: string;
  visit_day: string;
  time_window: string;
  instructions: string;
  gps_coordinates: { lat: number; lng: number } | null;
};


const EMPTY_FORM: DeliveryPointFormState = {
  customer_id: "",
  customer_name: "",
  contact_name: "",
  contact_email: "",
  address: "",
  phone: "",
  warehouse_id: "",
  delivery_day: "",
  visit_day: "",
  time_window: "",
  instructions: "",
  gps_coordinates: null,
};

export function DeliveryPointsPage() {
  const queryClient = useQueryClient();
  const [formState, setFormState] = useState<DeliveryPointFormState>(EMPTY_FORM);
  const [isOpen, setIsOpen] = useState(false);
  const [isCustomerSearchOpen, setIsCustomerSearchOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const deliveryPointsQuery = useQuery({
    queryKey: logisticsKeys.deliveryPoints(),
    queryFn: listDeliveryPoints,
  });
  const customersQuery = useQuery({
    queryKey: ["crm", "customers", "logistics-lookup"],
    queryFn: () => listCustomers({ limit: 200, offset: 0 }),
  });

  const saveMutation = useMutation({
    mutationFn: async (payload: DeliveryPointFormState) => {
      const normalized = {
        customer_id: payload.customer_id,
        contact_name: payload.contact_name || null,
        contact_email: payload.contact_email || null,
        address: payload.address,
        phone: payload.phone || null,
        warehouse_id: payload.warehouse_id || null,
        delivery_day: payload.delivery_day || null,
        visit_day: payload.visit_day || null,
        time_window: payload.time_window || null,
        instructions: payload.instructions || null,
        gps_coordinates: payload.gps_coordinates,
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

  function openCreateDialog() {
    setFormState(EMPTY_FORM);
    setError(null);
    setIsOpen(true);
  }

  function closeDialog() {
    setIsOpen(false);
  }

  function handleDialogClose() {
    if (isCustomerSearchOpen) {
      return;
    }
    closeDialog();
  }

  return (
    <LogisticsSection
      title="Puntos de entrega"
      description="Direcciones frecuentes para organizar la salida y el reparto."
      actions={<Button onClick={openCreateDialog}>Nuevo punto</Button>}
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
              {
                key: "customer",
                header: "Cliente",
                render: (row) => {
                  const customer = customersQuery.data?.items.find((item) => item.id === row.customer_id);
                  return customer?.commercial_name ?? customer?.legal_name ?? row.customer_name ?? "-";
                },
              },
              { key: "address", header: "Dirección", render: (row) => row.address },
              { key: "contact", header: "Contacto", render: (row) => row.contact_name ?? "-" },
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
                        customer_id: row.customer_id,
                        customer_name:
                          customersQuery.data?.items.find((item) => item.id === row.customer_id)?.commercial_name ??
                          customersQuery.data?.items.find((item) => item.id === row.customer_id)?.legal_name ??
                          row.customer_name ??
                          "",
                        contact_name: row.contact_name ?? "",
                        contact_email: row.contact_email ?? "",
                        address: row.address,
                        phone: row.phone ?? "",
                        warehouse_id: row.warehouse_id ?? "",
                        delivery_day: row.delivery_day ?? "",
                        visit_day: row.visit_day ?? "",
                        time_window: row.time_window ?? "",
                        instructions: row.instructions ?? "",
                        gps_coordinates: row.gps_coordinates ?? null,
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
        onClose={handleDialogClose}
      >
        <form className="space-y-4" onSubmit={onSubmit}>
          <div className="space-y-2 text-sm text-foreground">
            <span>Cliente</span>
            <Button type="button" variant="secondary" onClick={() => setIsCustomerSearchOpen(true)}>
              {formState.customer_name ? `${formState.customer_name} (${formState.customer_id})` : "Seleccionar cliente"}
            </Button>
          </div>
          <label className="block space-y-2 text-sm text-foreground">
            <span>Contacto</span>
            <Input value={formState.contact_name} onChange={(event) => setFormState((current) => ({ ...current, contact_name: event.target.value }))} />
          </label>
          <label className="block space-y-2 text-sm text-foreground">
            <span>Email contacto</span>
            <Input value={formState.contact_email} onChange={(event) => setFormState((current) => ({ ...current, contact_email: event.target.value }))} />
          </label>
          <label className="block space-y-2 text-sm text-foreground">
            <span>Dirección</span>
            <Input value={formState.address} onChange={(event) => setFormState((current) => ({ ...current, address: event.target.value }))} />
          </label>
          <div className="grid gap-4 md:grid-cols-2">
            <label className="block space-y-2 text-sm text-foreground">
              <span>Teléfono</span>
              <Input value={formState.phone} onChange={(event) => setFormState((current) => ({ ...current, phone: event.target.value }))} />
            </label>
            <label className="block space-y-2 text-sm text-foreground">
              <span>Día sugerido</span>
              <Input value={formState.delivery_day} onChange={(event) => setFormState((current) => ({ ...current, delivery_day: event.target.value }))} />
            </label>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <label className="block space-y-2 text-sm text-foreground">
              <span>Día de visita</span>
              <Input value={formState.visit_day} onChange={(event) => setFormState((current) => ({ ...current, visit_day: event.target.value }))} />
            </label>
            <label className="block space-y-2 text-sm text-foreground">
              <span>Ventana horaria</span>
              <Input value={formState.time_window} onChange={(event) => setFormState((current) => ({ ...current, time_window: event.target.value }))} />
            </label>
          </div>
          <label className="block space-y-2 text-sm text-foreground">
            <span>Indicaciones</span>
            <Input value={formState.instructions} onChange={(event) => setFormState((current) => ({ ...current, instructions: event.target.value }))} />
          </label>
          <div className="rounded-md border border-border p-4 space-y-4">
            <p className="text-sm font-medium text-foreground">Ubicación en mapa</p>
            <LocationPicker
              value={formState.gps_coordinates}
              onChange={(location) => setFormState((current) => ({ ...current, gps_coordinates: location }))}
              searchPlaceholder="Buscar dirección del punto"
              placeholder="Selecciona la ubicación exacta del punto de entrega"
              height={260}
              defaultCenter={DEFAULT_MAP_CENTER}
            />
          </div>
          <div className="flex justify-end gap-3">
            <Button type="button" variant="secondary" onClick={closeDialog}>
              Cancelar
            </Button>
            <Button type="submit" disabled={saveMutation.isPending}>
              Guardar
            </Button>
          </div>
        </form>
      </Dialog>

      <CustomerSearchDialog
        open={isCustomerSearchOpen}
        onOpenChange={setIsCustomerSearchOpen}
        onSelect={(customer: CustomerBrief) =>
          setFormState((current) => ({ ...current, customer_id: customer.id, customer_name: customer.display_name }))
        }
      />
    </LogisticsSection>
  );
}
