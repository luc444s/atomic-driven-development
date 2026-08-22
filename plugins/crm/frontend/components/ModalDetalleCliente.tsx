import { FormEvent, useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "../../../../apps/web/src/lib/react-query";
import { Alert } from "@systutor/shell/ui/alert";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@systutor/shell/ui/card";
import { ConfirmDialog } from "@systutor/shell/ui/confirm-dialog";
import { Dialog } from "@systutor/shell/ui/dialog";
import { toast } from "@systutor/shell/ui/toast";
import { logisticsKeys } from "../../../logistics/frontend/api";
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
import { BankAccountsDialog } from "./BankAccountsDialog";
import { CommercialDialog } from "./CommercialDialog";
import { ContactosDialog } from "./ContactosDialog";
import { CustomerContractsButton } from "./CustomerContractsButton";
import { CustomerOverviewCard } from "./CustomerOverviewCard";
import { DireccionesDialog } from "./DireccionesDialog";
import { PricingTermsDialog } from "./PricingTermsDialog";
import type {
  CustomerAddressPayload,
  CustomerCommercialAssignmentPayload,
  CustomerContactPayload,
} from "../types";

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
  country_code: "PE",
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
  const [isBankAccountsOpen, setIsBankAccountsOpen] = useState(false);
  const [isPricingOpen, setIsPricingOpen] = useState(false);
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

  const content = (
    <div className="space-y-6">
      {detailQuery.error ? <Alert title="No se pudo cargar el cliente">{detailQuery.error.message}</Alert> : null}
      {detailError ? <Alert title="No se pudo completar la acción">{detailError}</Alert> : null}

      {detailQuery.data ? (
        <>
          <div className="space-y-6">
            <CustomerOverviewCard customer={detailQuery.data} />

            <Card>
              <CardHeader>
                <CardTitle>Acciones</CardTitle>
              </CardHeader>
              <CardContent className="text-sm text-foreground">
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  <button
                    type="button"
                    onClick={() => onEditCustomer?.(customerId)}
                    className="rounded-lg border border-border bg-surface p-4 text-left transition hover:border-ring hover:bg-surface-alt"
                  >
                    <p className="text-sm font-medium text-foreground">Editar</p>
                    <p className="mt-1 text-xs text-muted-foreground">Modifica datos generales del cliente.</p>
                  </button>
                  <button
                    type="button"
                    onClick={() => setIsAddressesOpen(true)}
                    className="rounded-lg border border-border bg-surface p-4 text-left transition hover:border-ring hover:bg-surface-alt"
                  >
                    <p className="text-sm font-medium text-foreground">Direcciones</p>
                    <p className="mt-1 text-xs text-muted-foreground">Gestiona direcciones fiscales, comerciales y sedes.</p>
                  </button>
                  <button
                    type="button"
                    onClick={() => setIsContactsOpen(true)}
                    className="rounded-lg border border-border bg-surface p-4 text-left transition hover:border-ring hover:bg-surface-alt"
                  >
                    <p className="text-sm font-medium text-foreground">Contactos</p>
                    <p className="mt-1 text-xs text-muted-foreground">Teléfonos, emails y personas de contacto.</p>
                  </button>
                  <button
                    type="button"
                    onClick={() => setIsCommercialOpen(true)}
                    className="rounded-lg border border-border bg-surface p-4 text-left transition hover:border-ring hover:bg-surface-alt"
                  >
                    <p className="text-sm font-medium text-foreground">Gestión comercial</p>
                    <p className="mt-1 text-xs text-muted-foreground">Asigna agente y supervisor comercial.</p>
                  </button>
                  <button
                    type="button"
                    onClick={() => setIsBankAccountsOpen(true)}
                    className="rounded-lg border border-border bg-surface p-4 text-left transition hover:border-ring hover:bg-surface-alt"
                  >
                    <p className="text-sm font-medium text-foreground">Cuentas bancarias</p>
                    <p className="mt-1 text-xs text-muted-foreground">IBAN, titular y banco para domiciliaciones.</p>
                  </button>
                  <button
                    type="button"
                    onClick={() => setIsPricingOpen(true)}
                    className="rounded-lg border border-border bg-surface p-4 text-left transition hover:border-ring hover:bg-surface-alt"
                  >
                    <p className="text-sm font-medium text-foreground">Precios especiales</p>
                    <p className="mt-1 text-xs text-muted-foreground">Condiciones comerciales por cliente.</p>
                  </button>
                  <CustomerContractsButton customerId={customerId} />
                </div>
                {detailQuery.data.notes ? (
                  <div className="rounded-md border border-border bg-muted/20 p-4">
                    <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Notas</p>
                    <p className="mt-2 break-words">{detailQuery.data.notes}</p>
                  </div>
                ) : null}
              </CardContent>
            </Card>
          </div>

          <DireccionesDialog
            open={isAddressesOpen}
            onClose={() => setIsAddressesOpen(false)}
            addresses={detailQuery.data.addresses}
            fiscalAddressId={detailQuery.data.fiscal_address_id}
            addressForm={addressForm}
            onAddressFormChange={(form) => setAddressForm(form)}
            editingAddressId={editingAddressId}
            onEditingAddressIdChange={setEditingAddressId}
            onCancelEdit={() => {
              setEditingAddressId(null);
              setAddressForm(EMPTY_ADDRESS);
            }}
            onSubmit={submitAddress}
            isCreatePending={createAddressMutation.isPending}
            isUpdatePending={updateAddressMutation.isPending}
            onDelete={(id) => {
              setDetailError(null);
              setConfirmDelete({
                id,
                label: "dirección",
                onConfirm: () => deleteAddressMutation.mutate(id, {
                  onError: (cause) => {
                    setDetailError(cause instanceof Error ? cause.message : "No se pudo eliminar la dirección.");
                  },
                }),
              });
            }}
          />

          <ContactosDialog
            open={isContactsOpen}
            onClose={() => setIsContactsOpen(false)}
            contacts={detailQuery.data?.contacts ?? []}
            addresses={detailQuery.data?.addresses ?? []}
            filterContactAddress={filterContactAddress}
            onFilterContactAddressChange={setFilterContactAddress}
            filterContactPurpose={filterContactPurpose}
            onFilterContactPurposeChange={setFilterContactPurpose}
            contactForm={contactForm}
            onContactFormChange={(form) => setContactForm(form)}
            editingContactId={editingContactId}
            onEditingContactIdChange={setEditingContactId}
            onCancelEdit={() => {
              setEditingContactId(null);
              setContactForm(EMPTY_CONTACT);
            }}
            onSubmit={submitContact}
            isCreatePending={createContactMutation.isPending}
            isUpdatePending={updateContactMutation.isPending}
            onDelete={(id) => {
              setDetailError(null);
              setConfirmDelete({
                id,
                label: "contacto",
                onConfirm: () => deleteContactMutation.mutate(id, {
                  onError: (cause) => {
                    setDetailError(cause instanceof Error ? cause.message : "No se pudo eliminar el contacto.");
                  },
                }),
              });
            }}
          />

          <CommercialDialog
            open={isCommercialOpen}
            onClose={() => setIsCommercialOpen(false)}
            assignments={commercialAssignmentsQuery.data ?? []}
            addresses={detailQuery.data?.addresses ?? []}
            users={commercialUsersQuery.data ?? []}
            form={commercialAssignmentForm}
            onFormChange={(form) => setCommercialAssignmentForm(form)}
            editingId={editingCommercialAssignmentId}
            onEditingIdChange={setEditingCommercialAssignmentId}
            onCancelEdit={() => {
              setEditingCommercialAssignmentId(null);
              setCommercialAssignmentForm(EMPTY_COMMERCIAL_ASSIGNMENT);
            }}
            onSubmit={submitCommercialAssignment}
            isCreatePending={createCommercialAssignmentMutation.isPending}
            isUpdatePending={updateCommercialAssignmentMutation.isPending}
            onEdit={(id, data) => {
              setEditingCommercialAssignmentId(id);
              setCommercialAssignmentForm(data);
            }}
            onDelete={(id) => {
              setDetailError(null);
              setConfirmDelete({
                id,
                label: "asignación comercial",
                onConfirm: () => deleteCommercialAssignmentMutation.mutate(id, {
                  onError: (cause) => {
                    setDetailError(cause instanceof Error ? cause.message : "No se pudo eliminar la asignación comercial.");
                  },
                }),
              });
            }}
          />

          <BankAccountsDialog
            open={isBankAccountsOpen}
            onClose={() => setIsBankAccountsOpen(false)}
            customerId={customerId}
          />

          <PricingTermsDialog
            open={isPricingOpen}
            onClose={() => setIsPricingOpen(false)}
            customerId={customerId}
          />

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
      maxWidthClassName="max-w-[1000px]"
    >
      <div className="max-h-[85vh] overflow-y-auto">{content}</div>
    </Dialog>
  );
}
