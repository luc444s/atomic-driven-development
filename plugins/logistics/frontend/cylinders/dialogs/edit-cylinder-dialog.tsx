import type { FormEvent } from "react";
import { Button } from "../../../../../apps/web/src/shared/ui/button";
import { Dialog } from "../../../../../apps/web/src/shared/ui/dialog";
import { CylinderFormFields } from "../forms/cylinder-form-fields";
import type { CylinderFormState } from "../forms/cylinder-form-state";

type EditCylinderDialogProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  cylinderForm: CylinderFormState;
  onCylinderFormChange: (form: CylinderFormState) => void;
  gasOptions: Array<{ id: string; name: string }>;
  brandOptions: Array<{ id: string; name: string }>;
  sublineOptions: Array<{ value: string; label: string }>;
  conditions: Array<{ code: string; name: string }>;
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
  brandOptions,
  sublineOptions,
  conditions,
  isPending,
  serial,
  onSubmit,
}: EditCylinderDialogProps) {
  return (
    <Dialog
      open={open}
      title={`Editar ${serial}`}
      description="Actualiza la ficha completa del envase."
      maxWidthClassName="max-w-[1600px]"
      onClose={() => onOpenChange(false)}
    >
      <form className="space-y-4" onSubmit={onSubmit}>
        <CylinderFormFields
          form={cylinderForm}
          gasProducts={gasOptions}
          brands={brandOptions}
          conditions={conditions}
          onChange={onCylinderFormChange}
          includeActivation
        />
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
