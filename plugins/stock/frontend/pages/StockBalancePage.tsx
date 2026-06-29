import { useMemo, useState } from "react";

import type { ProductSearchDialogItem } from "../../../../apps/web/src/components/ProductSearchDialog";
import { useQuery } from "../../../../apps/web/src/lib/react-query";
import { Alert } from "../../../../apps/web/src/shared/ui/alert";
import { Button } from "../../../../apps/web/src/shared/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../../../apps/web/src/shared/ui/card";
import { DataTable } from "../../../../apps/web/src/shared/ui/data-table";
import { Input } from "../../../../apps/web/src/shared/ui/input";
import { listBalances, listWarehousesCatalog, stockKeys } from "../api";
import { ModalAjusteStock } from "../components/ModalAjusteStock";
import { ModalConfigStock } from "../components/ModalConfigStock";
import { ModalDetalleStock } from "../components/ModalDetalleStock";
import { StockSection } from "../components/StockSection";
import { ModalTransferenciaStock } from "../components/ModalTransferenciaStock";
import type { StockBalanceItem } from "../types";

type SelectionState = {
  productId: string;
  warehouseId: string;
  product: ProductSearchDialogItem;
};

function toProductSelection(row: StockBalanceItem): ProductSearchDialogItem {
  return {
    id: row.product_id,
    sku: row.product_sku,
    name: row.product_name,
    brand_name: null,
    condition_code: "-",
    is_active: true,
  };
}

