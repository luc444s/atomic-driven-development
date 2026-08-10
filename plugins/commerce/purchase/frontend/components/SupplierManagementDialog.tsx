import { useMutation, useQuery, useQueryClient } from "../../../../../apps/web/src/lib/react-query";
import { FormEvent, useState } from "react";
import {
  addSupplierAddress,
  addSupplierBankAccount,
  addSupplierContact,
  createSupplier,
  disableSupplier,
  listSuppliers,
  removeSupplierAddress,
  removeSupplierBankAccount,
  removeSupplierContact,
  updateSupplier,
} from "../api";
import type { Supplier } from "../types";
import { EMPTY_SUPPLIER_FORM, type SupplierFormState } from "../forms/purchase-form-state";
import { Button } from "../../../../../apps/web/src/shared/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../../../../apps/web/src/shared/ui/card";
import { DataTable } from "../../../../../apps/web/src/shared/ui/data-table";
import { Dialog } from "../../../../../apps/web/src/shared/ui/dialog";
import { Input } from "../../../../../apps/web/src/shared/ui/input";
import { Combobox } from "../../../../../apps/web/src/shared/ui/combobox";
import { Select } from "../../../../../apps/web/src/shared/ui/select";
import { Alert } from "../../../../../apps/web/src/shared/ui/alert";
import { LocationPicker } from "../../../../../apps/web/src/shared/ui/location-picker";
import { apiRequest } from "../../../../../apps/web/src/shared/api/client";

const CRM_BASE = "/api/v1/plugins/crm";

function buildQuery(params: Record<string, unknown>) {
  const q = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v === undefined || v === null || v === "") continue;
    q.set(k, String(v));
  }
  const qs = q.toString();
  return qs ? `?${qs}` : "";
}

function validateDocument(type: string, number: string): string | null {
  if (!number.trim()) return null;
  const n = number.trim().toUpperCase();
  if (type === "NIF") {
    if (!/^\d{8}[A-Z]$/.test(n)) return "NIF inválido: 8 dígitos + letra";
    const letters = "TRWAGMYFPDXBNJZSQVHLCKE";
    if (n[8] !== letters[parseInt(n.slice(0, 8)) % 23]) return "Letra de control del NIF incorrecta";
  }
  if (type === "NIE") {
    if (!/^[XYZ]\d{7}[A-Z]$/.test(n)) return "NIE inválido: X/Y/Z + 7 dígitos + letra";
    const letters = "TRWAGMYFPDXBNJZSQVHLCKE";
    const prefix = { X: "0", Y: "1", Z: "2" }[n[0] as "X" | "Y" | "Z"];
    if (n[7] !== letters[parseInt(prefix + n.slice(1, 8)) % 23]) return "Letra de control del NIE incorrecta";
  }
  if (type === "CIF") {
    if (!/^[A-HJ-NP-SUVW]\d{7}[A-J0-9]?$/i.test(n)) return "CIF inválido: letra + 7 dígitos + control";
  }
  if (type === "DNI") {
    if (!/^\d{8}$/.test(n)) return "DNI inválido: 8 dígitos";
  }
  if (type === "RUC") {
    if (!/^\d{11}$/.test(n)) return "RUC inválido: 11 dígitos";
  }
  if (type === "CE") {
    if (!/^\d{9,12}$/.test(n)) return "CE inválido";
  }
  return null;
}

function listCountries() { return apiRequest<Array<{ code: string; name: string; country_code: string }>>(`${CRM_BASE}/geography/countries`); }
function listDocumentTypes(countryCode?: string | null) { return apiRequest<Array<{ code: string; name: string }>>(`${CRM_BASE}/catalog/document-types${buildQuery({ country_code: countryCode ?? null })}`); }

type Props = { open: boolean; onClose: () => void };

