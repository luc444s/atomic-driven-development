import type { FormEvent } from "react";
import { Button } from "../../../../../apps/web/src/shared/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../../../../apps/web/src/shared/ui/card";
import { Combobox, type ComboboxOption } from "../../../../../apps/web/src/shared/ui/combobox";
import { Dialog } from "../../../../../apps/web/src/shared/ui/dialog";
import { Input } from "../../../../../apps/web/src/shared/ui/input";
import { Select } from "../../../../../apps/web/src/shared/ui/select";
import { Alert } from "../../../../../apps/web/src/shared/ui/alert";
import { CylinderFormFields } from "../forms/cylinder-form-fields";
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
  brandOptions: Array<{ id: string; name: string }>;
  warehouseOptions: ComboboxOption[];
  sublineOptions: Array<{ value: string; label: string }>;
  conditions: Array<{ code: string; name: string }>;
  isPending: boolean;
  error: string | null;
  onSubmit: (e: FormEvent<HTMLFormElement>) => void;
  onCustomerSearchClick: () => void;
  compactMode?: boolean;
  compactHint?: string | null;
};

export function CreateCylinderDialog({
  open,
  onOpenChange,
  cylinderForm,
  onCylinderFormChange,
  createMeta,
  onCreateMetaChange,
  gasOptions,
  brandOptions,
  warehouseOptions,
  sublineOptions,
  conditions,
  isPending,
  error,
  onSubmit,
  onCustomerSearchClick,
  compactMode = false,
  compactHint = null,
}: CreateCylinderDialogProps) {
  const selectedGasLabel = gasOptions.find((item) => item.id === cylinderForm.gas_group_id)?.name ?? "Sin producto inferido";

  return (
    <Dialog
      open={open}
      title="Nuevo envase"
      maxWidthClassName="max-w-[1600px]"
      onClose={() => onOpenChange(false)}
    >
      <form className="space-y-4" onSubmit={onSubmit}>
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
                    onChange={(value) =>
                      onCreateMetaChange({
                        ...createMeta,
                        entry_mode: (value as CylinderEntryMode) || "EMPTY_FROM_CUSTOMER",
                        customer_id: value === "FULL_FROM_SUPPLIER" ? "" : createMeta.customer_id,
                        customer_name: value === "FULL_FROM_SUPPLIER" ? "" : createMeta.customer_name,
                      })
                    }
                    options={[
                      { value: "EMPTY_FROM_CUSTOMER", label: "Vacio desde cliente" },
                      { value: "FULL_FROM_SUPPLIER", label: "Lleno desde proveedor" },
                    ]}
                  />
                </Field>
                <Field label="Almacen de alta">
                  <Combobox
                    value={createMeta.warehouse_id}
                    onChange={(value) =>
                      onCreateMetaChange({
                        ...createMeta,
                        warehouse_id: value,
                      })
                    }
                    options={warehouseOptions}
                    placeholder="Seleccionar almacen"
                    searchPlaceholder="Buscar almacen..."
                    emptyMessage="Sin almacenes disponibles."
                  />
                </Field>
                {createMeta.entry_mode === "EMPTY_FROM_CUSTOMER" ? (
                  <Field label="Cliente origen">
                    <Button type="button" variant="secondary" onClick={onCustomerSearchClick}>
                      {createMeta.customer_name
                        ? `${createMeta.customer_name} (${createMeta.customer_id})`
                        : "Seleccionar cliente"}
                    </Button>
                  </Field>
                ) : null}
              </CardContent>
            </Card>
            <CylinderFormFields
              form={cylinderForm}
              gasProducts={gasOptions}
              brands={brandOptions}
              conditions={conditions}
              onChange={onCylinderFormChange}
              includeActivation={false}
            />
          </>
        )}
        {error ? <Alert title="No se pudo guardar">{error}</Alert> : null}
        <div className="flex justify-end gap-2">
          <Button
            type="button"
            variant="secondary"
            onClick={() => onOpenChange(false)}
          >
            Cancelar
          </Button>
          <Button type="submit" disabled={isPending}>
            Guardar envase
          </Button>
        </div>
      </form>
    </Dialog>
  );
}
