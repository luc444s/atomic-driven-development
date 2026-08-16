import { useState, useEffect, useRef, useCallback } from "react";
import { apiRequest } from "@systutor/shell/api/client";
import { Combobox } from "@systutor/shell/ui/combobox";
import { Input } from "@systutor/shell/ui/input";
import type { ComboboxOption } from "@systutor/shell/ui/combobox";

interface ProductSearchItem {
  id: string;
  sku: string;
  name: string;
  brand_name: string | null;
}

export interface ProductLine {
  key: string;
  productId: string;
  productName: string;
  quantity: number;
}

export interface ProductLinesEditorProps {
  value: ProductLine[];
  onChange: (lines: ProductLine[]) => void;
}

let lineCounter = 0;
function nextKey(): string {
  return `line-${++lineCounter}-${Date.now()}`;
}

function emptyLine(): ProductLine {
  return { key: nextKey(), productId: "", productName: "", quantity: 1 };
}

export function ProductLinesEditor({ value, onChange }: ProductLinesEditorProps) {
  return (
    <label className="block space-y-2 text-sm text-foreground">
      <span>Items</span>
      <div className="space-y-2">
        {value.map((line, index) => (
          <ProductLineRow
            key={line.key}
            line={line}
            onChange={(updated) => {
              const next = [...value];
              next[index] = updated;
              onChange(next);
            }}
            onRemove={() => {
              if (value.length <= 1) return;
              onChange(value.filter((_, i) => i !== index));
            }}
            canRemove={value.length > 1}
          />
        ))}
      </div>
      <button
        type="button"
        onClick={() => onChange([...value, emptyLine()])}
        className="text-sm text-primary hover:text-primary/80 transition"
      >
        + Agregar item
      </button>
    </label>
  );
}

function ProductLineRow({
  line,
  onChange,
  onRemove,
  canRemove,
}: {
  line: ProductLine;
  onChange: (line: ProductLine) => void;
  onRemove: () => void;
  canRemove: boolean;
}) {
  const [searchInput, setSearchInput] = useState(line.productName);
  const [options, setOptions] = useState<ComboboxOption[]>([]);
  const [selectedLabel, setSelectedLabel] = useState(line.productName);
  const [isLoading, setIsLoading] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout>>();

  const search = useCallback(async (query: string) => {
    if (query.length < 1) {
      setOptions([]);
      return;
    }
    setIsLoading(true);
    try {
      const result = await apiRequest<ProductSearchItem[]>(
        `/api/v1/plugins/productos/products/search?q=${encodeURIComponent(query)}&limit=20`,
      );
      setOptions(
        result.map((p) => ({
          value: p.id,
          label: p.name,
          keywords: [p.sku, p.brand_name ?? ""],
        })),
      );
    } catch {
      setOptions([]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      search(searchInput);
    }, 300);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [searchInput, search]);

  return (
    <div className="flex gap-2 items-start">
      <div className="flex-1 min-w-0">
        <Combobox
          value={line.productId}
          onChange={(productId) => {
            const option = options.find((o) => o.value === productId);
            const label = option?.label ?? "";
            setSelectedLabel(label);
            onChange({ ...line, productId, productName: label });
          }}
          options={options}
          placeholder="Buscar producto..."
          searchPlaceholder="Escribe para buscar..."
          searchValue={searchInput}
          onSearchValueChange={setSearchInput}
          emptyMessage={isLoading ? "Buscando..." : "Sin resultados."}
          variant="button"
          minSearchLength={0}
          selectedLabel={selectedLabel}
        />
      </div>
      <div className="w-20 shrink-0">
        <Input
          type="number"
          min={1}
          value={line.quantity}
          onChange={(e) => {
            const qty = parseInt(e.target.value, 10);
            onChange({ ...line, quantity: isNaN(qty) || qty < 1 ? 1 : qty });
          }}
          className="text-sm h-9"
        />
      </div>
      <button
        type="button"
        onClick={onRemove}
        disabled={!canRemove}
        className="shrink-0 text-muted-foreground hover:text-red-400 disabled:opacity-30 disabled:cursor-not-allowed text-sm px-1 py-2"
        title="Eliminar item"
      >
        ✕
      </button>
    </div>
  );
}
