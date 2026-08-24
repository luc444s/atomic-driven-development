import { useMutation, useQueryClient } from "../../../../../apps/web/src/lib/react-query";
import { FormEvent, useState } from "react";
import {
  addSupplierAddress,
  addSupplierBankAccount,
  addSupplierContact,
  disableSupplier,
  removeSupplierAddress,
  removeSupplierBankAccount,
  removeSupplierContact,
} from "../api";
import type { Supplier } from "../types";
import { Button } from "@systutor/shell/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@systutor/shell/ui/card";
import { ConfirmDialog } from "@systutor/shell/ui/confirm-dialog";
import { DataTable } from "@systutor/shell/ui/data-table";
import { Dialog } from "@systutor/shell/ui/dialog";
import { Input } from "@systutor/shell/ui/input";
import { Alert } from "@systutor/shell/ui/alert";
import { LocationPickerLazy as LocationPicker } from "./LocationPickerLazy";
import { SupplierOverviewCard } from "./SupplierOverviewCard";

type Props = {
  open: boolean;
  /** Proveedor a mostrar; la página dueña de la lista lo mantiene actualizado. */
  supplier: Supplier | null;
  onClose: () => void;
  onEdit: (supplierId: string) => void;
};

const EMPTY_ADDR = { line1: "", label: "", district: "", city: "", latitude: null as number | null, longitude: null as number | null };
const EMPTY_CONTACT = { full_name: "", role: "", phone: "", email: "" };
const EMPTY_BANK = { bank_name: "", account_holder: "", iban: "", bic_swift: "" };

export function SupplierDetailModal({ open, supplier, onClose, onEdit }: Props) {
  const queryClient = useQueryClient();
  const [error, setError] = useState<string | null>(null);
  const [openSection, setOpenSection] = useState<"addresses" | "contacts" | "banks" | null>(null);

  const detail = supplier;

  function invalidate() {
    queryClient.invalidateQueries({ queryKey: ["compras", "suppliers"] });
  }

  function closeSection() {
    setOpenSection(null);
    setError(null);
  }

  const disableMut = useMutation({
    mutationFn: () => disableSupplier(detail!.id),
    onSuccess: invalidate,
  });

  if (!detail) {
    return (
      <Dialog open={open} title="Detalle del proveedor" onClose={onClose}>
        <p className="py-6 text-center text-sm text-muted-foreground">Proveedor no encontrado.</p>
      </Dialog>
    );
  }

  return (
    <>
      <Dialog
        open={open}
        title="Detalle del proveedor"
        description="Datos fiscales, direcciones, contactos y cuentas bancarias del proveedor."
        onClose={onClose}
        maxWidthClassName="max-w-4xl"
      >
        <div className="space-y-6">
          <div className="space-y-6">
            <SupplierOverviewCard supplier={detail} />

            <Card>
              <CardHeader>
                <CardTitle>Acciones</CardTitle>
              </CardHeader>
              <CardContent className="text-sm text-foreground">
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  <button
                    type="button"
                    onClick={() => onEdit(detail.id)}
                    className="rounded-lg border border-border bg-surface p-4 text-left transition hover:border-ring hover:bg-surface-alt"
                  >
                    <p className="font-medium">Editar</p>
                    <p className="mt-1 text-xs text-muted-foreground">Modifica datos generales y condiciones comerciales.</p>
                  </button>
                  <button
                    type="button"
                    onClick={() => setOpenSection("addresses")}
                    className="rounded-lg border border-border bg-surface p-4 text-left transition hover:border-ring hover:bg-surface-alt"
                  >
                    <p className="font-medium">Direcciones</p>
                    <p className="mt-1 text-xs text-muted-foreground">{detail.addresses.length} registradas.</p>
                  </button>
                  <button
                    type="button"
                    onClick={() => setOpenSection("contacts")}
                    className="rounded-lg border border-border bg-surface p-4 text-left transition hover:border-ring hover:bg-surface-alt"
                  >
                    <p className="font-medium">Contactos</p>
                    <p className="mt-1 text-xs text-muted-foreground">{detail.contacts.length} registrados.</p>
                  </button>
                  <button
                    type="button"
                    onClick={() => setOpenSection("banks")}
                    className="rounded-lg border border-border bg-surface p-4 text-left transition hover:border-ring hover:bg-surface-alt"
                  >
                    <p className="font-medium">Cuentas bancarias</p>
                    <p className="mt-1 text-xs text-muted-foreground">{detail.bank_accounts.length} registradas.</p>
                  </button>
                </div>
                {detail.notes ? (
                  <div className="mt-4 rounded-md border border-border bg-muted/20 p-4">
                    <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Notas</p>
                    <p className="mt-2 break-words">{detail.notes}</p>
                  </div>
                ) : null}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Envases en custodia</CardTitle>
                <CardDescription>Cilindros propios actualmente en poder de este proveedor.</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  Sin envases en custodia todavía. Esta sección se activará con el despacho de cilindros a proveedor.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </Dialog>

      <SupplierAddressesDialog
        open={openSection === "addresses"}
        supplier={detail}
        onError={setError}
        onClose={closeSection}
      />
      <SupplierContactsDialog
        open={openSection === "contacts"}
        supplier={detail}
        onError={setError}
        onClose={closeSection}
      />
      <SupplierBanksDialog
        open={openSection === "banks"}
        supplier={detail}
        onError={setError}
        onClose={closeSection}
      />
    </>
  );
}

