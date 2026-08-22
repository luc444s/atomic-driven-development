import { useEffect, useState } from "react";

import { useQuery } from "../../../../apps/web/src/lib/react-query";
import { Alert } from "@systutor/shell/ui/alert";
import { Button } from "@systutor/shell/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@systutor/shell/ui/card";
import { DataTable } from "@systutor/shell/ui/data-table";
import { Input } from "@systutor/shell/ui/input";
import { Pagination } from "@systutor/shell/ui/pagination";
import { listProducts, productosKeys } from "../api";
import { ModalCatalogo } from "../components/ModalCatalogo";
import { ModalDetalleProducto } from "../components/ModalDetalleProducto";
import { ModalNuevoProducto } from "../components/ModalNuevoProducto";
import { ProductosSection } from "../components/ProductosSection";

export function ProductListPage() {
  const pageSize = 10;
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [showNew, setShowNew] = useState(false);
  const [editId, setEditId] = useState<string | null>(null);
  const [detailId, setDetailId] = useState<string | null>(null);
  const [showCatalogo, setShowCatalogo] = useState(false);

  useEffect(() => {
    setPage(1);
  }, [search]);

  const productsQuery = useQuery({
    queryKey: productosKeys.products.list({ search, page, limit: pageSize }),
    queryFn: () =>
      listProducts({
        limit: pageSize,
        offset: (page - 1) * pageSize,
        sku: search,
        name: search,
      }),
  });
  const totalPages = productsQuery.data
    ? Math.max(1, Math.ceil(productsQuery.data.total / productsQuery.data.limit))
    : 1;

  return (
    <ProductosSection
      title="Productos"
      description="Catálogo maestro de productos, precios, costos, ADR y promociones."
      actions={
        <div className="flex gap-2">
          <Button variant="secondary" onClick={() => setShowCatalogo(true)}>Catálogos</Button>
          <Button onClick={() => { setEditId(null); setShowNew(true); }}>Nuevo producto</Button>
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
            <div className="text-sm text-muted-foreground">
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
            ]}
            rows={productsQuery.data?.items ?? []}
            rowKey={(row) => row.id}
            onRowDoubleClick={(row) => setDetailId(row.id)}
            emptyMessage="Aún no hay productos registrados."
          />
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-sm text-muted-foreground">
              {productsQuery.data
                ? `${productsQuery.data.total} productos`
                : "Cargando productos..."}
            </p>
            <Pagination page={page} totalPages={totalPages} onChange={setPage} />
          </div>
        </CardContent>
      </Card>

      <ModalNuevoProducto
        open={showNew}
        productId={editId ?? undefined}
        onClose={() => { setShowNew(false); setEditId(null); }}
        onSaved={() => {
          productsQuery.refetch();
        }}
        onOpenDetail={(id) => {
          setShowNew(false);
          setEditId(null);
          setDetailId(id);
        }}
      />

      <ModalDetalleProducto
        open={detailId !== null}
        productId={detailId ?? ""}
        onClose={() => setDetailId(null)}
        onEditProduct={(id) => {
          setDetailId(null);
          setEditId(id);
          setShowNew(true);
        }}
      />

      <ModalCatalogo
        open={showCatalogo}
        onClose={() => setShowCatalogo(false)}
      />
    </ProductosSection>
  );
}
