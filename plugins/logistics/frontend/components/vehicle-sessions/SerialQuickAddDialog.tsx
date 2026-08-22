import { useRef, useState } from "react";

import { useMutation, useQuery } from "../../../../../apps/web/src/lib/react-query";
import { Alert } from "@systutor/shell/ui/alert";
import { Button } from "@systutor/shell/ui/button";
import {
  Combobox,
  type ComboboxOption,
} from "@systutor/shell/ui/combobox";
import { Dialog } from "@systutor/shell/ui/dialog";

import {
  searchLoadSerials,
  selectLoadSerial,
  type LoadSerialAssignment,
} from "../../api";

export type InferredSerialSelection = {
  product_id: string;
  product_name: string;
  serial: string;
};

type Props = {
  open: boolean;
  sessionId: string;
  sourceWarehouseId?: string | null;
  onClose: () => void;
  onSelected: (selection: InferredSerialSelection) => void;
};

export function SerialQuickAddDialog({
  open,
  sessionId,
  sourceWarehouseId,
  onClose,
  onSelected,
}: Props) {
  const autoSubmittedQueryRef = useRef("");
  const [searchValue, setSearchValue] = useState("");
  const [manualSelected, setManualSelected] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [lastSelection, setLastSelection] = useState<InferredSerialSelection | null>(null);

  const searchQuery = useQuery({
    queryKey: ["logistics", "load-serials", "quick-search", sessionId, searchValue],
    queryFn: () =>
      searchLoadSerials(sessionId, {
        product_id: null,
        source_warehouse_id: sourceWarehouseId,
        selection_context: "LOAD_PLAN",
        query: searchValue,
      }),
    enabled: open && searchValue.trim().length >= 2,
  });

  const selectMutation = useMutation({
    mutationFn: (serial: string) =>
      selectLoadSerial(sessionId, {
        product_id: null,
        source_warehouse_id: sourceWarehouseId,
        selection_context: "LOAD_PLAN",
        serial,
      }),
    onSuccess: (assignment: LoadSerialAssignment) => {
      setError(null);
      setManualSelected("");
      setSearchValue("");
      const nameCandidate = (searchQuery.data ?? []).find(
        (result) => result.serial === assignment.cylinder_serial
      );
      const selection: InferredSerialSelection = {
        product_id: assignment.product_id,
        product_name: nameCandidate?.product_name ?? assignment.product_id,
        serial: assignment.cylinder_serial,
      };
      setLastSelection(selection);
      onSelected(selection);
    },
    onError: (cause) => {
      const message = cause instanceof Error ? cause.message : "No se pudo seleccionar el serial";
      setError(message);
    },
  });

  function finish() {
    onClose();
  }

  const manualOptions: ComboboxOption[] = (searchQuery.data ?? [])
    .filter((result) => result.availability_status === "AVAILABLE")
    .map((result) => ({
      value: result.serial,
      label: result.product_name
        ? `${result.serial} · ${result.product_name}`
        : result.serial,
      keywords: [result.serial, result.product_name ?? "", result.context_label ?? ""],
    }));

  return (
    <Dialog
      open={open}
      onClose={onClose}
      title="Agregar serial"
      description="Escanea o escribe un serial. El producto se infiere del envase."
      maxWidthClassName="max-w-2xl"
    >
      <div className="space-y-4">
        <div className="space-y-2">
          <p className="text-sm font-medium text-foreground">Serial del envase</p>
          <Combobox
            value={manualSelected}
            onChange={(value) => {
              setManualSelected(value);
              void selectMutation.mutateAsync(value);
            }}
            options={manualOptions}
            placeholder="Escanea o escribe serial"
            searchPlaceholder="Escanea o escribe serial"
            emptyMessage={
              searchValue.trim().length < 2 ? "Escribe al menos 2 caracteres." : "Sin coincidencias."
            }
            searchValue={searchValue}
            onSearchValueChange={(value) => setSearchValue(value.toUpperCase())}
            onSubmitQuery={(value) => void selectMutation.mutateAsync(value)}
            variant="input"
            minSearchLength={2}
          />
          <div className="flex justify-end">
            <Button
              type="button"
              disabled={selectMutation.isPending || searchValue.trim().length === 0}
              onClick={() => void selectMutation.mutateAsync(searchValue)}
            >
              {selectMutation.isPending ? "Agregando..." : "Agregar"}
            </Button>
          </div>
        </div>

        {error ? <Alert title="Serial no agregado">{error}</Alert> : null}

        {lastSelection ? (
          <div className="rounded-xl bg-muted/35 px-4 py-3 text-sm text-foreground">
            Agregado: {lastSelection.serial} · {lastSelection.product_name}
            <div className="mt-3 flex justify-end">
              <Button type="button" onClick={finish}>
                Cerrar
              </Button>
            </div>
          </div>
        ) : null}
      </div>
    </Dialog>
  );
}