type SectionProps = {
  open: boolean;
  supplier: Supplier;
  onClose: () => void;
  onError: (message: string | null) => void;
};

function SupplierAddressesDialog({ open, supplier, onClose, onError }: SectionProps) {
  const queryClient = useQueryClient();
  const [form, setForm] = useState(EMPTY_ADDR);
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);

  function invalidate() {
    queryClient.invalidateQueries({ queryKey: ["compras", "suppliers"] });
  }

  const saveMut = useMutation({
    mutationFn: (e: FormEvent) => {
      e.preventDefault();
      return addSupplierAddress(supplier.id, {
        line1: form.line1, label: form.label || null, district: form.district || null,
        city: form.city || null, latitude: form.latitude, longitude: form.longitude,
      });
    },
    onSuccess: () => { invalidate(); setEditingId(null); setForm(EMPTY_ADDR); },
    onError: (err) => onError(err instanceof Error ? err.message : "Error al guardar dirección"),
  });
  const deleteMut = useMutation({
    mutationFn: (addressId: string) => removeSupplierAddress(supplier.id, addressId),
    onSuccess: () => { invalidate(); setConfirmDeleteId(null); },
  });

  const isPending = saveMut.isPending;

  return (
    <Dialog open={open} title="Direcciones" description={`Direcciones de ${supplier.name}.`} onClose={onClose} maxWidthClassName="max-w-3xl">
      <div className="space-y-4">
        <DataTable
          dense
          columns={[
            { key: "label", header: "Etiqueta", render: (row: Supplier["addresses"][number]) => row.label ?? "-" },
            { key: "line1", header: "Dirección", render: (row: Supplier["addresses"][number]) => row.line1 ?? "-" },
            { key: "locality", header: "Localidad", render: (row: Supplier["addresses"][number]) => [row.district, row.city].filter(Boolean).join(", ") || "-" },
            {
              key: "actions",
              header: "",
              render: (row: Supplier["addresses"][number]) => (
                <Button variant="secondary" className="h-7 w-7 px-0 py-0" aria-label="Eliminar dirección" onClick={(event) => { event.stopPropagation(); setConfirmDeleteId(row.id); }}>x</Button>
              ),
            },
          ]}
          rows={supplier.addresses}
          rowKey={(row) => row.id}
          emptyMessage="No hay direcciones registradas."
        />
        <Button variant="secondary" onClick={() => { setEditingId(null); setForm(EMPTY_ADDR); }}>
          Agregar dirección
        </Button>

        <form
          className="space-y-3 rounded-md border border-dashed border-border p-3"
          onSubmit={saveMut.mutate}
        >
          <p className="text-sm font-medium text-foreground">Nueva dirección</p>
          <div className="grid gap-3 md:grid-cols-2">
            <Input value={form.label} onChange={(e) => setForm(p => ({ ...p, label: e.target.value }))} placeholder="Tipo (Principal)" />
            <Input value={form.line1} onChange={(e) => setForm(p => ({ ...p, line1: e.target.value }))} placeholder="Av. Principal 123" required />
            <Input value={form.district} onChange={(e) => setForm(p => ({ ...p, district: e.target.value }))} placeholder="Distrito" />
            <Input value={form.city} onChange={(e) => setForm(p => ({ ...p, city: e.target.value }))} placeholder="Ciudad" />
          </div>
          <LocationPicker
            value={form.latitude != null && form.longitude != null ? { lat: form.latitude, lng: form.longitude } : null}
            onChange={(loc) => setForm(p => ({ ...p, latitude: loc.lat, longitude: loc.lng }))}
            height={220}
          />
          <div className="flex justify-end">
            <Button type="submit" disabled={isPending}>Guardar dirección</Button>
          </div>
        </form>

        <ConfirmDialog
          open={confirmDeleteId !== null}
          onClose={() => setConfirmDeleteId(null)}
          onConfirm={() => { if (confirmDeleteId) deleteMut.mutate(confirmDeleteId); }}
          title="Eliminar dirección"
          description="¿Seguro que deseas eliminar esta dirección?"
        />
      </div>
    </Dialog>
  );
}

