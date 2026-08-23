import { DataTable } from "@systutor/shell/ui/data-table";
import { Pagination } from "@systutor/shell/ui/pagination";
import { CylinderStateBadge } from "../../CylinderStateBadge";
import type { LogisticsCylinder } from "../../api";

interface CylinderTableSectionProps {
  rows: LogisticsCylinder[];
  total: number | undefined;
  page: number;
  totalPages: number;
  productById: Map<string, string>;
  gasById: Map<string, string>;
  brandById: Map<string, string>;
  onOpenDetail: (cylinder: LogisticsCylinder) => void;
  onPageChange: (page: number) => void;
  formatDate: (value: string | null | undefined) => string;
}

export function CylinderTableSection({
  rows,
  total,
  page,
  totalPages,
  productById,
  gasById,
  brandById,
  onOpenDetail,
  onPageChange,
  formatDate,
}: CylinderTableSectionProps) {
  return (
    <>
      <DataTable
        columns={[
          {
            key: "serial",
            header: "Envase",
            render: (row) => (
              <div className="space-y-1">
                <button
                  type="button"
                  onClick={() => onOpenDetail(row)}
                  className="text-left font-medium text-cyan-300 hover:text-cyan-200"
                >
                  {row.serial}
                </button>

              </div>
            ),
          },
          {
            key: "gas",
            header: "Gas / marca",
            render: (row) => (
              <div className="space-y-1 text-sm text-foreground">
                <p>
                  {productById.get(row.product_id ?? "") ||
                    gasById.get(row.gas_group_id ?? "") ||
                    "Sin gas"}
                </p>
              </div>
            ),
          },
          {
            key: "state",
            header: "Estado",
            render: (row) => <CylinderStateBadge state={row.current_state} />,
          },
          {
            key: "ph",
            header: "PH",
            render: (row) => (
              <div className="space-y-1 text-xs text-muted-foreground">
                <p>PH: {formatDate(row.next_hydrotest_date)}</p>
                {row.is_medical ? (
                  <p className="font-medium text-amber-500">MEDICINAL</p>
                ) : null}
              </div>
            ),
          },
          {
            key: "location",
            header: "Ubicación",
            render: (row) => (
              <span className="text-sm text-foreground">
                {row.location_context || row.location || "-"}
              </span>
            ),
          },
        ]}
        rows={rows}
        rowKey={(row) => row.id}
        onRowDoubleClick={(row) => onOpenDetail(row)}
        emptyMessage="Aún no hay envases registrados."
      />
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <p className="text-sm text-muted-foreground">
          {total !== undefined ? `${total} envases` : "Cargando envases..."}
        </p>
        <Pagination page={page} totalPages={totalPages} onChange={onPageChange} />
      </div>
    </>
  );
}
