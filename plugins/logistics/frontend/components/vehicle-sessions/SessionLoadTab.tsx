import { useState } from "react";

import { Alert } from "@systutor/shell/ui/alert";
import { Button } from "@systutor/shell/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@systutor/shell/ui/card";
import { DataTable } from "@systutor/shell/ui/data-table";
import { Input } from "@systutor/shell/ui/input";

import type { SerializedCylinderSummary, VehicleSessionDetail } from "../../api";
import { LoadSerialsDialog } from "./LoadSerialsDialog";
import { SerialQuickAddDialog } from "./SerialQuickAddDialog";

export type EditableLoadPlanItem = {
  id?: string;
  product_id: string;
  product_name: string;
  planned_quantity: string;
  source_warehouse_id: string;
  requires_serials: boolean;
  selected_serials_count: number;
  serials_complete: boolean;
};

type Props = {
  session: VehicleSessionDetail;
  loadPlanItems: EditableLoadPlanItem[];
  setLoadPlanItems: React.Dispatch<React.SetStateAction<EditableLoadPlanItem[]>>;
  serializedRows: SerializedCylinderSummary[];
  onOpenProductSearch: () => void;
  onSavePlan: () => void;
  isPending: boolean;
  error: string | null;
};

export function SessionLoadTab({
  session,
  loadPlanItems,
  setLoadPlanItems,
  onOpenProductSearch,
  onSavePlan,
  isPending,
  error,
}: Props) {
  const isLoadingStep = session.status === "LOADING";
  const [serialItemProductId, setSerialItemProductId] = useState<string | null>(null);
  const [serialSearchOpen, setSerialSearchOpen] = useState(false);
  const serialItem = loadPlanItems.find((item) => item.product_id === serialItemProductId) ?? null;
  const hasIncompleteSerials = loadPlanItems.some((item) => {
    if (!item.requires_serials) {
      return false;
    }
    const target = Number(item.planned_quantity || "0");
    return !Number.isInteger(target) || item.selected_serials_count !== target;
  });
  const hasInvalidOriginQuantities = loadPlanItems.some((item) => {
    if (!item.source_warehouse_id) {
      return false;
    }
    const quantity = Number(item.planned_quantity || "0");
    return !Number.isFinite(quantity) || quantity <= 0;
  });

  function handleInferredSerialSelected(selection: {
    product_id: string;
    product_name: string;
    serial: string;
  }) {
    setLoadPlanItems((current) => {
      const existing = current.find((item) => item.product_id === selection.product_id);
      if (existing) {
        return current.map((item) =>
          item.product_id === selection.product_id
            ? {
                ...item,
                requires_serials: true,
                selected_serials_count: item.selected_serials_count + 1,
                serials_complete: true,
              }
            : item
        );
      }
      return [
        ...current,
        {
          product_id: selection.product_id,
          product_name: selection.product_name,
          planned_quantity: "1",
          source_warehouse_id: session.origin_warehouse_id,
          requires_serials: true,
          selected_serials_count: 1,
          serials_complete: true,
        },
      ];
    });
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Carga planificada</CardTitle>
          <CardDescription>
            Edita el plan. En estado Cargando, guardar tambien confirma la carga y avanza la jornada.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2">
            <Button variant="secondary" onClick={() => setSerialSearchOpen(true)}>
              Agregar serial
            </Button>
            <Button variant="secondary" onClick={onOpenProductSearch}>
              Agregar producto
            </Button>
            <Button
              disabled={
                isPending ||
                !session ||
                !["DRAFT", "LOADING", "READY_TO_DEPART"].includes(session.status) ||
                hasInvalidOriginQuantities ||
                (isLoadingStep && hasIncompleteSerials)
              }
              onClick={onSavePlan}
            >
              {isLoadingStep ? "Guardar y confirmar" : "Guardar plan"}
            </Button>
          </div>
          {error ? <Alert title="Estado no actualizado">{error}</Alert> : null}
          {hasInvalidOriginQuantities ? (
            <Alert title="Cantidad obligatoria">
              Hay líneas que salen desde almacén con cantidad faltante o inválida. Completa una cantidad mayor que cero antes de guardar la carga.
            </Alert>
          ) : null}
          {isLoadingStep && hasIncompleteSerials ? (
            <Alert title="Carga incompleta">
              Hay productos serializados con seriales faltantes. Completa la captura antes de confirmar la carga.
            </Alert>
          ) : null}
          <DataTable
            columns={[
              {
                key: "product",
                header: "Producto",
                render: (row: EditableLoadPlanItem) => row.product_name,
              },
              {
                key: "qty",
                header: "Planificado",
                render: (row: EditableLoadPlanItem) => (
                  <Input
                    value={row.planned_quantity}
                    onChange={(event) =>
                      setLoadPlanItems((current) =>
                        current.map((item) =>
                          item.product_id === row.product_id
                            ? { ...item, planned_quantity: event.target.value }
                            : item
                        )
                      )
                    }
                  />
                ),
              },
              {
                key: "serials",
                header: "Seriales",
                render: (row: EditableLoadPlanItem) => (
                  <div className="flex items-center gap-2">
                    <Button variant="secondary" onClick={() => setSerialItemProductId(row.product_id)}>
                      Seriales
                    </Button>
                    {row.requires_serials ? (
                      <span className="text-xs text-muted-foreground">
                        {row.selected_serials_count}/{Number(row.planned_quantity || "0")}
                      </span>
                    ) : null}
                  </div>
                ),
              },
              {
                key: "actions",
                header: "Quitar",
                render: (row: EditableLoadPlanItem) => (
                  <Button
                    variant="secondary"
                    onClick={() =>
                      setLoadPlanItems((current) =>
                        current.filter((item) => item.product_id !== row.product_id)
                      )
                    }
                  >
                    Quitar
                  </Button>
                ),
              },
            ]}
            rows={loadPlanItems}
            rowKey={(row) => row.product_id}
            emptyMessage="No hay productos en el plan de carga."
          />
        </CardContent>
      </Card>
      <LoadSerialsDialog
        open={Boolean(serialItem)}
        sessionId={session.id}
        item={serialItem}
        onClose={() => setSerialItemProductId(null)}
        onSelectionCountChange={(productId, selectedCount) =>
          setLoadPlanItems((current) =>
            current.map((item) =>
              item.product_id === productId
                ? {
                    ...item,
                    requires_serials: item.requires_serials || selectedCount > 0,
                    selected_serials_count: selectedCount,
                    serials_complete: selectedCount === Number(item.planned_quantity || "0"),
                  }
                : item
            )
          )
        }
      />
      <SerialQuickAddDialog
        open={serialSearchOpen}
        sessionId={session.id}
        sourceWarehouseId={session.origin_warehouse_id}
        onClose={() => setSerialSearchOpen(false)}
        onSelected={handleInferredSerialSelected}
      />
    </div>
  );
}