function SupplierContactsDialog({ open, supplier, onClose, onError }: SectionProps) {
  const queryClient = useQueryClient();
  const [form, setForm] = useState(EMPTY_CONTACT);
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);

  function invalidate() {
    queryClient.invalidateQueries({ queryKey: ["compras", "suppliers"] });
  }

  const saveMut = useMutation({
    mutationFn: (e: FormEvent) => {
      e.preventDefault();
      const payload = { full_name: form.full_name || null, role: form.role || null, phone: form.phone || null, email: form.email || null };
      return addSupplierContact(supplier.id, payload);
    },
    onSuccess: () => { invalidate(); setEditingId(null); setForm(EMPTY_CONTACT); },
    onError: (err) => onError(err instanceof Error ? err.message : "Error al guardar contacto"),
  });
  const deleteMut = useMutation({
    mutationFn: (contactId: string) => removeSupplierContact(supplier.id, contactId),
    onSuccess: () => { invalidate(); setConfirmDeleteId(null); },
  });

  return (
    <Dialog open={open} title="Contactos" description={`Contactos de ${supplier.name}.`} onClose={onClose} maxWidthClassName="max-w-3xl">
      <div className="space-y-4">
        <DataTable
          dense
          columns={[
            { key: "name", header: "Nombre", render: (row: Supplier["contacts"][number]) => row.full_name ?? "-" },
            { key: "role", header: "Cargo", render: (row: Supplier["contacts"][number]) => row.role ?? "-" },
            { key: "phone", header: "Teléfono", render: (row: Supplier["contacts"][number]) => row.phone ?? "-" },
            { key: "email", header: "Email", render: (row: Supplier["contacts"][number]) => row.email ?? "-" },
            {
              key: "actions",
              header: "",
              render: (row: Supplier["contacts"][number]) => (
                <Button variant="secondary" className="h-7 w-7 px-0 py-0" aria-label="Eliminar contacto" onClick={(event) => { event.stopPropagation(); setConfirmDeleteId(row.id); }}>x</Button>
              ),
            },
          ]}
          rows={supplier.contacts}
          rowKey={(row) => row.id}
          emptyMessage="No hay contactos registrados."
        />
        <Button variant="secondary" onClick={() => { setEditingId(null); setForm(EMPTY_CONTACT); }}>
          Agregar contacto
        </Button>

        <form className="space-y-3 rounded-md border border-dashed border-border p-3" onSubmit={saveMut.mutate}>
          <p className="text-sm font-medium text-foreground">Nuevo contacto</p>
          <div className="grid gap-3 md:grid-cols-2">
            <Input value={form.full_name} onChange={(e) => setForm(p => ({ ...p, full_name: e.target.value }))} placeholder="Nombre completo" />
            <Input value={form.role} onChange={(e) => setForm(p => ({ ...p, role: e.target.value }))} placeholder="Cargo" />
            <Input value={form.phone} onChange={(e) => setForm(p => ({ ...p, phone: e.target.value }))} placeholder="Teléfono" />
            <Input value={form.email} onChange={(e) => setForm(p => ({ ...p, email: e.target.value }))} placeholder="Email" />
          </div>
          <div className="flex justify-end">
            <Button type="submit" disabled={saveMut.isPending}>Guardar contacto</Button>
          </div>
        </form>

        <ConfirmDialog
          open={confirmDeleteId !== null}
          onClose={() => setConfirmDeleteId(null)}
          onConfirm={() => { if (confirmDeleteId) deleteMut.mutate(confirmDeleteId); }}
          title="Eliminar contacto"
          description="¿Seguro que deseas eliminar este contacto?"
        />
      </div>
    </Dialog>
  );
}

