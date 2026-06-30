import { FormEvent, useEffect, useState } from "react";

import { ProductSearchDialog, type ProductSearchDialogItem } from "../../../../apps/web/src/components/ProductSearchDialog";
import { useMutation, useQuery, useQueryClient } from "../../../../apps/web/src/lib/react-query";
import { Alert } from "../../../../apps/web/src/shared/ui/alert";
import { Button } from "../../../../apps/web/src/shared/ui/button";
import { Dialog } from "../../../../apps/web/src/shared/ui/dialog";
import { Input } from "../../../../apps/web/src/shared/ui/input";
import { adjustStock, listWarehousesCatalog, stockKeys } from "../api";
import type { LogisticsWarehouseOption, StockBalanceItem } from "../types";

const selectClassName =
  "w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-slate-50 outline-none transition focus:border-ring";

type ModalAjusteStockProps = {
  open: boolean;
  onClose: () => void;
  onSaved?: (balance: StockBalanceItem) => void;
  initialProduct?: ProductSearchDialogItem | null;
  initialWarehouseId?: string | null;
  asPage?: boolean;
};

export function ModalAjusteStock({
  open,
  onClose,
  onSaved,
  initialProduct,
  initialWarehouseId,
  asPage,
}: ModalAjusteStockProps) {
  const queryClient = useQueryClient();
  const [showSearch, setShowSearch] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState<ProductSearchDialogItem | null>(
    initialProduct ?? null,
  );
  const [warehouseId, setWarehouseId] = useState(initialWarehouseId ?? "");
  const [quantity, setQuantity] = useState("");
  const [reason, setReason] = useState("");
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
      setQuantity("");
      setReason("");
      setError(null);
    }
  }, [open, initialProduct, initialWarehouseId]);

  useEffect(() => {
    if (open) {
      setSelectedProduct(initialProduct ?? null);
      setWarehouseId(initialWarehouseId ?? "");
    }
  }, [open, initialProduct, initialWarehouseId]);

  const adjustMutation = useMutation({
    mutationFn: async () => {
      if (!selectedProduct) {
        throw new Error("Selecciona un producto");
      }
      if (!warehouseId) {
        throw new Error("Selecciona un almacén");
      }
      if (!quantity.trim()) {
        throw new Error("Ingresa una cantidad");
      }
      return adjustStock({
        product_id: selectedProduct.id,
        warehouse_id: warehouseId,
        quantity: Number(quantity),
        reason: reason.trim() || null,
      });
    },
    onSuccess: async (balance) => {
      await queryClient.invalidateQueries({ queryKey: stockKeys.all });
      onSaved?.(balance);
      onClose();
    },
  });

  async function submitForm(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    try {
      await adjustMutation.mutateAsync();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "No se pudo registrar el ajuste.");
    }
  }

  const formContent = (
    <form className="space-y-4" onSubmit={submitForm}>
      {error ? <Alert title="No se pudo registrar el ajuste">{error}</Alert> : null}
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
          <select className={selectClassName} value={warehouseId} onChange={(event) => setWarehouseId(event.target.value)}>
            <option value="">Selecciona un almacén</option>
            {(warehousesQuery.data ?? []).map((warehouse: LogisticsWarehouseOption) => (
              <option key={warehouse.id} value={warehouse.id}>
                {warehouse.code} · {warehouse.name}
              </option>
            ))}
          </select>
        </label>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <label className="block space-y-2 text-sm text-foreground">
          <span>Cantidad</span>
          <Input
            type="number"
            step="0.001"
            value={quantity}
            onChange={(event) => setQuantity(event.target.value)}
            placeholder="10 o -2"
          />
        </label>
        <label className="block space-y-2 text-sm text-foreground">
          <span>Motivo</span>
          <textarea
            className={`${selectClassName} min-h-24`}
            value={reason}
            onChange={(event) => setReason(event.target.value)}
            placeholder="Ajuste por conteo físico"
          />
        </label>
      </div>
      <div className="flex justify-end gap-2">
        <Button type="button" variant="secondary" onClick={onClose}>
          Cancelar
        </Button>
        <Button type="submit">Guardar ajuste</Button>
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
      title="Ajustar stock"
      description="Registra ajustes manuales positivos o negativos sobre el ledger."
      onClose={onClose}
      maxWidthClassName="max-w-4xl"
    >
      {formContent}
    </Dialog>
  );
}
