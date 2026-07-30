import { useEffect, useState } from "react";
import { useQuery } from "../../../../apps/web/src/lib/react-query";
import { Button } from "../../../../apps/web/src/shared/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../../../apps/web/src/shared/ui/card";
import { DataTable } from "../../../../apps/web/src/shared/ui/data-table";
import { Input } from "../../../../apps/web/src/shared/ui/input";
import { Pagination } from "../../../../apps/web/src/shared/ui/pagination";
import { crmKeys, listCustomers } from "../api";
import { ModalDetalleCliente } from "../components/ModalDetalleCliente";
import { ModalNuevoCliente } from "../components/ModalNuevoCliente";
import { CrmSection } from "../components/CrmSection";

export function CustomersListPage() {
  const pageSize = 10;
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [showNew, setShowNew] = useState(false);
  const [editId, setEditId] = useState<string | null>(null);
  const [detailId, setDetailId] = useState<string | null>(null);

  useEffect(() => {
    setPage(1);
  }, [search]);

  const customersQuery = useQuery({
    queryKey: crmKeys.customers.list({ search, page, limit: pageSize }),
    queryFn: () => listCustomers({ search, limit: pageSize, offset: (page - 1) * pageSize }),
  });
  const totalPages = customersQuery.data
    ? Math.max(1, Math.ceil(customersQuery.data.total / customersQuery.data.limit))
    : 1;

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
          <CardDescription>Búsqueda operativa por nombre fiscal, comercial, documento, teléfono, código o localidad.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-[1fr_auto]">
            <Input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Buscar por nombre, documento, teléfono, código o localidad"
            />
            <div className="text-sm text-muted-foreground">
              {customersQuery.data ? `${customersQuery.data.total} registros` : "Cargando..."}
            </div>
          </div>
          <DataTable
            columns={[
              {
                key: "name",
                header: "Cliente",
                render: (row) => (
                  <div className="space-y-1">
                    <p className="font-medium text-foreground">{row.commercial_name ?? row.legal_name}</p>
                    {row.commercial_name ? <p className="text-xs text-muted-foreground">Fiscal: {row.legal_name}</p> : null}
                  </div>
                ),
              },
              { key: "doc", header: "Documento", render: (row) => `${row.document_type_code} ${row.document_number}` },
              { key: "code", header: "Código", render: (row) => row.external_code ?? "-" },
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
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-sm text-muted-foreground">
              {customersQuery.data
                ? `${customersQuery.data.total} clientes`
                : "Cargando clientes..."}
            </p>
            <Pagination page={page} totalPages={totalPages} onChange={setPage} />
          </div>
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
