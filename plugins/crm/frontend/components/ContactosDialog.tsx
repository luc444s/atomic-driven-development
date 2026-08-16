import { FormEvent } from "react";
import { Button } from "@systutor/shell/ui/button";
import { Combobox } from "@systutor/shell/ui/combobox";
import { DataTable } from "@systutor/shell/ui/data-table";
import { Dialog } from "@systutor/shell/ui/dialog";
import { Input } from "@systutor/shell/ui/input";
import type { CustomerContactPayload } from "../types";

type ContactosDialogProps = {
  open: boolean;
  onClose: () => void;
  contacts: Array<Record<string, unknown>>;
  addresses: Array<Record<string, unknown>>;
  filterContactAddress: string | null;
  onFilterContactAddressChange: (v: string | null) => void;
  filterContactPurpose: string | null;
  onFilterContactPurposeChange: (v: string | null) => void;
  contactForm: CustomerContactPayload;
  onContactFormChange: (form: CustomerContactPayload) => void;
  editingContactId: string | null;
  onEditingContactIdChange: (id: string | null) => void;
  onCancelEdit: () => void;
  onSubmit: (e: FormEvent<HTMLFormElement>) => Promise<void>;
  isCreatePending: boolean;
  isUpdatePending: boolean;
  onDelete: (id: string) => void;
};

