import { useMutation, useQuery, useQueryClient } from "../../../../../../apps/web/src/lib/react-query";
import { FormEvent, forwardRef, useImperativeHandle, useState } from "react";
import {
  getOrder,
  listDispatches,
  listTanks,
  receiveOrder,
} from "../../api";
import type {
  PurchaseOrderDetail,
  ReceiveCostLine,
} from "../../types";
import type { ProductListItem } from "../../../../../productos/frontend/types";
import { listWarehouses, getRealWarehouses } from "../../../../../logistics/frontend/api/warehouses";
import { Button } from "@systutor/shell/ui/button";
import { Dialog } from "@systutor/shell/ui/dialog";
import { Input } from "@systutor/shell/ui/input";
import { Combobox } from "@systutor/shell/ui/combobox";

export type ReceiptPanelHandle = {
  openReceiveDialog: (orderId: string) => void;
};

type ReceiptPanelProps = {
  setError: (value: string | null) => void;
  products: ProductListItem[];
};

export const ReceiptPanel = forwardRef<ReceiptPanelHandle, ReceiptPanelProps>(function ReceiptPanel({ setError, products }, ref) {
  const queryClient = useQueryClient();
  const [isReceiveOpen, setIsReceiveOpen] = useState(false);
  const [selectedOrder, setSelectedOrder] = useState<PurchaseOrderDetail | null>(null);

  const [receiveForm, setReceiveForm] = useState<{
    warehouse_id: string; items: { purchase_item_id: string; quantity: number; qty_accepted?: number; qty_rejected?: number }[]; notes: string; tank_id: string; dispatch_id: string; cost_lines: ReceiveCostLine[];
  }>({ warehouse_id: "", items: [], notes: "", tank_id: "", dispatch_id: "", cost_lines: [] });

  const receiveMut = useMutation({
    mutationFn: () => selectedOrder ? receiveOrder(selectedOrder.id, { warehouse_id: receiveForm.warehouse_id, items: receiveForm.items, notes: receiveForm.notes || null, tank_id: receiveForm.tank_id || null, dispatch_id: receiveForm.dispatch_id || null, cost_lines: receiveForm.cost_lines.length ? receiveForm.cost_lines : null }) : Promise.reject("No order"),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["compras", "orders"] }); setIsReceiveOpen(false); setSelectedOrder(null); setError(null); },
    onError: (err) => setError(err instanceof Error ? err.message : "Error al recepcionar"),
  });

  const receiveProductId = selectedOrder?.items?.[0]?.product_id;
  const tanksQuery = useQuery({
    queryKey: ["compras", "tanks", receiveProductId],
    queryFn: () => listTanks(receiveProductId),
    enabled: isReceiveOpen && Boolean(receiveProductId),
  });
  const tankOptions = (tanksQuery.data ?? []).map(t => ({ value: t.id, label: `${t.serial} · ${t.description} (${t.content_kg?.toFixed(1) ?? 0} kg)` }));

  const warehousesQuery = useQuery({
    queryKey: ["logistics", "warehouses"],
    queryFn: listWarehouses,
  });
  const warehouseOptions = getRealWarehouses(warehousesQuery.data ?? []).map(w => ({
    value: w.id,
    label: `${w.code} · ${w.name}`,
  }));

  const orderDispatchesQuery = useQuery({
    queryKey: ["compras", "dispatches", { order_id: selectedOrder?.id }],
    queryFn: () => listDispatches({ order_id: selectedOrder!.id, limit: 50 }),
    enabled: isReceiveOpen && Boolean(selectedOrder),
  });
  const orderDispatchOptions = (orderDispatchesQuery.data?.items ?? []).map(d => ({
    value: d.id,
    label: `${d.dispatch_date} · ${d.status}${d.carrier ? ` · ${d.carrier}` : ""}`,
  }));

  function openReceiveDialog(orderId: string) {
    getOrder(orderId).then((detail) => {
      setSelectedOrder(detail);
      setReceiveForm({
        warehouse_id: "",
        items: detail.items.filter(i => i.received_qty < i.quantity).map(i => {
          const pending = i.quantity - i.received_qty;
          return { purchase_item_id: i.id, quantity: pending, qty_accepted: pending, qty_rejected: 0 };
        }),
        notes: "",
        tank_id: "",
        dispatch_id: "",
        cost_lines: [],
      });
      setIsReceiveOpen(true);
    });
  }

  useImperativeHandle(ref, () => ({ openReceiveDialog }));

  return (
    <Dialog open={isReceiveOpen} title="Recepcionar mercadería" description="Selecciona almacén y confirma cantidades." onClose={() => { setIsReceiveOpen(false); setSelectedOrder(null); }}>
      <form className="space-y-4" onSubmit={(e: FormEvent) => { e.preventDefault(); receiveMut.mutate(); }}>
        <label className="block space-y-2 text-sm text-foreground"><span>Almacén destino *</span><Combobox value={receiveForm.warehouse_id} onChange={(v) => setReceiveForm(p => ({ ...p, warehouse_id: v }))} options={warehouseOptions} placeholder="Seleccionar almacén" searchPlaceholder="Buscar almacén" /></label>
        {tankOptions.length > 0 ? (
          <label className="block space-y-2 text-sm text-foreground">
            <span>Tanque criogénico destino</span>
            <Combobox value={receiveForm.tank_id} onChange={(v) => setReceiveForm(p => ({ ...p, tank_id: v }))}
              options={tankOptions} placeholder="Seleccionar tanque (opcional)" searchPlaceholder="Buscar tanque" />
          </label>
        ) : null}
        {orderDispatchOptions.length > 0 ? (
          <label className="block space-y-2 text-sm text-foreground">
            <span>Despacho asociado</span>
            <Combobox value={receiveForm.dispatch_id} onChange={(v) => setReceiveForm(p => ({ ...p, dispatch_id: v }))}
              options={orderDispatchOptions} placeholder="Sin despacho (opcional)" searchPlaceholder="Buscar despacho" />
          </label>
        ) : null}
        <div className="space-y-2"><span className="text-sm text-foreground">Items a recibir</span>
          {receiveForm.items.map((item, i) => {
            const orderItem = selectedOrder?.items.find(oi => oi.id === item.purchase_item_id);
            const product = products.find(p => p.id === orderItem?.product_id);
            const accepted = item.qty_accepted ?? item.quantity;
            const rejected = item.qty_rejected ?? 0;
            const sum = Number(accepted) + Number(rejected);
            const sumOk = sum === Number(item.quantity);
            return (
              <div key={i} className="grid grid-cols-[1fr_70px_70px_70px] gap-2 items-center">
                <span className="text-sm flex-1">{product ? `${product.sku} · ${product.name}` : `Producto ${orderItem?.product_id?.slice(0, 8) ?? "desconocido"}`}</span>
                <Input className="w-20" value={item.quantity || ""} onChange={(e) => { const items = [...receiveForm.items]; items[i] = { ...items[i], quantity: Number(e.target.value) || 0 }; setReceiveForm(p => ({ ...p, items })); }} title="Recibidas" />
                <Input className="w-20" value={accepted} onChange={(e) => { const items = [...receiveForm.items]; items[i] = { ...items[i], qty_accepted: Number(e.target.value) || 0 }; setReceiveForm(p => ({ ...p, items })); }} title="Aceptadas" />
                <Input className="w-20" value={rejected} onChange={(e) => { const items = [...receiveForm.items]; items[i] = { ...items[i], qty_rejected: Number(e.target.value) || 0 }; setReceiveForm(p => ({ ...p, items })); }} title="Rechazadas" />
                {!sumOk ? <span className="text-xs text-destructive">acep+rech≠recib</span> : null}
              </div>
            );
          })}
          <p className="text-xs text-muted-foreground">Columnas: Recibidas · Aceptadas · Rechazadas</p>
        </div>
        <div className="space-y-2">
          <div className="flex items-center justify-between"><span className="text-sm text-foreground">Costos adicionales</span><Button type="button" variant="secondary" onClick={() => setReceiveForm(p => ({ ...p, cost_lines: [...p.cost_lines, { cost_type: "FLETE", amount: 0 }] }))}>+ Agregar</Button></div>
          {receiveForm.cost_lines.map((cl, i) => (
            <div key={i} className="grid grid-cols-[120px_100px_1fr_40px] gap-2">
              <Input value={cl.cost_type} onChange={(e) => { const cs = [...receiveForm.cost_lines]; cs[i] = { ...cs[i], cost_type: e.target.value }; setReceiveForm(p => ({ ...p, cost_lines: cs })); }} placeholder="FLETE" />
              <Input value={cl.amount || ""} onChange={(e) => { const cs = [...receiveForm.cost_lines]; cs[i] = { ...cs[i], amount: Number(e.target.value) || 0 }; setReceiveForm(p => ({ ...p, cost_lines: cs })); }} placeholder="Monto" />
              <Input value={cl.notes ?? ""} onChange={(e) => { const cs = [...receiveForm.cost_lines]; cs[i] = { ...cs[i], notes: e.target.value }; setReceiveForm(p => ({ ...p, cost_lines: cs })); }} placeholder="Notas" />
              <Button type="button" variant="secondary" onClick={() => setReceiveForm(p => ({ ...p, cost_lines: p.cost_lines.filter((_, j) => j !== i) }))}>X</Button>
            </div>
          ))}
        </div>
        <label className="block space-y-2 text-sm text-foreground"><span>Notas</span><Input value={receiveForm.notes} onChange={(e) => setReceiveForm(p => ({ ...p, notes: e.target.value }))} /></label>
        <div className="flex justify-end gap-3">
          <Button type="button" variant="secondary" onClick={() => { setIsReceiveOpen(false); setSelectedOrder(null); }}>Cancelar</Button>
          <Button type="submit" disabled={receiveMut.isPending}>{receiveMut.isPending ? "Recepcionando..." : "Recepcionar"}</Button>
        </div>
      </form>
    </Dialog>
  );
});
