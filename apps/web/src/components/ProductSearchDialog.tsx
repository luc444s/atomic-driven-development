import { useState } from "react";

import { useQuery } from "../lib/react-query";
import { apiRequest } from "../shared/api/client";
import { Alert } from "../shared/ui/alert";
import { DataTable } from "../shared/ui/data-table";
import { Dialog } from "../shared/ui/dialog";
import { Input } from "../shared/ui/input";

export type ProductSearchDialogItem = {
  id: string;
  sku: string;
  name: string;
  brand_name: string | null;
  condition_code: string;
  is_active: boolean;
};

type ProductSearchDialogProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSelect: (product: ProductSearchDialogItem) => void;
  title?: string;
};

function buildQuery(query: string) {
  const search = new URLSearchParams();
  search.set("q", query);
  search.set("limit", "20");
  return search.toString();
}

async function searchProducts(query: string): Promise<ProductSearchDialogItem[]> {
  return apiRequest(`/api/v1/plugins/productos/products/search?${buildQuery(query)}`);
}

export function ProductSearchDialog({
  open,
  onOpenChange,
  onSelect,
  title = "Seleccionar producto",
}: ProductSearchDialogProps) {
  const [query, setQuery] = useState("");
  const productsQuery = useQuery({
    queryKey: ["shared", "product-search", query],
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
            {
              key: "select",
              header: "Acción",
              render: (row) => (
                <button
                  type="button"
                  className="rounded-md border border-slate-700 px-3 py-1.5 text-sm text-slate-200 hover:border-cyan-500"
                  onClick={() => {
                    onSelect(row);
                    onOpenChange(false);
                  }}
                >
                  Seleccionar
                </button>
              ),
            },
          ]}
          rows={productsQuery.data ?? []}
          rowKey={(row) => row.id}
          emptyMessage={query.trim().length === 0 ? "Escribe algo para buscar." : "Sin resultados."}
        />
      </div>
    </Dialog>
  );
}
