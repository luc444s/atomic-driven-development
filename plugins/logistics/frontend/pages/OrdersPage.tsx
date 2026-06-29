import { useMutation, useQuery, useQueryClient } from "../../../../apps/web/src/lib/react-query";
import { FormEvent, useState } from "react";
import type { CustomerBrief } from "../../../crm/frontend/types";

import {
  createOrder,
  createOrderItem,
  listOrderItems,
  listOrders,
  listWarehouses,
  logisticsKeys,
} from "../api";
import { listCustomers } from "../../../crm/frontend/api";
import { CustomerSearchDialog } from "../../../crm/frontend/components/CustomerSearchDialog";
import { LogisticsSection } from "../components/LogisticsSection";
import { Alert } from "../../../../apps/web/src/shared/ui/alert";
import { Button } from "../../../../apps/web/src/shared/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../../../apps/web/src/shared/ui/card";
import { DataTable } from "../../../../apps/web/src/shared/ui/data-table";
import { Dialog } from "../../../../apps/web/src/shared/ui/dialog";
import { Input } from "../../../../apps/web/src/shared/ui/input";

type OrderFormState = {
  customer_id: string;
  customer_name: string;
  movement_type: string;
  warehouse_id: string;
  notes: string;
};

type OrderItemFormState = {
  product_name: string;
  quantity_requested: string;
  quantity_planned: string;
  location: string;
};

const EMPTY_ORDER: OrderFormState = { customer_id: "", customer_name: "", movement_type: "SC", warehouse_id: "", notes: "" };
const EMPTY_ITEM: OrderItemFormState = {
  product_name: "",
  quantity_requested: "1",
  quantity_planned: "1",
  location: "ALMACEN",
};

