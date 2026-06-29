import { useQuery } from "../../../../apps/web/src/lib/react-query";
import { Alert } from "../../../../apps/web/src/shared/ui/alert";
import { Button } from "../../../../apps/web/src/shared/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../../../apps/web/src/shared/ui/card";
import { DataTable } from "../../../../apps/web/src/shared/ui/data-table";
import { Dialog } from "../../../../apps/web/src/shared/ui/dialog";
import { getBalanceDetail, listProductWarehouseLedger, stockKeys } from "../api";

export type ModalDetalleStockProps = {
  open: boolean;
  productId: string;
  warehouseId: string;
  onClose: () => void;
  onOpenAdjust?: () => void;
  onOpenTransfer?: () => void;
  onOpenConfig?: () => void;
  asPage?: boolean;
};

export function ModalDetalleStock({
  open,
  productId,
  warehouseId,
  onClose,
  onOpenAdjust,
  onOpenTransfer,
  onOpenConfig,
  asPage,
}: ModalDetalleStockProps) {
  const detailQuery = useQuery({
    queryKey: stockKeys.balances.detail(productId, warehouseId),
    queryFn: () => getBalanceDetail(productId, warehouseId),
    enabled: open,
  });
  const ledgerQuery = useQuery({
    queryKey: stockKeys.ledger.byWarehouse(productId, warehouseId, {}),
    queryFn: () => listProductWarehouseLedger(productId, warehouseId, { limit: 100, offset: 0 }),
    enabled: open,
  });

  const content = (
    <div className="space-y-6">
      {detailQuery.error ? (
        <Alert title="No se pudo cargar el balance">{detailQuery.error.message}</Alert>
      ) : null}
      {ledgerQuery.error ? (
        <Alert title="No se pudo cargar el ledger">{ledgerQuery.error.message}</Alert>
      ) : null}
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm text-slate-400">
            {detailQuery.data
              ? `${detailQuery.data.product_sku} · ${detailQuery.data.warehouse_code}`
              : "Cargando..."}
          </p>
        </div>
        {onOpenAdjust || onOpenTransfer || onOpenConfig ? (
          <div className="flex gap-2">
            {onOpenAdjust ? (
              <Button variant="secondary" onClick={onOpenAdjust}>
                Ajustar
              </Button>
            ) : null}
            {onOpenTransfer ? (
              <Button variant="secondary" onClick={onOpenTransfer}>
                Transferir
              </Button>
            ) : null}
            {onOpenConfig ? (
              <Button variant="secondary" onClick={onOpenConfig}>
                Configurar
              </Button>
            ) : null}
          </div>
        ) : null}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Balance actual</CardTitle>
          <CardDescription>Resumen por producto y almacén.</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <div className="rounded-lg border border-slate-800 bg-slate-950 p-4">
            <p className="text-xs uppercase tracking-wide text-slate-500">Producto</p>
            <p className="mt-2 text-sm text-slate-100">{detailQuery.data?.product_name ?? "-"}</p>
          </div>
          <div className="rounded-lg border border-slate-800 bg-slate-950 p-4">
            <p className="text-xs uppercase tracking-wide text-slate-500">Almacén</p>
            <p className="mt-2 text-sm text-slate-100">{detailQuery.data?.warehouse_name ?? "-"}</p>
          </div>
          <div className="rounded-lg border border-slate-800 bg-slate-950 p-4">
            <p className="text-xs uppercase tracking-wide text-slate-500">Cantidad</p>
            <p className="mt-2 text-sm text-slate-100">{detailQuery.data?.quantity ?? 0}</p>
          </div>
          <div className="rounded-lg border border-slate-800 bg-slate-950 p-4">
            <p className="text-xs uppercase tracking-wide text-slate-500">Mín/Máx</p>
            <p className="mt-2 text-sm text-slate-100">
              {detailQuery.data?.min_quantity ?? "-"} / {detailQuery.data?.max_quantity ?? "-"}
            </p>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Ledger</CardTitle>
          <CardDescription>Movimientos registrados para este producto en este almacén.</CardDescription>
        </CardHeader>
        <CardContent>
          <DataTable
            columns={[
              { key: "operation", header: "Operación", render: (row) => row.operation },
              { key: "quantity", header: "Cantidad", render: (row) => row.quantity },
              { key: "after", header: "Saldo", render: (row) => row.balance_after },
              { key: "reference", header: "Referencia", render: (row) => row.reference_id ?? "-" },
              { key: "notes", header: "Notas", render: (row) => row.notes ?? "-" },
              { key: "created", header: "Fecha", render: (row) => new Date(row.created_at).toLocaleString() },
            ]}
            rows={ledgerQuery.data ?? []}
            rowKey={(row) => row.id}
            emptyMessage="Aún no hay movimientos registrados."
          />
        </CardContent>
      </Card>
    </div>
  );

  if (asPage) {
    return content;
  }

  return (
    <Dialog
      open={open}
      title="Detalle de stock"
      description="Vista operativa del balance y su ledger."
      onClose={onClose}
      maxWidthClassName="max-w-6xl"
    >
      {content}
    </Dialog>
  );
}
