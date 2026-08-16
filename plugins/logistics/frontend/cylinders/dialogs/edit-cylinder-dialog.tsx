import type { FormEvent } from "react";
import { Button } from "@systutor/shell/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@systutor/shell/ui/card";
import { Combobox } from "@systutor/shell/ui/combobox";
import { Dialog } from "@systutor/shell/ui/dialog";
import { Checkbox, Input } from "@systutor/shell/ui/input";
import { Field } from "../utils/formatters";
import type { CylinderFormState } from "../forms/cylinder-form-state";

type EditCylinderDialogProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  cylinderForm: CylinderFormState;
  onCylinderFormChange: (form: CylinderFormState) => void;
  gasOptions: Array<{ id: string; name: string }>;
  isPending: boolean;
  serial: string;
  onSubmit: (e: FormEvent<HTMLFormElement>) => void;
};

export function EditCylinderDialog({
  open,
  onOpenChange,
  cylinderForm,
  onCylinderFormChange,
  gasOptions,
  isPending,
  serial,
  onSubmit,
}: EditCylinderDialogProps) {
  function updateField<Key extends keyof CylinderFormState>(key: Key, value: CylinderFormState[Key]) {
    onCylinderFormChange({ ...cylinderForm, [key]: value });
  }

  return (
    <Dialog
      open={open}
      title={`Editar ${serial}`}
      description="Actualiza los datos del envase."
      maxWidthClassName="max-w-[1600px]"
      onClose={() => onOpenChange(false)}
    >
      <form className="space-y-4" onSubmit={onSubmit}>
        <Card>
          <CardHeader>
            <CardTitle>Datos del envase</CardTitle>
            <CardDescription>Los datos tecnicos se completan en el retimbrado.</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-3 md:grid-cols-3">
            <Field label="Serial">
              <Input
                value={cylinderForm.serial}
                onChange={(event) => updateField("serial", event.target.value)}
                placeholder="Nro. de serie del cilindro"
              />
            </Field>
            <Field label="Producto / Gas">
              <Combobox
                value={cylinderForm.gas_group_id}
                onChange={(value) => updateField("gas_group_id", value)}
                options={gasOptions.map((item) => ({ value: item.id, label: item.name }))}
                placeholder="Seleccionar producto"
                searchPlaceholder="Buscar producto..."
                emptyMessage="Sin productos disponibles."
              />
            </Field>
            <Field label="Matrícula">
              <Input
                value={cylinderForm.barcode2}
                onChange={(event) => updateField("barcode2", event.target.value)}
                placeholder="Codigo de etiqueta fisica"
              />
            </Field>
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
                onChange={(event) => updateField("is_active", event.target.checked)}
              />
              Envase activo
            </label>
            <label className="flex items-center gap-2 text-sm text-foreground">
              <Checkbox
                checked={cylinderForm.is_service}
                onChange={(event) => updateField("is_service", event.target.checked)}
              />
              Producto de servicio
            </label>
            <label className="flex items-center gap-2 text-sm text-foreground">
              <Checkbox
                checked={cylinderForm.is_medical}
                onChange={(event) => updateField("is_medical", event.target.checked)}
              />
              Envase para uso medicinal
            </label>
          </CardContent>
        </Card>

        <div className="flex justify-end gap-2">
          <Button type="button" variant="secondary" onClick={() => onOpenChange(false)}>
            Cancelar
          </Button>
          <Button type="submit" disabled={isPending}>
            Guardar cambios
          </Button>
        </div>
      </form>
    </Dialog>
  );
}
