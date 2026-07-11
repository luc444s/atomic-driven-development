import { useState } from "react";
import { useQuery } from "../../../../apps/web/src/lib/react-query";
import { Link } from "../../../../apps/web/src/lib/router";
import { Button } from "../../../../apps/web/src/shared/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../../../../apps/web/src/shared/ui/card";
import { DataTable } from "../../../../apps/web/src/shared/ui/data-table";
import { Dialog } from "../../../../apps/web/src/shared/ui/dialog";
import { Badge } from "../../../../apps/web/src/shared/ui/badge";
import { listContracts } from "../../../logistics/frontend/api/contracts";
import type { LogisticsCylinderContract } from "../../../logistics/frontend/api/contracts";

const STATUS_COLOR: Record<string, string> = {
  DRAFT: "bg-gray-100 text-gray-800",
  ACTIVE: "bg-green-100 text-green-800",
  TERMINATED: "bg-red-100 text-red-800",
  CANCELLED: "bg-yellow-100 text-yellow-800",
};

const STATUS_LABEL: Record<string, string> = {
  DRAFT: "Borrador",
  ACTIVE: "Activo",
  TERMINATED: "Terminado",
  CANCELLED: "Cancelado",
};

type CustomerContractsButtonProps = {
  customerId: string;
};

export function CustomerContractsButton({ customerId }: CustomerContractsButtonProps) {
  const [isOpen, setIsOpen] = useState(false);

  const { data: contracts = [], isLoading } = useQuery({
    queryKey: ["logistics", "contracts", "customer", customerId],
    queryFn: () => listContracts({ customer_id: customerId }),
    enabled: isOpen,
  });

  return (
    <>
      <Button variant="ghost" onClick={() => setIsOpen(true)}>
        Contratos
      </Button>

      <Dialog
        open={isOpen}
        title="Contratos de envases"
        onClose={() => setIsOpen(false)}
        maxWidthClassName="max-w-3xl"
      >
        <div className="space-y-4">
          <div className="flex items-center justify-end gap-2">
            <Link to={`/app/logistics/contracts?customer_id=${customerId}`}>
              <Button variant="outline" size="sm">
                Ver todos
              </Button>
            </Link>
            <Link to="/app/logistics/contracts">
              <Button size="sm">Nuevo contrato</Button>
            </Link>
          </div>

          {isLoading ? (
            <div className="py-8 text-center text-sm text-muted-foreground">
              Cargando contratos...
            </div>
          ) : contracts.length === 0 ? (
            <div className="py-8 text-center text-sm text-muted-foreground">
              Este cliente no tiene contratos de envases.
            </div>
          ) : (
            <DataTable
              dense
              rowKey={(row) => row.id}
              rows={contracts}
              columns={[
                {
                  key: "contract_number",
                  header: "Número",
                  render: (row) => row.contract_number || "-",
                },
                {
                  key: "type",
                  header: "Tipo",
                  render: (row) => (row.contract_type === "ANNUAL" ? "Anual" : "Diario"),
                },
                {
                  key: "status",
                  header: "Estado",
                  render: (row) => (
                    <Badge className={STATUS_COLOR[row.status] || "bg-gray-100 text-gray-800"}>
                      {STATUS_LABEL[row.status] || row.status}
                    </Badge>
                  ),
                },
                {
                  key: "quantity",
                  header: "Cant.",
                  render: (row) => `${row.quantity} x`,
                },
                {
                  key: "start_date",
                  header: "Inicio",
                  render: (row) => row.start_date,
                },
                {
                  key: "end_date",
                  header: "Fin",
                  render: (row) => row.end_date || "-",
                },
              ]}
            />
          )}
        </div>
      </Dialog>
    </>
  );
}
