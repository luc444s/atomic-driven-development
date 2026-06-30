import { SearchDialog } from "../../../../apps/web/src/shared/ui/search-dialog";
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
        { key: "name", header: "Cliente", render: (row) => row.legal_name },
        {
          key: "document",
          header: "Documento",
          render: (row) => `${row.document_type_code} ${row.document_number}`,
        },
        { key: "email", header: "Email", render: (row) => row.email ?? "-" },
        { key: "phone", header: "Teléfono", render: (row) => row.phone ?? "-" },
        {
          key: "address",
          header: "Dirección fiscal",
          render: (row) => row.fiscal_address_summary ?? "-",
        },
      ]}
    />
  );
}
