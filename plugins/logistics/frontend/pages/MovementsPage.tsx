import { FormEvent, useState } from "react";
import type { CustomerBrief } from "../../../crm/frontend/types";
import { useMutation, useQuery, useQueryClient } from "../../../../apps/web/src/lib/react-query";

import {
  assignDispatchGuide,
  cancelMovement,
  closeDispatch,
  confirmMovement,
  createMovement,
  getDispatchTicket,
  getTransferAlbaran,
  getWaybill,
  getWaybillSummary,
  listCylinders,
  listMovementHistory,
  listMovementItems,
  listMovements,
  listMovementTypes,
  listWarehouses,
  logisticsKeys,
  LogisticsMovement,
  vehicleReturn,
  Waybill,
} from "../api";
import { getRealWarehouses } from "../api/warehouses";
import { listCustomers } from "../../../crm/frontend/api";
import { CustomerSearchDialog } from "../../../crm/frontend/components/CustomerSearchDialog";
import { LogisticsSection } from "../components/LogisticsSection";
import { Alert } from "../../../../apps/web/src/shared/ui/alert";
import { Button } from "../../../../apps/web/src/shared/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../../../apps/web/src/shared/ui/card";
import { DataTable } from "../../../../apps/web/src/shared/ui/data-table";
import { Dialog } from "../../../../apps/web/src/shared/ui/dialog";
import { Input } from "../../../../apps/web/src/shared/ui/input";
import { Select } from "../../../../apps/web/src/shared/ui/select";
import { toast } from "../../../../apps/web/src/shared/ui/toast";

