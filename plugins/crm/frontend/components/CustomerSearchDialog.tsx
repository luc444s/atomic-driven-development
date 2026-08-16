import { SearchDialog } from "@systutor/shell/ui/search-dialog";
import { searchCustomers } from "../api";
import type { CustomerBrief } from "../types";

type CustomerSearchDialogProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSelect: (customer: CustomerBrief) => void;
  title?: string;
};

export function CustomerSearchDialog({
  open,
  onOpenChange,
  onSelect,
  title = "Seleccionar cliente",
}: CustomerSearchDialogProps) {
  return (
    <SearchDialog<CustomerBrief>
      open={open}
      onOpenChange={onOpenChange}
      title={title}
      placeholder="GLP Norte, 20123456789, ventas@..."
      fetchFn={searchCustomers}
      onSelect={onSelect}
      getRowId={(item) => item.id}
      columns={[
        {
          key: "name",
          header: "Cliente",
          render: (row) => (
            <div className="space-y-1">
              <p className="font-medium text-foreground">{row.display_name}</p>
              {row.commercial_name && row.commercial_name !== row.legal_name ? (
                <p className="text-xs text-muted-foreground">Fiscal: {row.legal_name}</p>
              ) : null}
            </div>
          ),
        },
        {
          key: "document",
          header: "Documento",
          render: (row) => (
            <div className="space-y-1">
              <p>{`${row.document_type_code} ${row.document_number}`}</p>
              <p className="text-xs text-muted-foreground">Código: {row.external_code ?? "-"}</p>
            </div>
          ),
        },
        { key: "email", header: "Email", render: (row) => row.email ?? "-" },
        { key: "phone", header: "Teléfono", render: (row) => row.phone ?? "-" },
        {
          key: "locality",
          header: "Localidad",
          render: (row) => row.locality_summary ?? "-",
        },
        {
          key: "address",
          header: "Dirección fiscal",
          render: (row) => row.fiscal_address_summary ?? "-",
        },
      ]}
    />
  );
}