export function ContactosDialog({
  open,
  onClose,
  contacts,
  addresses,
  filterContactAddress,
  onFilterContactAddressChange,
  filterContactPurpose,
  onFilterContactPurposeChange,
  contactForm,
  onContactFormChange,
  editingContactId,
  onEditingContactIdChange,
  onCancelEdit,
  onSubmit,
  isCreatePending,
  isUpdatePending,
  onDelete,
}: ContactosDialogProps) {
  const filtered = contacts.filter((c) => {
    if (filterContactAddress && c.address_id !== filterContactAddress) return false;
    if (filterContactPurpose && c.contact_purpose !== filterContactPurpose) return false;
    return true;
  });

  const addressOptions = [
    { value: "", label: "Todas las sedes", keywords: ["todas"] },
    ...addresses.map((a) => ({
      value: a.id as string,
      label: `${a.line1} (${a.address_type})`,
      keywords: [a.line1 as string, a.address_type as string],
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
    <Dialog
      open={open}
      title="Contactos base"
      description="Gestiona teléfonos, emails y otros contactos generales del cliente."
      onClose={onClose}
      maxWidthClassName="max-w-3xl"
    >
      <div className="space-y-4 text-sm text-foreground">
        <div className="flex flex-wrap gap-3">
          <Combobox
            value={filterContactAddress ?? ""}
            onChange={(v) => onFilterContactAddressChange(v || null)}
            options={addressOptions}
            placeholder="Filtrar por sede"
            searchPlaceholder="Buscar sede..."
          />
          <Combobox
            value={filterContactPurpose ?? ""}
            onChange={(v) => onFilterContactPurposeChange(v || null)}
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
              render: (row) => (row.full_name || row.contact_type) as string,
            },
            { key: "purpose", header: "Propósito", render: (row) => row.contact_purpose as string },
            { key: "label", header: "Etiqueta", render: (row) => (row.label ?? "-") as string },
            { key: "role", header: "Cargo", render: (row) => (row.role ?? "-") as string },
            { key: "phone", header: "Teléfono", render: (row) => (row.phone ?? "-") as string },
            { key: "email", header: "Email", render: (row) => (row.email ?? "-") as string },
            {
              key: "address",
              header: "Dirección",
              render: (row) => {
                if (!row.address_id) return "-";
                const addr = addresses.find((a) => a.id === row.address_id);
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
                    onDelete(row.id as string);
                  }}
                >
                  x
                </Button>
              ),
            },
          ]}
          rows={filtered}
          rowKey={(row) => row.id as string}
          emptyMessage="No hay contactos base cargados."
          onRowClick={(row) => {
            onEditingContactIdChange(row.id as string);
            onContactFormChange({
              full_name: (row.full_name as string) || null,
              label: (row.label as string) || null,
              role: (row.role as string) || null,
              phone: (row.phone as string) || null,
              email: (row.email as string) || null,
              address_id: (row.address_id as string) || null,
              contact_purpose: (row.contact_purpose as string) || "GENERAL",
              contact_type: (row.contact_type as string) || "PHONE",
              notes: (row.notes as string) || null,
              is_primary: (row.is_primary as boolean) || false,
            });
          }}
        />

        <form className="space-y-3 rounded-md border border-border p-4" onSubmit={onSubmit}>
          <div>
            <p className="font-medium text-foreground">{editingContactId ? "Editar contacto base" : "Nuevo contacto base"}</p>
            <p className="text-xs text-muted-foreground">Registra una persona de contacto con su propósito, canales y una dirección vinculada.</p>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <label className="block space-y-2 text-sm text-foreground">
              <span>Nombre completo</span>
              <Input value={contactForm.full_name ?? ""} onChange={(e) => onContactFormChange({ ...contactForm, full_name: e.target.value || null })} />
            </label>
            <label className="block space-y-2 text-sm text-foreground">
              <span>Etiqueta</span>
              <Input value={contactForm.label ?? ""} onChange={(e) => onContactFormChange({ ...contactForm, label: e.target.value || null })} />
            </label>
            <label className="block space-y-2 text-sm text-foreground">
              <span>Cargo / Rol</span>
              <Input value={contactForm.role ?? ""} onChange={(e) => onContactFormChange({ ...contactForm, role: e.target.value || null })} />
            </label>
            <label className="block space-y-2 text-sm text-foreground">
              <span>Teléfono</span>
              <Input value={contactForm.phone ?? ""} onChange={(e) => onContactFormChange({ ...contactForm, phone: e.target.value || null, contact_type: "PHONE" })} />
            </label>
            <label className="block space-y-2 text-sm text-foreground">
              <span>Email</span>
              <Input value={contactForm.email ?? ""} onChange={(e) => onContactFormChange({ ...contactForm, email: e.target.value || null, contact_type: "EMAIL" })} />
            </label>
            <label className="block space-y-2 text-sm text-foreground">
              <span>Propósito</span>
              <Combobox
                value={contactForm.contact_purpose}
                onChange={(v) => onContactFormChange({ ...contactForm, contact_purpose: v || "GENERAL" })}
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
                onChange={(v) => onContactFormChange({ ...contactForm, address_id: v || null })}
                options={addresses.map((addr) => ({
                  value: addr.id as string,
                  label: `${addr.line1}${addr.city ? `, ${addr.city}` : ""} (${addr.address_type})`,
                  keywords: [addr.line1 as string, (addr.city as string) ?? "", addr.address_type as string],
                }))}
                placeholder="Sin dirección"
                searchPlaceholder="Buscar dirección..."
              />
            </label>
            <label className="block space-y-2 text-sm text-foreground md:col-span-2">
              <span>Notas</span>
              <Input value={contactForm.notes ?? ""} onChange={(e) => onContactFormChange({ ...contactForm, notes: e.target.value || null })} />
            </label>
          </div>
          <label className="flex items-center gap-2 text-sm text-foreground">
            <input
              type="checkbox"
              checked={contactForm.is_primary}
              onChange={(e) => onContactFormChange({ ...contactForm, is_primary: e.target.checked })}
            />
            <span>Marcar como principal</span>
          </label>
          <div className="flex justify-end gap-2">
            {editingContactId ? (
              <Button variant="secondary" type="button" onClick={onCancelEdit}>
                Cancelar
              </Button>
            ) : null}
            <Button type="submit" disabled={isCreatePending || isUpdatePending}>
              {editingContactId ? "Guardar cambios" : "Agregar contacto"}
            </Button>
          </div>
        </form>
      </div>
    </Dialog>
  );
}
