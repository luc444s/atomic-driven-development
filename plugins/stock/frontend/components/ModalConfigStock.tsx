import { FormEvent, useEffect, useState } from "react";

import { ProductSearchDialog, type ProductSearchDialogItem } from "../../../../apps/web/src/components/ProductSearchDialog";
import { useMutation, useQuery, useQueryClient } from "../../../../apps/web/src/lib/react-query";
import { Alert } from "../../../../apps/web/src/shared/ui/alert";
import { Button } from "../../../../apps/web/src/shared/ui/button";
import { Dialog } from "../../../../apps/web/src/shared/ui/dialog";
import { Input, Switch } from "../../../../apps/web/src/shared/ui/input";
import { Select } from "../../../../apps/web/src/shared/ui/select";
import { toast } from "../../../../apps/web/src/shared/ui/toast";
import { listWarehousesCatalog, stockKeys, upsertConfig } from "../api";
import type { LogisticsWarehouseOption, StockConfig } from "../types";

type ModalConfigStockProps = {
  open: boolean;
  onClose: () => void;
  onSaved?: (config: StockConfig) => void;
  initialProduct?: ProductSearchDialogItem | null;
  initialWarehouseId?: string | null;
  asPage?: boolean;
};

export function ModalConfigStock({
  open,
  onClose,
  onSaved,
  initialProduct,
  initialWarehouseId,
  asPage,
}: ModalConfigStockProps) {
  const queryClient = useQueryClient();
  const [showSearch, setShowSearch] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState<ProductSearchDialogItem | null>(
    initialProduct ?? null,
  );
  const [warehouseId, setWarehouseId] = useState(initialWarehouseId ?? "");
  const [minQuantity, setMinQuantity] = useState("0");
  const [maxQuantity, setMaxQuantity] = useState("");
  const [isActive, setIsActive] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const warehousesQuery = useQuery({
    queryKey: stockKeys.warehouses,
    queryFn: listWarehousesCatalog,
    enabled: open,
  });

  useEffect(() => {
    if (!open) {
      setSelectedProduct(initialProduct ?? null);
      setWarehouseId(initialWarehouseId ?? "");
      setMinQuantity("0");
      setMaxQuantity("");
      setIsActive(true);
      setError(null);
    }
  }, [open, initialProduct, initialWarehouseId]);

  const configMutation = useMutation({
    mutationFn: async () => {
      if (!selectedProduct) {
        throw new Error("Selecciona un producto");
      }
      if (!warehouseId) {
        throw new Error("Selecciona un almacén");
      }
      return upsertConfig({
        product_id: selectedProduct.id,
        warehouse_id: warehouseId,
        min_quantity: Number(minQuantity),
        max_quantity: maxQuantity.trim() ? Number(maxQuantity) : null,
        is_active: isActive,
      });
    },
    onSuccess: async (config) => {
      await queryClient.invalidateQueries({ queryKey: stockKeys.all });
      toast.success("Configuración de stock guardada");
      onSaved?.(config);
      onClose();
    },
  });

  async function submitForm(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    try {
      await configMutation.mutateAsync();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "No se pudo guardar la configuración.");
    }
  }

  const formContent = (
    <form className="space-y-4" onSubmit={submitForm}>
      {error ? <Alert title="No se pudo guardar la configuración">{error}</Alert> : null}
      {warehousesQuery.error ? (
        <Alert title="No se pudo cargar almacenes">{warehousesQuery.error.message}</Alert>
      ) : null}
      <div className="grid gap-4 md:grid-cols-2">
        <label className="block space-y-2 text-sm text-foreground">
          <span>Producto</span>
          <div className="space-y-2">
            <div className="rounded-md border border-border bg-surface px-3 py-2 text-sm text-foreground">
              {selectedProduct ? `${selectedProduct.sku} · ${selectedProduct.name}` : "Sin seleccionar"}
            </div>
            <Button type="button" variant="secondary" onClick={() => setShowSearch(true)}>
              Buscar producto
            </Button>
          </div>
        </label>
        <label className="block space-y-2 text-sm text-foreground">
          <span>Almacén</span>
          <Select
            value={warehouseId}
            onChange={setWarehouseId}
            placeholder="Selecciona un almacén"
            options={[
              { value: "", label: "Selecciona un almacén" },
              ...(warehousesQuery.data ?? []).map((warehouse: LogisticsWarehouseOption) => ({
                value: warehouse.id,
                label: `${warehouse.code} · ${warehouse.name}`,
              })),
            ]}
          />
        </label>
      </div>
      <div className="grid gap-4 md:grid-cols-3">
        <label className="block space-y-2 text-sm text-foreground">
          <span>Mínimo</span>
          <Input type="number" step="0.001" value={minQuantity} onChange={(event) => setMinQuantity(event.target.value)} />
        </label>
        <label className="block space-y-2 text-sm text-foreground">
          <span>Máximo</span>
          <Input type="number" step="0.001" value={maxQuantity} onChange={(event) => setMaxQuantity(event.target.value)} />
        </label>
        <div className="flex items-center gap-3 rounded-md border border-border bg-surface px-3 py-2 text-sm text-foreground">
          <Switch checked={isActive} onChange={(event) => setIsActive(event.target.checked)} />
          <span>Configuración activa</span>
        </div>
      </div>
      <div className="flex justify-end gap-2">
        <Button type="button" variant="secondary" onClick={onClose}>
          Cancelar
        </Button>
        <Button type="submit">Guardar configuración</Button>
      </div>
      <ProductSearchDialog
        open={showSearch}
        onOpenChange={setShowSearch}
        onSelect={setSelectedProduct}
      />
    </form>
  );

  if (asPage) {
    return <div className="space-y-6">{formContent}</div>;
  }

  return (
    <Dialog
      open={open}
      title="Configurar mínimos y máximos"
      description="Define umbrales operativos por producto y almacén."
      onClose={onClose}
      maxWidthClassName="max-w-4xl"
    >
      {formContent}
    </Dialog>
  );
}
