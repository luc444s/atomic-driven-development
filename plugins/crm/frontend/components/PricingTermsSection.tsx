import { FormEvent, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "../../../../apps/web/src/lib/react-query";
import { Button } from "../../../../apps/web/src/shared/ui/button";
import { Combobox } from "../../../../apps/web/src/shared/ui/combobox";
import { ConfirmDialog } from "../../../../apps/web/src/shared/ui/confirm-dialog";
import { DataTable } from "../../../../apps/web/src/shared/ui/data-table";
import { Input } from "../../../../apps/web/src/shared/ui/input";
import {
  createCustomerPricingTerm,
  crmKeys,
  deleteCustomerPricingTerm,
  listCustomerPricingTerms,
  updateCustomerPricingTerm,
} from "../api";
import { listAllProducts } from "../../../productos/frontend/api";
import type { ProductListItem } from "../../../productos/frontend/types";
import type { CustomerPricingTerm, CustomerPricingTermPayload } from "../types";

type PricingTermsSectionProps = {
  customerId: string;
  canManage?: boolean;
};

const EMPTY_PRICING: CustomerPricingTermPayload = {
  product_id: null,
  scope_type: "GLOBAL",
  pricing_mode: "FIXED_PRICE",
  fixed_amount: null,
  discount_percent: null,
  currency: null,
  valid_from: "",
  valid_to: null,
  source_quote_ref: null,
  notes: null,
};

function formatAmount(value: string | null): string {
  if (value === null || value === undefined) return "-";
  const num = parseFloat(value);
  if (isNaN(num)) return value;
  return num.toFixed(2);
}

export function PricingTermsSection({ customerId, canManage = false }: PricingTermsSectionProps) {
  const queryClient = useQueryClient();
  const [form, setForm] = useState<CustomerPricingTermPayload>(EMPTY_PRICING);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);

  const query = useQuery({
    queryKey: crmKeys.customers.pricingTerms(customerId),
    queryFn: () => listCustomerPricingTerms(customerId),
  });

  const productsQuery = useQuery({
    queryKey: ["productos", "all"],
    queryFn: () => listAllProducts({ is_active: "true" }),
    staleTime: 5 * 60 * 1000,
  });

  const createMutation = useMutation({
    mutationFn: () => createCustomerPricingTerm(customerId, form),
    onSuccess: async () => {
      setForm(EMPTY_PRICING);
      await queryClient.invalidateQueries({ queryKey: crmKeys.customers.pricingTerms(customerId) });
    },
  });

  const updateMutation = useMutation({
    mutationFn: () => updateCustomerPricingTerm(editingId!, form),
    onSuccess: async () => {
      setForm(EMPTY_PRICING);
      setEditingId(null);
      await queryClient.invalidateQueries({ queryKey: crmKeys.customers.pricingTerms(customerId) });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (pricingTermId: string) => deleteCustomerPricingTerm(pricingTermId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: crmKeys.customers.pricingTerms(customerId) });
    },
  });

  async function submitForm(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (editingId) {
      await updateMutation.mutateAsync();
    } else {
      await createMutation.mutateAsync();
    }
  }

  function startEdit(row: CustomerPricingTerm) {
    setEditingId(row.id);
    setForm({
      product_id: row.product_id,
      scope_type: row.scope_type,
      pricing_mode: row.pricing_mode,
      fixed_amount: row.fixed_amount,
      discount_percent: row.discount_percent,
      currency: row.currency,
      valid_from: row.valid_from ? row.valid_from.slice(0, 10) : "",
      valid_to: row.valid_to ? row.valid_to.slice(0, 10) : null,
      source_quote_ref: row.source_quote_ref,
      notes: row.notes,
    });
  }

  function cancelEdit() {
    setEditingId(null);
    setForm(EMPTY_PRICING);
  }

  const isPending = createMutation.isPending || updateMutation.isPending;

  return (
    <div className="space-y-4">
      <DataTable
        dense
        columns={[
          { key: "scope", header: "Alcance", render: (row: CustomerPricingTerm) => row.scope_type },
          { key: "mode", header: "Tipo", render: (row: CustomerPricingTerm) => row.pricing_mode },
          {
            key: "value",
            header: "Valor",
            render: (row: CustomerPricingTerm) =>
              row.pricing_mode === "FIXED_PRICE"
                ? `${formatAmount(row.fixed_amount)} ${row.currency ?? ""}`.trim()
                : `${formatAmount(row.discount_percent)}%`,
          },
          { key: "currency", header: "Divisa", render: (row: CustomerPricingTerm) => row.currency ?? "-" },
          {
            key: "valid_from",
            header: "Desde",
            render: (row: CustomerPricingTerm) => (row.valid_from ? row.valid_from.slice(0, 10) : "-"),
          },
          {
            key: "valid_to",
            header: "Hasta",
            render: (row: CustomerPricingTerm) => (row.valid_to ? row.valid_to.slice(0, 10) : "-"),
          },
          { key: "active", header: "Activo", render: (row: CustomerPricingTerm) => (row.is_active ? "Sí" : "No") },
          {
            key: "actions",
            header: "",
            render: (row: CustomerPricingTerm) =>
              canManage ? (
                <Button
                  variant="secondary"
                  className="h-7 w-7 px-0 py-0"
                  aria-label="Eliminar precio especial"
                  onClick={(event) => {
                    event.stopPropagation();
                    setConfirmDeleteId(row.id);
                  }}
                >
                  x
                </Button>
              ) : null,
          },
        ]}
        rows={query.data ?? []}
        rowKey={(row) => row.id}
        emptyMessage="No hay precios especiales cargados."
        onRowClick={canManage ? startEdit : undefined}
      />

      <ConfirmDialog
        open={confirmDeleteId !== null}
        onClose={() => setConfirmDeleteId(null)}
        onConfirm={() => {
          if (confirmDeleteId) deleteMutation.mutate(confirmDeleteId);
          setConfirmDeleteId(null);
        }}
        title="Eliminar precio especial"
        description="¿Estás seguro de eliminar este precio especial?"
        destructive
        confirmLabel="Eliminar"
      />

      {canManage ? (
        <form className="space-y-3 rounded-md border border-border p-4" onSubmit={submitForm}>
          <div>
            <p className="text-sm font-medium text-foreground">
              {editingId ? "Editar precio especial" : "Nuevo precio especial"}
            </p>
            <p className="text-xs text-muted-foreground">
              Condicion comercial del cliente. El precio base sigue viviendo en productos.
            </p>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <label className="block space-y-2 text-sm text-foreground">
              <span>Alcance</span>
              <Combobox
                value={form.scope_type}
                onChange={(value) =>
                  setForm((current) => ({
                    ...current,
                    scope_type: (value as "GLOBAL" | "PRODUCT") || "GLOBAL",
                    product_id: value === "PRODUCT" ? current.product_id : null,
                  }))
                }
                options={[
                  { value: "GLOBAL", label: "Global", keywords: ["global"] },
                  { value: "PRODUCT", label: "Producto", keywords: ["producto"] },
                ]}
                placeholder="Seleccionar alcance"
                searchPlaceholder="Buscar..."
              />
            </label>
            <label className="block space-y-2 text-sm text-foreground">
              <span>Tipo de precio</span>
              <Combobox
                value={form.pricing_mode}
                onChange={(value) =>
                  setForm((current) => ({
                    ...current,
                    pricing_mode: (value as "FIXED_PRICE" | "PERCENT_DISCOUNT") || "FIXED_PRICE",
                    fixed_amount: value === "FIXED_PRICE" ? current.fixed_amount : null,
                    discount_percent: value === "PERCENT_DISCOUNT" ? current.discount_percent : null,
                  }))
                }
                options={[
                  { value: "FIXED_PRICE", label: "Precio fijo", keywords: ["fijo"] },
                  { value: "PERCENT_DISCOUNT", label: "Descuento %", keywords: ["descuento", "porcentaje"] },
                ]}
                placeholder="Seleccionar tipo"
                searchPlaceholder="Buscar..."
              />
            </label>
            {form.pricing_mode === "FIXED_PRICE" ? (
              <label className="block space-y-2 text-sm text-foreground">
                <span>Precio fijo</span>
                <Input
                  value={form.fixed_amount ?? ""}
                  onChange={(event) =>
                    setForm((current) => ({ ...current, fixed_amount: event.target.value || null }))
                  }
                  placeholder="Ej. 15.750"
                  inputMode="decimal"
                />
              </label>
            ) : (
              <label className="block space-y-2 text-sm text-foreground">
                <span>Descuento (%)</span>
                <Input
                  value={form.discount_percent ?? ""}
                  onChange={(event) =>
                    setForm((current) => ({ ...current, discount_percent: event.target.value || null }))
                  }
                  placeholder="Ej. 12.500"
                  inputMode="decimal"
                />
              </label>
            )}
            <label className="block space-y-2 text-sm text-foreground">
              <span>Divisa</span>
              <Input
                value={form.currency ?? ""}
                onChange={(event) =>
                  setForm((current) => ({ ...current, currency: event.target.value || null }))
                }
                placeholder="EUR"
              />
            </label>
            <label className="block space-y-2 text-sm text-foreground">
              <span>Vigencia desde</span>
              <Input
                type="date"
                value={form.valid_from}
                onChange={(event) =>
                  setForm((current) => ({ ...current, valid_from: event.target.value }))
                }
              />
            </label>
            <label className="block space-y-2 text-sm text-foreground">
              <span>Vigencia hasta</span>
              <Input
                type="date"
                value={form.valid_to ?? ""}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    valid_to: event.target.value ? event.target.value : null,
                  }))
                }
              />
            </label>
            <label className="block space-y-2 text-sm text-foreground">
              <span>Ref. presupuesto origen</span>
              <Input
                value={form.source_quote_ref ?? ""}
                onChange={(event) =>
                  setForm((current) => ({ ...current, source_quote_ref: event.target.value || null }))
                }
                placeholder="Opcional"
              />
            </label>
            <label className="block space-y-2 text-sm text-foreground">
              <span>Notas</span>
              <Input
                value={form.notes ?? ""}
                onChange={(event) =>
                  setForm((current) => ({ ...current, notes: event.target.value || null }))
                }
                placeholder="Opcional"
              />
            </label>
            {form.scope_type === "PRODUCT" ? (
              <label className="block space-y-2 text-sm text-foreground md:col-span-2">
                <span>Producto</span>
                <Combobox
                  value={form.product_id ?? ""}
                  onChange={(value) =>
                    setForm((current) => ({ ...current, product_id: value || null }))
                  }
                  options={(productsQuery.data ?? []).map((p: ProductListItem) => ({
                    value: p.id,
                    label: `${p.sku} — ${p.name}`,
                    keywords: [p.sku, p.name, p.brand_name ?? ""],
                  }))}
                  placeholder="Seleccionar producto"
                  searchPlaceholder="Buscar por SKU o nombre..."
                />
              </label>
            ) : null}
          </div>
          <div className="flex justify-end gap-2">
            {editingId ? (
              <Button variant="secondary" type="button" onClick={cancelEdit}>
                Cancelar
              </Button>
            ) : null}
            <Button type="submit" disabled={isPending}>
              {editingId ? "Guardar cambios" : "Agregar precio"}
            </Button>
          </div>
        </form>
      ) : null}
    </div>
  );
}
