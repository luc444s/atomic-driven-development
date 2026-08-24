import { useMutation, useQuery, useQueryClient } from "../../../../../apps/web/src/lib/react-query";
import { FormEvent, useState } from "react";
import {
  createSupplier,
  updateSupplier,
} from "../api";
import type { Supplier } from "../types";
import { EMPTY_SUPPLIER_FORM, type SupplierFormState } from "../forms/purchase-form-state";
import { Button } from "@systutor/shell/ui/button";
import { Dialog } from "@systutor/shell/ui/dialog";
import { Input } from "@systutor/shell/ui/input";
import { Combobox } from "@systutor/shell/ui/combobox";
import { Select } from "@systutor/shell/ui/select";
import { Alert } from "@systutor/shell/ui/alert";
import { apiRequest } from "@systutor/shell/api/client";

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

export function validateDocument(type: string, number: string): string | null {
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

export function supplierToForm(s: Supplier): SupplierFormState {
  return {
    id: s.id, name: s.name, commercial_name: s.commercial_name ?? "",
    document_type_code: s.document_type_code ?? "", document_number: s.document_number ?? "",
    country_code: s.country_code ?? "PE", email: s.email ?? "",
    phone: s.phone ?? "", mobile: s.mobile ?? "",
    payment_term_code: s.payment_term_code ?? "", billing_type: s.billing_type ?? "",
    accounting_code: s.accounting_code ?? "", fiscal_operation_key: s.fiscal_operation_key ?? "",
    tax_regime_code: s.tax_regime_code ?? "", notes: s.notes ?? "",
  };
}

type Props = {
  open: boolean;
  /** Proveedor a editar; null = alta nueva. */
  supplier: Supplier | null;
  onClose: () => void;
};

export function SupplierFormModal({ open, supplier, onClose }: Props) {
  const queryClient = useQueryClient();
  const [error, setError] = useState<string | null>(null);
  const [docError, setDocError] = useState<string | null>(null);
  const [form, setForm] = useState<SupplierFormState>(
    supplier ? supplierToForm(supplier) : EMPTY_SUPPLIER_FORM,
  );

  // Re-sincroniza el formulario cuando cambia el proveedor objetivo.
  const [syncedFor, setSyncedFor] = useState<string | null>(supplier?.id ?? null);
  const targetKey = supplier?.id ?? "new";
  if (open && syncedFor !== targetKey) {
    setSyncedFor(targetKey);
    setForm(supplier ? supplierToForm(supplier) : EMPTY_SUPPLIER_FORM);
    setDocError(null);
    setError(null);
  }

  const countriesQuery = useQuery({
    queryKey: ["crm", "geography", "countries"],
    queryFn: () => listCountries(),
    enabled: open,
  });

  const docTypesQuery = useQuery({
    queryKey: ["crm", "catalog", "document-types", form.country_code],
    queryFn: () => listDocumentTypes(form.country_code || null),
    enabled: open && Boolean(form.country_code),
  });

  function payload() {
    return {
      name: form.name, commercial_name: form.commercial_name || null,
      document_type_code: form.document_type_code || null, document_number: form.document_number || null,
      country_code: form.country_code || null, email: form.email || null,
      phone: form.phone || null, mobile: form.mobile || null,
      payment_term_code: form.payment_term_code || null, billing_type: form.billing_type || null,
      accounting_code: form.accounting_code || null, fiscal_operation_key: form.fiscal_operation_key || null,
      tax_regime_code: form.tax_regime_code || null, notes: form.notes || null,
    };
  }

  const saveMut = useMutation({
    mutationFn: () => (form.id ? updateSupplier(form.id, payload()) : createSupplier(payload())),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["compras", "suppliers"] });
      onClose();
    },
    onError: (err) => setError(err instanceof Error ? err.message : "Error al guardar proveedor"),
  });

  const countryOptions = (countriesQuery.data ?? []).map(c => ({ value: c.country_code, label: c.name }));
  const docTypeOptions = (docTypesQuery.data ?? []).map(dt => ({ value: dt.code, label: dt.name }));

  return (
    <Dialog
      open={open}
      title={form.id ? "Editar proveedor" : "Nuevo proveedor"}
      description="Datos fiscales y condiciones comerciales. Direcciones, contactos y bancos se gestionan desde el detalle."
      onClose={onClose}
      maxWidthClassName="max-w-3xl"
    >
      <div className="space-y-4">
        {error ? <Alert title="Error">{error}</Alert> : null}
        <form className="space-y-6" onSubmit={(e: FormEvent) => { e.preventDefault(); saveMut.mutate(); }}>
          <div className="space-y-4">
            <p className="text-sm font-medium text-foreground">Identificación fiscal</p>
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
                {docError ? <p className="text-xs text-destructive">{docError}</p> : null}
              </label>
            </div>
          </div>

          <div className="space-y-4">
            <p className="text-sm font-medium text-foreground">Datos fiscales y comerciales</p>
            <div className="grid gap-4 md:grid-cols-3">
              <label className="block space-y-2 text-sm text-foreground"><span>Código contable</span><Input value={form.accounting_code} onChange={(e) => setForm(p => ({ ...p, accounting_code: e.target.value }))} placeholder="Ej. 43000001" /></label>
              <label className="block space-y-2 text-sm text-foreground"><span>Clave operación fiscal</span><Input value={form.fiscal_operation_key} onChange={(e) => setForm(p => ({ ...p, fiscal_operation_key: e.target.value }))} placeholder="Ej. S1" /></label>
              <label className="block space-y-2 text-sm text-foreground"><span>Régimen fiscal</span><Input value={form.tax_regime_code} onChange={(e) => setForm(p => ({ ...p, tax_regime_code: e.target.value }))} placeholder="Ej. 612" /></label>
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              <label className="block space-y-2 text-sm text-foreground"><span>Razón social / nombre *</span><Input value={form.name} onChange={(e) => setForm(p => ({ ...p, name: e.target.value }))} required /></label>
              <label className="block space-y-2 text-sm text-foreground"><span>Nombre comercial</span><Input value={form.commercial_name} onChange={(e) => setForm(p => ({ ...p, commercial_name: e.target.value }))} /></label>
              <label className="block space-y-2 text-sm text-foreground"><span>Email</span><Input value={form.email} onChange={(e) => setForm(p => ({ ...p, email: e.target.value }))} /></label>
              <label className="block space-y-2 text-sm text-foreground"><span>Teléfono</span><Input value={form.phone} onChange={(e) => setForm(p => ({ ...p, phone: e.target.value }))} /></label>
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

          <div className="flex justify-end">
            <Button type="submit" disabled={saveMut.isPending}>
              {form.id ? "Actualizar" : "Guardar proveedor"}
            </Button>
          </div>
        </form>
      </div>
    </Dialog>
  );
}
