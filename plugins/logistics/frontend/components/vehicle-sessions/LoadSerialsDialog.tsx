import { useEffect, useRef, useState } from "react";

import { useMutation, useQuery, useQueryClient } from "../../../../../apps/web/src/lib/react-query";
import { Alert } from "../../../../../apps/web/src/shared/ui/alert";
import { Button } from "../../../../../apps/web/src/shared/ui/button";
import {
  Combobox,
  type ComboboxOption,
} from "../../../../../apps/web/src/shared/ui/combobox";
import { Dialog } from "../../../../../apps/web/src/shared/ui/dialog";
import {
  createCylinder,
  listSelectedLoadSerials,
  logisticsKeys,
  type LoadSerialSelectionContext,
  releaseLoadSerial,
  searchLoadSerials,
  selectLoadSerial,
  toggleDeliverySelection,
  type LoadSerialAssignment,
} from "../../api";
import { CreateCylinderDialog } from "../../cylinders/dialogs/create-cylinder-dialog";
import {
  EMPTY_CYLINDER_CREATE_META,
  EMPTY_CYLINDER_FORM,
  type CylinderCreateMetaState,
  type CylinderFormState,
} from "../../cylinders/forms/cylinder-form-state";
import { formatLoadSerialAssignmentStatus } from "./jornada-labels";

export type SerialSelectionItem = {
  product_id: string;
  product_name: string;
  planned_quantity: string;
  source_warehouse_id?: string | null;
};

type Props = {
  open: boolean;
  sessionId: string;
  item: SerialSelectionItem | null;
  selectionContext?: LoadSerialSelectionContext;
  allowCreateFallback?: boolean;
  onClose: () => void;
  onSelectionCountChange: (productId: string, selectedCount: number) => void;
};

