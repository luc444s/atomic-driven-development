import { FormEvent, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "../../../../apps/web/src/lib/react-query";

import {
  createReceptionIncident,
  getReceptionDetail,
  listIncidentReasons,
  listMovementItems,
  listPendingReceptions,
  listWarehouses,
  logisticsKeys,
  LogisticsMovement,
  LogisticsMovementItem,
  receiveMovement,
  receptionKeys,
} from "../api";
import { LogisticsSection } from "../components/LogisticsSection";
import { Alert } from "../../../../apps/web/src/shared/ui/alert";
import { Button } from "../../../../apps/web/src/shared/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../../../apps/web/src/shared/ui/card";
import { DataTable } from "../../../../apps/web/src/shared/ui/data-table";
import { Dialog } from "../../../../apps/web/src/shared/ui/dialog";
import { Input } from "../../../../apps/web/src/shared/ui/input";
import { Select } from "../../../../apps/web/src/shared/ui/select";

const controlClassName =
  "w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-slate-50 outline-none transition focus:border-ring";

export function ReceptionPage() {
  const queryClient = useQueryClient();
  const [warehouseFilter, setWarehouseFilter] = useState("");
  const [selectedMovement, setSelectedMovement] = useState<LogisticsMovement | null>(null);
  const [isReceiveOpen, setIsReceiveOpen] = useState(false);
  const [isIncidentOpen, setIsIncidentOpen] = useState(false);
  const [receiveNotes, setReceiveNotes] = useState("");
  const [receiveQtys, setReceiveQtys] = useState<Record<string, string>>({});
  const [incidentCylinderId, setIncidentCylinderId] = useState("");
  const [incidentReason, setIncidentReason] = useState("");
  const [incidentDesc, setIncidentDesc] = useState("");
  const [error, setError] = useState<string | null>(null);

  const warehousesQuery = useQuery({ queryKey: logisticsKeys.warehouses(), queryFn: listWarehouses });
  const pendingQuery = useQuery({
    queryKey: receptionKeys.pending(),
    queryFn: () => listPendingReceptions(warehouseFilter || undefined),
  });
  const itemsQuery = useQuery({
    queryKey: logisticsKeys.movements.items(selectedMovement?.id ?? ""),
    queryFn: () => listMovementItems(selectedMovement!.id),
    enabled: selectedMovement !== null,
  });
  const incidentReasonsQuery = useQuery({
    queryKey: receptionKeys.incidentReasons(),
    queryFn: listIncidentReasons,
  });

  const receiveMutation = useMutation({
    mutationFn: () => receiveMovement(selectedMovement!.id, {
      items: (itemsQuery.data ?? []).map((item) => ({
        movement_item_id: item.id,
        quantity_received: Number(receiveQtys[item.id] ?? item.quantity ?? 1),
      })),
      notes: receiveNotes || undefined,
    }),
    onSuccess: () => {
      setIsReceiveOpen(false);
      setSelectedMovement(null);
      setReceiveNotes("");
      setError(null);
      Promise.all([
        queryClient.invalidateQueries({ queryKey: receptionKeys.pending() }),
        queryClient.invalidateQueries({ queryKey: logisticsKeys.movements.all() }),
        queryClient.invalidateQueries({ queryKey: logisticsKeys.cylinders.all() }),
      ]);
    },
  });

  const incidentMutation = useMutation({
    mutationFn: () => createReceptionIncident(selectedMovement!.id, {
      cylinder_id: incidentCylinderId || undefined,
      reason_code: incidentReason,
      description: incidentDesc || undefined,
    }),
    onSuccess: () => {
      setIsIncidentOpen(false);
      setIncidentCylinderId("");
      setIncidentReason("");
      setIncidentDesc("");
      setError(null);
      queryClient.invalidateQueries({ queryKey: logisticsKeys.movements.history(selectedMovement!.id) });
    },
  });

  async function handleReceive(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    try {
      await receiveMutation.mutateAsync();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Error al recepcionar");
    }
  }

  async function handleIncident(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    try {
      await incidentMutation.mutateAsync();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Error al registrar incidencia");
    }
  }

  function openReceive(movement: LogisticsMovement) {
    setSelectedMovement(movement);
    const initialQtys: Record<string, string> = {};
    // Will be filled when itemsQuery loads
    setIsReceiveOpen(true);
  }

  // When items load, initialize receive quantities
  function initReceiveQtys(items: LogisticsMovementItem[]) {
    if (Object.keys(receiveQtys).length === 0 && items.length > 0) {
      const qty: Record<string, string> = {};
      items.forEach((item) => {
        qty[item.id] = String(item.quantity ?? item.quantity_in ?? 1);
      });
      setReceiveQtys(qty);
    }
  }

  return (
    <LogisticsSection
      title="Recepcion"
      description="Movimientos pendientes de recepcion, recepcion de items y registro de incidencias."
    >
      {error ? <Alert title="Operacion no completada">{error}</Alert> : null}

      <div className="flex flex-wrap gap-3">
        <Select value={warehouseFilter} onChange={(value) => setWarehouseFilter(value)}
          placeholder="Todos los almacenes"
          options={(warehousesQuery.data ?? []).map((wh) => ({ value: wh.id, label: wh.name }))} />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Pendientes de recepcion</CardTitle>
          <CardDescription>Movimientos en estado DESCARGADO_POR_RECEPCIONAR.</CardDescription>
        </CardHeader>
        <CardContent>
          <DataTable
            columns={[
              { key: "type", header: "Tipo", render: (row) => row.movement_type },
              { key: "customer", header: "Cliente", render: (row) => row.customer_name || "-" },
              { key: "warehouse", header: "Almacen destino", render: (row) => row.warehouse_id || "-" },
              { key: "status", header: "Estado", render: (row) => row.status },
              {
                key: "actions", header: "", className: "w-40",
                render: (row) => (
                  <div className="flex gap-2">
                    <Button variant="secondary" onClick={() => { setSelectedMovement(row); }}>Ver</Button>
                    <Button onClick={() => openReceive(row)}>Recepcionar</Button>
                  </div>
                ),
              },
            ]}
            rows={pendingQuery.data ?? []}
            rowKey={(row) => row.id}
            emptyMessage="No hay movimientos pendientes de recepcion."
          />
        </CardContent>
      </Card>

      <Dialog
        open={selectedMovement !== null && !isReceiveOpen && !isIncidentOpen}
        title={selectedMovement ? `Movimiento: ${selectedMovement.movement_type}` : ""}
        description={selectedMovement ? `Cliente: ${selectedMovement.customer_name || "-"} | Estado: ${selectedMovement.status}` : ""}
        onClose={() => { setSelectedMovement(null); setError(null); }}
      >
        {selectedMovement ? (
          <div className="space-y-4">
            <DataTable
              columns={[
                { key: "product", header: "Producto", render: (row) => row.product_name || row.cylinder_id || "-" },
                { key: "qty_in", header: "Cant. entrada", render: (row) => String(row.quantity_in) },
                { key: "qty_out", header: "Cant. salida", render: (row) => String(row.quantity_out) },
              ]}
              rows={itemsQuery.data ?? []}
              rowKey={(row) => row.id}
              emptyMessage="Sin items"
            />
            <div className="flex flex-wrap gap-2 justify-end">
              <Button variant="secondary" onClick={() => setIsIncidentOpen(true)}>Registrar incidencia</Button>
              <Button onClick={() => openReceive(selectedMovement)}>Recepcionar</Button>
            </div>
          </div>
        ) : null}
      </Dialog>

      <Dialog
        open={isReceiveOpen}
        title="Recepcionar movimiento"
        description="Confirma cantidades recibidas por linea."
        onClose={() => setIsReceiveOpen(false)}
      >
        {selectedMovement ? (
          <form className="space-y-4" onSubmit={handleReceive}>
            {itemsQuery.data && itemsQuery.data.length > 0 ? (
              (() => {
                initReceiveQtys(itemsQuery.data);
                return (
                  <div className="space-y-3">
                    {itemsQuery.data.map((item) => (
                      <div key={item.id} className="grid grid-cols-2 gap-3 items-end">
                        <span className="text-sm text-foreground">{item.product_name || item.cylinder_id || "-"}</span>
                        <Input
                          type="number"
                          value={receiveQtys[item.id] ?? String(item.quantity ?? item.quantity_in ?? 1)}
                          onChange={(e) => setReceiveQtys((prev) => ({ ...prev, [item.id]: e.target.value }))}
                        />
                      </div>
                    ))}
                  </div>
                );
              })()
            ) : (
              <p className="text-sm text-muted-foreground">Este movimiento no tiene items.</p>
            )}
            <label className="block space-y-2 text-sm text-foreground">
              <span>Notas</span>
              <Input value={receiveNotes} onChange={(e) => setReceiveNotes(e.target.value)} />
            </label>
            <div className="flex justify-end gap-2">
              <Button variant="secondary" onClick={() => setIsReceiveOpen(false)}>Cancelar</Button>
              <Button type="submit" disabled={receiveMutation.isPending}>Confirmar recepcion</Button>
            </div>
          </form>
        ) : null}
      </Dialog>

      <Dialog
        open={isIncidentOpen}
        title="Registrar incidencia"
        description="Registra una incidencia durante la recepcion."
        onClose={() => setIsIncidentOpen(false)}
      >
        <form className="space-y-4" onSubmit={handleIncident}>
          <label className="block space-y-2 text-sm text-foreground">
            <span>Motivo</span>
            <Select value={incidentReason} onChange={(value) => setIncidentReason(value)} required
              placeholder="Selecciona motivo"
              options={(incidentReasonsQuery.data ?? []).map((r) => ({ value: r.code, label: r.description }))} />
          </label>
          <label className="block space-y-2 text-sm text-foreground">
            <span>Cilindro (opcional)</span>
            <Input value={incidentCylinderId} onChange={(e) => setIncidentCylinderId(e.target.value)} />
          </label>
          <label className="block space-y-2 text-sm text-foreground">
            <span>Descripcion</span>
            <Input value={incidentDesc} onChange={(e) => setIncidentDesc(e.target.value)} />
          </label>
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setIsIncidentOpen(false)}>Cancelar</Button>
            <Button type="submit" disabled={incidentMutation.isPending}>Registrar</Button>
          </div>
        </form>
      </Dialog>
    </LogisticsSection>
  );
}