export function SupplierManagementDialog({ open, onClose }: Props) {
  const queryClient = useQueryClient();
  const [error, setError] = useState<string | null>(null);
  const [docError, setDocError] = useState<string | null>(null);
  const [form, setForm] = useState<SupplierFormState>(EMPTY_SUPPLIER_FORM);

  const [addrForm, setAddrForm] = useState({
    line1: "", label: "", district: "", city: "",
    latitude: null as number | null, longitude: null as number | null,
  });
  const [addrSupplier, setAddrSupplier] = useState<string | null>(null);

  const [contactForm, setContactForm] = useState({ full_name: "", role: "", phone: "", email: "" });
  const [contactSupplier, setContactSupplier] = useState<string | null>(null);

  const [bankForm, setBankForm] = useState({ bank_name: "", account_holder: "", iban: "", bic_swift: "" });
  const [bankSupplier, setBankSupplier] = useState<string | null>(null);

  const suppliersQuery = useQuery({
    queryKey: ["compras", "suppliers"],
    queryFn: () => listSuppliers(),
  });

  const countriesQuery = useQuery({
    queryKey: ["crm", "geography", "countries"],
    queryFn: () => listCountries(),
  });

  const docTypesQuery = useQuery({
    queryKey: ["crm", "catalog", "document-types", form.country_code],
    queryFn: () => listDocumentTypes(form.country_code || null),
    enabled: Boolean(form.country_code),
  });

  const createMut = useMutation({
    mutationFn: () => createSupplier({
      name: form.name, commercial_name: form.commercial_name || null,
      document_type_code: form.document_type_code || null, document_number: form.document_number || null,
      country_code: form.country_code || null, email: form.email || null,
      phone: form.phone || null, mobile: form.mobile || null,
      payment_term_code: form.payment_term_code || null, billing_type: form.billing_type || null,
      accounting_code: form.accounting_code || null, fiscal_operation_key: form.fiscal_operation_key || null,
      tax_regime_code: form.tax_regime_code || null, notes: form.notes || null,
    }),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["compras", "suppliers"] }); setForm(EMPTY_SUPPLIER_FORM); setError(null); },
    onError: (err) => setError(err instanceof Error ? err.message : "Error al crear proveedor"),
  });

  const updateMut = useMutation({
    mutationFn: () => updateSupplier(form.id!, {
      name: form.name, commercial_name: form.commercial_name || null,
      document_type_code: form.document_type_code || null, document_number: form.document_number || null,
      country_code: form.country_code || null, email: form.email || null,
      phone: form.phone || null, mobile: form.mobile || null,
      payment_term_code: form.payment_term_code || null, billing_type: form.billing_type || null,
      accounting_code: form.accounting_code || null, fiscal_operation_key: form.fiscal_operation_key || null,
      tax_regime_code: form.tax_regime_code || null, notes: form.notes || null,
    }),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["compras", "suppliers"] }); setForm(EMPTY_SUPPLIER_FORM); setError(null); },
    onError: (err) => setError(err instanceof Error ? err.message : "Error al actualizar"),
  });

  const disableMut = useMutation({
    mutationFn: (id: string) => disableSupplier(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["compras", "suppliers"] }),
  });

  const addAddrMut = useMutation({
    mutationFn: () => addSupplierAddress(addrSupplier!, { line1: addrForm.line1, label: addrForm.label || null, district: addrForm.district || null, city: addrForm.city || null, latitude: addrForm.latitude, longitude: addrForm.longitude }),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["compras", "suppliers"] }); setAddrSupplier(null); },
  });

  const removeAddrMut = useMutation({
    mutationFn: (p: { supplierId: string; addressId: string }) => removeSupplierAddress(p.supplierId, p.addressId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["compras", "suppliers"] }),
  });

  const addContactMut = useMutation({
    mutationFn: () => addSupplierContact(contactSupplier!, { full_name: contactForm.full_name || null, role: contactForm.role || null, phone: contactForm.phone || null, email: contactForm.email || null }),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["compras", "suppliers"] }); setContactSupplier(null); },
  });

  const removeContactMut = useMutation({
    mutationFn: (p: { supplierId: string; contactId: string }) => removeSupplierContact(p.supplierId, p.contactId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["compras", "suppliers"] }),
  });

  const addBankMut = useMutation({
    mutationFn: () => addSupplierBankAccount(bankSupplier!, { bank_name: bankForm.bank_name, account_holder: bankForm.account_holder, iban: bankForm.iban, bic_swift: bankForm.bic_swift || null }),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["compras", "suppliers"] }); setBankSupplier(null); },
  });

  const removeBankMut = useMutation({
    mutationFn: (p: { supplierId: string; accountId: string }) => removeSupplierBankAccount(p.supplierId, p.accountId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["compras", "suppliers"] }),
  });

  function openEdit(s: Supplier) {
    setForm({
      id: s.id, name: s.name, commercial_name: s.commercial_name ?? "",
      document_type_code: s.document_type_code ?? "", document_number: s.document_number ?? "",
      country_code: s.country_code ?? "PE", email: s.email ?? "",
      phone: s.phone ?? "", mobile: s.mobile ?? "",
      payment_term_code: s.payment_term_code ?? "", billing_type: s.billing_type ?? "",
      accounting_code: s.accounting_code ?? "", fiscal_operation_key: s.fiscal_operation_key ?? "",
      tax_regime_code: s.tax_regime_code ?? "", notes: s.notes ?? "",
    });
  }

  const countryOptions = (countriesQuery.data ?? []).map(c => ({ value: c.country_code, label: c.name }));
  const docTypeOptions = (docTypesQuery.data ?? []).map(dt => ({ value: dt.code, label: dt.name }));

  return (
    <Dialog open={open} title="Proveedores" description="Gestión completa de proveedores con datos fiscales, direcciones, contactos y cuentas bancarias."
      onClose={() => { onClose(); setForm(EMPTY_SUPPLIER_FORM); setError(null); }}
      maxWidthClassName="max-w-5xl"
    >
      <div className="space-y-6">
        {error ? <Alert title="Error">{error}</Alert> : null}

        <Card>
          <CardHeader>
            <CardTitle>{form.id ? "Editar proveedor" : "Nuevo proveedor"}</CardTitle>
            <CardDescription>Formulario base del proveedor. Las direcciones se completan en el segundo bloque.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <form className="space-y-6" onSubmit={(e: FormEvent) => { e.preventDefault(); form.id ? updateMut.mutate() : createMut.mutate(); }}>
              <div className="space-y-4">
                <p className="text-sm font-medium text-foreground">Identificación fiscal y datos comerciales</p>
                <div className="grid gap-4 md:grid-cols-3">
                  <label className="block space-y-2 text-sm text-foreground">
                    <span>País</span>
                    <Combobox value={form.country_code} onChange={(v) => {
                      setForm(p => ({ ...p, country_code: v, document_type_code: "" }));
                      setDocError(null);
                    }} options={countryOptions} placeholder="Seleccionar país" searchPlaceholder="Buscar país" />
                  </label>
                  <label className="block space-y-2 text-sm text-foreground">
                    <span>Tipo documento</span>
                    <Combobox value={form.document_type_code} onChange={(v) => {
                      setForm(p => ({ ...p, document_type_code: v }));
                      setDocError(validateDocument(v, form.document_number));
                    }} options={docTypeOptions} placeholder="Seleccionar tipo" searchPlaceholder="Buscar tipo" />
                  </label>
                  <label className="block space-y-2 text-sm text-foreground">
                    <span>Número documento</span>
                    <Input
                      value={form.document_number}
                      onChange={(e) => {
                        const num = e.target.value;
                        setForm(p => ({ ...p, document_number: num }));
                        setDocError(validateDocument(form.document_type_code, num));
                      }}
                    />
                    {docError ? <p className="text-xs text-red-600">{docError}</p> : null}
                  </label>
                </div>
              </div>

              <div className="space-y-4">
                <p className="text-sm font-medium text-foreground">Datos fiscales</p>
                <div className="grid gap-4 md:grid-cols-3">
                  <label className="block space-y-2 text-sm text-foreground"><span>Código contable</span><Input value={form.accounting_code} onChange={(e) => setForm(p => ({ ...p, accounting_code: e.target.value }))} placeholder="Ej. 43000001" /></label>
                  <label className="block space-y-2 text-sm text-foreground"><span>Clave operación fiscal</span><Input value={form.fiscal_operation_key} onChange={(e) => setForm(p => ({ ...p, fiscal_operation_key: e.target.value }))} placeholder="Ej. S1" /></label>
                  <label className="block space-y-2 text-sm text-foreground"><span>Régimen fiscal</span><Input value={form.tax_regime_code} onChange={(e) => setForm(p => ({ ...p, tax_regime_code: e.target.value }))} placeholder="Ej. 612" /></label>
                </div>
                <div className="grid gap-4 md:grid-cols-2">
                  <label className="block space-y-2 text-sm text-foreground"><span>Razón social / nombre</span><Input value={form.name} onChange={(e) => setForm(p => ({ ...p, name: e.target.value }))} required /></label>
                  <label className="block space-y-2 text-sm text-foreground"><span>Nombre comercial</span><Input value={form.commercial_name} onChange={(e) => setForm(p => ({ ...p, commercial_name: e.target.value }))} /></label>
                  <label className="block space-y-2 text-sm text-foreground"><span>Email</span><Input value={form.email} onChange={(e) => setForm(p => ({ ...p, email: e.target.value }))} /></label>
                  <label className="block space-y-2 text-sm text-foreground"><span>Teléfono</span><Input value={form.phone} onChange={(e) => setForm(p => ({ ...p, phone: e.target.value }))} /></label>
                </div>
                <div className="grid gap-4 md:grid-cols-2">
                  <label className="block space-y-2 text-sm text-foreground"><span>Celular</span><Input value={form.mobile} onChange={(e) => setForm(p => ({ ...p, mobile: e.target.value }))} /></label>
                </div>
              </div>

              <div className="space-y-4">
                <p className="text-sm font-medium text-foreground">Condiciones comerciales</p>
                <div className="grid gap-4 md:grid-cols-2">
                  <label className="block space-y-2 text-sm text-foreground">
                    <span>Forma de pago</span>
                    <Select value={form.payment_term_code} onChange={(v) => setForm(p => ({ ...p, payment_term_code: v }))}
                      options={[
                        { value: "", label: "Sin definir" },
                        { value: "CONTADO", label: "Contado" },
                        { value: "CREDITO_15", label: "Crédito 15 días" },
                        { value: "CREDITO_30", label: "Crédito 30 días" },
                        { value: "CREDITO_60", label: "Crédito 60 días" },
                        { value: "TRANSFERENCIA", label: "Transferencia" },
                      ]} placeholder="Seleccionar forma de pago" />
                  </label>
                  <label className="block space-y-2 text-sm text-foreground">
                    <span>Tipo de facturación</span>
                    <Select value={form.billing_type} onChange={(v) => setForm(p => ({ ...p, billing_type: v }))}
                      options={[
                        { value: "", label: "Sin definir" },
                        { value: "por_operacion", label: "Por operación" },
                        { value: "mensual", label: "Mensual" },
                        { value: "quincenal", label: "Quincenal" },
                      ]} placeholder="Seleccionar tipo" />
                  </label>
                </div>
              </div>

              <div className="flex justify-end gap-3">
                {form.id ? <Button type="button" variant="secondary" onClick={() => setForm(EMPTY_SUPPLIER_FORM)}>Cancelar edición</Button> : null}
                <Button type="submit" disabled={createMut.isPending || updateMut.isPending}>
                  {form.id ? "Actualizar" : "Guardar proveedor"}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>

        {addrSupplier ? (
          <Card>
            <CardHeader><CardTitle>Agregar dirección</CardTitle></CardHeader>
            <CardContent className="space-y-3">
              <div className="grid gap-4 md:grid-cols-2">
                <label className="block space-y-2 text-sm text-foreground"><span>Tipo de dirección</span><Input value={addrForm.label} onChange={(e) => setAddrForm(p => ({ ...p, label: e.target.value }))} placeholder="Principal" /></label>
                <label className="block space-y-2 text-sm text-foreground"><span>Dirección</span><Input value={addrForm.line1} onChange={(e) => setAddrForm(p => ({ ...p, line1: e.target.value }))} placeholder="Av. Principal 123" /></label>
              </div>
              <div className="grid gap-4 md:grid-cols-2">
                <label className="block space-y-2 text-sm text-foreground"><span>Distrito / Ciudad</span><Input value={addrForm.district} onChange={(e) => setAddrForm(p => ({ ...p, district: e.target.value }))} placeholder="Miraflores" /></label>
                <label className="block space-y-2 text-sm text-foreground"><span>Contacto</span><Input value={addrForm.city} onChange={(e) => setAddrForm(p => ({ ...p, city: e.target.value }))} placeholder="Lima" /></label>
              </div>
              <label className="block space-y-2 text-sm text-foreground">
                <span>Coordenadas GPS</span>
                <LocationPicker
                  value={addrForm.latitude != null && addrForm.longitude != null ? { lat: addrForm.latitude, lng: addrForm.longitude } : null}
                  onChange={(loc) => setAddrForm(p => ({ ...p, latitude: loc.lat, longitude: loc.lng }))}
                  height={250}
                />
              </label>
              <div className="flex justify-end gap-3">
                <Button variant="secondary" onClick={() => setAddrSupplier(null)}>Cancelar</Button>
                <Button onClick={() => addAddrMut.mutate()}>Guardar dirección</Button>
              </div>
            </CardContent>
          </Card>
        ) : null}

        {contactSupplier ? (
          <Card>
            <CardHeader><CardTitle>Agregar contacto</CardTitle></CardHeader>
            <CardContent className="space-y-3">
              <div className="grid gap-4 md:grid-cols-2">
                <Input value={contactForm.full_name} onChange={(e) => setContactForm(p => ({ ...p, full_name: e.target.value }))} placeholder="Nombre completo" />
                <Input value={contactForm.role} onChange={(e) => setContactForm(p => ({ ...p, role: e.target.value }))} placeholder="Cargo" />
                <Input value={contactForm.phone} onChange={(e) => setContactForm(p => ({ ...p, phone: e.target.value }))} placeholder="Teléfono" />
                <Input value={contactForm.email} onChange={(e) => setContactForm(p => ({ ...p, email: e.target.value }))} placeholder="Email" />
              </div>
              <div className="flex justify-end gap-3">
                <Button variant="secondary" onClick={() => setContactSupplier(null)}>Cancelar</Button>
                <Button onClick={() => addContactMut.mutate()}>Guardar contacto</Button>
              </div>
            </CardContent>
          </Card>
        ) : null}

        {bankSupplier ? (
          <Card>
            <CardHeader><CardTitle>Agregar cuenta bancaria</CardTitle></CardHeader>
            <CardContent className="space-y-3">
              <div className="grid gap-4 md:grid-cols-2">
                <Input value={bankForm.bank_name} onChange={(e) => setBankForm(p => ({ ...p, bank_name: e.target.value }))} placeholder="Nombre del banco" />
                <Input value={bankForm.account_holder} onChange={(e) => setBankForm(p => ({ ...p, account_holder: e.target.value }))} placeholder="Titular" />
                <Input value={bankForm.iban} onChange={(e) => setBankForm(p => ({ ...p, iban: e.target.value }))} placeholder="IBAN" />
                <Input value={bankForm.bic_swift} onChange={(e) => setBankForm(p => ({ ...p, bic_swift: e.target.value }))} placeholder="BIC/SWIFT" />
              </div>
              <div className="flex justify-end gap-3">
                <Button variant="secondary" onClick={() => setBankSupplier(null)}>Cancelar</Button>
                <Button onClick={() => addBankMut.mutate()}>Guardar cuenta</Button>
              </div>
            </CardContent>
          </Card>
        ) : null}

        <Card>
          <CardHeader>
            <CardTitle>Proveedores</CardTitle>
            <CardDescription>Lista de proveedores registrados.</CardDescription>
          </CardHeader>
          <CardContent>
            <DataTable
              columns={[
                { key: "name", header: "Nombre", render: (row: Supplier) => row.name },
                { key: "doc", header: "Documento", render: (row: Supplier) => row.document_number ? `${row.document_type_code ?? ""} ${row.document_number}` : "-" },
                { key: "email", header: "Email", render: (row: Supplier) => row.email ?? "-" },
                { key: "phone", header: "Teléfono", render: (row: Supplier) => row.phone ?? "-" },
                { key: "addresses", header: "Dir.", render: (row: Supplier) => <span className="text-xs">{row.addresses?.length ?? 0}</span> },
                { key: "contacts", header: "Cont.", render: (row: Supplier) => <span className="text-xs">{row.contacts?.length ?? 0}</span> },
                { key: "actions", header: "", render: (row: Supplier) => (
                  <div className="flex flex-wrap gap-1">
                    <Button variant="secondary" onClick={() => openEdit(row)}>Editar</Button>
                    <Button variant="secondary" onClick={() => { setAddrSupplier(row.id); setAddrForm({ line1: "", label: "", district: "", city: "", latitude: null, longitude: null }); }}>+Dir</Button>
                    <Button variant="secondary" onClick={() => { setContactSupplier(row.id); setContactForm({ full_name: "", role: "", phone: "", email: "" }); }}>+Contacto</Button>
                    <Button variant="secondary" onClick={() => { setBankSupplier(row.id); setBankForm({ bank_name: "", account_holder: "", iban: "", bic_swift: "" }); }}>+Banco</Button>
                    {row.is_active ? <Button variant="secondary" onClick={() => disableMut.mutate(row.id)}>Desactivar</Button> : null}
                    {row.addresses?.map((a) => <Button key={a.id} variant="secondary" onClick={() => removeAddrMut.mutate({ supplierId: row.id, addressId: a.id })}>✕D</Button>)}
                    {row.contacts?.map((c) => <Button key={c.id} variant="secondary" onClick={() => removeContactMut.mutate({ supplierId: row.id, contactId: c.id })}>✕C</Button>)}
                    {row.bank_accounts?.map((ba) => <Button key={ba.id} variant="secondary" onClick={() => removeBankMut.mutate({ supplierId: row.id, accountId: ba.id })}>✕B</Button>)}
                  </div>
                )},
              ]}
              rows={suppliersQuery.data ?? []}
              rowKey={(row: Supplier) => row.id}
              emptyMessage="No hay proveedores."
            />
          </CardContent>
        </Card>
      </div>
    </Dialog>
  );
}
