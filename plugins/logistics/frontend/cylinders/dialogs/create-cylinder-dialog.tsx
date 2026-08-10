import { useState, useEffect, useRef, useCallback, useMemo, type FormEvent } from "react";
import { Button } from "../../../../../apps/web/src/shared/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../../../../apps/web/src/shared/ui/card";
import { Combobox, type ComboboxOption } from "../../../../../apps/web/src/shared/ui/combobox";
import { Dialog } from "../../../../../apps/web/src/shared/ui/dialog";
import { Checkbox, Input } from "../../../../../apps/web/src/shared/ui/input";
import { Select } from "../../../../../apps/web/src/shared/ui/select";
import { Alert } from "../../../../../apps/web/src/shared/ui/alert";
import { apiRequest } from "../../../../../apps/web/src/shared/api/client";
import { Field } from "../utils/formatters";
import type { CylinderEntryMode } from "../../api";
import type { CylinderFormState, CylinderCreateMetaState } from "../forms/cylinder-form-state";

type CreateCylinderDialogProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  cylinderForm: CylinderFormState;
  onCylinderFormChange: (form: CylinderFormState) => void;
  createMeta: CylinderCreateMetaState;
  onCreateMetaChange: (meta: CylinderCreateMetaState) => void;
  gasOptions: Array<{ id: string; name: string }>;
  warehouseOptions: ComboboxOption[];
  isPending: boolean;
  error: string | null;
  onSubmit: (serials: string[]) => Promise<void>;
  compactMode?: boolean;
  compactHint?: string | null;
};

interface CustomerSearchItem {
  id: string;
  legal_name: string;
  commercial_name: string | null;
  display_name: string;
  document_number: string;
}

const ENTRY_MODE_OPTIONS = [
  { value: "EMPTY_FROM_WAREHOUSE", label: "Vacío desde almacén" },
  { value: "EMPTY_FROM_CUSTOMER", label: "Vacío desde cliente" },
];

const WAREHOUSE_SESSION_KEY = "systutor:last-alta-warehouse";

const CONTAINER_TYPE_OPTIONS = [
  { value: "CYLINDER", label: "Estandar" },
  { value: "CRYOGENIC_TANK", label: "Criogenico (tanque)" },
];

function parseSerials(raw: string): string[] {
  return raw
    .split(/[,;\n]+/)
    .map((s) => s.trim())
    .filter((s) => s.length > 0);
}

