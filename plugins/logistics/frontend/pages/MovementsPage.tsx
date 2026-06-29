import { useMutation, useQuery, useQueryClient } from "../../../../apps/web/src/lib/react-query";
import { FormEvent, useState } from "react";
import type { CustomerBrief } from "../../../crm/frontend/types";

import {
  cancelMovement,
  confirmMovement,
  createMovement,
  listCylinderSummary,
  listCylinders,
  listMovementHistory,
  listMovementItems,
  listMovements,
  listMovementTypes,
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

type MovementFormState = {
  movement_type: string;
  customer_id: string;
  customer_name: string;
  warehouse_id: string;
  cylinder_id: string;
  quantity: string;
};

const EMPTY_FORM: MovementFormState = {
  movement_type: "SC",
  customer_id: "",
  customer_name: "",
  warehouse_id: "",
  cylinder_id: "",
  quantity: "1",
};

export function MovementsPage() {
  const queryClient = useQueryClient();
  const [formState, setFormState] = useState<MovementFormState>(EMPTY_FORM);
  const [selectedMovementId, setSelectedMovementId] = useState<string | null>(null);
  const [isOpen, setIsOpen] = useState(false);
  const [isCustomerSearchOpen, setIsCustomerSearchOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const movementsQuery = useQuery({ queryKey: logisticsKeys.movements.list({}), queryFn: () => listMovements({}) });
  const movementTypesQuery = useQuery({ queryKey: logisticsKeys.movementTypes(), queryFn: listMovementTypes });
  const warehousesQuery = useQuery({ queryKey: logisticsKeys.warehouses(), queryFn: listWarehouses });
  const customersQuery = useQuery({
    queryKey: ["crm", "customers", "logistics-lookup"],
    queryFn: () => listCustomers({ limit: 200, offset: 0 }),
  });
  const cylindersQuery = useQuery({ queryKey: logisticsKeys.cylinders.list({ active: true }), queryFn: () => listCylinders({ active: true }) });
  const itemsQuery = useQuery({
    queryKey: logisticsKeys.movements.items(selectedMovementId ?? ""),
    queryFn: () => listMovementItems(selectedMovementId!),
    enabled: selectedMovementId !== null,
  });
  const historyQuery = useQuery({
    queryKey: logisticsKeys.movements.history(selectedMovementId ?? ""),
    queryFn: () => listMovementHistory(selectedMovementId!),
    enabled: selectedMovementId !== null,
  });

  const createMutation = useMutation({
    mutationFn: createMovement,
    onSuccess: async (movement) => {
      setSelectedMovementId(movement.id);
      setIsOpen(false);
      setFormState(EMPTY_FORM);
      setError(null);
      await queryClient.invalidateQueries({ queryKey: logisticsKeys.movements.all() });
    },
  });
  const confirmMutation = useMutation({
    mutationFn: confirmMovement,
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: logisticsKeys.movements.all() }),
        queryClient.invalidateQueries({ queryKey: logisticsKeys.movements.history(selectedMovementId!) }),
        queryClient.invalidateQueries({ queryKey: logisticsKeys.cylinders.all() }),
      ]);
    },
  });
  const cancelMutation = useMutation({
    mutationFn: (movementId: string) => cancelMovement(movementId, "Cancelado desde panel"),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: logisticsKeys.movements.all() });
    },
  });

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    try {
        await createMutation.mutateAsync({
          movement_type: formState.movement_type,
          customer_id: formState.customer_id || null,
          warehouse_id: formState.warehouse_id || null,
          items: [
          {
            cylinder_id: formState.cylinder_id,
            quantity: Number(formState.quantity),
            quantity_in: formState.movement_type === "IC" || formState.movement_type === "IP" ? Number(formState.quantity) : 0,
            quantity_out: formState.movement_type === "SC" || formState.movement_type === "SP" ? Number(formState.quantity) : 0,
          },
        ],
      });
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "No se pudo crear el movimiento.");
    }
  }

  return (
    <LogisticsSection
      title="Movimientos"
      description="Registra ingresos, salidas y devoluciones con trazabilidad sobre cada envase."
      actions={<Button onClick={() => setIsOpen(true)}>Nuevo movimiento</Button>}
    >
      {error ? <Alert title="No se pudo completar la acción">{error}</Alert> : null}

      <div className="grid gap-6 xl:grid-cols-[1.2fr,1fr]">
        <Card>
          <CardHeader>
            <CardTitle>Movimientos</CardTitle>
            <CardDescription>Resumen reciente del trabajo operativo.</CardDescription>
          </CardHeader>
          <CardContent>
            <DataTable
              columns={[
                { key: "type", header: "Tipo", render: (row) => row.movement_type },
                {
                  key: "customer",
                  header: "Cliente",
                  render: (row) =>
                    (row.customer_id && customersQuery.data?.items.find((item) => item.id === row.customer_id)?.legal_name) ||
                    row.customer_name ||
                    "-",
                },
                { key: "status", header: "Estado", render: (row) => row.status },
                {
                  key: "actions",
                  header: "Acciones",
                  className: "w-40",
                  render: (row) => (
                    <div className="flex gap-2">
                      <Button variant="secondary" onClick={() => setSelectedMovementId(row.id)}>
                        Ver
                      </Button>
                      <Button variant="secondary" onClick={() => confirmMutation.mutate(row.id)}>
                        Confirmar
                      </Button>
                    </div>
                  ),
                },
              ]}
              rows={movementsQuery.data ?? []}
              rowKey={(row) => row.id}
              emptyMessage="Todavía no hay movimientos registrados."
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center justify-between gap-3">
              <div>
                <CardTitle>Detalle</CardTitle>
                <CardDescription>Envases y cambios del movimiento seleccionado.</CardDescription>
              </div>
              {selectedMovementId ? (
                <Button variant="secondary" onClick={() => cancelMutation.mutate(selectedMovementId)}>
                  Cancelar
                </Button>
              ) : null}
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <p className="mb-2 text-sm font-medium text-white">Items</p>
              <DataTable
                columns={[
                  { key: "cylinder", header: "Envase", render: (row) => row.cylinder_id },
                  { key: "before", header: "Antes", render: (row) => row.state_before ?? "-" },
                  { key: "after", header: "Después", render: (row) => row.state_after ?? "-" },
                ]}
                rows={itemsQuery.data ?? []}
                rowKey={(row) => row.id}
                emptyMessage={selectedMovementId ? "Sin items registrados." : "Selecciona un movimiento."}
              />
            </div>
            <div>
              <p className="mb-2 text-sm font-medium text-white">Historial</p>
              <DataTable
                columns={[
                  { key: "field", header: "Campo", render: (row) => row.field_name },
                  { key: "from", header: "Antes", render: (row) => row.from_value ?? "-" },
                  { key: "to", header: "Ahora", render: (row) => row.to_value },
                ]}
                rows={historyQuery.data ?? []}
                rowKey={(row) => row.id}
                emptyMessage={selectedMovementId ? "Sin cambios registrados." : "Selecciona un movimiento."}
              />
            </div>
          </CardContent>
        </Card>
      </div>

      <Dialog
        open={isOpen}
        title="Nuevo movimiento"
        description="Crea una operación básica y asóciala a un envase."
        onClose={() => setIsOpen(false)}
      >
        <form className="space-y-4" onSubmit={onSubmit}>
          <div className="grid gap-4 md:grid-cols-2">
            <label className="block space-y-2 text-sm text-slate-300">
              <span>Tipo</span>
              <select
                value={formState.movement_type}
                onChange={(event) => setFormState((current) => ({ ...current, movement_type: event.target.value }))}
                className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-200"
              >
                {(movementTypesQuery.data ?? []).map((type) => (
                  <option key={type.code} value={type.code}>
                    {type.name}
                  </option>
                ))}
              </select>
            </label>
            <label className="block space-y-2 text-sm text-slate-300">
              <span>Almacén</span>
              <select
                value={formState.warehouse_id}
                onChange={(event) => setFormState((current) => ({ ...current, warehouse_id: event.target.value }))}
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
          <div className="space-y-2 text-sm text-slate-300">
            <span>Cliente</span>
            <Button type="button" variant="secondary" onClick={() => setIsCustomerSearchOpen(true)}>
              {formState.customer_name ? `${formState.customer_name} (${formState.customer_id})` : "Seleccionar cliente"}
            </Button>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <label className="block space-y-2 text-sm text-slate-300">
              <span>Envase</span>
              <select
                value={formState.cylinder_id}
                onChange={(event) => setFormState((current) => ({ ...current, cylinder_id: event.target.value }))}
                className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-200"
              >
                <option value="">Selecciona</option>
                {(cylindersQuery.data ?? []).map((cylinder) => (
                  <option key={cylinder.id} value={cylinder.id}>
                    {cylinder.serial}
                  </option>
                ))}
              </select>
            </label>
            <label className="block space-y-2 text-sm text-slate-300">
              <span>Cantidad</span>
              <Input value={formState.quantity} onChange={(event) => setFormState((current) => ({ ...current, quantity: event.target.value }))} />
            </label>
          </div>
          <div className="flex justify-end gap-3">
            <Button type="button" variant="secondary" onClick={() => setIsOpen(false)}>
              Cancelar
            </Button>
            <Button type="submit" disabled={createMutation.isPending}>
              Guardar
            </Button>
          </div>
        </form>
      </Dialog>

      <CustomerSearchDialog
        open={isCustomerSearchOpen}
        onOpenChange={setIsCustomerSearchOpen}
        onSelect={(customer: CustomerBrief) =>
          setFormState((current) => ({ ...current, customer_id: customer.id, customer_name: customer.legal_name }))
        }
      />
    </LogisticsSection>
  );
}