export function LoadSerialsDialog({
  open,
  sessionId,
  item,
  selectionContext = "LOAD_PLAN",
  allowCreateFallback = true,
  onClose,
  onSelectionCountChange,
}: Props) {
  const queryClient = useQueryClient();
  const autoSubmittedQueryRef = useRef("");
  const [manualSearchValue, setManualSearchValue] = useState("");
  const [manualSearchSelected, setManualSearchSelected] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);
  const [fallbackAvailable, setFallbackAvailable] = useState(false);
  const [cylinderForm, setCylinderForm] = useState<CylinderFormState>(EMPTY_CYLINDER_FORM);
  const [createMeta, setCreateMeta] = useState<CylinderCreateMetaState>(EMPTY_CYLINDER_CREATE_META);

  const selectedQuery = useQuery({
    queryKey: item
      ? logisticsKeys.loadSerials.selected(sessionId, item.product_id, selectionContext)
      : ["logistics", "load-serials", "none"],
    queryFn: () => listSelectedLoadSerials(sessionId, item!.product_id, selectionContext),
    enabled: open && Boolean(item),
  });
  const manualSearchQuery = useQuery({
    queryKey: item
      ? logisticsKeys.loadSerials.search(sessionId, item.product_id, manualSearchValue, selectionContext)
      : ["logistics", "load-serials", "search", "none"],
    queryFn: () =>
      searchLoadSerials(sessionId, {
        product_id: item!.product_id,
        source_warehouse_id: item!.source_warehouse_id,
        selection_context: selectionContext,
        query: manualSearchValue,
      }),
    enabled: open && Boolean(item) && manualSearchValue.trim().length >= 2,
  });

  const selectMutation = useMutation({
    mutationFn: (serial: string) =>
      selectLoadSerial(sessionId, {
        product_id: item!.product_id,
        source_warehouse_id: item!.source_warehouse_id,
        selection_context: selectionContext,
        serial,
      }),
    onSuccess: async () => {
      setError(null);
      setCreateError(null);
      setFallbackAvailable(false);
      setManualSearchValue("");
      setManualSearchSelected("");
      await queryClient.invalidateQueries({
        queryKey: logisticsKeys.loadSerials.selected(sessionId, item!.product_id, selectionContext),
      });
    },
    onError: (cause) => {
      const message = cause instanceof Error ? cause.message : "No se pudo seleccionar el serial";
      setError(message);
      setFallbackAvailable(message.toLowerCase().includes("serial no encontrado"));
    },
  });

  const createCylinderMutation = useMutation({
    mutationFn: () =>
      createCylinder({
        serial: cylinderForm.serial,
        barcode2: cylinderForm.barcode2 || null,
        product_id: cylinderForm.gas_group_id || null,
        warehouse_id: createMeta.warehouse_id || null,
        entry_mode: createMeta.entry_mode,
        minimal_route_create: true,
        customer_id: createMeta.customer_id || null,
      }),
    onSuccess: async (cylinder) => {
      setCreateError(null);
      setError(null);
      setFallbackAvailable(false);
      setIsCreateOpen(false);
      setCylinderForm(EMPTY_CYLINDER_FORM);
      setCreateMeta(EMPTY_CYLINDER_CREATE_META);
      setManualSearchSelected(cylinder.serial);
      await selectMutation.mutateAsync(cylinder.serial);
    },
    onError: (cause) => {
      setCreateError(cause instanceof Error ? cause.message : "No se pudo registrar el envase");
    },
  });

  const releaseMutation = useMutation({
    mutationFn: (assignmentId: string) =>
      releaseLoadSerial(sessionId, assignmentId, { release_reason: "MANUAL" }),
    onSuccess: async () => {
      setError(null);
      await queryClient.invalidateQueries({
        queryKey: logisticsKeys.loadSerials.selected(sessionId, item!.product_id, selectionContext),
      });
    },
    onError: (cause) => {
      setError(cause instanceof Error ? cause.message : "No se pudo liberar el serial");
    },
  });

  const toggleMutation = useMutation({
    mutationFn: (assignmentId: string) => toggleDeliverySelection(sessionId, assignmentId),
    onSuccess: async () => {
      setError(null);
      await queryClient.invalidateQueries({
        queryKey: logisticsKeys.loadSerials.selected(sessionId, item!.product_id, selectionContext),
      });
    },
    onError: (cause) => {
      setError(cause instanceof Error ? cause.message : "No se pudo cambiar la selección");
    },
  });

  const selectedAssignments = selectedQuery.data ?? [];
  const targetCount = item ? Number(item.planned_quantity || "0") : 0;
  const manualOptions: ComboboxOption[] = (manualSearchQuery.data ?? []).map((result) => ({
    value: result.serial,
    label: result.context_label ? `${result.serial} · ${result.context_label}` : result.serial,
    keywords: [result.serial, result.availability_status, result.context_label ?? ""],
  }));

  useEffect(() => {
    if (!item) {
      return;
    }
    if (selectedAssignments.length === 0 && selectedQuery.isFetching) {
      return;
    }
    onSelectionCountChange(item.product_id, selectedAssignments.length);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [item?.product_id, selectedAssignments.length, selectedQuery.isFetching]);

  useEffect(() => {
    if (!open) {
      autoSubmittedQueryRef.current = "";
      setManualSearchValue("");
      setManualSearchSelected("");
      setError(null);
      setCreateError(null);
      setFallbackAvailable(false);
      return;
    }
  }, [open]);

  useEffect(() => {
    const normalizedQuery = manualSearchValue.trim().toUpperCase();
    if (!normalizedQuery) {
      autoSubmittedQueryRef.current = "";
      return;
    }
    if (!/^\d+$/.test(normalizedQuery) || normalizedQuery.length < 4) {
      return;
    }
    if (selectMutation.isPending || manualSearchQuery.isFetching) {
      return;
    }
    if (autoSubmittedQueryRef.current === normalizedQuery) {
      return;
    }

    const matches = (manualSearchQuery.data ?? []).filter(
      (result) =>
        result.availability_status === "AVAILABLE" &&
        result.serial.toUpperCase().endsWith(normalizedQuery)
    );
    if (matches.length !== 1) {
      return;
    }

    autoSubmittedQueryRef.current = normalizedQuery;
    setManualSearchSelected(matches[0].serial);
    void selectMutation.mutateAsync(normalizedQuery);
  }, [manualSearchQuery.data, manualSearchQuery.isFetching, manualSearchValue, selectMutation]);

  function openRegisterFallback() {
    if (!item || !manualSearchValue.trim()) {
      return;
    }
    const normalizedSerial = manualSearchValue.trim().toUpperCase();
    setCylinderForm({
      ...EMPTY_CYLINDER_FORM,
      serial: normalizedSerial,
      barcode2: normalizedSerial,
      gas_group_id: item.product_id,
    });
    setCreateMeta({
      ...EMPTY_CYLINDER_CREATE_META,
      entry_mode: "FULL_FROM_SUPPLIER",
      warehouse_id: item.source_warehouse_id,
    });
    setCreateError(null);
    setIsCreateOpen(true);
  }

  return (
    <Dialog
      open={open}
      onClose={onClose}
      title={item ? `Seriales · ${item.product_name}` : "Seriales de carga"}
      description={
        item
          ? selectionContext === "ROUTE_PICKUP"
            ? `Escanea o escribe seriales recogidos en ruta. Seleccionados ${selectedAssignments.length} / ${targetCount}.`
            : selectionContext === "ROUTE_DELIVERY"
              ? `Escanea los seriales del vehículo a entregar en esta parada. Seleccionados ${selectedAssignments.length}.`
              : `Escanea o escribe seriales. Seleccionados ${selectedAssignments.length} / ${targetCount}.`
          : "Escanea o escribe seriales de envases."
      }
      maxWidthClassName="max-w-3xl"
    >
      {!item ? null : (
        <div className="space-y-4">
          <div className="space-y-2">
            <p className="text-sm font-medium text-foreground">Escanear o escribir serial</p>
            <Combobox
              value={manualSearchSelected}
              onChange={(value) => {
                setManualSearchSelected(value);
                void selectMutation.mutateAsync(value);
              }}
              options={manualOptions}
              placeholder="Escanea o escribe serial"
              searchPlaceholder="Escanea o escribe serial"
              emptyMessage={
                manualSearchValue.trim().length < 1
                  ? "Escribe al menos 1 carácter."
                  : "Sin coincidencias."
              }
              searchValue={manualSearchValue}
              onSearchValueChange={(value) => setManualSearchValue(value.toUpperCase())}
              onSubmitQuery={(value) => void selectMutation.mutateAsync(value)}
              variant="input"
              minSearchLength={1}
            />
            <div className="flex justify-end">
              <Button
                type="button"
                disabled={selectMutation.isPending || manualSearchValue.trim().length === 0}
                onClick={() => void selectMutation.mutateAsync(manualSearchValue)}
              >
                {selectMutation.isPending ? "Agregando..." : "Agregar"}
              </Button>
            </div>
          </div>

          {error ? <Alert title="Serial no agregado">{error}</Alert> : null}
          {fallbackAvailable && allowCreateFallback ? (
            <div className="flex justify-end">
              <Button type="button" variant="secondary" onClick={openRegisterFallback}>
                Registrar envase
              </Button>
            </div>
          ) : null}

          <div className="rounded-xl bg-muted/35 px-4 py-3 text-sm text-foreground">
            {selectionContext === "ROUTE_DELIVERY"
              ? `Seleccionados para entrega: ${selectedAssignments.length}`
              : `Objetivo: ${targetCount} · Seleccionados: ${selectedAssignments.length}`}
          </div>

          <div className="space-y-2">
            <p className="text-sm font-medium text-foreground">Seriales seleccionados</p>
            {selectedAssignments.length ? (
              <div className="space-y-2">
                {selectedAssignments.map((assignment: LoadSerialAssignment) => (
                  <div key={assignment.id} className="flex items-center justify-between gap-3 rounded-lg border border-border px-3 py-2 text-sm">
                    <div className="min-w-0">
                      <p className="font-medium text-foreground">{assignment.cylinder_serial}</p>
                      <p className="text-muted-foreground">
                        {formatLoadSerialAssignmentStatus(assignment.assignment_status)} · {new Date(assignment.selected_at).toLocaleString()}
                      </p>
                    </div>
                    <Button
                      type="button"
                      variant="secondary"
                      disabled={
                        selectionContext === "ROUTE_DELIVERY"
                          ? toggleMutation.isPending
                          : releaseMutation.isPending || assignment.assignment_status !== "SELECTED"
                      }
                      onClick={() =>
                        // ROUTE_DELIVERY: "Quitar" hace toggle a CONFIRMED (no libera).
                        // El cilindro sigue en el vehículo, disponible para otra parada.
                        // LOAD_PLAN / ROUTE_PICKUP: "Quitar" libera el assignment.
                        selectionContext === "ROUTE_DELIVERY"
                          ? toggleMutation.mutate(assignment.id)
                          : releaseMutation.mutate(assignment.id)
                      }
                    >
                      Quitar
                    </Button>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">Sin seriales seleccionados todavía.</p>
            )}
          </div>

          <CreateCylinderDialog
            open={isCreateOpen}
            onOpenChange={(nextOpen) => {
              setIsCreateOpen(nextOpen);
              if (!nextOpen) {
                setCreateError(null);
              }
            }}
            cylinderForm={cylinderForm}
            onCylinderFormChange={setCylinderForm}
            createMeta={createMeta}
            onCreateMetaChange={setCreateMeta}
            gasOptions={item ? [{ id: item.product_id, name: item.product_name }] : []}
            warehouseOptions={[]}
            isPending={createCylinderMutation.isPending}
            error={createError}
            onSubmit={async (serials) => {
              await createCylinderMutation.mutateAsync();
            }}
            compactMode
            compactHint="Envase no registrado. Se creara con serial, codigo de barras y producto inferido desde la carga planificada."
          />
        </div>
      )}
    </Dialog>
  );
}
