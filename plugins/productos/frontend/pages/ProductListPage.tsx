import { useState } from "react";

import { useQuery } from "../../../../apps/web/src/lib/react-query";
import { Link } from "../../../../apps/web/src/lib/router";
import { Alert } from "../../../../apps/web/src/shared/ui/alert";
import { Button } from "../../../../apps/web/src/shared/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../../../apps/web/src/shared/ui/card";
import { DataTable } from "../../../../apps/web/src/shared/ui/data-table";
import { Input } from "../../../../apps/web/src/shared/ui/input";
import { listProducts, productosKeys } from "../api";
import { ProductosSection } from "../components/ProductosSection";

export function ProductListPage() {
  const [search, setSearch] = useState("");
  const productsQuery = useQuery({
    queryKey: productosKeys.products.list({ search }),
    queryFn: () =>
      listProducts({
        limit: 50,
        offset: 0,
        sku: search,
        name: search,
      }),
  });

  return (
    <ProductosSection
      title="Productos"
      description="Catálogo maestro de productos, precios, costos, ADR y promociones."
      actions={
        <div className="flex gap-2">
          <Link to="/app/productos/catalogs">
            <Button variant="secondary">Catálogos</Button>
          </Link>
          <Link to="/app/productos/new">
            <Button>Nuevo producto</Button>
          </Link>
        </div>
      }
    >
      {productsQuery.error ? (
        <Alert title="No se pudo cargar productos">{productsQuery.error.message}</Alert>
      ) : null}
      <Card>
        <CardHeader>
          <CardTitle>Catálogo de productos</CardTitle>
          <CardDescription>Consulta por nombre o SKU y entra al detalle operativo del producto.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-[1fr_auto]">
            <Input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Busca por SKU o nombre"
            />
            <div className="text-sm text-slate-400">
              {productsQuery.data ? `${productsQuery.data.total} registros` : "Cargando..."}
            </div>
          </div>
          <DataTable
            columns={[
              { key: "sku", header: "SKU", render: (row) => row.sku },
              { key: "name", header: "Producto", render: (row) => row.name },
              { key: "line", header: "Línea", render: (row) => row.line_name ?? "-" },
              { key: "brand", header: "Marca", render: (row) => row.brand_name ?? "-" },
              { key: "condition", header: "Condición", render: (row) => row.condition_code },
              { key: "active", header: "Activo", render: (row) => (row.is_active ? "Sí" : "No") },
              {
                key: "actions",
                header: "Acciones",
                render: (row) => (
                  <div className="flex gap-2">
                    <Link to={`/app/productos/${row.id}`}>
                      <Button variant="secondary">Editar</Button>
                    </Link>
                    <Link to={`/app/productos/${row.id}/detail`}>
                      <Button variant="secondary">Detalle</Button>
                    </Link>
                  </div>
                ),
              },
            ]}
            rows={productsQuery.data?.items ?? []}
            rowKey={(row) => row.id}
            emptyMessage="Aún no hay productos registrados."
          />
        </CardContent>
      </Card>
    </ProductosSection>
  );
}
