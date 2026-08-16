import { useMutation, useQuery, useQueryClient } from "../../../../apps/web/src/lib/react-query";
import { FormEvent, useState } from "react";
import type { CustomerBrief } from "../../../crm/frontend/types";
import type { ProductSearchItem } from "../../../productos/frontend/types";

import {
  createOrder,
  createOrderItem,
  listOrderItems,
  listOrders,
  listWarehouses,
  logisticsKeys,
} from "../api";
import { getRealWarehouses } from "../api/warehouses";
import { listCustomers } from "../../../crm/frontend/api";
import { CustomerSearchDialog } from "../../../crm/frontend/components/CustomerSearchDialog";
import { ProductSearchDialog } from "../../../productos/frontend/components/ProductSearchDialog";
import { LogisticsSection } from "../components/LogisticsSection";
import { Alert } from "@systutor/shell/ui/alert";
import { Button } from "@systutor/shell/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@systutor/shell/ui/card";
import { DataTable } from "@systutor/shell/ui/data-table";
import { Dialog } from "@systutor/shell/ui/dialog";
import { Input } from "@systutor/shell/ui/input";
import { Select } from "@systutor/shell/ui/select";

type OrderFormState = {
  customer_id: string;
  customer_name: string;
  movement_type: string;
  warehouse_id: string;
  notes: string;
};

type OrderItemFormState = {
  product_id: string;
  product_name: string;
  quantity_requested: string;
  quantity_planned: string;
  location: string;
};

const EMPTY_ORDER: OrderFormState = { customer_id: "", customer_name: "", movement_type: "SC", warehouse_id: "", notes: "" };
const EMPTY_ITEM: OrderItemFormState = {
  product_id: "",
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
  const [isProductSearchOpen, setIsProductSearchOpen] = useState(false);
  const [selectedOrderId, setSelectedOrderId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const ordersQuery = useQuery({
    queryKey: logisticsKeys.orders.list({}),
    queryFn: () => listOrders({}),
  });
  const warehousesQuery = useQuery({ queryKey: logisticsKeys.warehouses(), queryFn: listWarehouses });
  const realWarehouses = getRealWarehouses(warehousesQuery.data ?? []);
  const customersQuery = useQuery({
    queryKey: ["crm", "customers", "logistics-lookup"],
    queryFn: () => listCustomers({ limit: 200, offset: 0 }),
  });
  const itemsQuery = useQuery({
    queryKey: logisticsKeys.orders.items(selectedOrderId ?? ""),
    queryFn: () => listOrderItems(selectedOrderId!),
    enabled: selectedOrderId !== null,
  });

  function openItemDialog() {
    setError(null);
    setItemForm(EMPTY_ITEM);
    setIsItemOpen(true);
  }

  function closeItemDialog() {
    setIsItemOpen(false);
    setIsProductSearchOpen(false);
    setItemForm(EMPTY_ITEM);
  }

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
        product_id: payload.product_id,
        product_name: payload.product_name,
        quantity_requested: Number(payload.quantity_requested),
        quantity_planned: Number(payload.quantity_planned),
        location: payload.location,
      }),
    onSuccess: async () => {
      setIsItemOpen(false);
      setIsProductSearchOpen(false);
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
    if (!itemForm.product_id) {
      setError("Selecciona un producto para continuar.");
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
                    customersQuery.data?.items.find((item) => item.id === row.customer_id)?.commercial_name ??
                    customersQuery.data?.items.find((item) => item.id === row.customer_id)?.legal_name ??
                    row.customer_name,
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
                <Button variant="secondary" onClick={openItemDialog}>
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
          <div className="space-y-2 text-sm text-foreground">
            <span>Cliente</span>
            <Button type="button" variant="secondary" onClick={() => setIsCustomerSearchOpen(true)}>
              {orderForm.customer_name ? `${orderForm.customer_name} (${orderForm.customer_id})` : "Seleccionar cliente"}
            </Button>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <label className="block space-y-2 text-sm text-foreground">
              <span>Tipo</span>
              <Select
                value={orderForm.movement_type}
                onChange={(value) => setOrderForm((current) => ({ ...current, movement_type: value }))}
                options={[
                  { value: "SC", label: "Salida cliente" },
                  { value: "IC", label: "Ingreso cliente" },
                  { value: "TR", label: "Traslado" },
                ]} />
            </label>
            <label className="block space-y-2 text-sm text-foreground">
              <span>Almacén</span>
              <Select
                value={orderForm.warehouse_id}
                onChange={(value) => setOrderForm((current) => ({ ...current, warehouse_id: value }))}
                placeholder="Sin definir"
                options={realWarehouses.map((warehouse) => ({ value: warehouse.id, label: warehouse.name }))} />
            </label>
          </div>
          <label className="block space-y-2 text-sm text-foreground">
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
          setOrderForm((current) => ({ ...current, customer_id: customer.id, customer_name: customer.display_name }))
        }
      />

      <Dialog
        open={isItemOpen}
        title="Agregar línea"
        description="Selecciona un producto real para agregar la línea del pedido."
        onClose={closeItemDialog}
      >
        <form className="space-y-4" onSubmit={submitItem}>
          <div className="space-y-3 rounded-lg border border-border bg-card p-4">
            <div className="flex items-start justify-between gap-4">
              <div className="space-y-1">
                <p className="text-sm font-medium text-foreground">Producto seleccionado</p>
                <p className="text-sm text-muted-foreground">
                  {itemForm.product_id
                    ? `${itemForm.product_name} (${itemForm.product_id})`
                    : "Selecciona un producto del catálogo para continuar."}
                </p>
              </div>
              <Button type="button" variant="secondary" onClick={() => setIsProductSearchOpen(true)}>
                {itemForm.product_id ? "Cambiar producto" : "Buscar producto"}
              </Button>
            </div>
          </div>
          <div className="grid gap-4 md:grid-cols-3">
            <label className="block space-y-2 text-sm text-foreground">
              <span>Solicitado</span>
              <Input value={itemForm.quantity_requested} onChange={(event) => setItemForm((current) => ({ ...current, quantity_requested: event.target.value }))} />
            </label>
            <label className="block space-y-2 text-sm text-foreground">
              <span>Planificado</span>
              <Input value={itemForm.quantity_planned} onChange={(event) => setItemForm((current) => ({ ...current, quantity_planned: event.target.value }))} />
            </label>
            <label className="block space-y-2 text-sm text-foreground">
              <span>Origen</span>
              <Input value={itemForm.location} onChange={(event) => setItemForm((current) => ({ ...current, location: event.target.value }))} />
            </label>
          </div>
          <div className="flex justify-end gap-3">
            <Button type="button" variant="secondary" onClick={closeItemDialog}>
              Cancelar
            </Button>
            <Button type="submit" disabled={!itemForm.product_id || createItemMutation.isPending}>
              Guardar
            </Button>
          </div>
        </form>
      </Dialog>

      <ProductSearchDialog
        open={isProductSearchOpen}
        onOpenChange={setIsProductSearchOpen}
        onSelect={(product: ProductSearchItem) =>
          setItemForm((current) => ({
            ...current,
            product_id: product.id,
            product_name: product.name,
          }))
        }
      />
    </LogisticsSection>
  );
}
