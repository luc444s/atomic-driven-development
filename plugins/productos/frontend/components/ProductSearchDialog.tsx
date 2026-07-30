import { SearchDialog } from "../../../../apps/web/src/shared/ui/search-dialog";
import { searchProducts } from "../api";
import type { ProductSearchItem } from "../types";

type ProductSearchDialogProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSelect: (product: ProductSearchItem) => void;
  title?: string;
  fetchFn?: (query: string) => Promise<ProductSearchItem[]>;
};

export function ProductSearchDialog({
  open,
  onOpenChange,
  onSelect,
  title = "Seleccionar producto",
  fetchFn = searchProducts,
}: ProductSearchDialogProps) {
  return (
    <SearchDialog<ProductSearchItem>
      open={open}
      onOpenChange={onOpenChange}
      title={title}
      placeholder="GLP 10kg, SKU-001, 7750..."
      fetchFn={fetchFn}
      onSelect={onSelect}
      getRowId={(item) => item.id}
      columns={[
        { key: "sku", header: "SKU", render: (row) => row.sku },
        { key: "name", header: "Producto", render: (row) => row.name },
        { key: "brand", header: "Marca", render: (row) => row.brand_name ?? "-" },
        { key: "condition", header: "Condición", render: (row) => row.condition_code },
        { key: "status", header: "Activo", render: (row) => (row.is_active ? "Sí" : "No") },
      ]}
    />
  );
}
