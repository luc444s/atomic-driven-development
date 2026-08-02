import { useEffect, useState, type FormEvent } from "react";
import { Button } from "../../../../../apps/web/src/shared/ui/button";
import { Dialog } from "../../../../../apps/web/src/shared/ui/dialog";
import { FileUpload } from "../../../../../apps/web/src/shared/ui/file-upload";
import { Input } from "../../../../../apps/web/src/shared/ui/input";
import { Select } from "../../../../../apps/web/src/shared/ui/select";
import { Alert } from "../../../../../apps/web/src/shared/ui/alert";
import { useQuery } from "../../../../../apps/web/src/lib/react-query";
import { CustomerSearchDialog } from "../../../../crm/frontend/components/CustomerSearchDialog";
import { ProductSearchDialog } from "../../../../productos/frontend/components/ProductSearchDialog";
import { listConditions } from "../../api/cylinders";
import { listContractTypes } from "../../api/contracts";
import { getRealWarehouses, listWarehouses } from "../../api/warehouses";
import type { ContractFormState } from "../forms/contract-form-state";

type ContractFormDialogProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  form: ContractFormState;
  onFormChange: (form: ContractFormState) => void;
  isPending: boolean;
  error: string | null;
  title: string;
  onSubmit: (e: FormEvent<HTMLFormElement>) => void;
  onFileSelect: (file: File | null) => void;
  showNotes?: boolean;
};

