import { FormEvent } from "react";
import { AddressSection } from "./AddressSection";
import { Button } from "../../../../apps/web/src/shared/ui/button";
import { PaginatedDataTable } from "../../../../apps/web/src/shared/ui/paginated-data-table";
import { Dialog } from "../../../../apps/web/src/shared/ui/dialog";
import { Input } from "../../../../apps/web/src/shared/ui/input";
import type { CustomerAddressPayload } from "../types";

type DireccionesDialogProps = {
  open: boolean;
  onClose: () => void;
  addresses: Array<Record<string, unknown>>;
  fiscalAddressId: string | null | undefined;
  addressForm: CustomerAddressPayload;
  onAddressFormChange: (form: CustomerAddressPayload) => void;
  editingAddressId: string | null;
  onEditingAddressIdChange: (id: string | null) => void;
  onCancelEdit: () => void;
  onSubmit: (e: FormEvent<HTMLFormElement>) => Promise<void>;
  isCreatePending: boolean;
  isUpdatePending: boolean;
  onDelete: (id: string) => void;
};

export function DireccionesDialog({
  open,
  onClose,
  addresses,
  fiscalAddressId,
  addressForm,
  onAddressFormChange,
  editingAddressId,
  onEditingAddressIdChange,
  onCancelEdit,
  onSubmit,
  isCreatePending,
  isUpdatePending,
  onDelete,
}: DireccionesDialogProps) {
  return (
    <Dialog
      open={open}
      title="Direcciones"
      description="Gestiona direcciones fiscales, comerciales y otras direcciones base del cliente."
      onClose={onClose}
      maxWidthClassName="max-w-6xl"
    >
      <div className="space-y-4 text-sm text-foreground">
        <PaginatedDataTable
          dense
          columns={[
            {
              key: "label",
              header: "Etiqueta",
              render: (row) => (row.label as string) || (row.address_type as string),
            },
            { key: "type", header: "Tipo", render: (row) => row.address_type as string },
            {
              key: "address",
              header: "Dirección",
              render: (row) => {
                const line1 = (row.line1 as string) || "";
                const parts = line1.split(",").map((part) => part.trim()).filter(Boolean);
                return parts.slice(0, 2).join(", ") || "-";
              },
            },
            {
              key: "locality",
              header: "Localidad",
              render: (row) => (row.district ?? row.city ?? row.state ?? "-") as string,
            },
            {
              key: "site",
              header: "Sede",
              render: (row) => (row.is_operational_site ? "Sí" : "No"),
            },
            { key: "contact", header: "Contacto", render: (row) => (row.contact_name ?? "-") as string },
            { key: "phone", header: "Teléfono", render: (row) => (row.contact_phone ?? "-") as string },
            {
              key: "fiscal",
              header: "Fiscal",
              render: (row) => (fiscalAddressId === row.id ? "Sí" : "No"),
            },
            {
              key: "actions",
              header: "",
              render: (row) => {
                const canDelete = fiscalAddressId !== row.id;
                return canDelete ? (
                  <Button
                    variant="secondary"
                    className="h-7 w-7 px-0 py-0"
                    aria-label="Eliminar dirección"
                    onClick={(event) => {
                      event.stopPropagation();
                      onDelete(row.id as string);
                    }}
                  >
                    x
                  </Button>
                ) : null;
              },
            },
          ]}
          rows={addresses}
          rowKey={(row) => row.id as string}
          emptyMessage="No hay direcciones cargadas."
          onRowClick={(row) => {
            onEditingAddressIdChange(row.id as string);
            onAddressFormChange({
              address_type: (row.address_type as string) || "COMERCIAL",
              label: (row.label as string) || null,
              geography_id: (row.geography_id as string) || null,
              line1: (row.line1 as string) || "",
              line2: (row.line2 as string) || null,
              city: (row.city as string) || null,
              state: (row.state as string) || null,
              district: (row.district as string) || null,
              postal_code: (row.postal_code as string) || null,
              country_code: (row.country_code as string) || "PER",
              latitude: (row.latitude as number) || null,
              longitude: (row.longitude as number) || null,
              place_id: (row.place_id as string) || null,
              formatted_address: (row.formatted_address as string) || null,
              street_name: (row.street_name as string) || null,
              street_number: (row.street_number as string) || null,
              geocode_source: (row.geocode_source as string) || "MANUAL",
              precision_meters: (row.precision_meters as number) || null,
              gps_link: (row.gps_link as string) || null,
              contact_name: (row.contact_name as string) || null,
              contact_phone: (row.contact_phone as string) || null,
              contact_email: (row.contact_email as string) || null,
              is_operational_site: (row.is_operational_site as boolean) || false,
              notes: (row.notes as string) || null,
              ubigeo_code: (row.ubigeo_code as string) || null,
            });
          }}
        />

        <form className="space-y-3 rounded-md border border-border p-4" onSubmit={onSubmit}>
          <div>
            <p className="font-medium text-foreground">{editingAddressId ? "Editar dirección" : "Nueva dirección CRM"}</p>
            <p className="text-xs text-muted-foreground">Úsala para sedes fiscales, comerciales u otras direcciones base del cliente.</p>
          </div>
          <label className="block space-y-2 text-sm text-foreground">
            <span>Etiqueta</span>
            <Input value={addressForm.label ?? ""} onChange={(event) => onAddressFormChange({ ...addressForm, label: event.target.value || null })} />
          </label>
          <AddressSection value={addressForm} onChange={onAddressFormChange} />
          <div className="flex justify-end gap-2">
            {editingAddressId ? (
              <Button variant="secondary" type="button" onClick={onCancelEdit}>
                Cancelar
              </Button>
            ) : null}
            <Button type="submit" disabled={isCreatePending || isUpdatePending}>
              {editingAddressId ? "Guardar cambios" : "Agregar dirección"}
            </Button>
          </div>
        </form>
      </div>
    </Dialog>
  );
}
