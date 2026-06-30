import { useState } from "react";

import { useQuery } from "../../../../apps/web/src/lib/react-query";
import { Alert } from "../../../../apps/web/src/shared/ui/alert";
import { DataTable } from "../../../../apps/web/src/shared/ui/data-table";
import { Dialog } from "../../../../apps/web/src/shared/ui/dialog";
import { Input } from "../../../../apps/web/src/shared/ui/input";
import { crmKeys, searchCustomers } from "../api";
import type { CustomerBrief } from "../types";

type CustomerSearchDialogProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSelect: (customer: CustomerBrief) => void;
  title?: string;
};

export function CustomerSearchDialog({ open, onOpenChange, onSelect, title = "Seleccionar cliente" }: CustomerSearchDialogProps) {
  const [query, setQuery] = useState("");
  const customersQuery = useQuery({
    queryKey: crmKeys.customers.search(query),
    queryFn: () => searchCustomers(query),
    enabled: open && query.trim().length > 0,
  });

  return (
    <Dialog
      open={open}
      title={title}
      description="Busca por nombre, documento, email, telefono o codigo externo."
      onClose={() => onOpenChange(false)}
      maxWidthClassName="max-w-4xl"
    >
      <div className="space-y-4">
        <Input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="GLP Norte, 20123456789, ventas@..." />
        {customersQuery.error ? <Alert title="No se pudo buscar clientes">{customersQuery.error.message}</Alert> : null}
        <DataTable
          columns={[
            { key: "name", header: "Cliente", render: (row) => row.legal_name },
            { key: "document", header: "Documento", render: (row) => `${row.document_type_code} ${row.document_number}` },
            { key: "email", header: "Email", render: (row) => row.email ?? "-" },
            { key: "phone", header: "Teléfono", render: (row) => row.phone ?? "-" },
            { key: "address", header: "Dirección fiscal", render: (row) => row.fiscal_address_summary ?? "-" },
          ]}
          rows={customersQuery.data ?? []}
          rowKey={(row) => row.id}
          emptyMessage={query.trim().length === 0 ? "Escribe algo para buscar." : "Sin resultados."}
        />
        {(customersQuery.data ?? []).length > 0 ? (
          <div className="grid gap-2">
            {(customersQuery.data ?? []).map((customer) => (
              <button
                key={customer.id}
                type="button"
                className="rounded-md border border-border bg-surface px-3 py-2 text-left text-sm text-foreground hover:border-ring"
                onClick={() => {
                  onSelect(customer);
                  onOpenChange(false);
                }}
              >
                {customer.legal_name} · {customer.document_type_code} {customer.document_number}
              </button>
            ))}
          </div>
        ) : null}
      </div>
    </Dialog>
  );
}
