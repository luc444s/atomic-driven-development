import { FormEvent, useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "../../../../apps/web/src/lib/react-query";
import { Button } from "../../../../apps/web/src/shared/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../../../apps/web/src/shared/ui/card";
import { Input } from "../../../../apps/web/src/shared/ui/input";
import { Alert } from "../../../../apps/web/src/shared/ui/alert";
import { Dialog } from "../../../../apps/web/src/shared/ui/dialog";
import {
  createCustomer,
  createCustomerAddress,
  crmKeys,
  getCustomer,
  listCountries,
  listDocumentTypes,
  setFiscalAddress,
  updateCustomer,
  updateCustomerAddress,
} from "../api";
import { AddressSection } from "./AddressSection";
import { ContactSection } from "./ContactSection";
import { FiscalInfoSection } from "./FiscalInfoSection";
import type { Customer, CustomerAddressPayload, CustomerPayload } from "../types";

const EMPTY_CUSTOMER: CustomerPayload = {
  external_code: null,
  legal_name: "",
  commercial_name: null,
  document_type_code: "RUC",
  document_number: "",
  country_code: "PER",
  email: null,
  phone: null,
  mobile: null,
  economic_activity_code: null,
  economic_activity_description: null,
  payment_term_code: null,
  billing_type: "por_operacion",
  is_exempt: false,
  first_name: null,
  last_name: null,
  birth_date: null,
  gender: null,
  notes: null,
};

function emptyAddress(address_type = "FISCAL"): CustomerAddressPayload {
  return {
    address_type,
    label: address_type === "FISCAL" ? "Fiscal" : address_type === "COMERCIAL" ? "Comercial" : address_type === "ENTREGA" ? "Entrega" : "Otra",
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
}

export type ModalNuevoClienteProps = {
  open: boolean;
  customerId?: string;
  onClose: () => void;
  onSaved?: (customer: Customer) => void;
  onOpenDetail?: (customerId: string) => void;
  asPage?: boolean;
};

export function ModalNuevoCliente({ open, customerId, onClose, onSaved, onOpenDetail, asPage }: ModalNuevoClienteProps) {
  const queryClient = useQueryClient();
  const [formState, setFormState] = useState<CustomerPayload>(EMPTY_CUSTOMER);
  const [addressesState, setAddressesState] = useState<CustomerAddressPayload[]>([emptyAddress()]);
  const [error, setError] = useState<string | null>(null);

  const detailQuery = useQuery({
    queryKey: crmKeys.customers.detail(customerId ?? "new"),
    queryFn: () => getCustomer(customerId!),
    enabled: Boolean(customerId) && open,
  });
  const countriesQuery = useQuery({
    queryKey: crmKeys.geography.countries,
    queryFn: listCountries,
    enabled: open,
  });
  const documentTypesQuery = useQuery({
    queryKey: crmKeys.catalogs.documentTypes(formState.country_code),
    queryFn: () => listDocumentTypes(formState.country_code),
    enabled: open,
  });

  useEffect(() => {
    if (!detailQuery.data) {
      return;
    }
    setFormState({
      external_code: detailQuery.data.external_code,
      legal_name: detailQuery.data.legal_name,
      commercial_name: detailQuery.data.commercial_name,
      document_type_code: detailQuery.data.document_type_code,
      document_number: detailQuery.data.document_number,
      country_code: detailQuery.data.country_code,
      email: detailQuery.data.email,
      phone: detailQuery.data.phone,
      mobile: detailQuery.data.mobile,
      economic_activity_code: detailQuery.data.economic_activity_code,
      economic_activity_description: detailQuery.data.economic_activity_description,
      payment_term_code: detailQuery.data.payment_term_code,
      billing_type: detailQuery.data.billing_type,
      is_exempt: detailQuery.data.is_exempt,
      first_name: detailQuery.data.first_name,
      last_name: detailQuery.data.last_name,
      birth_date: detailQuery.data.birth_date,
      gender: detailQuery.data.gender,
      notes: detailQuery.data.notes,
    });
    if (detailQuery.data.addresses.length > 0) {
      setAddressesState(
        detailQuery.data.addresses.map((item) => ({
          address_type: item.address_type,
          label: item.label,
          geography_id: item.geography_id,
          line1: item.line1,
          line2: item.line2,
          city: item.city,
          state: item.state,
          district: item.district,
          postal_code: item.postal_code,
          country_code: item.country_code,
          latitude: item.latitude,
          longitude: item.longitude,
          place_id: item.place_id,
          formatted_address: item.formatted_address,
          street_name: item.street_name,
          street_number: item.street_number,
          geocode_source: item.geocode_source,
          precision_meters: item.precision_meters,
          gps_link: item.gps_link,
          contact_name: item.contact_name,
          contact_phone: item.contact_phone,
          contact_email: item.contact_email,
          notes: item.notes,
          ubigeo_code: item.ubigeo_code,
        }))
      );
    }
  }, [detailQuery.data]);

  useEffect(() => {
    if (!open) {
      setFormState(EMPTY_CUSTOMER);
      setAddressesState([emptyAddress()]);
      setError(null);
    }
  }, [open]);

  const createMutation = useMutation({
    mutationFn: async (payload: CustomerPayload) => {
      const customer = await createCustomer(payload);
      const validAddresses = addressesState.filter((a) => a.line1.trim());
      let fiscalId: string | null = null;
      for (const addr of validAddresses) {
        const created = await createCustomerAddress(customer.id, addr);
        if (addr.address_type === "FISCAL" && !fiscalId) {
          fiscalId = created.id;
        }
      }
      if (fiscalId) {
        await setFiscalAddress(customer.id, fiscalId);
      }
      return getCustomer(customer.id);
    },
    onSuccess: async (customer) => {
      await queryClient.invalidateQueries({ queryKey: crmKeys.customers.all });
      onSaved?.(customer);
      onClose();
    },
  });

  const updateMutation = useMutation({
    mutationFn: async (payload: CustomerPayload) => {
      const customer = await updateCustomer(customerId!, payload);
      const fiscalAddress = detailQuery.data?.addresses.find((item) => item.id === detailQuery.data?.fiscal_address_id);
      const firstAddress = addressesState.find((a) => a.line1.trim());
      if (firstAddress) {
        if (fiscalAddress) {
          await updateCustomerAddress(fiscalAddress.id, { ...firstAddress, address_type: fiscalAddress.address_type });
        } else {
          const address = await createCustomerAddress(customer.id, firstAddress);
          await setFiscalAddress(customer.id, address.id);
        }
      }
      return getCustomer(customer.id);
    },
    onSuccess: async (customer) => {
      await queryClient.invalidateQueries({ queryKey: crmKeys.customers.all });
      await queryClient.invalidateQueries({ queryKey: crmKeys.customers.detail(customer.id) });
      onSaved?.(customer);
      onClose();
    },
  });

  async function submitForm(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    try {
      if (customerId) {
        await updateMutation.mutateAsync(formState);
      } else {
        await createMutation.mutateAsync(formState);
      }
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "No se pudo guardar el cliente.");
    }
  }

  const formContent = (
    <form className="space-y-6" onSubmit={submitForm}>
      {error ? <Alert title="No se pudo guardar">{error}</Alert> : null}

      <Card>
        <CardHeader>
          <CardTitle>Datos generales</CardTitle>
          <CardDescription>Identificación fiscal y datos comerciales.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <FiscalInfoSection
            documentType={formState.document_type_code}
            documentNumber={formState.document_number}
            countryCode={formState.country_code}
            countryOptions={(countriesQuery.data ?? []).map((item) => ({
              value: item.country_code,
              label: item.name,
              keywords: [item.code ?? "", item.country_code],
            }))}
            documentTypeOptions={(documentTypesQuery.data ?? []).map((item) => ({
              value: item.code,
              label: item.name,
              keywords: [item.code, item.description ?? ""],
            }))}
            onChange={(field, value) => setFormState((current) => ({ ...current, [field]: value }))}
          />
          <div className="grid gap-4 md:grid-cols-2">
            <label className="block space-y-2 text-sm text-foreground">
              <span>Razón social / nombre</span>
              <Input value={formState.legal_name} onChange={(event) => setFormState((current) => ({ ...current, legal_name: event.target.value }))} />
            </label>
            <label className="block space-y-2 text-sm text-foreground">
              <span>Nombre comercial</span>
              <Input value={formState.commercial_name ?? ""} onChange={(event) => setFormState((current) => ({ ...current, commercial_name: event.target.value || null }))} />
            </label>
          </div>
          <ContactSection
            email={formState.email ?? ""}
            phone={formState.phone ?? ""}
            mobile={formState.mobile ?? ""}
            onChange={(field, value) => setFormState((current) => ({ ...current, [field]: value || null }))}
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Direcciones</CardTitle>
          <CardDescription>
            Dirección fiscal, comercial, entrega u otras. La primera dirección con tipo "Fiscal" se usará como domicilio fiscal.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {addressesState.map((addr, i) => (
            <div key={i} className="space-y-3 rounded-lg border border-border p-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-semibold text-foreground">
                  Dirección {i + 1}
                  {i === 0 ? <span className="ml-2 text-xs font-normal text-muted-foreground">(fiscal por defecto)</span> : null}
                </span>
                {addressesState.length > 1 ? (
                  <button
                    type="button"
                    className="text-sm text-muted-foreground hover:text-foreground"
                    onClick={() => setAddressesState((prev) => prev.filter((_, j) => j !== i))}
                  >
                    x
                  </button>
                ) : null}
              </div>
              <AddressSection
                value={addr}
                onChange={(updated) => setAddressesState((prev) => prev.map((item, j) => (j === i ? updated : item)))}
              />
            </div>
          ))}
          <button
            type="button"
            className="text-sm font-medium text-primary hover:underline"
            onClick={() => setAddressesState((prev) => [...prev, emptyAddress("COMERCIAL")])}
          >
            + Agregar dirección
          </button>
        </CardContent>
      </Card>

      {detailQuery.data ? (
        <Card>
                  </Card>
      ) : null}

      {customerId ? (
        <Card>
          <CardHeader>
            <CardTitle>Detalle del cliente</CardTitle>
            <CardDescription>Ver la ficha completa con direcciones y contactos.</CardDescription>
          </CardHeader>
          <CardContent>
            <Button type="button" variant="secondary" onClick={() => onOpenDetail?.(customerId)}>
              Ir al detalle
            </Button>
          </CardContent>
        </Card>
      ) : null}

      <div className="flex justify-end gap-3">
        <Button type="button" variant="secondary" onClick={onClose}>Cancelar</Button>
        <Button type="submit" disabled={createMutation.isPending || updateMutation.isPending}>Guardar</Button>
      </div>
    </form>
  );

  if (asPage) {
    return <div className="p-6">{formContent}</div>;
  }

  return (
    <Dialog
      open={open}
      title={customerId ? "Editar cliente" : "Nuevo cliente"}
      description="Formulario base del cliente. La dirección fiscal se completa en el segundo bloque."
      onClose={onClose}
      maxWidthClassName="max-w-3xl"
    >
      <div className="max-h-[75vh] overflow-y-auto">{formContent}</div>
    </Dialog>
  );
}
