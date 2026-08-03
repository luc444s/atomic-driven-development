import type { FormEvent } from "react";

import { Alert } from "../../../../../apps/web/src/shared/ui/alert";
import { Button } from "../../../../../apps/web/src/shared/ui/button";
import { Combobox, type ComboboxOption } from "../../../../../apps/web/src/shared/ui/combobox";
import { Dialog } from "../../../../../apps/web/src/shared/ui/dialog";
import { Input, Textarea } from "../../../../../apps/web/src/shared/ui/input";
import type { LogisticsCylinder } from "../../api";
import type {
  CylinderFillingFormState,
  CylinderFillingMode,
} from "../forms/cylinder-filling";
import { formatDateTime } from "../utils/formatters";

interface CylinderFillingDialogProps {
  open: boolean;
  mode: CylinderFillingMode;
  cylinder: LogisticsCylinder | null;
  form: CylinderFillingFormState;
  warehouseOptions: ComboboxOption[];
  error: string | null;
  isPending: boolean;
  onOpenChange: (open: boolean) => void;
  onFormChange: (form: CylinderFillingFormState) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
}

export function CylinderFillingDialog({
  open,
  mode,
  cylinder,
  form,
  warehouseOptions,
  error,
  isPending,
  onOpenChange,
  onFormChange,
  onSubmit,
}: CylinderFillingDialogProps) {
  const isFillMode = mode === "fill";
  const title = isFillMode ? "Registrar llenado" : "Registrar vaciado";
  const description = isFillMode
    ? "Descuenta stock libre del producto operativo y deja la carga técnica auditada dentro del envase."
    : "Marca el envase como vacío y deja trazado el cambio material sin devolver stock al sistema en este slice.";

  return (
    <Dialog
      open={open}
      title={title}
      description={description}
      onClose={() => onOpenChange(false)}
    >
      <form className="space-y-6" onSubmit={onSubmit}>
        {error ? <Alert title="Operación no completada">{error}</Alert> : null}

        <div className="rounded-md border border-border p-4">
          <p className="mb-3 text-sm font-medium text-foreground">Contexto del envase</p>
          <div className="grid gap-4 md:grid-cols-2">
            <label className="block space-y-2 text-sm text-foreground">
              <span>Serial</span>
              <div className="rounded-md border border-input bg-surface px-3 py-2 text-sm text-foreground">
                {cylinder?.serial ?? "-"}
              </div>
            </label>
            <label className="block space-y-2 text-sm text-foreground">
              <span>Lectura actual</span>
              <div className="rounded-md border border-input bg-surface px-3 py-2 text-sm text-foreground">
                {cylinder?.fill_status ?? "VACIO"}
              </div>
            </label>
            <label className="block space-y-2 text-sm text-foreground">
              <span>Carga actual kg</span>
              <div className="rounded-md border border-input bg-surface px-3 py-2 text-sm text-foreground">
                {cylinder?.content_kg?.toString() ?? "-"}
              </div>
            </label>
            <label className="block space-y-2 text-sm text-foreground">
              <span>Último llenado</span>
              <div className="rounded-md border border-input bg-surface px-3 py-2 text-sm text-foreground">
                {formatDateTime(cylinder?.last_fill_at)}
                {cylinder?.last_fill_warehouse_name ? ` · ${cylinder.last_fill_warehouse_name}` : ""}
              </div>
            </label>
          </div>
        </div>

        <div className="rounded-md border border-border p-4">
          <p className="mb-3 text-sm font-medium text-foreground">
            {isFillMode ? "Datos del llenado" : "Datos del vaciado"}
          </p>
          <div className="grid gap-4 md:grid-cols-2">
            <label className="block space-y-2 text-sm text-foreground md:col-span-2">
              <span>Almacén origen</span>
              <Combobox
                value={form.warehouse_id}
                onChange={(value) => onFormChange({ ...form, warehouse_id: value })}
                options={warehouseOptions}
                placeholder="Seleccionar almacén"
                searchPlaceholder="Buscar almacén..."
                emptyMessage="Sin almacenes disponibles."
              />
            </label>

            {isFillMode ? (
              <>
                <label className="block space-y-2 text-sm text-foreground">
                  <span>Contenido kg</span>
                  <Input
                    type="number"
                    step="0.01"
                    value={form.content_kg}
                    onChange={(event) =>
                      onFormChange({ ...form, content_kg: event.target.value })
                    }
                  />
                </label>
                <label className="block space-y-2 text-sm text-foreground">
                  <span>Volumen m3</span>
                  <Input
                    type="number"
                    step="0.0001"
                    value={form.volume_m3}
                    onChange={(event) =>
                      onFormChange({ ...form, volume_m3: event.target.value })
                    }
                  />
                </label>
              </>
            ) : null}

            <label className="block space-y-2 text-sm text-foreground md:col-span-2">
              <span>Peso actual</span>
              <Input
                type="number"
                step="0.01"
                value={form.weight_current}
                onChange={(event) =>
                  onFormChange({ ...form, weight_current: event.target.value })
                }
              />
            </label>

            <label className="block space-y-2 text-sm text-foreground md:col-span-2">
              <span>Notas</span>
              <Textarea
                value={form.notes}
                onChange={(event) =>
                  onFormChange({ ...form, notes: event.target.value })
                }
                rows={4}
                placeholder={
                  isFillMode
                    ? "Observación operativa del llenado"
                    : "Observación operativa del vaciado"
                }
              />
            </label>
          </div>
        </div>

        <div className="flex justify-end gap-3">
          <Button type="button" variant="secondary" onClick={() => onOpenChange(false)}>
            Cancelar
          </Button>
          <Button type="submit" disabled={isPending}>
            {isFillMode ? "Registrar llenado" : "Registrar vaciado"}
          </Button>
        </div>
      </form>
    </Dialog>
  );
}
