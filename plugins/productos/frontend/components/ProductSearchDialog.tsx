import { useState } from "react";

import { useQuery } from "../../../../apps/web/src/lib/react-query";
import { Alert } from "../../../../apps/web/src/shared/ui/alert";
import { DataTable } from "../../../../apps/web/src/shared/ui/data-table";
import { Dialog } from "../../../../apps/web/src/shared/ui/dialog";
import { Input } from "../../../../apps/web/src/shared/ui/input";
import { productosKeys, searchProducts } from "../api";
import type { ProductSearchItem } from "../types";

type ProductSearchDialogProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSelect: (product: ProductSearchItem) => void;
  title?: string;
};

export function ProductSearchDialog({
  open,
  onOpenChange,
  onSelect,
  title = "Seleccionar producto",
}: ProductSearchDialogProps) {
  const [query, setQuery] = useState("");
  const productsQuery = useQuery({
    queryKey: productosKeys.products.search(query),
    queryFn: () => searchProducts(query),
    enabled: open && query.trim().length > 0,
  });

  return (
    <Dialog
      open={open}
      title={title}
      description="Busca por SKU, nombre o código de barras."
      onClose={() => onOpenChange(false)}
      maxWidthClassName="max-w-4xl"
    >
      <div className="space-y-4">
        <Input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="GLP 10kg, SKU-001, 7750..."
        />
        {productsQuery.error ? (
          <Alert title="No se pudo buscar productos">{productsQuery.error.message}</Alert>
        ) : null}
        <DataTable
          columns={[
            { key: "sku", header: "SKU", render: (row) => row.sku },
            { key: "name", header: "Producto", render: (row) => row.name },
            { key: "brand", header: "Marca", render: (row) => row.brand_name ?? "-" },
            { key: "condition", header: "Condición", render: (row) => row.condition_code },
            { key: "status", header: "Activo", render: (row) => (row.is_active ? "Sí" : "No") },
          ]}
          rows={productsQuery.data ?? []}
          rowKey={(row) => row.id}
          emptyMessage={query.trim().length === 0 ? "Escribe algo para buscar." : "Sin resultados."}
        />
        {(productsQuery.data ?? []).length > 0 ? (
          <div className="grid gap-2">
            {(productsQuery.data ?? []).map((product) => (
              <button
                key={product.id}
                type="button"
                className="rounded-md border border-border bg-surface px-3 py-2 text-left text-sm text-foreground hover:border-ring"
                onClick={() => {
                  onSelect(product);
                  onOpenChange(false);
                }}
              >
                {product.sku} · {product.name}
              </button>
            ))}
          </div>
        ) : null}
      </div>
    </Dialog>
  );
}