export function StockBalancePage() {
  const [search, setSearch] = useState("");
  const [warehouseFilter, setWarehouseFilter] = useState("");
  const [belowMinOnly, setBelowMinOnly] = useState(false);
  const [adjustSelection, setAdjustSelection] = useState<SelectionState | null>(null);
  const [transferSelection, setTransferSelection] = useState<SelectionState | null>(null);
  const [configSelection, setConfigSelection] = useState<SelectionState | null>(null);
  const [detailSelection, setDetailSelection] = useState<SelectionState | null>(null);

  const balancesQuery = useQuery({
    queryKey: stockKeys.balances.list({ search, warehouseFilter, belowMinOnly }),
    queryFn: () =>
      listBalances({
        q: search,
        warehouse_id: warehouseFilter || undefined,
        below_min_only: belowMinOnly,
        limit: 100,
        offset: 0,
      }),
  });
  const warehousesQuery = useQuery({ queryKey: stockKeys.warehouses, queryFn: listWarehousesCatalog });

  const totals = useMemo(() => {
    const items = balancesQuery.data?.items ?? [];
    return {
      balances: items.length,
      alerts: items.filter((item) => item.is_below_min).length,
      quantity: items.reduce((sum, item) => sum + item.quantity, 0),
    };
  }, [balancesQuery.data?.items]);

  return (
    <StockSection
      title="Stock"
      description="Balance por producto y almacén, ledger de movimientos y configuración de mínimos/máximos."
      actions={
        <div className="flex gap-2">
          <Button variant="secondary" onClick={() => setConfigSelection({ productId: "", warehouseId: "", product: { id: "", sku: "", name: "", brand_name: null, condition_code: "-", is_active: true } })}>
            Configurar
          </Button>
          <Button variant="secondary" onClick={() => setTransferSelection({ productId: "", warehouseId: "", product: { id: "", sku: "", name: "", brand_name: null, condition_code: "-", is_active: true } })}>
            Transferir
          </Button>
          <Button onClick={() => setAdjustSelection({ productId: "", warehouseId: "", product: { id: "", sku: "", name: "", brand_name: null, condition_code: "-", is_active: true } })}>
            Ajustar
          </Button>
        </div>
      }
    >
      {balancesQuery.error ? (
        <Alert title="No se pudo cargar el stock">{balancesQuery.error.message}</Alert>
      ) : null}
      {warehousesQuery.error ? (
        <Alert title="No se pudo cargar almacenes">{warehousesQuery.error.message}</Alert>
      ) : null}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>Bases activas</CardTitle>
            <CardDescription>Producto + almacén con balance materializado.</CardDescription>
          </CardHeader>
          <CardContent className="text-2xl font-semibold text-white">{totals.balances}</CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Alertas</CardTitle>
            <CardDescription>Balances por debajo del mínimo configurado.</CardDescription>
          </CardHeader>
          <CardContent className="text-2xl font-semibold text-amber-300">{totals.alerts}</CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Cantidad total</CardTitle>
            <CardDescription>Suma de balances visibles en el filtro actual.</CardDescription>
          </CardHeader>
          <CardContent className="text-2xl font-semibold text-cyan-300">{totals.quantity}</CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Balance por producto y almacén</CardTitle>
          <CardDescription>Consulta operativa con filtros y acceso al detalle.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-[1fr_260px_auto]">
            <Input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Busca por SKU, producto o almacén"
            />
            <select
              className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-50 outline-none transition focus:border-cyan-500"
              value={warehouseFilter}
              onChange={(event) => setWarehouseFilter(event.target.value)}
            >
              <option value="">Todos los almacenes</option>
              {(warehousesQuery.data ?? []).map((warehouse) => (
                <option key={warehouse.id} value={warehouse.id}>
                  {warehouse.code} · {warehouse.name}
                </option>
              ))}
            </select>
            <label className="flex items-center gap-3 rounded-md border border-slate-800 bg-slate-950 px-3 py-2 text-sm text-slate-300">
              <input
                type="checkbox"
                checked={belowMinOnly}
                onChange={(event) => setBelowMinOnly(event.target.checked)}
              />
              Solo bajo mínimo
            </label>
          </div>
          <DataTable
            columns={[
              { key: "sku", header: "SKU", render: (row) => row.product_sku },
              { key: "product", header: "Producto", render: (row) => row.product_name },
              { key: "warehouse", header: "Almacén", render: (row) => `${row.warehouse_code} · ${row.warehouse_name}` },
              { key: "quantity", header: "Cantidad", render: (row) => row.quantity },
              { key: "limits", header: "Mín / Máx", render: (row) => `${row.min_quantity ?? "-"} / ${row.max_quantity ?? "-"}` },
              { key: "alert", header: "Alerta", render: (row) => (row.is_below_min ? "Bajo mínimo" : "OK") },
              {
                key: "actions",
                header: "Acciones",
                render: (row) => (
                  <div className="flex gap-2">
                    <Button
                      variant="secondary"
                      onClick={() =>
                        setDetailSelection({
                          productId: row.product_id,
                          warehouseId: row.warehouse_id,
                          product: toProductSelection(row),
                        })
                      }
                    >
                      Detalle
                    </Button>
                    <Button
                      variant="secondary"
                      onClick={() =>
                        setAdjustSelection({
                          productId: row.product_id,
                          warehouseId: row.warehouse_id,
                          product: toProductSelection(row),
                        })
                      }
                    >
                      Ajustar
                    </Button>
                  </div>
                ),
              },
            ]}
            rows={balancesQuery.data?.items ?? []}
            rowKey={(row) => `${row.product_id}:${row.warehouse_id}`}
            emptyMessage="Aún no hay balances materializados."
          />
        </CardContent>
      </Card>

      <ModalAjusteStock
        open={adjustSelection !== null}
        initialProduct={adjustSelection?.product.id ? adjustSelection.product : null}
        initialWarehouseId={adjustSelection?.warehouseId || null}
        onClose={() => setAdjustSelection(null)}
      />

      <ModalTransferenciaStock
        open={transferSelection !== null}
        initialProduct={transferSelection?.product.id ? transferSelection.product : null}
        initialWarehouseId={transferSelection?.warehouseId || null}
        onClose={() => setTransferSelection(null)}
      />

      <ModalConfigStock
        open={configSelection !== null}
        initialProduct={configSelection?.product.id ? configSelection.product : null}
        initialWarehouseId={configSelection?.warehouseId || null}
        onClose={() => setConfigSelection(null)}
      />

      <ModalDetalleStock
        open={detailSelection !== null}
        productId={detailSelection?.productId ?? ""}
        warehouseId={detailSelection?.warehouseId ?? ""}
        onClose={() => setDetailSelection(null)}
        onOpenAdjust={() => {
          if (!detailSelection) {
            return;
          }
          setAdjustSelection(detailSelection);
          setDetailSelection(null);
        }}
        onOpenTransfer={() => {
          if (!detailSelection) {
            return;
          }
          setTransferSelection(detailSelection);
          setDetailSelection(null);
        }}
        onOpenConfig={() => {
          if (!detailSelection) {
            return;
          }
          setConfigSelection(detailSelection);
          setDetailSelection(null);
        }}
      />
    </StockSection>
  );
}
