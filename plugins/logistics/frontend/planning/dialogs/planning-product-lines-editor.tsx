import { useState } from "react";
import { Button } from "@systutor/shell/ui/button";
import {
  Combobox,
  type ComboboxOption,
} from "@systutor/shell/ui/combobox";
import { Input } from "@systutor/shell/ui/input";
import type { PlanningReservationProductLine } from "./planning-load-summary";

type ResolvedProduct = {
  product_id: string;
  product_name: string;
  sku: string;
  adr_required: boolean;
  unit_weight_kg: number | null;
};

export type PlanningProductCatalogItem = {
  id: string;
  name: string;
  sku: string;
  brand_name: string | null;
};

type Props = {
  lines: PlanningReservationProductLine[];
  setLines: (updater: (current: PlanningReservationProductLine[]) => PlanningReservationProductLine[]) => void;
  productOptions: ComboboxOption[];
  availableByProductId: Map<string, number>;
  disabled?: boolean;
  resolveProduct: (productId: string) => Promise<ResolvedProduct>;
  onAddLine: () => void;
};

export function PlanningProductLinesEditor({
  lines,
  setLines,
  productOptions,
  availableByProductId,
  disabled,
  resolveProduct,
  onAddLine,
}: Props) {
  const [resolvingIndex, setResolvingIndex] = useState<number | null>(null);

  async function handleSelectProduct(index: number, productId: string) {
    setResolvingIndex(index);
    try {
      const product = await resolveProduct(productId);
      setLines((current) =>
        current.map((line, lineIndex) =>
          lineIndex === index
            ? {
                ...line,
                product_id: product.product_id,
                product_name: product.product_name,
                sku: product.sku,
                adr_required: product.adr_required,
                unit_weight_kg: product.unit_weight_kg,
              }
            : line,
        ),
      );
    } finally {
      setResolvingIndex(null);
    }
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h3 className="text-sm font-medium text-foreground">Productos esperados</h3>
          <p className="text-xs text-muted-foreground">Selecciona productos reales y cantidades. El peso total se calcula automáticamente.</p>
        </div>
        <Button type="button" variant="secondary" onClick={onAddLine}>Agregar línea</Button>
      </div>

      <div className="space-y-2">
        {lines.map((line, index) => {
          return (
            <div key={`${line.product_id || "line"}-${index}`} className="grid gap-2 rounded-xl border border-border/70 p-3 md:grid-cols-[minmax(0,1fr)_110px_auto]">
              <div className="space-y-1">
                <label className="text-xs text-muted-foreground">Producto</label>
                <Combobox
                  value={line.product_id}
                  onChange={(value) => void handleSelectProduct(index, value)}
                  options={productOptions}
                  placeholder="Seleccionar producto"
                  searchPlaceholder="Buscar producto..."
                  disabled={disabled}
                />
              </div>

              <div className="space-y-1">
                <label className="text-xs text-muted-foreground">Cantidad</label>
                <Input
                  value={line.quantity}
                  disabled={disabled}
                  onChange={(event) => {
                    const value = event.target.value;
                    setLines((current) =>
                      current.map((item, itemIndex) =>
                        itemIndex === index ? { ...item, quantity: value } : item,
                      ),
                    );
                  }}
                />
              </div>

              <div className="space-y-1">
                <label className="text-xs text-transparent">Acción</label>
                <div className="flex justify-end gap-2">
                <Button
                  type="button"
                  variant="secondary"
                  disabled={disabled}
                  onClick={() =>
                    setLines((current) =>
                      current.length > 1
                        ? current.filter((_, itemIndex) => itemIndex !== index)
                        : current,
                    )
                  }
                >
                  Quitar
                </Button>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
