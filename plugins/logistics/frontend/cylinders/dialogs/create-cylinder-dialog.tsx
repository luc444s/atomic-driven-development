import type { FormEvent } from "react";
import { Button } from "../../../../../apps/web/src/shared/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../../../../apps/web/src/shared/ui/card";
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
  sublineOptions: Array<{ value: string; label: string }>;
  conditions: Array<{ code: string; name: string }>;
  isPending: boolean;
  error: string | null;
  onSubmit: (e: FormEvent<HTMLFormElement>) => void;
  onCustomerSearchClick: () => void;
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
  sublineOptions,
  conditions,
  isPending,
  error,
  onSubmit,
  onCustomerSearchClick,
}: CreateCylinderDialogProps) {
  return (
    <Dialog
      open={open}
      title="Nuevo envase"
      maxWidthClassName="max-w-[1600px]"
      onClose={() => onOpenChange(false)}
    >
      <form className="space-y-4" onSubmit={onSubmit}>
        <Card>
          <CardHeader>
            <CardTitle>Origen operativo</CardTitle>
            <CardDescription>Define la rama de alta y la referencia documental obligatoria.</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
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
            <Field label="Tipo de documento">
              <Input
                value={createMeta.document_type}
                onChange={(event) =>
                  onCreateMetaChange({
                    ...createMeta,
                    document_type: event.target.value.toUpperCase(),
                  })
                }
                placeholder="FACTURA, GUIA, OC"
              />
            </Field>
            <Field label="Numero de documento">
              <Input
                value={createMeta.document_number}
                onChange={(event) =>
                  onCreateMetaChange({
                    ...createMeta,
                    document_number: event.target.value.toUpperCase(),
                  })
                }
                placeholder="F001-000123"
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
            ) : (
              <Field label="Contexto stock">
                <p className="rounded-md border border-border bg-surface px-3 py-2 text-sm text-muted-foreground">
                  Esta rama dejara contrapartida minima en stock usando el almacen activo del usuario.
                </p>
              </Field>
            )}
          </CardContent>
        </Card>
        <CylinderFormFields
          form={cylinderForm}
          gasProducts={gasOptions}
          brands={brandOptions}
          adrSublineOptions={sublineOptions}
          conditions={conditions}
          onChange={onCylinderFormChange}
          includeActivation={false}
        />
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
