import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../../../../../apps/web/src/shared/ui/card";
import { DataTable } from "../../../../../apps/web/src/shared/ui/data-table";

import type { StockBalanceItem } from "../../../../stock/frontend/types";
import type { VehicleSessionDetail } from "../../api";

type Props = {
  session: VehicleSessionDetail;
  mobileRows: StockBalanceItem[];
};

export function SessionSummaryTab({ session, mobileRows }: Props) {
  return (
    <div className="grid gap-4 md:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle>Resumen operativo</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          <div>
            <span className="font-medium">Última actividad:</span> {session.last_activity ?? "-"}
          </div>
          <div>
            <span className="font-medium">Capacidad ocupada:</span> {session.occupancy_percent ?? 0}%
          </div>
          <div>
            <span className="font-medium">Saldo actual móvil:</span> {session.current_stock.total_units} unidades / {session.current_stock.total_products} productos
          </div>
          <div>
            <span className="font-medium">Puede salir:</span> {session.can_depart ? "Sí" : "No"}
          </div>
          <div>
            <span className="font-medium">Puede cerrar:</span> {session.can_close ? "Sí" : "No"}
          </div>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Stock actual del almacén móvil</CardTitle>
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
                header: "Cantidad",
                render: (row: StockBalanceItem) => String(row.quantity),
              },
            ]}
            rows={mobileRows}
            rowKey={(row) => `${row.warehouse_id}-${row.product_id}`}
            emptyMessage="Sin saldo móvil todavía."
          />
        </CardContent>
      </Card>
    </div>
  );
}
