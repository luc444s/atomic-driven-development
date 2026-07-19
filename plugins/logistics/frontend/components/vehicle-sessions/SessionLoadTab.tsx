import { Alert } from "../../../../../apps/web/src/shared/ui/alert";
import { Button } from "../../../../../apps/web/src/shared/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "../../../../../apps/web/src/shared/ui/card";
import { DataTable } from "../../../../../apps/web/src/shared/ui/data-table";
import { Input } from "../../../../../apps/web/src/shared/ui/input";

import type { StockBalanceItem } from "../../../../stock/frontend/types";
import type { VehicleSessionDetail } from "../../api";

export type EditableLoadPlanItem = {
  product_id: string;
  product_name: string;
  planned_quantity: string;
};

type Props = {
  session: VehicleSessionDetail;
  loadPlanItems: EditableLoadPlanItem[];
  setLoadPlanItems: React.Dispatch<React.SetStateAction<EditableLoadPlanItem[]>>;
  originRows: StockBalanceItem[];
  onOpenProductSearch: () => void;
  onSavePlan: () => void;
  isPending: boolean;
  error: string | null;
};

export function SessionLoadTab({
  session,
  loadPlanItems,
  setLoadPlanItems,
  originRows,
  onOpenProductSearch,
  onSavePlan,
  isPending,
  error,
}: Props) {
  const isLoadingStep = session.status === "LOADING";

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Carga planificada</CardTitle>
          <CardDescription>
            Edita el plan. En `LOADING`, guardar también confirma la carga y avanza la jornada.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2">
            <Button variant="secondary" onClick={onOpenProductSearch}>
              Agregar producto
            </Button>
            <Button
              disabled={
                isPending || !session || !["DRAFT", "LOADING", "READY_TO_DEPART"].includes(session.status)
              }
              onClick={onSavePlan}
            >
              {isLoadingStep ? "Guardar y confirmar" : "Guardar plan"}
            </Button>
          </div>
          {error ? <Alert title="Estado no actualizado">{error}</Alert> : null}
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
      <Card>
        <CardHeader>
          <CardTitle>Disponibilidad en origen</CardTitle>
        </CardHeader>
        <CardContent>
          <DataTable
            columns={[
              {
                key: "product",
                header: "Producto",
                render: (row: StockBalanceItem) => row.product_name,
              },
              {
                key: "qty",
                header: "Disponible",
                render: (row: StockBalanceItem) => String(row.quantity),
              },
            ]}
            rows={originRows}
            rowKey={(row) => `${row.warehouse_id}-${row.product_id}`}
            emptyMessage="Sin saldo visible en el almacén origen."
          />
        </CardContent>
      </Card>
    </div>
  );
}