const controlClassName =
  "w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-slate-50 outline-none transition focus:border-ring";

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

  const [isGuideOpen, setIsGuideOpen] = useState(false);
  const [guideSeries, setGuideSeries] = useState("");
  const [isVehicleReturnOpen, setIsVehicleReturnOpen] = useState(false);
  const [returnCylinderIds, setReturnCylinderIds] = useState("");
  const [returnNotes, setReturnNotes] = useState("");
  const [isWaybillOpen, setIsWaybillOpen] = useState(false);
  const [waybillData, setWaybillData] = useState<Waybill | null>(null);

  const movementsQuery = useQuery({ queryKey: logisticsKeys.movements.list({}), queryFn: () => listMovements({}) });
  const movementTypesQuery = useQuery({ queryKey: logisticsKeys.movementTypes(), queryFn: listMovementTypes });
  const warehousesQuery = useQuery({ queryKey: logisticsKeys.warehouses(), queryFn: listWarehouses });
  const realWarehouses = getRealWarehouses(warehousesQuery.data ?? []);
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
  const selectedMovement = movementsQuery.data?.find((m) => m.id === selectedMovementId);

  const createMutation = useMutation({
    mutationFn: createMovement,
    onSuccess: async (movement) => {
      toast.success("Movimiento creado");
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
      toast.success("Movimiento confirmado");
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: logisticsKeys.movements.all() }),
        queryClient.invalidateQueries({ queryKey: logisticsKeys.movements.history(selectedMovementId!) }),
        queryClient.invalidateQueries({ queryKey: logisticsKeys.cylinders.all() }),
      ]);
    },
    onError: () => {
      toast.error("Error al confirmar movimiento");
    },
  });
  const cancelMutation = useMutation({
    mutationFn: (movementId: string) => cancelMovement(movementId, "Cancelado desde panel"),
    onSuccess: async () => {
      toast.success("Movimiento cancelado");
      await queryClient.invalidateQueries({ queryKey: logisticsKeys.movements.all() });
    },
    onError: () => {
      toast.error("Error al cancelar movimiento");
    },
  });
  const guideMutation = useMutation({
    mutationFn: () => assignDispatchGuide(selectedMovementId!, { document_series: guideSeries }),
    onSuccess: async () => {
      toast.success("Guía asignada");
      setIsGuideOpen(false);
      setGuideSeries("");
      setError(null);
      await queryClient.invalidateQueries({ queryKey: logisticsKeys.movements.all() });
    },
  });
  const closeDispatchMutation = useMutation({
    mutationFn: () => closeDispatch(selectedMovementId!),
    onSuccess: async () => {
      toast.success("Despacho cerrado");
      setError(null);
      await queryClient.invalidateQueries({ queryKey: logisticsKeys.movements.all() });
    },
    onError: () => {
      toast.error("Error al cerrar despacho");
    },
  });
  const vehicleReturnMutation = useMutation({
    mutationFn: () => vehicleReturn(selectedMovementId!, {
      cylinder_ids: returnCylinderIds.split(",").map((s) => s.trim()).filter(Boolean),
      notes: returnNotes || undefined,
    }),
    onSuccess: async () => {
      toast.success("Retorno de vehículo registrado");
      setIsVehicleReturnOpen(false);
      setReturnCylinderIds("");
      setReturnNotes("");
      setError(null);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: logisticsKeys.movements.all() }),
        queryClient.invalidateQueries({ queryKey: logisticsKeys.cylinders.all() }),
      ]);
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

  async function loadWaybill() {
    if (!selectedMovementId) return;
    try {
      const data = await getWaybill(selectedMovementId);
      setWaybillData(data);
      setIsWaybillOpen(true);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Error al cargar Carta Porte");
    }
  }

  return (
    <LogisticsSection
      title="Movimientos"
      description="Registra ingresos, salidas y devoluciones con trazabilidad sobre cada envase."
      actions={<Button onClick={() => setIsOpen(true)}>Nuevo movimiento</Button>}
    >
      {error ? <Alert title="No se pudo completar la accion">{error}</Alert> : null}

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
                    (row.customer_id &&
                      (customersQuery.data?.items.find((item) => item.id === row.customer_id)?.commercial_name ||
                        customersQuery.data?.items.find((item) => item.id === row.customer_id)?.legal_name)) ||
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
              emptyMessage="Todavia no hay movimientos registrados."
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center justify-between gap-3">
              <div>
                <CardTitle>Detalle</CardTitle>
                <CardDescription>Items, cambios y acciones de despacho.</CardDescription>
              </div>
              {selectedMovementId ? (
                <div className="flex flex-wrap gap-2">
                  <Button variant="secondary" onClick={() => cancelMutation.mutate(selectedMovementId)}>
                    Cancelar
                  </Button>
                  {selectedMovement?.status === "CONFIRMADO" ? (
                    <>
                      <Button variant="secondary" onClick={() => setIsGuideOpen(true)}>Asignar guia</Button>
                      <Button onClick={() => closeDispatchMutation.mutate()}>Cerrar despacho</Button>
                    </>
                  ) : null}
                  {selectedMovement?.status === "EN_RUTA" || selectedMovement?.status === "DESPACHADO" ? (
                    <Button variant="secondary" onClick={() => setIsVehicleReturnOpen(true)}>Retorno vehiculo</Button>
                  ) : null}
                  <Button variant="secondary" onClick={loadWaybill}>Carta Porte</Button>
                </div>
              ) : null}
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <p className="mb-2 text-sm font-medium text-foreground">Items</p>
              <DataTable
                columns={[
                  { key: "product", header: "Producto / Envase", render: (row) => row.product_name || "-" },
                  { key: "before", header: "Antes", render: (row) => row.state_before ?? "-" },
                  { key: "after", header: "Despues", render: (row) => row.state_after ?? "-" },
                ]}
                rows={itemsQuery.data ?? []}
                rowKey={(row) => row.id}
                emptyMessage={selectedMovementId ? "Sin items registrados." : "Selecciona un movimiento."}
              />
            </div>
            <div>
              <p className="mb-2 text-sm font-medium text-foreground">Historial</p>
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

      <Dialog open={isOpen} title="Nuevo movimiento" description="Crea una operacion basica." onClose={() => setIsOpen(false)}>
        <form className="space-y-4" onSubmit={onSubmit}>
          <div className="grid gap-4 md:grid-cols-2">
            <label className="block space-y-2 text-sm text-foreground">
              <span>Tipo</span>
              <Select value={formState.movement_type} onChange={(value) => setFormState((current) => ({ ...current, movement_type: value }))}
                options={(movementTypesQuery.data ?? []).map((type) => ({ value: type.code, label: type.name }))} />
            </label>
            <label className="block space-y-2 text-sm text-foreground">
              <span>Almacen</span>
              <Select value={formState.warehouse_id} onChange={(value) => setFormState((current) => ({ ...current, warehouse_id: value }))}
                placeholder="Sin definir"
                options={realWarehouses.map((warehouse) => ({ value: warehouse.id, label: warehouse.name }))} />
            </label>
          </div>
          <div className="space-y-2 text-sm text-foreground">
            <span>Cliente</span>
            <Button type="button" variant="secondary" onClick={() => setIsCustomerSearchOpen(true)}>
              {formState.customer_name ? `${formState.customer_name} (${formState.customer_id})` : "Seleccionar cliente"}
            </Button>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <label className="block space-y-2 text-sm text-foreground">
              <span>Envase</span>
              <Select value={formState.cylinder_id} onChange={(value) => setFormState((current) => ({ ...current, cylinder_id: value }))}
                placeholder="Selecciona"
                options={(cylindersQuery.data ?? []).map((cylinder) => ({ value: cylinder.id, label: cylinder.serial }))} />
            </label>
            <label className="block space-y-2 text-sm text-foreground">
              <span>Cantidad</span>
              <Input value={formState.quantity} onChange={(event) => setFormState((current) => ({ ...current, quantity: event.target.value }))} />
            </label>
          </div>
          <div className="flex justify-end gap-3">
            <Button type="button" variant="secondary" onClick={() => setIsOpen(false)}>Cancelar</Button>
            <Button type="submit" disabled={createMutation.isPending}>Guardar</Button>
          </div>
        </form>
      </Dialog>

      <CustomerSearchDialog open={isCustomerSearchOpen} onOpenChange={setIsCustomerSearchOpen}
        onSelect={(customer: CustomerBrief) => setFormState((current) => ({ ...current, customer_id: customer.id, customer_name: customer.display_name }))} />

      <Dialog open={isGuideOpen} title="Asignar guia de despacho" description="Ingresa la serie del documento."
        onClose={() => setIsGuideOpen(false)}>
        <form className="space-y-4" onSubmit={(e) => { e.preventDefault(); guideMutation.mutate(); }}>
          <label className="block space-y-2 text-sm text-foreground">
            <span>Serie</span>
            <Input value={guideSeries} onChange={(e) => setGuideSeries(e.target.value)} placeholder="Ej: G001" required />
          </label>
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setIsGuideOpen(false)}>Cancelar</Button>
            <Button type="submit" disabled={guideMutation.isPending}>Asignar</Button>
          </div>
        </form>
      </Dialog>

      <Dialog open={isVehicleReturnOpen} title="Retorno de vehiculo" description="Ingresa los cilindros que retornan."
        onClose={() => setIsVehicleReturnOpen(false)}>
        <form className="space-y-4" onSubmit={(e) => { e.preventDefault(); vehicleReturnMutation.mutate(); }}>
          <label className="block space-y-2 text-sm text-foreground">
            <span>IDs de cilindros (separados por coma)</span>
            <Input value={returnCylinderIds} onChange={(e) => setReturnCylinderIds(e.target.value)} placeholder="id1, id2, id3" />
          </label>
          <label className="block space-y-2 text-sm text-foreground">
            <span>Notas</span>
            <Input value={returnNotes} onChange={(e) => setReturnNotes(e.target.value)} />
          </label>
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setIsVehicleReturnOpen(false)}>Cancelar</Button>
            <Button type="submit" disabled={vehicleReturnMutation.isPending}>Registrar retorno</Button>
          </div>
        </form>
      </Dialog>

      <Dialog open={isWaybillOpen} title="Carta Porte" description="Datos estructurados del documento."
        maxWidthClassName="max-w-[900px]" onClose={() => { setIsWaybillOpen(false); setWaybillData(null); }}>
        {waybillData ? (
          <div className="space-y-4 text-sm text-foreground">
            <div className="grid grid-cols-2 gap-3">
              <div><span className="text-muted-foreground">Documento:</span> {waybillData.document || "-"}</div>
              <div><span className="text-muted-foreground">Almacen:</span> {waybillData.warehouse_name || "-"}</div>
              <div><span className="text-muted-foreground">Cliente:</span> {waybillData.customer_name || "-"}</div>
              <div><span className="text-muted-foreground">Vehiculo:</span> {waybillData.vehicle_plate || "-"}</div>
              <div><span className="text-muted-foreground">Destino:</span> {waybillData.destination_place || "-"}</div>
              <div><span className="text-muted-foreground">Direccion:</span> {waybillData.destination_address || "-"}</div>
            </div>
            <DataTable
              columns={[
                { key: "product", header: "Producto", render: (row) => row.product_name || "-" },
                { key: "qty", header: "Cant.", render: (row) => String(row.quantity) },
                { key: "weight", header: "Peso kg", render: (row) => row.total_weight_kg?.toString() || "-" },
                { key: "adr", header: "Puntos ADR", render: (row) => row.adr_points?.toString() || "-" },
              ]}
              rows={waybillData.items}
              rowKey={(row) => `${row.product_id}-${row.product_name}`}
              emptyMessage="Sin items"
            />
            <div className="grid grid-cols-3 gap-3 pt-2 border-t border-border text-muted-foreground">
              <div>Total bultos: {waybillData.total_packages}</div>
              <div>Peso total: {waybillData.total_weight_kg} kg</div>
              <div>ADR total: {waybillData.total_adr_points}</div>
            </div>
          </div>
        ) : null}
      </Dialog>
    </LogisticsSection>
  );
}
