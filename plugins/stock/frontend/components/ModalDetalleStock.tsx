import { useQuery } from "../../../../apps/web/src/lib/react-query";
import { Alert } from "../../../../apps/web/src/shared/ui/alert";
import { Button } from "../../../../apps/web/src/shared/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../../../apps/web/src/shared/ui/card";
import { DataTable } from "../../../../apps/web/src/shared/ui/data-table";
import { Dialog } from "../../../../apps/web/src/shared/ui/dialog";
import { getBalanceDetail, listProductWarehouseLedger, stockKeys } from "../api";

const OPERATION_LABELS: Record<string, string> = {
  SALE_OUT: "Salida por venta",
  sale_out: "Salida por venta",
  PURCHASE_IN: "Entrada por compra",
  purchase_in: "Entrada por compra",
  RETURN_IN: "Devolución recibida",
  return_in: "Devolución recibida",
  RETURN_IN_FALLBACK: "Devolución (fallback)",
  return_in_fallback: "Devolución (fallback)",
  PURCHASE_IN_FALLBACK: "Compra (fallback)",
  purchase_in_fallback: "Compra (fallback)",
  DAMAGE_OUT: "Baja por daño",
  damage_out: "Baja por daño",
  TRANSFER_OUT: "Transferencia (salida)",
  transfer_out: "Transferencia (salida)",
  TRANSFER_IN: "Transferencia (entrada)",
  transfer_in: "Transferencia (entrada)",
  ADJUST: "Ajuste manual",
  adjust: "Ajuste manual",
  INITIAL: "Stock inicial",
  SEED: "Carga inicial",
  LEGACY: "Migración legacy",
  FILL: "Llenado de envase",
  CREATE: "Alta de envase",
};

const TYPE_LABELS: Record<string, string> = {
  movement: "Movimiento",
  purchase_order: "Orden de compra",
  waybill: "Guía de remisión",
  quote: "Cotización",
  return_note: "Nota de devolución",
  damage_report: "Reporte de daño",
  seed: "Carga inicial",
  manual: "Manual",
  adjustment: "Ajuste",
  initial_setup: "Configuración inicial",
  test: "Prueba",
  transfer: "Transferencia",
};

const OP_TAGS: Record<string, string> = {
  sale_out: "Venta",
  purchase_in: "Compra",
  return_in: "Devolución",
  return_in_fallback: "Devolución (alt)",
  purchase_in_fallback: "Compra (alt)",
  damage_out: "Daño",
  transfer: "Transferencia",
  legacy: "Legacy",
  stock: "Stock",
  "cylinder-fill": "Llenado de envase",
  "cylinder-create": "Alta de envase",
};

function formatReference(referenceType: string | null, referenceId: string | null, operation: string): string {
  const opLabel = OPERATION_LABELS[operation] || operation;
  const typeLabel = referenceType ? TYPE_LABELS[referenceType] || referenceType : null;
  const base = typeLabel || opLabel;

  if (!referenceId) return base;

  const parts = referenceId.split(":");
  if (parts.length >= 2) {
    const middle = parts[1];
    if (middle && OP_TAGS[middle]) {
      return `${base} · ${OP_TAGS[middle]}`;
    }
    if (parts.length >= 2 && parts[0] in OP_TAGS) {
      return `${base} · ${OP_TAGS[parts[0]]}`;
    }
  }

  if (referenceId.length <= 20) return `${base} · ${referenceId}`;
  return base;
}

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
          <p className="text-sm text-muted-foreground">
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
          <div className="rounded-lg border border-border bg-surface p-4">
            <p className="text-xs uppercase tracking-wide text-muted-foreground">Producto</p>
            <p className="mt-2 text-sm text-foreground">{detailQuery.data?.product_name ?? "-"}</p>
          </div>
          <div className="rounded-lg border border-border bg-surface p-4">
            <p className="text-xs uppercase tracking-wide text-muted-foreground">Almacén</p>
            <p className="mt-2 text-sm text-foreground">{detailQuery.data?.warehouse_name ?? "-"}</p>
          </div>
          <div className="rounded-lg border border-border bg-surface p-4">
            <p className="text-xs uppercase tracking-wide text-muted-foreground">Cantidad</p>
            <p className="mt-2 text-sm text-foreground">{detailQuery.data?.quantity ?? 0}</p>
          </div>
          <div className="rounded-lg border border-border bg-surface p-4">
            <p className="text-xs uppercase tracking-wide text-muted-foreground">Mín/Máx</p>
            <p className="mt-2 text-sm text-foreground">
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
              { key: "reference", header: "Referencia", render: (row) => formatReference(row.reference_type, row.reference_id, row.operation) },
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
