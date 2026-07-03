import { FormEvent, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "../../../../apps/web/src/lib/react-query";
import { Alert } from "../../../../apps/web/src/shared/ui/alert";
import { Button } from "../../../../apps/web/src/shared/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../../../apps/web/src/shared/ui/card";
import { DataTable } from "../../../../apps/web/src/shared/ui/data-table";
import { Dialog } from "../../../../apps/web/src/shared/ui/dialog";
import { Input } from "../../../../apps/web/src/shared/ui/input";
import { listDeliveryPoints, logisticsKeys } from "../../../logistics/frontend/api";
import {
  createCustomerAddress,
  createCustomerContact,
  crmKeys,
  deleteCustomerAddress,
  deleteCustomerContact,
  getCustomer,
  setFiscalAddress,
} from "../api";
import { CustomerInfoCard } from "./CustomerInfoCard";
import { DeliveryPointsSection } from "./DeliveryPointsSection";
import type { CustomerAddressPayload, CustomerContactPayload } from "../types";
import { AddressSection } from "./AddressSection";
import { Combobox } from "../../../../apps/web/src/shared/ui/combobox";

const EMPTY_ADDRESS: CustomerAddressPayload = {
  address_type: "COMERCIAL",
  label: null,
  geography_id: null,
  line1: "",
  line2: null,
  city: null,
  state: null,
  district: null,
  postal_code: null,
  country_code: "PER",
  latitude: null,
  longitude: null,
  place_id: null,
  formatted_address: null,
  street_name: null,
  street_number: null,
  geocode_source: "MANUAL",
  precision_meters: null,
  gps_link: null,
  contact_name: null,
  contact_phone: null,
  contact_email: null,
  notes: null,
  ubigeo_code: null,
};

const EMPTY_CONTACT: CustomerContactPayload = {
  contact_type: "PHONE",
  value: "",
  label: null,
  is_primary: false,
};

export type ModalDetalleClienteProps = {
  open: boolean;
  customerId: string;
  onClose: () => void;
  onEditCustomer?: (customerId: string) => void;
  asPage?: boolean;
};

export function ModalDetalleCliente({ open, customerId, onClose, onEditCustomer, asPage }: ModalDetalleClienteProps) {
  const queryClient = useQueryClient();
  const [detailError, setDetailError] = useState<string | null>(null);
  const [addressForm, setAddressForm] = useState<CustomerAddressPayload>(EMPTY_ADDRESS);
  const [contactForm, setContactForm] = useState<CustomerContactPayload>(EMPTY_CONTACT);
  const [isAddressesOpen, setIsAddressesOpen] = useState(false);
  const [isContactsOpen, setIsContactsOpen] = useState(false);
  const [isDeliveryPointsOpen, setIsDeliveryPointsOpen] = useState(false);
  const detailQuery = useQuery({
    queryKey: crmKeys.customers.detail(customerId),
    queryFn: () => getCustomer(customerId),
    enabled: open,
  });
  const deliveryPointsQuery = useQuery({
    queryKey: logisticsKeys.deliveryPoints(),
    queryFn: listDeliveryPoints,
    enabled: open,
  });

  const refreshCustomer = async () => {
    await queryClient.invalidateQueries({ queryKey: crmKeys.customers.all });
    await queryClient.invalidateQueries({ queryKey: crmKeys.customers.detail(customerId) });
  };

  const createAddressMutation = useMutation({
    mutationFn: () => createCustomerAddress(customerId, addressForm),
    onSuccess: async () => {
      setAddressForm(EMPTY_ADDRESS);
      setDetailError(null);
      await refreshCustomer();
    },
  });

  const setFiscalMutation = useMutation({
    mutationFn: (addressId: string) => setFiscalAddress(customerId, addressId),
    onSuccess: async () => {
      setDetailError(null);
      await refreshCustomer();
    },
  });

  const deleteAddressMutation = useMutation({
    mutationFn: (addressId: string) => deleteCustomerAddress(addressId),
    onSuccess: async () => {
      setDetailError(null);
      await refreshCustomer();
    },
  });

  const createContactMutation = useMutation({
    mutationFn: () => createCustomerContact(customerId, contactForm),
    onSuccess: async () => {
      setContactForm(EMPTY_CONTACT);
      setDetailError(null);
      await refreshCustomer();
    },
  });

  const deleteContactMutation = useMutation({
    mutationFn: (contactId: string) => deleteCustomerContact(contactId),
    onSuccess: async () => {
      setDetailError(null);
      await refreshCustomer();
    },
  });

  async function submitAddress(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setDetailError(null);
    try {
      await createAddressMutation.mutateAsync();
    } catch (cause) {
      setDetailError(cause instanceof Error ? cause.message : "No se pudo guardar la dirección.");
    }
  }

  async function submitContact(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setDetailError(null);
    try {
      await createContactMutation.mutateAsync();
    } catch (cause) {
      setDetailError(cause instanceof Error ? cause.message : "No se pudo guardar el contacto.");
    }
  }

  const deliveryPoints = (deliveryPointsQuery.data ?? [])
    .filter((point) => point.customer_id === customerId)
    .map((point) => ({
      id: point.id,
      address: point.address,
      contact_name: point.contact_name,
      phone: point.phone,
      delivery_day: point.delivery_day,
      time_window: point.time_window,
      is_active: point.is_active,
    }));

  const content = (
    <div className="space-y-6">
      {detailQuery.error ? <Alert title="No se pudo cargar el cliente">{detailQuery.error.message}</Alert> : null}
      {detailError ? <Alert title="No se pudo completar la acción">{detailError}</Alert> : null}

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
                <CardTitle>Resumen del cliente</CardTitle>
                <CardDescription>Vista rápida del maestro CRM antes de abrir sus gestiones específicas.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6 text-sm text-foreground">
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="rounded-md border border-border p-4">
                    <p className="text-xs uppercase tracking-wide text-muted-foreground">Direcciones CRM</p>
                    <p className="mt-2 text-2xl font-semibold text-foreground">{detailQuery.data.addresses.length}</p>
                    <p className="mt-1 text-sm text-muted-foreground">
                      Fiscal activa: {detailQuery.data.addresses.find((item) => item.id === detailQuery.data.fiscal_address_id)?.label || "-"}
                    </p>
                  </div>
                  <div className="rounded-md border border-border p-4">
                    <p className="text-xs uppercase tracking-wide text-muted-foreground">Contactos base</p>
                    <p className="mt-2 text-2xl font-semibold text-foreground">{detailQuery.data.contacts.length}</p>
                    <p className="mt-1 text-sm text-muted-foreground">
                      Principal: {detailQuery.data.contacts.find((item) => item.is_primary)?.label || detailQuery.data.contacts.find((item) => item.is_primary)?.value || "-"}
                    </p>
                  </div>
                </div>
                <div>
                  <p className="font-medium text-foreground">Notas</p>
                  <p>{detailQuery.data.notes ?? "-"}</p>
                </div>
                <div className="flex flex-wrap gap-3">
                  <Button variant="secondary" onClick={() => setIsAddressesOpen(true)}>Direcciones</Button>
                  <Button variant="secondary" onClick={() => setIsContactsOpen(true)}>Contactos</Button>
                  <Button variant="secondary" onClick={() => setIsDeliveryPointsOpen(true)}>Puntos de entrega</Button>
                </div>
              </CardContent>
            </Card>
          </div>

          <Dialog
            open={isAddressesOpen}
            title="Direcciones CRM"
            description="Gestiona direcciones fiscales, comerciales y otras direcciones base del cliente."
            onClose={() => setIsAddressesOpen(false)}
            maxWidthClassName="max-w-4xl"
          >
            <div className="space-y-4 text-sm text-foreground">
              <DataTable
                dense
                columns={[
                  {
                    key: "label",
                    header: "Etiqueta",
                    render: (row) => row.label || row.address_type,
                  },
                  { key: "type", header: "Tipo", render: (row) => row.address_type },
                  { key: "address", header: "Dirección", render: (row) => row.line1 },
                  {
                    key: "locality",
                    header: "Localidad",
                    render: (row) => row.district ?? row.city ?? row.state ?? "-",
                  },
                  { key: "contact", header: "Contacto", render: (row) => row.contact_name ?? "-" },
                  { key: "phone", header: "Teléfono", render: (row) => row.contact_phone ?? "-" },
                  {
                    key: "fiscal",
                    header: "Fiscal",
                    render: (row) => (detailQuery.data.fiscal_address_id === row.id ? "Sí" : "No"),
                  },
                  {
                    key: "actions",
                    header: "Acciones",
                    render: (row) => {
                      const isFiscal = detailQuery.data.fiscal_address_id === row.id;
                      return (
                        <div className="flex flex-wrap gap-2">
                          {!isFiscal ? (
                            <Button
                              variant="secondary"
                              onClick={() => {
                                setDetailError(null);
                                setFiscalMutation.mutate(row.id, {
                                  onError: (cause) => {
                                    setDetailError(cause instanceof Error ? cause.message : "No se pudo marcar la dirección fiscal.");
                                  },
                                });
                              }}
                            >
                              Marcar fiscal
                            </Button>
                          ) : null}
                          {!isFiscal ? (
                            <Button
                              variant="secondary"
                              className="h-7 w-7 px-0 py-0"
                              aria-label="Eliminar dirección"
                              onClick={() => {
                                setDetailError(null);
                                deleteAddressMutation.mutate(row.id, {
                                  onError: (cause) => {
                                    setDetailError(cause instanceof Error ? cause.message : "No se pudo eliminar la dirección.");
                                  },
                                });
                              }}
                            >
                              x
                            </Button>
                          ) : null}
                        </div>
                      );
                    },
                  },
                ]}
                rows={detailQuery.data.addresses}
                rowKey={(row) => row.id}
                emptyMessage="No hay direcciones cargadas."
              />

              <form className="space-y-3 rounded-md border border-border p-4" onSubmit={submitAddress}>
                <div>
                  <p className="font-medium text-foreground">Nueva dirección CRM</p>
                  <p className="text-xs text-muted-foreground">Úsala para sedes fiscales, comerciales u otras direcciones base del cliente.</p>
                </div>
                <label className="block space-y-2 text-sm text-foreground">
                  <span>Etiqueta</span>
                  <Input value={addressForm.label ?? ""} onChange={(event) => setAddressForm((current) => ({ ...current, label: event.target.value || null }))} />
                </label>
                <AddressSection value={addressForm} onChange={setAddressForm} />
                <div className="flex justify-end">
                  <Button type="submit" disabled={createAddressMutation.isPending}>Agregar dirección</Button>
                </div>
              </form>
            </div>
          </Dialog>

          <Dialog
            open={isContactsOpen}
            title="Contactos base"
            description="Gestiona teléfonos, emails y otros contactos generales del cliente."
            onClose={() => setIsContactsOpen(false)}
            maxWidthClassName="max-w-3xl"
          >
            <div className="space-y-4 text-sm text-foreground">
              <DataTable
                dense
                columns={[
                  {
                    key: "label",
                    header: "Etiqueta",
                    render: (row) => row.label || row.contact_type,
                  },
                  { key: "type", header: "Tipo", render: (row) => row.contact_type },
                  { key: "value", header: "Valor", render: (row) => row.value },
                  {
                    key: "primary",
                    header: "Principal",
                    render: (row) => (row.is_primary ? "Sí" : "No"),
                  },
                  {
                    key: "actions",
                    header: "Acciones",
                    render: (row) => (
                      <Button
                        variant="secondary"
                        className="h-7 w-7 px-0 py-0"
                        aria-label="Eliminar contacto"
                        onClick={() => {
                          setDetailError(null);
                          deleteContactMutation.mutate(row.id, {
                            onError: (cause) => {
                              setDetailError(cause instanceof Error ? cause.message : "No se pudo eliminar el contacto.");
                            },
                          });
                        }}
                      >
                        x
                      </Button>
                    ),
                  },
                ]}
                rows={detailQuery.data.contacts}
                rowKey={(row) => row.id}
                emptyMessage="No hay contactos base cargados."
              />

              <form className="space-y-3 rounded-md border border-border p-4" onSubmit={submitContact}>
                <div>
                  <p className="font-medium text-foreground">Nuevo contacto base</p>
                  <p className="text-xs text-muted-foreground">Para teléfono, email u otro dato general del cliente.</p>
                </div>
                <label className="block space-y-2 text-sm text-foreground">
                  <span>Tipo</span>
                  <Combobox
                    value={contactForm.contact_type}
                    onChange={(value) => setContactForm((current) => ({ ...current, contact_type: value as CustomerContactPayload["contact_type"] }))}
                    options={[
                      { value: "PHONE", label: "Teléfono" },
                      { value: "EMAIL", label: "Email" },
                      { value: "OTHER", label: "Otro" },
                    ]}
                    placeholder="Seleccionar tipo"
                    searchPlaceholder="Buscar tipo"
                  />
                </label>
                <div className="grid gap-4 md:grid-cols-2">
                  <label className="block space-y-2 text-sm text-foreground">
                    <span>Etiqueta</span>
                    <Input value={contactForm.label ?? ""} onChange={(event) => setContactForm((current) => ({ ...current, label: event.target.value || null }))} />
                  </label>
                  <label className="block space-y-2 text-sm text-foreground">
                    <span>Valor</span>
                    <Input value={contactForm.value} onChange={(event) => setContactForm((current) => ({ ...current, value: event.target.value }))} />
                  </label>
                </div>
                <label className="flex items-center gap-2 text-sm text-foreground">
                  <input
                    type="checkbox"
                    checked={contactForm.is_primary}
                    onChange={(event) => setContactForm((current) => ({ ...current, is_primary: event.target.checked }))}
                  />
                  <span>Marcar como principal</span>
                </label>
                <div className="flex justify-end">
                  <Button type="submit" disabled={createContactMutation.isPending}>Agregar contacto</Button>
                </div>
              </form>
            </div>
          </Dialog>

          <Dialog
            open={isDeliveryPointsOpen}
            title="Puntos de entrega"
            description="Vista operativa de los puntos de entrega gestionados por logistics para este cliente."
            onClose={() => setIsDeliveryPointsOpen(false)}
            maxWidthClassName="max-w-5xl"
          >
            <DeliveryPointsSection points={deliveryPoints} isLoading={deliveryPointsQuery.isLoading} />
          </Dialog>
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
