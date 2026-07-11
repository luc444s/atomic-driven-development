import { FormEvent, useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "../../../../apps/web/src/lib/react-query";
import { Alert } from "../../../../apps/web/src/shared/ui/alert";
import { Button } from "../../../../apps/web/src/shared/ui/button";
import { ConfirmDialog } from "../../../../apps/web/src/shared/ui/confirm-dialog";
import { DataTable } from "../../../../apps/web/src/shared/ui/data-table";
import { Dialog } from "../../../../apps/web/src/shared/ui/dialog";
import { Input } from "../../../../apps/web/src/shared/ui/input";
import { Popover } from "../../../../apps/web/src/shared/ui/popover";
import { toast } from "../../../../apps/web/src/shared/ui/toast";
import { listDeliveryPoints, logisticsKeys } from "../../../logistics/frontend/api";
import { listContracts, type LogisticsCylinderContract } from "../../../logistics/frontend/api/contracts";
import {
  createCustomerAddress,
  createCustomerCommercialAssignment,
  createCustomerContact,
  crmKeys,
  deleteCustomerAddress,
  deleteCustomerCommercialAssignment,
  deleteCustomerContact,
  getCustomer,
  listCommercialUsers,
  listCustomerCommercialAssignments,
  setFiscalAddress,
  updateCustomerAddress,
  updateCustomerCommercialAssignment,
  updateCustomerContact,
} from "../api";
import { BankAccountsSection } from "./BankAccountsSection";
import { CustomerOverviewCard } from "./CustomerOverviewCard";
import { DeliveryPointsSection } from "./DeliveryPointsSection";
import { PricingTermsSection } from "./PricingTermsSection";
import type {
  CustomerAddressPayload,
  CustomerCommercialAssignmentPayload,
  CustomerContactPayload,
} from "../types";
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
  is_operational_site: false,
  notes: null,
  ubigeo_code: null,
};

const EMPTY_CONTACT: CustomerContactPayload = {
  full_name: null,
  label: null,
  role: null,
  phone: null,
  email: null,
  address_id: null,
  contact_purpose: "GENERAL",
  contact_type: "PHONE",
  notes: null,
  is_primary: false,
};

