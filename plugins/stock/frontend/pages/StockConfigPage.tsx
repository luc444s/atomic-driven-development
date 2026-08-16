import { useState } from "react";

import type { ProductSearchDialogItem } from "../../../../apps/web/src/components/ProductSearchDialog";
import { useQuery } from "../../../../apps/web/src/lib/react-query";
import { Alert } from "@systutor/shell/ui/alert";
import { Button } from "@systutor/shell/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@systutor/shell/ui/card";
import { DataTable } from "@systutor/shell/ui/data-table";
import { Input } from "@systutor/shell/ui/input";
import { Select } from "@systutor/shell/ui/select";
import { listConfigs, listWarehousesCatalog, stockKeys } from "../api";
import { ModalConfigStock } from "../components/ModalConfigStock";
import { StockSection } from "../components/StockSection";
import type { StockConfig } from "../types";

export function StockConfigPage() {
  const [search, setSearch] = useState("");
  const [warehouseFilter, setWarehouseFilter] = useState("");
  const [editConfig, setEditConfig] = useState<ProductSearchDialogItem | null>(null);
  const [editWarehouseId, setEditWarehouseId] = useState<string>("");

  const configsQuery = useQuery({
    queryKey: stockKeys.config.list({ q: search, warehouse_id: warehouseFilter }),
    queryFn: () =>
      listConfigs({
        warehouse_id: warehouseFilter || undefined,
      }),
  });
  const warehousesQuery = useQuery({ queryKey: stockKeys.warehouses, queryFn: listWarehousesCatalog });

  const filteredConfigs = (configsQuery.data ?? []).filter(
    (config) =>
      !search ||
      config.product_sku.toLowerCase().includes(search.toLowerCase()) ||
      config.product_name.toLowerCase().includes(search.toLowerCase()),
  );

  return (
    <StockSection
      title="Configuración de Stock"
      description="Mínimos y máximos por producto y almacén."
      actions={
        <Button
          onClick={() => {
            setEditConfig({ id: "", sku: "", name: "", brand_name: null, condition_code: "-", is_active: true });
            setEditWarehouseId("");
          }}
        >
          Nueva configuración
        </Button>
      }
    >
      {configsQuery.error ? (
        <Alert title="No se pudo cargar configuraciones">{configsQuery.error.message}</Alert>
      ) : null}
      {warehousesQuery.error ? (
        <Alert title="No se pudo cargar almacenes">{warehousesQuery.error.message}</Alert>
      ) : null}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Configuraciones</CardTitle>
            <CardDescription>
              {filteredConfigs.length} configuración{filteredConfigs.length !== 1 ? "es" : ""}.
            </CardDescription>
          </CardHeader>
          <CardContent className="text-2xl font-semibold text-foreground">
            {filteredConfigs.filter((c) => c.is_active).length} activas
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Con alerta</CardTitle>
            <CardDescription>Configuraciones con mínimo mayor a cero.</CardDescription>
          </CardHeader>
          <CardContent className="text-2xl font-semibold text-amber-300">
            {filteredConfigs.filter((c) => c.is_active && c.min_quantity > 0).length}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Lista de configuraciones</CardTitle>
          <CardDescription>Gestiona los umbrales de stock por producto y almacén.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-[1fr_260px]">
            <Input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Buscar por SKU o producto"
            />
            <Select
              value={warehouseFilter}
              onChange={setWarehouseFilter}
              placeholder="Todos los almacenes"
              options={[
                { value: "", label: "Todos los almacenes" },
                ...(warehousesQuery.data ?? []).map((warehouse) => ({
                  value: warehouse.id,
                  label: `${warehouse.code} · ${warehouse.name}`,
                })),
              ]}
            />
          </div>
          <DataTable
            columns={[
              { key: "sku", header: "SKU", render: (row: StockConfig) => row.product_sku },
              { key: "product", header: "Producto", render: (row: StockConfig) => row.product_name },
              { key: "warehouse", header: "Almacén", render: (row: StockConfig) => `${row.warehouse_code} · ${row.warehouse_name}` },
              { key: "min", header: "Mínimo", render: (row: StockConfig) => row.min_quantity },
              { key: "max", header: "Máximo", render: (row: StockConfig) => row.max_quantity ?? "-" },
              { key: "active", header: "Activo", render: (row: StockConfig) => (row.is_active ? "Sí" : "No") },
              {
                key: "actions",
                header: "Acciones",
                render: (row: StockConfig) => (
                  <Button
                    variant="secondary"
                    onClick={() => {
                      setEditConfig({
                        id: row.product_id,
                        sku: row.product_sku,
                        name: row.product_name,
                        brand_name: null,
                        condition_code: "-",
                        is_active: true,
                      });
                      setEditWarehouseId(row.warehouse_id);
                    }}
                  >
                    Editar
                  </Button>
                ),
              },
            ]}
            rows={filteredConfigs}
            rowKey={(row: StockConfig) => row.id}
            emptyMessage="No hay configuraciones de stock."
          />
        </CardContent>
      </Card>

      <ModalConfigStock
        open={editConfig !== null}
        initialProduct={editConfig?.id ? editConfig : null}
        initialWarehouseId={editWarehouseId || null}
        onClose={() => {
          setEditConfig(null);
          setEditWarehouseId("");
        }}
      />
    </StockSection>
  );
}
