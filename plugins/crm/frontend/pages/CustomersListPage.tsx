import { useState } from "react";
import { useQuery } from "../../../../apps/web/src/lib/react-query";
import { Button } from "../../../../apps/web/src/shared/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../../../apps/web/src/shared/ui/card";
import { DataTable } from "../../../../apps/web/src/shared/ui/data-table";
import { crmKeys, listCustomers } from "../api";
import { ModalDetalleCliente } from "../components/ModalDetalleCliente";
import { ModalNuevoCliente } from "../components/ModalNuevoCliente";
import { CrmSection } from "../components/CrmSection";

export function CustomersListPage() {
  const [showNew, setShowNew] = useState(false);
  const [editId, setEditId] = useState<string | null>(null);
  const [detailId, setDetailId] = useState<string | null>(null);

  const customersQuery = useQuery({
    queryKey: crmKeys.customers.list({}),
    queryFn: () => listCustomers({ limit: 50, offset: 0 }),
  });

  return (
    <CrmSection
      title="Clientes"
      description="Gestiona clientes con datos fiscales, direcciones y contactos."
      actions={
        <Button onClick={() => { setEditId(null); setShowNew(true); }}>Nuevo cliente</Button>
      }
    >
      <Card>
        <CardHeader>
          <CardTitle>Catálogo de clientes</CardTitle>
          <CardDescription>Listado operativo del tenant actual.</CardDescription>
        </CardHeader>
        <CardContent>
          <DataTable
            columns={[
              { key: "name", header: "Cliente", render: (row) => row.legal_name },
              { key: "doc", header: "Documento", render: (row) => `${row.document_type_code} ${row.document_number}` },
              { key: "country", header: "País", render: (row) => row.country_code },
              { key: "phone", header: "Teléfono", render: (row) => row.phone ?? "-" },
              { key: "status", header: "Activo", render: (row) => (row.is_active ? "Sí" : "No") },
              {
                key: "actions",
                header: "Acciones",
                render: (row) => (
                  <div className="flex gap-2">
                    <Button variant="secondary" onClick={() => { setEditId(row.id); setShowNew(true); }}>Editar</Button>
                    <Button variant="secondary" onClick={() => setDetailId(row.id)}>Ver</Button>
                  </div>
                ),
              },
            ]}
            rows={customersQuery.data?.items ?? []}
            rowKey={(row) => row.id}
            emptyMessage="Aún no hay clientes registrados."
          />
        </CardContent>
      </Card>

      <ModalNuevoCliente
        open={showNew}
        customerId={editId ?? undefined}
        onClose={() => { setShowNew(false); setEditId(null); }}
        onSaved={() => customersQuery.refetch()}
        onOpenDetail={(id) => {
          setShowNew(false);
          setEditId(null);
          setDetailId(id);
        }}
      />

      <ModalDetalleCliente
        open={detailId !== null}
        customerId={detailId ?? ""}
        onClose={() => setDetailId(null)}
        onEditCustomer={(id) => {
          setDetailId(null);
          setEditId(id);
          setShowNew(true);
        }}
      />
    </CrmSection>
  );
}
