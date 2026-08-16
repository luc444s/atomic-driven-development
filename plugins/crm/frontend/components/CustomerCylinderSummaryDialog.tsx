import { DataTable } from "@systutor/shell/ui/data-table";
import { Dialog } from "@systutor/shell/ui/dialog";

import type { CustomerCylinderSummary } from "../../../logistics/frontend/api";

type CustomerCylinderSummaryDialogProps = {
  open: boolean;
  onClose: () => void;
  summary: CustomerCylinderSummary;
};

export function CustomerCylinderSummaryDialog({
  open,
  onClose,
  summary,
}: CustomerCylinderSummaryDialogProps) {
  return (
    <Dialog
      open={open}
      onClose={onClose}
      title="Envases en posesión del cliente"
      description="Cruza contrato, asignación contractual y estado operativo actual sin depender del motor de stock."
      maxWidthClassName="max-w-5xl"
    >
      <div className="space-y-4 text-sm text-foreground">
        <DataTable
          dense
          columns={[
            { key: "product", header: "Producto", render: (row) => row.product_name },
            { key: "contracted", header: "Contrato", render: (row) => row.contracted },
            { key: "customer", header: "En cliente", render: (row) => row.at_customer },
            {
              key: "unknown",
              header: "Sin asignación",
              render: (row) => row.at_customer_unknown,
            },
            { key: "pipeline", header: "En tránsito", render: (row) => row.pipeline.total },
            { key: "lost", header: "Perdidos", render: (row) => row.lost },
            { key: "deviation", header: "Desviación", render: (row) => row.deviation },
          ]}
          rows={summary.by_product}
          rowKey={(row) => row.product_id ?? row.product_name}
          emptyMessage="No hay productos relacionados para este cliente."
        />

        {summary.by_product.length > 0 ? (
          <div className="space-y-4">
            {summary.by_product.map((row) => (
              <div key={`detail-${row.product_id ?? row.product_name}`} className="rounded-md border border-border p-4">
                <div className="mb-3 flex items-center justify-between gap-4">
                  <div>
                    <p className="font-medium text-foreground">{row.product_name}</p>
                    <p className="text-xs text-muted-foreground">
                      En tránsito: {row.pipeline.in_vehicle} vehículo, {row.pipeline.in_transit} transbordo, {row.pipeline.in_warehouse} almacén, {row.pipeline.unknown} sin ubicación
                    </p>
                  </div>
                </div>

                <DataTable
                  dense
                  columns={[
                    { key: "condition", header: "Condición", render: (condition) => condition.code },
                    { key: "customer", header: "En cliente", render: (condition) => condition.at_customer },
                    { key: "pipeline", header: "En tránsito", render: (condition) => condition.pipeline },
                    { key: "lost", header: "Perdidos", render: (condition) => condition.lost },
                  ]}
                  rows={Object.entries(row.by_condition).map(([code, metrics]) => ({ code, ...metrics }))}
                  rowKey={(condition) => condition.code}
                  emptyMessage="Sin desglose por condición."
                />
              </div>
            ))}
          </div>
        ) : null}
      </div>
    </Dialog>
  );
}