export function CreateCylinderDialog({
  open,
  onOpenChange,
  cylinderForm,
  onCylinderFormChange,
  createMeta,
  onCreateMetaChange,
  gasOptions,
  warehouseOptions,
  isPending,
  error,
  onSubmit,
  compactMode = false,
  compactHint = null,
}: CreateCylinderDialogProps) {
  const [customerOptions, setCustomerOptions] = useState<ComboboxOption[]>([]);
  const [customerSearch, setCustomerSearch] = useState("");
  const [customerLoading, setCustomerLoading] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout>>();
  const serialInputRef = useRef<HTMLInputElement>(null);
  const [duplicateSerials, setDuplicateSerials] = useState<Set<string>>(new Set());
  const dedupRef = useRef<ReturnType<typeof setTimeout>>();

  const searchCustomers = useCallback(async (query: string) => {
    if (query.length < 1) {
      setCustomerOptions([]);
      return;
    }
    setCustomerLoading(true);
    try {
      const result = await apiRequest<CustomerSearchItem[]>(
        `/api/v1/plugins/crm/customers/search?query=${encodeURIComponent(query)}&limit=20`,
      );
      setCustomerOptions(
        result.map((c) => ({
          value: c.id,
          label: c.display_name || c.legal_name,
          keywords: [c.legal_name, c.commercial_name ?? "", c.document_number ?? ""],
        })),
      );
    } catch {
      setCustomerOptions([]);
    } finally {
      setCustomerLoading(false);
    }
  }, []);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      searchCustomers(customerSearch);
    }, 300);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [customerSearch, searchCustomers]);

  useEffect(() => {
    if (open && !compactMode) {
      const timer = setTimeout(() => serialInputRef.current?.focus(), 100);
      return () => clearTimeout(timer);
    }
  }, [open, compactMode]);

  const serials = useMemo(() => parseSerials(cylinderForm.serial), [cylinderForm.serial]);

  useEffect(() => {
    const items = serials.filter((s) => s.length > 0);
    if (items.length === 0) {
      setDuplicateSerials(new Set());
      return;
    }
    if (dedupRef.current) clearTimeout(dedupRef.current);
    dedupRef.current = setTimeout(async () => {
      const results = await Promise.allSettled(
        items.map((s) =>
          apiRequest<unknown>(`/api/v1/plugins/logistics/cylinders/by-serial/${encodeURIComponent(s)}`),
        ),
      );
      const existing = new Set<string>();
      results.forEach((r, i) => {
        if (r.status === "fulfilled") {
          existing.add(items[i]);
        }
      });
      setDuplicateSerials(existing);
    }, 400);
    return () => {
      if (dedupRef.current) clearTimeout(dedupRef.current);
    };
  }, [serials]);

  const validSerials = useMemo(
    () => serials.filter((s) => !duplicateSerials.has(s)),
    [serials, duplicateSerials],
  );

  const batchCount = validSerials.length;
  const hasBatch = batchCount > 1;
  const dupList = serials.filter((s) => duplicateSerials.has(s));

  const selectedGasLabel = gasOptions.find((item) => item.id === cylinderForm.gas_group_id)?.name ?? "Sin producto inferido";
  const isCustomerMode = createMeta.entry_mode === "EMPTY_FROM_CUSTOMER";
  const customerId = createMeta.customer_id;

  function handleEntryModeChange(value: string) {
    const entryMode = (value as CylinderEntryMode) || "EMPTY_FROM_WAREHOUSE";
    onCreateMetaChange({
      ...createMeta,
      entry_mode: entryMode,
    });
  }

  useEffect(() => {
    if (!open) {
      return;
    }
    if (!createMeta.warehouse_id) {
      const saved =
        window.sessionStorage.getItem(WAREHOUSE_SESSION_KEY) ?? "";
      if (saved && warehouseOptions.some((option) => option.value === saved)) {
        onCreateMetaChange({ ...createMeta, warehouse_id: saved });
      }
    }
  }, [open]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (isPending) return;
    if (validSerials.length === 0) return;
    await onSubmit(validSerials);
  }

  return (
    <Dialog
      open={open}
      title="Nuevo envase"
      maxWidthClassName="max-w-[1600px]"
      onClose={() => onOpenChange(false)}
    >
      <form className="space-y-4" onSubmit={handleSubmit}>
        {compactMode ? (
          <Card>
            <CardHeader>
              <CardTitle>Alta mínima en ruta</CardTitle>
              <CardDescription>
                {compactHint ?? "Registra el envase con serial y barcode. El producto se infiere desde la operación actual."}
              </CardDescription>
            </CardHeader>
            <CardContent className="grid gap-3 md:grid-cols-2">
              <Field label="Serial">
                <Input value={cylinderForm.serial} onChange={(event) => onCylinderFormChange({ ...cylinderForm, serial: event.target.value })} />
              </Field>
              <Field label="Barcode / etiqueta">
                <Input value={cylinderForm.barcode2} onChange={(event) => onCylinderFormChange({ ...cylinderForm, barcode2: event.target.value })} />
              </Field>
              <Field className="md:col-span-2" label="Producto inferido">
                <div className="rounded-md border border-input bg-surface px-3 py-2 text-sm text-foreground">
                  {selectedGasLabel}
                </div>
              </Field>
            </CardContent>
          </Card>
        ) : (
          <>
            <Card>
              <CardHeader>
                <CardTitle>Origen operativo</CardTitle>
                <CardDescription>Define como entra el envase al almacen y desde que origen operativo.</CardDescription>
              </CardHeader>
              <CardContent className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                <Field label="Rama de alta">
                  <Select
                    value={createMeta.entry_mode}
                    onChange={handleEntryModeChange}
                    options={ENTRY_MODE_OPTIONS}
                  />
                </Field>
                <Field label="Almacen de alta">
                  <Combobox
                    value={createMeta.warehouse_id}
                    onChange={(value) => {
                      onCreateMetaChange({ ...createMeta, warehouse_id: value });
                      if (value) {
                        window.sessionStorage.setItem(WAREHOUSE_SESSION_KEY, value);
                      }
                    }}
                    options={warehouseOptions}
                    placeholder="Seleccionar almacen"
                    searchPlaceholder="Buscar almacen..."
                    emptyMessage="Sin almacenes disponibles."
                  />
                </Field>
                {isCustomerMode ? (
                  <Field label="Cliente origen">
                    <Combobox
                      value={customerId}
                      onChange={(id) => {
                        const option = customerOptions.find((o) => o.value === id);
                        onCreateMetaChange({
                          ...createMeta,
                          customer_id: id,
                          customer_name: option?.label ?? createMeta.customer_name,
                        });
                      }}
                      options={customerOptions}
                      placeholder="Seleccionar cliente"
                      searchPlaceholder="Escribe para buscar cliente..."
                      searchValue={customerSearch}
                      onSearchValueChange={setCustomerSearch}
                      emptyMessage={
                        customerLoading
                          ? "Buscando..."
                          : customerSearch.length >= 1
                            ? "Sin resultados."
                            : "Escribe para buscar..."
                      }
                      variant="button"
                      minSearchLength={0}
                      selectedLabel={createMeta.customer_name || undefined}
                    />
                  </Field>
                ) : null}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Datos del envase</CardTitle>
                <CardDescription>Registra los datos minimos del envase. Separa seriales con coma para crear varios a la vez.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-3 md:grid-cols-3">
                  <Field label="Serial">
                    <div className="relative">
                      <Input
                        ref={serialInputRef}
                        value={cylinderForm.serial}
                        onChange={(event) => onCylinderFormChange({ ...cylinderForm, serial: event.target.value })}
                        placeholder={hasBatch ? "" : "Nro. de serie del cilindro"}
                      />
                      {hasBatch ? (
                        <span className="absolute right-2 top-1/2 -translate-y-1/2 rounded-full bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary">
                          {batchCount} envases
                        </span>
                      ) : null}
                    </div>
                  </Field>
                  <Field label="Producto / Gas">
                    <Combobox
                      value={cylinderForm.gas_group_id}
                      onChange={(value) => onCylinderFormChange({ ...cylinderForm, gas_group_id: value })}
                      options={gasOptions.map((item) => ({ value: item.id, label: item.name }))}
                      placeholder="Seleccionar producto"
                      searchPlaceholder="Buscar producto..."
                      emptyMessage="Sin productos disponibles."
                    />
                  </Field>
                  <Field label="Matrícula">
                    <Input
                      value={cylinderForm.barcode2}
                      onChange={(event) => onCylinderFormChange({ ...cylinderForm, barcode2: event.target.value })}
                      placeholder="Codigo de etiqueta fisica"
                    />
                  </Field>
                  <Field label="Tipo de envase">
                    <Select
                      value={cylinderForm.container_type}
                      onChange={(value) =>
                        onCylinderFormChange({ ...cylinderForm, container_type: value })
                      }
                      options={CONTAINER_TYPE_OPTIONS}
                    />
                  </Field>
                </div>
                {cylinderForm.container_type === "CRYOGENIC_TANK" ? (
                  <Alert title="Envase criogenico (tanque)">
                    El producto seleccionado es el gas liquido del tanque y debe ser fuente de al menos una receta criogenica. La capacidad nominal se registra en el campo volumen (m3).
                  </Alert>
                ) : null}
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Estado y clasificación</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <label className="flex items-center gap-2 text-sm text-foreground">
                  <Checkbox
                    checked={cylinderForm.is_active}
                    onChange={(event) => onCylinderFormChange({ ...cylinderForm, is_active: event.target.checked })}
                  />
                  Envase activo
                </label>
                <label className="flex items-center gap-2 text-sm text-foreground">
                  <Checkbox
                    checked={cylinderForm.is_service}
                    onChange={(event) => onCylinderFormChange({ ...cylinderForm, is_service: event.target.checked })}
                  />
                  Producto de servicio
                </label>
                <label className="flex items-center gap-2 text-sm text-foreground">
                  <Checkbox
                    checked={cylinderForm.is_medical}
                    onChange={(event) => onCylinderFormChange({ ...cylinderForm, is_medical: event.target.checked })}
                  />
                  Envase para uso medicinal
                </label>
              </CardContent>
            </Card>
          </>
        )}
        {dupList.length > 0 ? (
          <Alert title="Seriales duplicados">
            Ya existen {dupList.length} envase{dupList.length > 1 ? "s" : ""} con este serial: {dupList.join(", ")}. No se crearan de nuevo.
          </Alert>
        ) : null}
        {error ? <Alert title="No se pudo guardar">{error}</Alert> : null}
        <div className="flex justify-end gap-2">
          <Button
            type="button"
            variant="secondary"
            onClick={() => onOpenChange(false)}
          >
            Cancelar
          </Button>
          <Button type="submit" disabled={isPending || validSerials.length === 0}>
            {hasBatch ? `Crear ${batchCount} envases` : "Guardar envase"}
          </Button>
        </div>
      </form>
    </Dialog>
  );
}