function SupplierBanksDialog({ open, supplier, onClose, onError }: SectionProps) {
  const queryClient = useQueryClient();
  const [form, setForm] = useState(EMPTY_BANK);
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);

  function invalidate() {
    queryClient.invalidateQueries({ queryKey: ["compras", "suppliers"] });
  }

  const saveMut = useMutation({
    mutationFn: (e: FormEvent) => {
      e.preventDefault();
      const payload = { bank_name: form.bank_name, account_holder: form.account_holder, iban: form.iban, bic_swift: form.bic_swift || null };
      return addSupplierBankAccount(supplier.id, payload);
    },
    onSuccess: () => { invalidate(); setEditingId(null); setForm(EMPTY_BANK); },
    onError: (err) => onError(err instanceof Error ? err.message : "Error al guardar cuenta"),
  });
  const deleteMut = useMutation({
    mutationFn: (accountId: string) => removeSupplierBankAccount(supplier.id, accountId),
    onSuccess: () => { invalidate(); setConfirmDeleteId(null); },
  });

  return (
    <Dialog open={open} title="Cuentas bancarias" description={`Cuentas de ${supplier.name}.`} onClose={onClose} maxWidthClassName="max-w-3xl">
      <div className="space-y-4">
        <DataTable
          dense
          columns={[
            { key: "bank_name", header: "Banco", render: (row: Supplier["bank_accounts"][number]) => row.bank_name },
            { key: "holder", header: "Titular", render: (row: Supplier["bank_accounts"][number]) => row.account_holder },
            { key: "iban", header: "IBAN", render: (row: Supplier["bank_accounts"][number]) => row.iban },
            { key: "bic", header: "BIC/SWIFT", render: (row: Supplier["bank_accounts"][number]) => row.bic_swift ?? "-" },
            {
              key: "actions",
              header: "",
              render: (row: Supplier["bank_accounts"][number]) => (
                <Button variant="secondary" className="h-7 w-7 px-0 py-0" aria-label="Eliminar cuenta" onClick={(event) => { event.stopPropagation(); setConfirmDeleteId(row.id); }}>x</Button>
              ),
            },
          ]}
          rows={supplier.bank_accounts}
          rowKey={(row) => row.id}
          emptyMessage="No hay cuentas registradas."
        />
        <Button variant="secondary" onClick={() => { setEditingId(null); setForm(EMPTY_BANK); }}>
          Agregar cuenta
        </Button>

        <form className="space-y-3 rounded-md border border-dashed border-border p-3" onSubmit={saveMut.mutate}>
          <p className="text-sm font-medium text-foreground">Nueva cuenta</p>
          <div className="grid gap-3 md:grid-cols-2">
            <Input value={form.bank_name} onChange={(e) => setForm(p => ({ ...p, bank_name: e.target.value }))} placeholder="Banco" required />
            <Input value={form.account_holder} onChange={(e) => setForm(p => ({ ...p, account_holder: e.target.value }))} placeholder="Titular" required />
            <Input value={form.iban} onChange={(e) => setForm(p => ({ ...p, iban: e.target.value }))} placeholder="IBAN" required />
            <Input value={form.bic_swift} onChange={(e) => setForm(p => ({ ...p, bic_swift: e.target.value }))} placeholder="BIC/SWIFT" />
          </div>
          <div className="flex justify-end">
            <Button type="submit" disabled={saveMut.isPending}>Guardar cuenta</Button>
          </div>
        </form>

        <ConfirmDialog
          open={confirmDeleteId !== null}
          onClose={() => setConfirmDeleteId(null)}
          onConfirm={() => { if (confirmDeleteId) deleteMut.mutate(confirmDeleteId); }}
          title="Eliminar cuenta bancaria"
          description="¿Seguro que deseas eliminar esta cuenta bancaria?"
        />
      </div>
    </Dialog>
  );
}
