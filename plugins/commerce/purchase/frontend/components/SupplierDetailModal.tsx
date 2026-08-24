import { useMutation, useQueryClient } from "../../../../../apps/web/src/lib/react-query";
import { useState } from "react";
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

export function SupplierDetailModal({ open, supplier, onClose, onEdit }: Props) {
  const queryClient = useQueryClient();
  const [error, setError] = useState<string | null>(null);

  const [addrForm, setAddrForm] = useState({
    line1: "", label: "", district: "", city: "",
    latitude: null as number | null, longitude: null as number | null,
  });
  const [showAddrForm, setShowAddrForm] = useState(false);
  const [contactForm, setContactForm] = useState({ full_name: "", role: "", phone: "", email: "" });
  const [showContactForm, setShowContactForm] = useState(false);
  const [bankForm, setBankForm] = useState({ bank_name: "", account_holder: "", iban: "", bic_swift: "" });
  const [showBankForm, setShowBankForm] = useState(false);

  // Al invalidarse la lista tras cada mutación, el padre re-renderiza con el
  // Supplier actualizado y el detalle se refresca solo.
  const detail = supplier;

  const addAddrMut = useMutation({
    mutationFn: () => addSupplierAddress(detail!.id, { line1: addrForm.line1, label: addrForm.label || null, district: addrForm.district || null, city: addrForm.city || null, latitude: addrForm.latitude, longitude: addrForm.longitude }),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["compras", "suppliers"] }); setShowAddrForm(false); setAddrForm({ line1: "", label: "", district: "", city: "", latitude: null, longitude: null }); },
    onError: (err) => setError(err instanceof Error ? err.message : "Error al agregar dirección"),
  });
  const removeAddrMut = useMutation({
    mutationFn: (addressId: string) => removeSupplierAddress(detail!.id, addressId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["compras", "suppliers"] }),
  });
  const addContactMut = useMutation({
    mutationFn: () => addSupplierContact(detail!.id, { full_name: contactForm.full_name || null, role: contactForm.role || null, phone: contactForm.phone || null, email: contactForm.email || null }),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["compras", "suppliers"] }); setShowContactForm(false); setContactForm({ full_name: "", role: "", phone: "", email: "" }); },
    onError: (err) => setError(err instanceof Error ? err.message : "Error al agregar contacto"),
  });
  const removeContactMut = useMutation({
    mutationFn: (contactId: string) => removeSupplierContact(detail!.id, contactId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["compras", "suppliers"] }),
  });
  const addBankMut = useMutation({
    mutationFn: () => addSupplierBankAccount(detail!.id, { bank_name: bankForm.bank_name, account_holder: bankForm.account_holder, iban: bankForm.iban, bic_swift: bankForm.bic_swift || null }),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["compras", "suppliers"] }); setShowBankForm(false); setBankForm({ bank_name: "", account_holder: "", iban: "", bic_swift: "" }); },
    onError: (err) => setError(err instanceof Error ? err.message : "Error al agregar cuenta"),
  });
  const removeBankMut = useMutation({
    mutationFn: (accountId: string) => removeSupplierBankAccount(detail!.id, accountId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["compras", "suppliers"] }),
  });
  const disableMut = useMutation({
    mutationFn: () => disableSupplier(detail!.id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["compras", "suppliers"] }),
  });

  return (
    <Dialog
      open={open}
      title="Detalle del proveedor"
      description="Datos fiscales, direcciones, contactos, cuentas bancarias y envases en custodia."
      onClose={onClose}
      maxWidthClassName="max-w-4xl"
    >
      {!detail ? (
        <p className="py-6 text-center text-sm text-muted-foreground">Proveedor no encontrado.</p>
      ) : (
        <div className="grid gap-4 lg:grid-cols-[1fr_260px]">
          <div className="space-y-4">
            <SupplierOverviewCard supplier={detail} />

            {error ? <Alert title="Error">{error}</Alert> : null}

            <Card>
              <CardHeader className="flex-row items-center justify-between">
                <div>
                  <CardTitle>Direcciones</CardTitle>
                  <CardDescription>{detail.addresses.length} registradas</CardDescription>
                </div>
                <Button variant="secondary" size="sm" onClick={() => setShowAddrForm(p => !p)}>Agregar</Button>
              </CardHeader>
              <CardContent className="space-y-2">
                {detail.addresses.map((a) => (
                  <div key={a.id} className="flex items-start justify-between gap-3 rounded-md border border-border px-3 py-2 text-sm">
                    <div className="min-w-0">
                      <p className="font-medium text-foreground">{a.label ?? "Dirección"} · {a.line1}</p>
                      <p className="text-xs text-muted-foreground">{[a.district, a.city].filter(Boolean).join(", ") || "-"}</p>
                    </div>
                    <Button variant="secondary" size="sm" onClick={() => removeAddrMut.mutate(a.id)}>Quitar</Button>
                  </div>
                ))}
                {detail.addresses.length === 0 && !showAddrForm ? (
                  <p className="text-sm text-muted-foreground">Sin direcciones registradas.</p>
                ) : null}
                {showAddrForm ? (
                  <div className="space-y-3 rounded-md border border-dashed border-border p-3">
                    <div className="grid gap-3 md:grid-cols-2">
                      <Input value={addrForm.label} onChange={(e) => setAddrForm(p => ({ ...p, label: e.target.value }))} placeholder="Tipo (Principal)" />
                      <Input value={addrForm.line1} onChange={(e) => setAddrForm(p => ({ ...p, line1: e.target.value }))} placeholder="Av. Principal 123" />
                      <Input value={addrForm.district} onChange={(e) => setAddrForm(p => ({ ...p, district: e.target.value }))} placeholder="Distrito" />
                      <Input value={addrForm.city} onChange={(e) => setAddrForm(p => ({ ...p, city: e.target.value }))} placeholder="Ciudad" />
                    </div>
                    <LocationPicker
                      value={addrForm.latitude != null && addrForm.longitude != null ? { lat: addrForm.latitude, lng: addrForm.longitude } : null}
                      onChange={(loc) => setAddrForm(p => ({ ...p, latitude: loc.lat, longitude: loc.lng }))}
                      height={220}
                    />
                    <div className="flex justify-end gap-2">
                      <Button variant="secondary" size="sm" onClick={() => setShowAddrForm(false)}>Cancelar</Button>
                      <Button size="sm" disabled={!addrForm.line1.trim() || addAddrMut.isPending} onClick={() => addAddrMut.mutate()}>Guardar dirección</Button>
                    </div>
                  </div>
                ) : null}
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex-row items-center justify-between">
                <div>
                  <CardTitle>Contactos</CardTitle>
                  <CardDescription>{detail.contacts.length} registrados</CardDescription>
                </div>
                <Button variant="secondary" size="sm" onClick={() => setShowContactForm(p => !p)}>Agregar</Button>
              </CardHeader>
              <CardContent className="space-y-2">
                {detail.contacts.map((c) => (
                  <div key={c.id} className="flex items-start justify-between gap-3 rounded-md border border-border px-3 py-2 text-sm">
                    <div className="min-w-0">
                      <p className="font-medium text-foreground">{c.full_name}{c.role ? ` · ${c.role}` : ""}</p>
                      <p className="text-xs text-muted-foreground">{[c.phone, c.email].filter(Boolean).join(" · ") || "-"}</p>
                    </div>
                    <Button variant="secondary" size="sm" onClick={() => removeContactMut.mutate(c.id)}>Quitar</Button>
                  </div>
                ))}
                {detail.contacts.length === 0 && !showContactForm ? (
                  <p className="text-sm text-muted-foreground">Sin contactos registrados.</p>
                ) : null}
                {showContactForm ? (
                  <div className="space-y-3 rounded-md border border-dashed border-border p-3">
                    <div className="grid gap-3 md:grid-cols-2">
                      <Input value={contactForm.full_name} onChange={(e) => setContactForm(p => ({ ...p, full_name: e.target.value }))} placeholder="Nombre completo" />
                      <Input value={contactForm.role} onChange={(e) => setContactForm(p => ({ ...p, role: e.target.value }))} placeholder="Cargo" />
                      <Input value={contactForm.phone} onChange={(e) => setContactForm(p => ({ ...p, phone: e.target.value }))} placeholder="Teléfono" />
                      <Input value={contactForm.email} onChange={(e) => setContactForm(p => ({ ...p, email: e.target.value }))} placeholder="Email" />
                    </div>
                    <div className="flex justify-end gap-2">
                      <Button variant="secondary" size="sm" onClick={() => setShowContactForm(false)}>Cancelar</Button>
                      <Button size="sm" disabled={!contactForm.full_name.trim() || addContactMut.isPending} onClick={() => addContactMut.mutate()}>Guardar contacto</Button>
                    </div>
                  </div>
                ) : null}
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex-row items-center justify-between">
                <div>
                  <CardTitle>Cuentas bancarias</CardTitle>
                  <CardDescription>{detail.bank_accounts.length} registradas</CardDescription>
                </div>
                <Button variant="secondary" size="sm" onClick={() => setShowBankForm(p => !p)}>Agregar</Button>
              </CardHeader>
              <CardContent className="space-y-2">
                {detail.bank_accounts.map((b) => (
                  <div key={b.id} className="flex items-start justify-between gap-3 rounded-md border border-border px-3 py-2 text-sm">
                    <div className="min-w-0">
                      <p className="font-medium text-foreground">{b.bank_name} · {b.account_holder}</p>
                      <p className="text-xs text-muted-foreground">{[b.iban, b.bic_swift].filter(Boolean).join(" · ") || "-"}</p>
                    </div>
                    <Button variant="secondary" size="sm" onClick={() => removeBankMut.mutate(b.id)}>Quitar</Button>
                  </div>
                ))}
                {detail.bank_accounts.length === 0 && !showBankForm ? (
                  <p className="text-sm text-muted-foreground">Sin cuentas registradas.</p>
                ) : null}
                {showBankForm ? (
                  <div className="space-y-3 rounded-md border border-dashed border-border p-3">
                    <div className="grid gap-3 md:grid-cols-2">
                      <Input value={bankForm.bank_name} onChange={(e) => setBankForm(p => ({ ...p, bank_name: e.target.value }))} placeholder="Banco" />
                      <Input value={bankForm.account_holder} onChange={(e) => setBankForm(p => ({ ...p, account_holder: e.target.value }))} placeholder="Titular" />
                      <Input value={bankForm.iban} onChange={(e) => setBankForm(p => ({ ...p, iban: e.target.value }))} placeholder="IBAN" />
                      <Input value={bankForm.bic_swift} onChange={(e) => setBankForm(p => ({ ...p, bic_swift: e.target.value }))} placeholder="BIC/SWIFT" />
                    </div>
                    <div className="flex justify-end gap-2">
                      <Button variant="secondary" size="sm" onClick={() => setShowBankForm(false)}>Cancelar</Button>
                      <Button size="sm" disabled={!bankForm.bank_name.trim() || !bankForm.account_holder.trim() || addBankMut.isPending} onClick={() => addBankMut.mutate()}>Guardar cuenta</Button>
                    </div>
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

          <Card className="h-fit">
            <CardHeader>
              <CardTitle>Acciones</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <Button variant="secondary" className="w-full" onClick={() => onEdit(detail.id)}>Editar proveedor</Button>
              {detail.is_active ? (
                <Button
                  variant="secondary"
                  className="w-full"
                  disabled={disableMut.isPending}
                  onClick={() => disableMut.mutate()}
                >
                  Desactivar proveedor
                </Button>
              ) : null}
            </CardContent>
          </Card>
        </div>
      )}
    </Dialog>
  );
}