export function OrdersPage() {
  const queryClient = useQueryClient();
  const [orderForm, setOrderForm] = useState<OrderFormState>(EMPTY_ORDER);
  const [itemForm, setItemForm] = useState<OrderItemFormState>(EMPTY_ITEM);
  const [isOrderOpen, setIsOrderOpen] = useState(false);
  const [isItemOpen, setIsItemOpen] = useState(false);
  const [isCustomerSearchOpen, setIsCustomerSearchOpen] = useState(false);
  const [selectedOrderId, setSelectedOrderId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const ordersQuery = useQuery({
    queryKey: logisticsKeys.orders.list({}),
    queryFn: () => listOrders({}),
  });
  const warehousesQuery = useQuery({ queryKey: logisticsKeys.warehouses(), queryFn: listWarehouses });
  const customersQuery = useQuery({
    queryKey: ["crm", "customers", "logistics-lookup"],
    queryFn: () => listCustomers({ limit: 200, offset: 0 }),
  });
  const itemsQuery = useQuery({
    queryKey: logisticsKeys.orders.items(selectedOrderId ?? ""),
    queryFn: () => listOrderItems(selectedOrderId!),
    enabled: selectedOrderId !== null,
  });

  const createOrderMutation = useMutation({
    mutationFn: createOrder,
    onSuccess: async (order) => {
      setIsOrderOpen(false);
      setOrderForm(EMPTY_ORDER);
      setSelectedOrderId(order.id);
      setError(null);
      await queryClient.invalidateQueries({ queryKey: logisticsKeys.orders.all() });
    },
  });

  const createItemMutation = useMutation({
    mutationFn: async (payload: OrderItemFormState) =>
      createOrderItem(selectedOrderId!, {
        product_name: payload.product_name,
        quantity_requested: Number(payload.quantity_requested),
        quantity_planned: Number(payload.quantity_planned),
        location: payload.location,
      }),
    onSuccess: async () => {
      setIsItemOpen(false);
      setItemForm(EMPTY_ITEM);
      setError(null);
      await queryClient.invalidateQueries({ queryKey: logisticsKeys.orders.items(selectedOrderId!) });
    },
  });

  async function submitOrder(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    try {
      await createOrderMutation.mutateAsync({
        customer_id: orderForm.customer_id,
        movement_type: orderForm.movement_type,
        warehouse_id: orderForm.warehouse_id || null,
        notes: orderForm.notes || null,
      });
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "No se pudo crear el pedido.");
    }
  }

  async function submitItem(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedOrderId) {
      return;
    }
    setError(null);
    try {
      await createItemMutation.mutateAsync(itemForm);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "No se pudo agregar la línea.");
    }
  }

  return (
    <LogisticsSection
      title="Pedidos"
      description="Registra solicitudes y completa las líneas que después alimentarán rutas y movimientos."
      actions={<Button onClick={() => setIsOrderOpen(true)}>Nuevo pedido</Button>}
    >
      {error ? <Alert title="No se pudo completar la acción">{error}</Alert> : null}

      <div className="grid gap-6 xl:grid-cols-[1.35fr,1fr]">
        <Card>
          <CardHeader>
            <CardTitle>Pedidos activos</CardTitle>
            <CardDescription>Vista simple del trabajo pendiente y en curso.</CardDescription>
          </CardHeader>
          <CardContent>
            <DataTable
              columns={[
                {
                  key: "customer",
                  header: "Cliente",
                  render: (row) =>
                    customersQuery.data?.items.find((item) => item.id === row.customer_id)?.legal_name ?? row.customer_name,
                },
                { key: "type", header: "Tipo", render: (row) => row.movement_type },
                { key: "status", header: "Estado", render: (row) => row.status },
                {
                  key: "warehouse",
                  header: "Almacén",
                  render: (row) => warehousesQuery.data?.find((item) => item.id === row.warehouse_id)?.name ?? "-",
                },
                {
                  key: "actions",
                  header: "Detalle",
                  className: "w-32",
                  render: (row) => (
                    <Button variant="secondary" onClick={() => setSelectedOrderId(row.id)}>
                      Ver
                    </Button>
                  ),
                },
              ]}
              rows={ordersQuery.data ?? []}
              rowKey={(row) => row.id}
              emptyMessage="Aún no hay pedidos registrados."
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center justify-between gap-3">
              <div>
                <CardTitle>Detalle</CardTitle>
                <CardDescription>Líneas del pedido seleccionado.</CardDescription>
              </div>
              {selectedOrderId ? (
                <Button variant="secondary" onClick={() => setIsItemOpen(true)}>
                  Agregar línea
                </Button>
              ) : null}
            </div>
          </CardHeader>
          <CardContent>
            <DataTable
              columns={[
                { key: "product", header: "Producto", render: (row) => row.product_name },
                { key: "qty", header: "Solicitado", render: (row) => String(row.quantity_requested) },
                { key: "planned", header: "Planificado", render: (row) => String(row.quantity_planned) },
                { key: "location", header: "Origen", render: (row) => row.location ?? "-" },
              ]}
              rows={itemsQuery.data ?? []}
              rowKey={(row) => row.id}
              emptyMessage={selectedOrderId ? "Este pedido aún no tiene líneas." : "Selecciona un pedido."}
            />
          </CardContent>
        </Card>
      </div>

      <Dialog
        open={isOrderOpen}
        title="Nuevo pedido"
        description="Crea una cabecera simple para empezar a trabajar la solicitud."
        onClose={() => setIsOrderOpen(false)}
      >
        <form className="space-y-4" onSubmit={submitOrder}>
          <div className="space-y-2 text-sm text-slate-300">
            <span>Cliente</span>
            <Button type="button" variant="secondary" onClick={() => setIsCustomerSearchOpen(true)}>
              {orderForm.customer_name ? `${orderForm.customer_name} (${orderForm.customer_id})` : "Seleccionar cliente"}
            </Button>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <label className="block space-y-2 text-sm text-slate-300">
              <span>Tipo</span>
              <select
                value={orderForm.movement_type}
                onChange={(event) => setOrderForm((current) => ({ ...current, movement_type: event.target.value }))}
                className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-200"
              >
                <option value="SC">Salida cliente</option>
                <option value="IC">Ingreso cliente</option>
                <option value="TR">Traslado</option>
              </select>
            </label>
            <label className="block space-y-2 text-sm text-slate-300">
              <span>Almacén</span>
              <select
                value={orderForm.warehouse_id}
                onChange={(event) => setOrderForm((current) => ({ ...current, warehouse_id: event.target.value }))}
                className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-200"
              >
                <option value="">Sin definir</option>
                {(warehousesQuery.data ?? []).map((warehouse) => (
                  <option key={warehouse.id} value={warehouse.id}>
                    {warehouse.name}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <label className="block space-y-2 text-sm text-slate-300">
            <span>Notas</span>
            <Input value={orderForm.notes} onChange={(event) => setOrderForm((current) => ({ ...current, notes: event.target.value }))} />
          </label>
          <div className="flex justify-end gap-3">
            <Button type="button" variant="secondary" onClick={() => setIsOrderOpen(false)}>
              Cancelar
            </Button>
            <Button type="submit" disabled={createOrderMutation.isPending}>
              Guardar
            </Button>
          </div>
        </form>
      </Dialog>

      <CustomerSearchDialog
        open={isCustomerSearchOpen}
        onOpenChange={setIsCustomerSearchOpen}
        onSelect={(customer: CustomerBrief) =>
          setOrderForm((current) => ({ ...current, customer_id: customer.id, customer_name: customer.legal_name }))
        }
      />

      <Dialog
        open={isItemOpen}
        title="Agregar línea"
        description="Añade una referencia básica al pedido seleccionado."
        onClose={() => setIsItemOpen(false)}
      >
        <form className="space-y-4" onSubmit={submitItem}>
          <label className="block space-y-2 text-sm text-slate-300">
            <span>Producto</span>
            <Input value={itemForm.product_name} onChange={(event) => setItemForm((current) => ({ ...current, product_name: event.target.value }))} />
          </label>
          <div className="grid gap-4 md:grid-cols-3">
            <label className="block space-y-2 text-sm text-slate-300">
              <span>Solicitado</span>
              <Input value={itemForm.quantity_requested} onChange={(event) => setItemForm((current) => ({ ...current, quantity_requested: event.target.value }))} />
            </label>
            <label className="block space-y-2 text-sm text-slate-300">
              <span>Planificado</span>
              <Input value={itemForm.quantity_planned} onChange={(event) => setItemForm((current) => ({ ...current, quantity_planned: event.target.value }))} />
            </label>
            <label className="block space-y-2 text-sm text-slate-300">
              <span>Origen</span>
              <Input value={itemForm.location} onChange={(event) => setItemForm((current) => ({ ...current, location: event.target.value }))} />
            </label>
          </div>
          <div className="flex justify-end gap-3">
            <Button type="button" variant="secondary" onClick={() => setIsItemOpen(false)}>
              Cancelar
            </Button>
            <Button type="submit" disabled={createItemMutation.isPending}>
              Guardar
            </Button>
          </div>
        </form>
      </Dialog>
    </LogisticsSection>
  );
}
