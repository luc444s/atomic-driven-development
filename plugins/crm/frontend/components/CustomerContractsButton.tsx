import { useState } from "react";
import { useQuery } from "../../../../apps/web/src/lib/react-query";
import { Link } from "../../../../apps/web/src/lib/router";
import { Button } from "@systutor/shell/ui/button";
import { DataTable } from "@systutor/shell/ui/data-table";
import { Dialog } from "@systutor/shell/ui/dialog";
import { Badge } from "@systutor/shell/ui/badge";
import { listContracts } from "../../../logistics/frontend/api/contracts";
import type { LogisticsCylinderContract } from "../../../logistics/frontend/api/contracts";

const STATUS_COLOR: Record<string, string> = {
  DRAFT: "border-border bg-muted text-muted-foreground",
  ACTIVE: "border-success/30 bg-success/10 text-success",
  TERMINATED: "border-destructive/30 bg-destructive/10 text-destructive",
  CANCELLED: "border-warning/30 bg-warning/10 text-warning",
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
      <button
        type="button"
        onClick={() => setIsOpen(true)}
        className="rounded-lg border border-border bg-surface p-4 text-left transition hover:border-ring hover:bg-surface-alt"
      >
        <p className="text-sm font-medium text-foreground">Contratos</p>
        <p className="mt-1 text-xs text-muted-foreground">Gestiona contratos de envases del cliente.</p>
      </button>

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
                    <Badge className={STATUS_COLOR[row.status] || "border-border bg-muted text-muted-foreground"}>
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
