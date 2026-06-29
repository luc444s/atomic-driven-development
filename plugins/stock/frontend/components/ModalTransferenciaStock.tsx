import { FormEvent, useEffect, useState } from "react";

import { ProductSearchDialog, type ProductSearchDialogItem } from "../../../../apps/web/src/components/ProductSearchDialog";
import { useMutation, useQuery, useQueryClient } from "../../../../apps/web/src/lib/react-query";
import { Alert } from "../../../../apps/web/src/shared/ui/alert";
import { Button } from "../../../../apps/web/src/shared/ui/button";
import { Dialog } from "../../../../apps/web/src/shared/ui/dialog";
import { Input } from "../../../../apps/web/src/shared/ui/input";
import { listWarehousesCatalog, stockKeys, transferStock } from "../api";
import type { LogisticsWarehouseOption, StockTransferResult } from "../types";

const selectClassName =
  "w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-50 outline-none transition focus:border-cyan-500";

type ModalTransferenciaStockProps = {
  open: boolean;
  onClose: () => void;
  onSaved?: (result: StockTransferResult) => void;
  initialProduct?: ProductSearchDialogItem | null;
  initialWarehouseId?: string | null;
  asPage?: boolean;
};

export function ModalTransferenciaStock({
  open,
  onClose,
  onSaved,
  initialProduct,
  initialWarehouseId,
  asPage,
}: ModalTransferenciaStockProps) {
  const queryClient = useQueryClient();
  const [showSearch, setShowSearch] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState<ProductSearchDialogItem | null>(
    initialProduct ?? null,
  );
  const [fromWarehouseId, setFromWarehouseId] = useState(initialWarehouseId ?? "");
  const [toWarehouseId, setToWarehouseId] = useState("");
  const [quantity, setQuantity] = useState("");
  const [notes, setNotes] = useState("");
  const [error, setError] = useState<string | null>(null);

  const warehousesQuery = useQuery({
    queryKey: stockKeys.warehouses,
    queryFn: listWarehousesCatalog,
    enabled: open,
  });

  useEffect(() => {
    if (!open) {
      setSelectedProduct(initialProduct ?? null);
      setFromWarehouseId(initialWarehouseId ?? "");
      setToWarehouseId("");
      setQuantity("");
      setNotes("");
      setError(null);
    }
  }, [open, initialProduct, initialWarehouseId]);

  const transferMutation = useMutation({
    mutationFn: async () => {
      if (!selectedProduct) {
        throw new Error("Selecciona un producto");
      }
      if (!fromWarehouseId || !toWarehouseId) {
        throw new Error("Selecciona almacenes origen y destino");
      }
      return transferStock({
        product_id: selectedProduct.id,
        from_warehouse_id: fromWarehouseId,
        to_warehouse_id: toWarehouseId,
        quantity: Number(quantity),
        notes: notes.trim() || null,
      });
    },
    onSuccess: async (result) => {
      await queryClient.invalidateQueries({ queryKey: stockKeys.all });
      onSaved?.(result);
      onClose();
    },
  });

  async function submitForm(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    try {
      await transferMutation.mutateAsync();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "No se pudo registrar la transferencia.");
    }
  }

  const formContent = (
    <form className="space-y-4" onSubmit={submitForm}>
      {error ? <Alert title="No se pudo registrar la transferencia">{error}</Alert> : null}
      {warehousesQuery.error ? (
        <Alert title="No se pudo cargar almacenes">{warehousesQuery.error.message}</Alert>
      ) : null}
      <div className="grid gap-4 md:grid-cols-2">
        <label className="block space-y-2 text-sm text-slate-300">
          <span>Producto</span>
          <div className="space-y-2">
            <div className="rounded-md border border-slate-800 bg-slate-950 px-3 py-2 text-sm text-slate-200">
              {selectedProduct ? `${selectedProduct.sku} · ${selectedProduct.name}` : "Sin seleccionar"}
            </div>
            <Button type="button" variant="secondary" onClick={() => setShowSearch(true)}>
              Buscar producto
            </Button>
          </div>
        </label>
        <label className="block space-y-2 text-sm text-slate-300">
          <span>Cantidad</span>
          <Input
            type="number"
            step="0.001"
            value={quantity}
            onChange={(event) => setQuantity(event.target.value)}
            placeholder="20"
          />
        </label>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <label className="block space-y-2 text-sm text-slate-300">
          <span>Almacén origen</span>
          <select className={selectClassName} value={fromWarehouseId} onChange={(event) => setFromWarehouseId(event.target.value)}>
            <option value="">Selecciona un almacén</option>
            {(warehousesQuery.data ?? []).map((warehouse: LogisticsWarehouseOption) => (
              <option key={warehouse.id} value={warehouse.id}>
                {warehouse.code} · {warehouse.name}
              </option>
            ))}
          </select>
        </label>
        <label className="block space-y-2 text-sm text-slate-300">
          <span>Almacén destino</span>
          <select className={selectClassName} value={toWarehouseId} onChange={(event) => setToWarehouseId(event.target.value)}>
            <option value="">Selecciona un almacén</option>
            {(warehousesQuery.data ?? []).map((warehouse: LogisticsWarehouseOption) => (
              <option key={warehouse.id} value={warehouse.id}>
                {warehouse.code} · {warehouse.name}
              </option>
            ))}
          </select>
        </label>
      </div>
      <label className="block space-y-2 text-sm text-slate-300">
        <span>Notas</span>
        <textarea
          className={`${selectClassName} min-h-24`}
          value={notes}
          onChange={(event) => setNotes(event.target.value)}
          placeholder="Traslado a almacén de reparto"
        />
      </label>
      <div className="flex justify-end gap-2">
        <Button type="button" variant="secondary" onClick={onClose}>
          Cancelar
        </Button>
        <Button type="submit">Guardar transferencia</Button>
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
      title="Transferir stock"
      description="Mueve existencias entre almacenes registrando salida y entrada en el ledger."
      onClose={onClose}
      maxWidthClassName="max-w-4xl"
    >
      {formContent}
    </Dialog>
  );
}