export function ContractFormDialog({
  open,
  onOpenChange,
  form,
  onFormChange,
  isPending,
  error,
  title,
  onSubmit,
  onFileSelect,
  showNotes = true,
}: ContractFormDialogProps) {
  const [isCustomerSearchOpen, setIsCustomerSearchOpen] = useState(false);
  const [isProductSearchOpen, setIsProductSearchOpen] = useState(false);
  const [productLabel, setProductLabel] = useState("");
  const contractTypesQuery = useQuery({ queryKey: ["logistics", "contract-types"], queryFn: listContractTypes });
  const conditionsQuery = useQuery({ queryKey: ["logistics", "conditions"], queryFn: listConditions });
  const warehousesQuery = useQuery({ queryKey: ["logistics", "warehouses"], queryFn: listWarehouses });
  const realWarehouses = getRealWarehouses(warehousesQuery.data ?? []);

  const field = (key: keyof ContractFormState) => (e: React.ChangeEvent<HTMLInputElement>) =>
    onFormChange({ ...form, [key]: e.target.value });

  useEffect(() => {
    if (!open) {
      setProductLabel("");
    }
  }, [open]);

  return (
    <Dialog
      open={open}
      title={title}
      maxWidthClassName="max-w-xl"
      onClose={() => onOpenChange(false)}
    >
      <form className="space-y-4" onSubmit={onSubmit}>
        {error && <Alert variant="error">{error}</Alert>}

        <div className="grid gap-3">
          <Labeled label="Tipo de contrato">
            <Select
              value={form.contract_type}
              onChange={(v) => onFormChange({ ...form, contract_type: v })}
              options={(contractTypesQuery.data ?? []).map((item) => ({ value: item.code, label: item.name }))}
            />
          </Labeled>

          <div className="grid grid-cols-2 gap-3">
            <Labeled label="Cliente">
              <div className="flex items-center gap-2">
                <Input
                  value={form.customer_name}
                  readOnly
                  placeholder="Seleccione un cliente..."
                  className="flex-1 cursor-pointer"
                  onClick={() => setIsCustomerSearchOpen(true)}
                />
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setIsCustomerSearchOpen(true)}
                >
                  Buscar
                </Button>
              </div>
            </Labeled>

            <Labeled label="Almacen responsable">
              <Select
                value={form.warehouse_id}
                onChange={(v) => onFormChange({ ...form, warehouse_id: v })}
                options={[
                  { value: "", label: "Seleccione almacen responsable" },
                  ...realWarehouses.map((warehouse) => ({
                    value: warehouse.id,
                    label: `${warehouse.code} - ${warehouse.name}`,
                  })),
                ]}
              />
            </Labeled>
          </div>

          <CustomerSearchDialog
            open={isCustomerSearchOpen}
            onOpenChange={setIsCustomerSearchOpen}
            onSelect={(customer) =>
              onFormChange({
                ...form,
                customer_id: customer.id,
                customer_name: customer.display_name,
              })
            }
          />

          <ProductSearchDialog
            open={isProductSearchOpen}
            onOpenChange={setIsProductSearchOpen}
            title="Seleccionar tipo de envase"
            onSelect={(product) => {
              setProductLabel(product.name);
              onFormChange({
                ...form,
                cylinder_type_id: product.id,
                cylinder_condition: product.condition_code,
              });
              setIsProductSearchOpen(false);
            }}
          />

          <div className="grid grid-cols-2 gap-3">
            <Labeled label="Tipo de envase">
              <div className="flex items-center gap-2">
                <Input
                  value={productLabel || form.cylinder_type_id}
                  readOnly
                  placeholder="Seleccione tipo de envase..."
                  className="flex-1 cursor-pointer"
                  onClick={() => setIsProductSearchOpen(true)}
                />
                <Button type="button" variant="outline" onClick={() => setIsProductSearchOpen(true)}>
                  Buscar
                </Button>
              </div>
            </Labeled>

            <Labeled label="Condición">
              <Select
                value={form.cylinder_condition}
                onChange={(v) => onFormChange({ ...form, cylinder_condition: v })}
                options={[
                  { value: "", label: "Sin condición" },
                  ...(conditionsQuery.data ?? []).map((item) => ({
                    value: item.code,
                    label: item.name,
                  })),
                ]}
              />
            </Labeled>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Labeled label="Fecha inicio">
              <Input type="date" value={form.start_date} onChange={field("start_date")} />
            </Labeled>

            <Labeled label="Fecha fin">
              <Input type="date" value={form.end_date} onChange={field("end_date")} />
            </Labeled>
          </div>

          <Labeled label="Tipo de renovación">
            <Select
              value={form.renewal_type}
              onChange={(v) => onFormChange({ ...form, renewal_type: v })}
              options={[
                { value: "", label: "Manual" },
                { value: "AUTO", label: "Automática" },
                { value: "NONE", label: "Sin renovación" },
              ]}
            />
          </Labeled>

          <div className="grid grid-cols-2 gap-3">
            <Labeled label="Cantidad">
              <Input type="number" value={form.quantity} onChange={field("quantity")} min="1" />
            </Labeled>
            <Labeled label="Precio unitario">
              <Input type="number" value={form.unit_price} onChange={field("unit_price")} step="0.01" min="0" />
            </Labeled>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Labeled label="Límite de espera de exceso (días)">
              <Input
                type="number"
                value={form.excess_wait_days}
                onChange={field("excess_wait_days")}
                min="0"
                placeholder="Días de tolerancia antes de auto-crear contrato"
              />
            </Labeled>
            <Labeled label="Auto-crear contrato al exceder">
              <Select
                value={form.auto_renew_on_excess ? "true" : "false"}
                onChange={(v) => onFormChange({ ...form, auto_renew_on_excess: v === "true" })}
                options={[
                  { value: "true", label: "Sí (automático)" },
                  { value: "false", label: "No (requiere acción manual)" },
                ]}
              />
            </Labeled>
          </div>
          <p className="text-xs text-muted-foreground">
            Si el cliente supera el cupo y el exceso persiste más del límite de espera, el sistema crea
            automáticamente un contrato nuevo por los envases excedentes.
          </p>

          <Labeled label="Archivo contrato">
            <div className="space-y-2">
              {form.contract_file_path ? (
                <div className="text-xs text-muted-foreground break-all">
                  Archivo actual: {form.contract_file_path}
                </div>
              ) : null}
              <FileUpload
                onFiles={(files) => onFileSelect(files[0] ?? null)}
                accept=".pdf,.png,.jpg,.jpeg"
                maxSize={10 * 1024 * 1024}
                className="p-4"
              />
            </div>
          </Labeled>

          {showNotes && (
            <Labeled label="Notas">
              <Input value={form.notes} onChange={field("notes")} placeholder="Notas opcionales..." />
            </Labeled>
          )}

          <Labeled label="Observaciones">
            <Input value={form.observations} onChange={field("observations")} placeholder="Observaciones del contrato..." />
          </Labeled>
        </div>

        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
            Cancelar
          </Button>
          <Button type="submit" disabled={isPending}>
            {isPending ? "Guardando..." : "Guardar"}
          </Button>
        </div>
      </form>
    </Dialog>
  );
}

function Labeled({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <div className="text-sm font-medium mb-1">{label}</div>
      {children}
    </div>
  );
}
