import { useQuery } from "../../../../apps/web/src/lib/react-query";
import { Link } from "../../../../apps/web/src/lib/router";
import { Button } from "../../../../apps/web/src/shared/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../../../apps/web/src/shared/ui/card";
import { DataTable } from "../../../../apps/web/src/shared/ui/data-table";
import { crmKeys, listCustomers } from "../api";
import { CrmSection } from "../components/CrmSection";

export function CustomersListPage() {
  const customersQuery = useQuery({
    queryKey: crmKeys.customers.list({}),
    queryFn: () => listCustomers({ limit: 50, offset: 0 }),
  });

  return (
    <CrmSection
      title="Clientes"
      description="Gestiona clientes con datos fiscales, direcciones y contactos."
      actions={
        <Link to="/app/crm/customers/new">
          <Button>Nuevo cliente</Button>
        </Link>
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
                key: "detail",
                header: "Detalle",
                render: (row) => (
                  <div className="flex gap-2">
                    <Link to={`/app/crm/customers/${row.id}`}>
                      <Button variant="secondary">Editar</Button>
                    </Link>
                    <Link to={`/app/crm/customers/${row.id}/detail`}>
                      <Button variant="secondary">Ver</Button>
                    </Link>
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
    </CrmSection>
  );
}