const EMPTY_COMMERCIAL_ASSIGNMENT: CustomerCommercialAssignmentPayload = {
  address_id: null,
  user_id: "",
  assignment_role: "AGENT",
  notes: null,
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
  const [editingAddressId, setEditingAddressId] = useState<string | null>(null);
  const [contactForm, setContactForm] = useState<CustomerContactPayload>(EMPTY_CONTACT);
  const [commercialAssignmentForm, setCommercialAssignmentForm] = useState<CustomerCommercialAssignmentPayload>(EMPTY_COMMERCIAL_ASSIGNMENT);
  const [editingContactId, setEditingContactId] = useState<string | null>(null);
  const [editingCommercialAssignmentId, setEditingCommercialAssignmentId] = useState<string | null>(null);
  const [filterContactAddress, setFilterContactAddress] = useState<string | null>(null);
  const [filterContactPurpose, setFilterContactPurpose] = useState<string | null>(null);
  const [isAddressesOpen, setIsAddressesOpen] = useState(false);
  const [isContactsOpen, setIsContactsOpen] = useState(false);
  const [isCommercialOpen, setIsCommercialOpen] = useState(false);
  const [isDeliveryPointsOpen, setIsDeliveryPointsOpen] = useState(false);
  const [isBankAccountsOpen, setIsBankAccountsOpen] = useState(false);
  const [isPricingOpen, setIsPricingOpen] = useState(false);
  const [isContractsOpen, setIsContractsOpen] = useState(false);
  const [envasesDialogOpen, setEnvasesDialogOpen] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState<{ id: string; label: string; onConfirm: () => void } | null>(null);

  useEffect(() => {
    if (!isContactsOpen) {
      setFilterContactAddress(null);
      setFilterContactPurpose(null);
    }
  }, [isContactsOpen]);

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
  const commercialAssignmentsQuery = useQuery({
    queryKey: crmKeys.customers.commercialAssignments(customerId),
    queryFn: () => listCustomerCommercialAssignments(customerId),
    enabled: open,
  });
  const commercialUsersQuery = useQuery({
    queryKey: crmKeys.commercial.users,
    queryFn: listCommercialUsers,
    enabled: open && isCommercialOpen,
  });

  const { data: contracts = [], isLoading: contractsLoading } = useQuery({
    queryKey: ["logistics", "contracts", "customer", customerId],
    queryFn: () => listContracts({ customer_id: customerId }),
    enabled: open && isContractsOpen,
  });

  const refreshCustomer = async () => {
    await queryClient.invalidateQueries({ queryKey: crmKeys.customers.all });
    await queryClient.invalidateQueries({ queryKey: crmKeys.customers.detail(customerId) });
    await queryClient.invalidateQueries({ queryKey: crmKeys.customers.commercialAssignments(customerId) });
  };

  const createAddressMutation = useMutation({
    mutationFn: () => createCustomerAddress(customerId, addressForm),
    onSuccess: async () => {
      toast.success("Dirección creada");
      setAddressForm(EMPTY_ADDRESS);
      setDetailError(null);
      await refreshCustomer();
    },
  });

  const setFiscalMutation = useMutation({
    mutationFn: (addressId: string) => setFiscalAddress(customerId, addressId),
    onSuccess: async () => {
      toast.success("Dirección fiscal actualizada");
      setDetailError(null);
      await refreshCustomer();
    },
  });

  const updateAddressMutation = useMutation({
    mutationFn: () => updateCustomerAddress(editingAddressId!, addressForm),
    onSuccess: async () => {
      toast.success("Dirección actualizada");
      setAddressForm(EMPTY_ADDRESS);
      setEditingAddressId(null);
      setDetailError(null);
      await refreshCustomer();
    },
  });

  const deleteAddressMutation = useMutation({
    mutationFn: (addressId: string) => deleteCustomerAddress(addressId),
    onSuccess: async () => {
      toast.success("Dirección eliminada");
      setDetailError(null);
      await refreshCustomer();
    },
  });

  const createContactMutation = useMutation({
    mutationFn: () => createCustomerContact(customerId, contactForm),
    onSuccess: async () => {
      toast.success("Contacto creado");
      setContactForm(EMPTY_CONTACT);
      setEditingContactId(null);
      setDetailError(null);
      await refreshCustomer();
    },
  });

  const updateContactMutation = useMutation({
    mutationFn: () => updateCustomerContact(editingContactId!, contactForm),
    onSuccess: async () => {
      toast.success("Contacto actualizado");
      setContactForm(EMPTY_CONTACT);
      setEditingContactId(null);
      setDetailError(null);
      await refreshCustomer();
    },
  });

  const deleteContactMutation = useMutation({
    mutationFn: (contactId: string) => deleteCustomerContact(contactId),
    onSuccess: async () => {
      toast.success("Contacto eliminado");
      setDetailError(null);
      await refreshCustomer();
    },
  });

  const createCommercialAssignmentMutation = useMutation({
    mutationFn: () => createCustomerCommercialAssignment(customerId, commercialAssignmentForm),
    onSuccess: async () => {
      toast.success("Asignación comercial creada");
      setCommercialAssignmentForm(EMPTY_COMMERCIAL_ASSIGNMENT);
      setEditingCommercialAssignmentId(null);
      setDetailError(null);
      await refreshCustomer();
    },
  });

  const updateCommercialAssignmentMutation = useMutation({
    mutationFn: () => updateCustomerCommercialAssignment(editingCommercialAssignmentId!, commercialAssignmentForm),
    onSuccess: async () => {
      toast.success("Asignación comercial actualizada");
      setCommercialAssignmentForm(EMPTY_COMMERCIAL_ASSIGNMENT);
      setEditingCommercialAssignmentId(null);
      setDetailError(null);
      await refreshCustomer();
    },
  });

  const deleteCommercialAssignmentMutation = useMutation({
    mutationFn: (assignmentId: string) => deleteCustomerCommercialAssignment(assignmentId),
    onSuccess: async () => {
      toast.success("Asignación comercial eliminada");
      setDetailError(null);
      await refreshCustomer();
    },
  });

  async function submitAddress(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setDetailError(null);
    try {
      if (editingAddressId) {
        await updateAddressMutation.mutateAsync();
      } else {
        await createAddressMutation.mutateAsync();
      }
    } catch (cause) {
      setDetailError(cause instanceof Error ? cause.message : "No se pudo guardar la dirección.");
    }
  }

  async function submitContact(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setDetailError(null);
    try {
      if (editingContactId) {
        await updateContactMutation.mutateAsync();
      } else {
        await createContactMutation.mutateAsync();
      }
    } catch (cause) {
      setDetailError(cause instanceof Error ? cause.message : "No se pudo guardar el contacto.");
    }
  }

  async function submitCommercialAssignment(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setDetailError(null);
    try {
      if (editingCommercialAssignmentId) {
        await updateCommercialAssignmentMutation.mutateAsync();
      } else {
        await createCommercialAssignmentMutation.mutateAsync();
      }
    } catch (cause) {
      setDetailError(cause instanceof Error ? cause.message : "No se pudo guardar la asignación comercial.");
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
          <div className="space-y-6">
            <CustomerOverviewCard
              customer={detailQuery.data}
              envasesDialogOpen={envasesDialogOpen}
              onEnvasesDialogClose={() => setEnvasesDialogOpen(false)}
            />

            {detailQuery.data.notes ? (
              <div className="rounded-md border border-border bg-muted/20 p-4">
                <p className="text-xs font-semibold text-muted-foreground">Notas</p>
                <p className="mt-2 break-words text-sm">{detailQuery.data.notes}</p>
              </div>
            ) : null}

            <div className="flex flex-col items-center gap-3 rounded-lg border border-border p-6">
              <Button size="lg" className="w-full max-w-xs" onClick={() => setEnvasesDialogOpen(true)}>
                Ver envases
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  window.location.href = `/app/logistics/movements?customerId=${customerId}`;
                }}
              >
                Ver movimientos
              </Button>
              <div className="self-end">
                <Popover
                  trigger={
                    <Button variant="ghost" className="text-muted-foreground">⋯</Button>
                  }
                  align="end"
                  contentClassName="w-56"
                >
                  <div className="py-1">
                    <p className="px-3 py-1 text-xs font-semibold text-muted-foreground">General</p>
                    <button
                      type="button"
                      className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm text-popover-foreground hover:bg-accent hover:text-accent-foreground"
                      onClick={() => { onEditCustomer?.(customerId); }}
                    >
                      Editar
                    </button>
                    <div className="my-1 border-t" />
                    <p className="px-3 py-1 text-xs font-semibold text-muted-foreground">Operación</p>
                    <button
                      type="button"
                      className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm text-popover-foreground hover:bg-accent hover:text-accent-foreground"
                      onClick={() => { setIsAddressesOpen(true); }}
                    >
                      Direcciones
                    </button>
                    <button
                      type="button"
                      className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm text-popover-foreground hover:bg-accent hover:text-accent-foreground"
                      onClick={() => { setIsContactsOpen(true); }}
                    >
                      Contactos
                    </button>
                    <button
                      type="button"
                      className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm text-popover-foreground hover:bg-accent hover:text-accent-foreground"
                      onClick={() => { setIsDeliveryPointsOpen(true); }}
                    >
                      Puntos de entrega
                    </button>
                    <div className="my-1 border-t" />
                    <p className="px-3 py-1 text-xs font-semibold text-muted-foreground">Administración</p>
                    <button
                      type="button"
                      className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm text-popover-foreground hover:bg-accent hover:text-accent-foreground"
                      onClick={() => { setIsContractsOpen(true); }}
                    >
                      Contratos
                    </button>
                    <button
                      type="button"
                      className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm text-popover-foreground hover:bg-accent hover:text-accent-foreground"
                      onClick={() => { setIsPricingOpen(true); }}
                    >
                      Precios especiales
                    </button>
                    <button
                      type="button"
                      className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm text-popover-foreground hover:bg-accent hover:text-accent-foreground"
                      onClick={() => { setIsBankAccountsOpen(true); }}
                    >
                      Cuentas bancarias
                    </button>
                    <button
                      type="button"
                      className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm text-popover-foreground hover:bg-accent hover:text-accent-foreground"
                      onClick={() => { setIsCommercialOpen(true); }}
                    >
                      Gestión comercial
                    </button>
                  </div>
                </Popover>
              </div>
            </div>
          </div>

          <Dialog
            open={isAddressesOpen}
            title="Direcciones"
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
                  {
                    key: "site",
                    header: "Sede",
                    render: (row) => (row.is_operational_site ? "Sí" : "No"),
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
                    header: "",
                    render: (row) => {
                      const canDelete = detailQuery.data.fiscal_address_id !== row.id;
                      return canDelete ? (
                        <Button
                          variant="secondary"
                          className="h-7 w-7 px-0 py-0"
                          aria-label="Eliminar dirección"
                          onClick={(event) => {
                            event.stopPropagation();
                            setDetailError(null);
                            setConfirmDelete({
                              id: row.id,
                              label: "dirección",
                              onConfirm: () => deleteAddressMutation.mutate(row.id, {
                                onError: (cause) => {
                                  setDetailError(cause instanceof Error ? cause.message : "No se pudo eliminar la dirección.");
                                },
                              }),
                            });
                          }}
                        >
                          x
                        </Button>
                      ) : null;
                    },
                  },
                ]}
                rows={detailQuery.data.addresses}
                rowKey={(row) => row.id}
                emptyMessage="No hay direcciones cargadas."
                onRowClick={(row) => {
                  setEditingAddressId(row.id);
                  setAddressForm({
                    address_type: row.address_type,
                    label: row.label,
                    geography_id: row.geography_id,
                    line1: row.line1,
                    line2: row.line2,
                    city: row.city,
                    state: row.state,
                    district: row.district,
                    postal_code: row.postal_code,
                    country_code: row.country_code || "PER",
                    latitude: row.latitude,
                    longitude: row.longitude,
                    place_id: row.place_id,
                    formatted_address: row.formatted_address,
                    street_name: row.street_name,
                    street_number: row.street_number,
                    geocode_source: row.geocode_source || "MANUAL",
                    precision_meters: row.precision_meters,
                    gps_link: row.gps_link,
                    contact_name: row.contact_name,
                    contact_phone: row.contact_phone,
                    contact_email: row.contact_email,
                    is_operational_site: row.is_operational_site,
                    notes: row.notes,
                    ubigeo_code: row.ubigeo_code,
                  });
                }}
              />

              <form className="space-y-3 rounded-md border border-border p-4" onSubmit={submitAddress}>
                <div>
                  <p className="font-medium text-foreground">{editingAddressId ? "Editar dirección" : "Nueva dirección CRM"}</p>
                  <p className="text-xs text-muted-foreground">Úsala para sedes fiscales, comerciales u otras direcciones base del cliente.</p>
                </div>
                <label className="block space-y-2 text-sm text-foreground">
                  <span>Etiqueta</span>
                  <Input value={addressForm.label ?? ""} onChange={(event) => setAddressForm((current) => ({ ...current, label: event.target.value || null }))} />
                </label>
                <AddressSection value={addressForm} onChange={setAddressForm} />
                <div className="flex justify-end gap-2">
                  {editingAddressId ? (
                    <Button
                      variant="secondary"
                      type="button"
                      onClick={() => {
                        setEditingAddressId(null);
                        setAddressForm(EMPTY_ADDRESS);
                      }}
                    >
                      Cancelar
                    </Button>
                  ) : null}
                  <Button type="submit" disabled={createAddressMutation.isPending || updateAddressMutation.isPending}>
                    {editingAddressId ? "Guardar cambios" : "Agregar dirección"}
                  </Button>
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
              {(() => {
                const contacts = detailQuery.data?.contacts ?? [];
                const filtered = contacts.filter((c) => {
                  if (filterContactAddress && c.address_id !== filterContactAddress) return false;
                  if (filterContactPurpose && c.contact_purpose !== filterContactPurpose) return false;
                  return true;
                });
                const addressOptions = [
                  { value: "", label: "Todas las sedes", keywords: ["todas"] },
                  ...(detailQuery.data?.addresses ?? []).map((a) => ({
                    value: a.id,
                    label: `${a.line1} (${a.address_type})`,
                    keywords: [a.line1, a.address_type],
                  })),
                ];
                const purposeOptions = [
                  { value: "", label: "Todos los propósitos", keywords: ["todos"] },
                  ...["GENERAL", "FACTURACION", "COBRANZA", "COMPRAS", "OPERACIONES", "RECEPCION", "OTRO"].map((p) => ({
                    value: p,
                    label: p.charAt(0) + p.slice(1).toLowerCase(),
                    keywords: [p],
                  })),
                ];
                return (
                  <>
                    <div className="flex flex-wrap gap-3">
                      <Combobox
                        value={filterContactAddress ?? ""}
                        onChange={(value) => setFilterContactAddress(value || null)}
                        options={addressOptions}
                        placeholder="Filtrar por sede"
                        searchPlaceholder="Buscar sede..."
                      />
                      <Combobox
                        value={filterContactPurpose ?? ""}
                        onChange={(value) => setFilterContactPurpose(value || null)}
                        options={purposeOptions}
                        placeholder="Filtrar por propósito"
                        searchPlaceholder="Buscar propósito..."
                      />
                    </div>
                    <DataTable
                      dense
                      columns={[
                        {
                          key: "person",
                          header: "Persona",
                          render: (row) => row.full_name || row.contact_type,
                        },
                        { key: "purpose", header: "Propósito", render: (row) => row.contact_purpose },
                        { key: "label", header: "Etiqueta", render: (row) => row.label ?? "-" },
                        { key: "role", header: "Cargo", render: (row) => row.role ?? "-" },
                        { key: "phone", header: "Teléfono", render: (row) => row.phone ?? "-" },
                        { key: "email", header: "Email", render: (row) => row.email ?? "-" },
                        {
                          key: "address",
                          header: "Dirección",
                          render: (row) => {
                            if (!row.address_id) return "-";
                            const addr = detailQuery.data.addresses.find((a) => a.id === row.address_id);
                            return addr ? `${addr.line1} (${addr.address_type})` : "-";
                          },
                        },
                        {
                          key: "primary",
                          header: "Principal",
                          render: (row) => (row.is_primary ? "Sí" : "No"),
                        },
                        {
                          key: "actions",
                          header: "",
                          render: (row) => (
                            <Button
                              variant="secondary"
                              className="h-7 w-7 px-0 py-0"
                              aria-label="Eliminar contacto"
                              onClick={(event) => {
                                event.stopPropagation();
                                setDetailError(null);
                                setConfirmDelete({
                                  id: row.id,
                                  label: "contacto",
                                  onConfirm: () => deleteContactMutation.mutate(row.id, {
                                    onError: (cause) => {
                                      setDetailError(cause instanceof Error ? cause.message : "No se pudo eliminar el contacto.");
                                    },
                                  }),
                                });
                              }}
                            >
                              x
                            </Button>
                          ),
                        },
                      ]}
                      rows={filtered}
                      rowKey={(row) => row.id}
                      emptyMessage="No hay contactos base cargados."
                      onRowClick={(row) => {
                        setEditingContactId(row.id);
                        setContactForm({
                          full_name: row.full_name,
                          label: row.label,
                          role: row.role,
                          phone: row.phone,
                          email: row.email,
                          address_id: row.address_id,
                          contact_purpose: row.contact_purpose,
                          contact_type: row.contact_type,
                          notes: row.notes,
                          is_primary: row.is_primary,
                        });
                      }}
                    />
                  </>
                );
              })()}

              <form className="space-y-3 rounded-md border border-border p-4" onSubmit={submitContact}>
                <div>
                  <p className="font-medium text-foreground">{editingContactId ? "Editar contacto base" : "Nuevo contacto base"}</p>
                  <p className="text-xs text-muted-foreground">Registra una persona de contacto con su propósito, canales y una dirección vinculada.</p>
                </div>
                <div className="grid gap-4 md:grid-cols-2">
                  <label className="block space-y-2 text-sm text-foreground">
                    <span>Nombre completo</span>
                    <Input value={contactForm.full_name ?? ""} onChange={(event) => setContactForm((current) => ({ ...current, full_name: event.target.value || null }))} />
                  </label>
                  <label className="block space-y-2 text-sm text-foreground">
                    <span>Etiqueta</span>
                    <Input value={contactForm.label ?? ""} onChange={(event) => setContactForm((current) => ({ ...current, label: event.target.value || null }))} />
                  </label>
                  <label className="block space-y-2 text-sm text-foreground">
                    <span>Cargo / Rol</span>
                    <Input value={contactForm.role ?? ""} onChange={(event) => setContactForm((current) => ({ ...current, role: event.target.value || null }))} />
                  </label>
                  <label className="block space-y-2 text-sm text-foreground">
                    <span>Teléfono</span>
                    <Input value={contactForm.phone ?? ""} onChange={(event) => setContactForm((current) => ({ ...current, phone: event.target.value || null, contact_type: "PHONE" }))} />
                  </label>
                  <label className="block space-y-2 text-sm text-foreground">
                    <span>Email</span>
                    <Input value={contactForm.email ?? ""} onChange={(event) => setContactForm((current) => ({ ...current, email: event.target.value || null, contact_type: "EMAIL" }))} />
                  </label>
                  <label className="block space-y-2 text-sm text-foreground">
                    <span>Propósito</span>
                    <Combobox
                      value={contactForm.contact_purpose}
                      onChange={(value) => setContactForm((current) => ({ ...current, contact_purpose: value || "GENERAL" }))}
                      options={[
                        { value: "GENERAL", label: "General" },
                        { value: "FACTURACION", label: "Facturación" },
                        { value: "COBRANZA", label: "Cobranza" },
                        { value: "COMPRAS", label: "Compras" },
                        { value: "OPERACIONES", label: "Operaciones" },
                        { value: "RECEPCION", label: "Recepción" },
                        { value: "OTRO", label: "Otro" },
                      ]}
                      placeholder="Seleccionar propósito"
                      searchPlaceholder="Buscar propósito..."
                    />
                  </label>
                  <label className="block space-y-2 text-sm text-foreground">
                    <span>Dirección vinculada</span>
                    <Combobox
                      value={contactForm.address_id ?? ""}
                      onChange={(value) => setContactForm((current) => ({ ...current, address_id: value || null }))}
                      options={(detailQuery.data?.addresses ?? []).map((addr) => ({
                        value: addr.id,
                        label: `${addr.line1}${addr.city ? `, ${addr.city}` : ""} (${addr.address_type})`,
                        keywords: [addr.line1, addr.city ?? "", addr.address_type],
                      }))}
                      placeholder="Sin dirección"
                      searchPlaceholder="Buscar dirección..."
                    />
                  </label>
                  <label className="block space-y-2 text-sm text-foreground md:col-span-2">
                    <span>Notas</span>
                    <Input value={contactForm.notes ?? ""} onChange={(event) => setContactForm((current) => ({ ...current, notes: event.target.value || null }))} />
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
                <div className="flex justify-end gap-2">
                  {editingContactId ? (
                    <Button
                      variant="secondary"
                      type="button"
                      onClick={() => {
                        setEditingContactId(null);
                        setContactForm(EMPTY_CONTACT);
                      }}
                    >
                      Cancelar
                    </Button>
                  ) : null}
                  <Button type="submit" disabled={createContactMutation.isPending || updateContactMutation.isPending}>
                    {editingContactId ? "Guardar cambios" : "Agregar contacto"}
                  </Button>
                </div>
              </form>
            </div>
          </Dialog>

          <Dialog
            open={isCommercialOpen}
            title="Gestión comercial"
            description="Asigna agente y supervisor comercial a nivel cliente o sede, sin mezclarlo con contactos externos ni operación diaria."
            onClose={() => setIsCommercialOpen(false)}
            maxWidthClassName="max-w-4xl"
          >
            <div className="space-y-4 text-sm text-foreground">
              <DataTable
                dense
                columns={[
                  { key: "role", header: "Rol", render: (row) => row.assignment_role },
                  { key: "user", header: "Usuario", render: (row) => row.user_display_name },
                  { key: "email", header: "Email", render: (row) => row.user_email },
                  {
                    key: "address",
                    header: "Sede",
                    render: (row) => {
                      if (!row.address_id) return "Cliente general";
                      const addr = detailQuery.data.addresses.find((a) => a.id === row.address_id);
                      return addr ? `${addr.line1} (${addr.address_type})` : "-";
                    },
                  },
                  { key: "primary", header: "Principal", render: (row) => (row.is_primary ? "Sí" : "No") },
                  {
                    key: "actions",
                    header: "Acciones",
                    render: (row) => (
                      <div className="flex flex-wrap gap-2">
                        <Button
                          variant="secondary"
                          onClick={() => {
                            setEditingCommercialAssignmentId(row.id);
                            setCommercialAssignmentForm({
                              address_id: row.address_id,
                              user_id: row.user_id,
                              assignment_role: row.assignment_role,
                              notes: row.notes,
                              is_primary: row.is_primary,
                              is_active: row.is_active,
                            });
                          }}
                        >
                          Editar
                        </Button>
                        <Button
                          variant="secondary"
                          className="h-7 w-7 px-0 py-0"
                          aria-label="Eliminar asignación comercial"
                          onClick={() => {
                            setDetailError(null);
                            setConfirmDelete({
                              id: row.id,
                              label: "asignación comercial",
                              onConfirm: () => deleteCommercialAssignmentMutation.mutate(row.id, {
                                onError: (cause) => {
                                  setDetailError(cause instanceof Error ? cause.message : "No se pudo eliminar la asignación comercial.");
                                },
                              }),
                            });
                          }}
                        >
                          x
                        </Button>
                      </div>
                    ),
                  },
                ]}
                rows={commercialAssignmentsQuery.data ?? []}
                rowKey={(row) => row.id}
                emptyMessage="No hay asignaciones comerciales cargadas."
              />

              <form className="space-y-3 rounded-md border border-border p-4" onSubmit={submitCommercialAssignment}>
                <div>
                  <p className="font-medium text-foreground">{editingCommercialAssignmentId ? "Editar asignación comercial" : "Nueva asignación comercial"}</p>
                  <p className="text-xs text-muted-foreground">Define ownership comercial interno por cliente o por sede.</p>
                </div>
                <div className="grid gap-4 md:grid-cols-2">
                  <label className="block space-y-2 text-sm text-foreground">
                    <span>Rol comercial</span>
                    <Combobox
                      value={commercialAssignmentForm.assignment_role}
                      onChange={(value) => setCommercialAssignmentForm((current) => ({ ...current, assignment_role: value || "AGENT" }))}
                      options={[
                        { value: "AGENT", label: "Agente" },
                        { value: "SUPERVISOR", label: "Supervisor" },
                      ]}
                      placeholder="Seleccionar rol"
                      searchPlaceholder="Buscar rol..."
                    />
                  </label>
                  <label className="block space-y-2 text-sm text-foreground">
                    <span>Usuario interno</span>
                    <Combobox
                      value={commercialAssignmentForm.user_id}
                      onChange={(value) => setCommercialAssignmentForm((current) => ({ ...current, user_id: value || "" }))}
                      options={(commercialUsersQuery.data ?? []).map((user) => ({
                        value: user.id,
                        label: `${user.full_name} (${user.email})`,
                        keywords: [user.full_name, user.email],
                      }))}
                      placeholder="Seleccionar usuario"
                      searchPlaceholder="Buscar usuario..."
                    />
                  </label>
                  <label className="block space-y-2 text-sm text-foreground">
                    <span>Sede vinculada</span>
                    <Combobox
                      value={commercialAssignmentForm.address_id ?? ""}
                      onChange={(value) => setCommercialAssignmentForm((current) => ({ ...current, address_id: value || null }))}
                      options={[
                        { value: "", label: "Cliente general", keywords: ["general", "cliente"] },
                        ...(detailQuery.data?.addresses ?? []).map((addr) => ({
                          value: addr.id,
                          label: `${addr.line1}${addr.city ? `, ${addr.city}` : ""} (${addr.address_type})`,
                          keywords: [addr.line1, addr.city ?? "", addr.address_type],
                        })),
                      ]}
                      placeholder="Cliente general"
                      searchPlaceholder="Buscar sede..."
                    />
                  </label>
                  <label className="block space-y-2 text-sm text-foreground">
                    <span>Notas</span>
                    <Input value={commercialAssignmentForm.notes ?? ""} onChange={(event) => setCommercialAssignmentForm((current) => ({ ...current, notes: event.target.value || null }))} />
                  </label>
                </div>
                <label className="flex items-center gap-2 text-sm text-foreground">
                  <input
                    type="checkbox"
                    checked={commercialAssignmentForm.is_primary}
                    onChange={(event) => setCommercialAssignmentForm((current) => ({ ...current, is_primary: event.target.checked }))}
                  />
                  <span>Marcar como principal</span>
                </label>
                <div className="flex justify-end gap-2">
                  {editingCommercialAssignmentId ? (
                    <Button
                      variant="secondary"
                      type="button"
                      onClick={() => {
                        setEditingCommercialAssignmentId(null);
                        setCommercialAssignmentForm(EMPTY_COMMERCIAL_ASSIGNMENT);
                      }}
                    >
                      Cancelar
                    </Button>
                  ) : null}
                  <Button type="submit" disabled={createCommercialAssignmentMutation.isPending || updateCommercialAssignmentMutation.isPending}>
                    {editingCommercialAssignmentId ? "Guardar cambios" : "Agregar asignación"}
                  </Button>
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

          <Dialog
            open={isBankAccountsOpen}
            title="Cuentas bancarias"
            description="Gestiona IBAN, titular y banco del cliente para domiciliaciones y remesas."
            onClose={() => setIsBankAccountsOpen(false)}
            maxWidthClassName="max-w-4xl"
          >
            <BankAccountsSection customerId={customerId} canManage />
          </Dialog>

          <Dialog
            open={isPricingOpen}
            title="Precios especiales"
            description="Condiciones comerciales del cliente. El precio base sigue viviendo en productos."
            onClose={() => setIsPricingOpen(false)}
            maxWidthClassName="max-w-4xl"
          >
            <PricingTermsSection customerId={customerId} canManage />
          </Dialog>

          <Dialog
            open={isContractsOpen}
            title="Contratos de envases"
            onClose={() => setIsContractsOpen(false)}
            maxWidthClassName="max-w-3xl"
          >
            <div className="space-y-4 text-sm text-foreground">
              {contractsLoading ? (
                <p className="text-sm text-muted-foreground">Cargando contratos...</p>
              ) : contracts.length === 0 ? (
                <p className="text-sm text-muted-foreground">Este cliente no tiene contratos de envases.</p>
              ) : (
                <DataTable
                  dense
                  rowKey={(row: LogisticsCylinderContract) => row.id}
                  rows={contracts}
                  columns={[
                    { key: "contract_number", header: "Número", render: (row: LogisticsCylinderContract) => row.contract_number || "-" },
                    { key: "type", header: "Tipo", render: (row: LogisticsCylinderContract) => row.contract_type === "ANNUAL" ? "Anual" : "Diario" },
                    { key: "status", header: "Estado", render: (row: LogisticsCylinderContract) => row.status },
                    { key: "quantity", header: "Cant.", render: (row: LogisticsCylinderContract) => `${row.quantity} x` },
                    { key: "start_date", header: "Inicio", render: (row: LogisticsCylinderContract) => row.start_date },
                    { key: "end_date", header: "Fin", render: (row: LogisticsCylinderContract) => row.end_date || "-" },
                  ]}
                />
              )}
            </div>
          </Dialog>

          <ConfirmDialog
            open={confirmDelete !== null}
            onClose={() => setConfirmDelete(null)}
            onConfirm={() => {
              confirmDelete?.onConfirm();
              setConfirmDelete(null);
            }}
            title="Confirmar eliminación"
            description={confirmDelete ? `¿Estás seguro de eliminar ${confirmDelete.label}?` : ""}
            destructive
            confirmLabel="Eliminar"
          />
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
      description="Información general del cliente, envases en posesión y acceso a secciones administrativas."
      onClose={onClose}
      maxWidthClassName="max-w-4xl"
    >
      <div className="max-h-[85vh] overflow-y-auto">{content}</div>
    </Dialog>
  );
}
