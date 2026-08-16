import { useState, useEffect, useRef, useCallback } from "react";
import { apiRequest } from "@systutor/shell/api/client";
import { Combobox } from "@systutor/shell/ui/combobox";
import { Button } from "@systutor/shell/ui/button";
import { Input } from "@systutor/shell/ui/input";
import { Alert } from "@systutor/shell/ui/alert";
import type { ComboboxOption } from "@systutor/shell/ui/combobox";

interface CustomerSearchItem {
  id: string;
  legal_name: string;
  commercial_name: string | null;
  display_name: string;
  document_type_code: string | null;
  document_number: string | null;
}

const DOC_TYPE_PRESETS = [
  { value: "RUC", label: "RUC" },
  { value: "DNI", label: "DNI" },
  { value: "CE", label: "CE" },
];

export interface CustomerSelectProps {
  value: string;
  onChange: (customerId: string, customerName: string) => void;
  placeholder?: string;
}

export function CustomerSelect({
  value,
  onChange,
  placeholder = "Buscar cliente...",
}: CustomerSelectProps) {
  const [searchInput, setSearchInput] = useState("");
  const [options, setOptions] = useState<ComboboxOption[]>([]);
  const [selectedLabel, setSelectedLabel] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout>>();

  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState("");
  const [newDocType, setNewDocType] = useState("RUC");
  const [newDocNumber, setNewDocNumber] = useState("");
  const [createError, setCreateError] = useState<string | null>(null);
  const [isCreating, setIsCreating] = useState(false);

  const search = useCallback(async (query: string) => {
    if (query.length < 1) {
      setOptions([]);
      return;
    }
    setIsLoading(true);
    try {
      const result = await apiRequest<CustomerSearchItem[]>(
        `/api/v1/plugins/crm/customers/search?query=${encodeURIComponent(query)}&limit=20`,
      );
      setOptions(
        result.map((c) => ({
          value: c.id,
          label: c.display_name || c.legal_name,
          keywords: [c.legal_name, c.commercial_name ?? "", c.document_number ?? ""],
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

  const handleCreateCustomer = useCallback(async () => {
    if (!newName.trim() || !newDocNumber.trim()) return;
    setIsCreating(true);
    setCreateError(null);
    try {
      const result = await apiRequest<{ id: string; legal_name: string; display_name?: string }>(
        "/api/v1/plugins/crm/customers",
        {
          method: "POST",
          body: JSON.stringify({
            legal_name: newName.trim(),
            document_type_code: newDocType,
            document_number: newDocNumber.trim(),
            country_code: "PER",
          }),
        },
      );
      const label = result.display_name || result.legal_name;
      setSelectedLabel(label);
      onChange(result.id, label);
      setShowCreate(false);
      setNewName("");
      setNewDocNumber("");
    } catch (e) {
      setCreateError(e instanceof Error ? e.message : "Error al crear cliente");
    } finally {
      setIsCreating(false);
    }
  }, [newName, newDocType, newDocNumber, onChange]);

  const handleCancelCreate = useCallback(() => {
    setShowCreate(false);
    setNewName("");
    setNewDocNumber("");
    setCreateError(null);
  }, []);

  return (
    <div className="space-y-2">
      {!showCreate ? (
        <label className="block space-y-2 text-sm text-foreground">
          <span>Cliente</span>
          <Combobox
            value={value}
            onChange={(id) => {
              const option = options.find((o) => o.value === id);
              const label = option?.label ?? "";
              setSelectedLabel(label);
              onChange(id, label);
            }}
            options={options}
            placeholder={placeholder}
            searchPlaceholder="Escribe para buscar cliente..."
            searchValue={searchInput}
            onSearchValueChange={setSearchInput}
            emptyMessage={
              isLoading
                ? "Buscando..."
                : searchInput.length >= 1 ? (
                    <span
                      onMouseDown={(e) => {
                        e.preventDefault();
                        setShowCreate(true);
                        setNewName(searchInput);
                      }}
                      className="cursor-pointer hover:text-primary transition"
                    >
                      Sin resultados. Crear cliente &ldquo;{searchInput}&rdquo;
                    </span>
                  ) : (
                    "Escribe para buscar..."
                  )
            }
            variant="button"
            minSearchLength={0}
            selectedLabel={selectedLabel}
          />
        </label>
      ) : (
        <div className="rounded-md border border-border p-3 space-y-3">
          <p className="text-sm font-medium text-foreground">Nuevo cliente</p>

          {createError && <Alert title="Error">{createError}</Alert>}

          <label className="block space-y-2 text-sm text-foreground">
            <span>Razón social / nombre</span>
            <Input
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              placeholder="Nombre del cliente"
            />
          </label>

          <div className="grid gap-3 md:grid-cols-2">
            <label className="block space-y-2 text-sm text-foreground">
              <span>Tipo de documento</span>
              <select
                value={newDocType}
                onChange={(e) => setNewDocType(e.target.value)}
                className="w-full rounded-md border border-input bg-surface px-3 py-2 text-sm text-foreground outline-none transition focus:border-ring focus:ring-1 focus:ring-ring h-9"
              >
                {DOC_TYPE_PRESETS.map((d) => (
                  <option key={d.value} value={d.value}>{d.label}</option>
                ))}
              </select>
            </label>

            <label className="block space-y-2 text-sm text-foreground">
              <span>Nro. de documento</span>
              <Input
                value={newDocNumber}
                onChange={(e) => setNewDocNumber(e.target.value)}
                placeholder="Ej: 20123456789"
              />
            </label>
          </div>

          <div className="flex justify-end gap-3">
            <Button type="button" variant="secondary" onClick={handleCancelCreate}>
              Cancelar
            </Button>
            <Button
              type="button"
              onClick={handleCreateCustomer}
              disabled={!newName.trim() || !newDocNumber.trim() || isCreating}
            >
              {isCreating ? "Creando..." : "Crear cliente"}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
