import { FormEvent, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "../../../../apps/web/src/lib/react-query";

import {
  assignEquipmentToMovement,
  createEquipment,
  equipmentKeys,
  listEquipment,
  listMovementEquipment,
  listMovements,
  listMovementItems,
  logisticsKeys,
  returnMovementEquipment,
} from "../api";
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

export function EquipmentPage() {
  const queryClient = useQueryClient();
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [equipName, setEquipName] = useState("");
  const [equipType, setEquipType] = useState("");
  const [selectedMovementId, setSelectedMovementId] = useState<string | null>(null);
  const [isAssignOpen, setIsAssignOpen] = useState(false);
  const [assignEquipId, setAssignEquipId] = useState("");
  const [assignNotes, setAssignNotes] = useState("");
  const [error, setError] = useState<string | null>(null);

  const equipmentQuery = useQuery({ queryKey: equipmentKeys.list(), queryFn: listEquipment });
  const movementsQuery = useQuery({ queryKey: logisticsKeys.movements.list({}), queryFn: () => listMovements({}) });
  const movementEquipQuery = useQuery({
    queryKey: equipmentKeys.movementEquipment(selectedMovementId ?? ""),
    queryFn: () => listMovementEquipment(selectedMovementId!),
    enabled: selectedMovementId !== null,
  });

  const createMutation = useMutation({
    mutationFn: () => createEquipment({
      name: equipName,
      equipment_type: equipType || undefined,
    }),
    onSuccess: () => {
      toast.success("Equipo creado");
      setIsCreateOpen(false);
      setEquipName("");
      setEquipType("");
      setError(null);
      queryClient.invalidateQueries({ queryKey: equipmentKeys.all() });
    },
  });

  const assignMutation = useMutation({
    mutationFn: () => assignEquipmentToMovement(selectedMovementId!, {
      equipment_id: assignEquipId,
      notes: assignNotes || undefined,
    }),
    onSuccess: () => {
      toast.success("Equipo asignado");
      setIsAssignOpen(false);
      setAssignEquipId("");
      setAssignNotes("");
      setError(null);
      queryClient.invalidateQueries({ queryKey: equipmentKeys.movementEquipment(selectedMovementId!) });
    },
  });

  const returnMutation = useMutation({
    mutationFn: (eqId: string) => returnMovementEquipment(selectedMovementId!, eqId),
    onSuccess: () => {
      toast.success("Equipo devuelto");
      queryClient.invalidateQueries({ queryKey: equipmentKeys.movementEquipment(selectedMovementId!) });
    },
    onError: () => {
      toast.error("Error al devolver equipo");
    },
  });

  async function handleCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    try {
      await createMutation.mutateAsync();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Error al crear equipo");
    }
  }

  async function handleAssign(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    try {
      await assignMutation.mutateAsync();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Error al asignar equipo");
    }
  }

  return (
    <LogisticsSection
      title="Equipos"
      description="Catalogo de equipos y asignacion a movimientos."
      actions={<Button onClick={() => setIsCreateOpen(true)}>Nuevo equipo</Button>}
    >
      {error ? <Alert title="Operacion no completada">{error}</Alert> : null}

      <div className="grid gap-6 xl:grid-cols-[1.2fr,1fr]">
        <Card>
          <CardHeader>
            <CardTitle>Catalogo de equipos</CardTitle>
            <CardDescription>Bombas, mangueras y otros equipos.</CardDescription>
          </CardHeader>
          <CardContent>
            <DataTable
              columns={[
                { key: "name", header: "Nombre", render: (row) => row.name },
                { key: "type", header: "Tipo", render: (row) => row.equipment_type || "-" },
                { key: "active", header: "Activo", render: (row) => row.is_active ? "Si" : "No" },
              ]}
              rows={equipmentQuery.data ?? []}
              rowKey={(row) => row.id}
              emptyMessage="No hay equipos registrados."
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Asignacion a movimientos</CardTitle>
                <CardDescription>Equipos asignados al movimiento seleccionado.</CardDescription>
              </div>
              {selectedMovementId ? (
                <Button variant="secondary" onClick={() => setIsAssignOpen(true)}>Asignar equipo</Button>
              ) : null}
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <Select value={selectedMovementId ?? ""}
              onChange={(value) => setSelectedMovementId(value || null)}
              placeholder="Selecciona movimiento"
              options={(movementsQuery.data ?? []).map((m) => ({ value: m.id, label: `${m.movement_type} - ${m.customer_name || "Sin cliente"}` }))} />
            <DataTable
              columns={[
                { key: "equip", header: "Equipo", render: (row) => equipmentQuery.data?.find((e) => e.id === row.equipment_id)?.name || "-" },
                { key: "assigned", header: "Asignado", render: (row) => new Date(row.assigned_at).toLocaleString() },
                { key: "returned", header: "Devuelto", render: (row) => row.returned_at ? new Date(row.returned_at).toLocaleString() : "Pendiente" },
                {
                  key: "actions", header: "", className: "w-24",
                  render: (row) => !row.returned_at ? (
                    <Button variant="secondary" onClick={() => returnMutation.mutate(row.equipment_id)}>Devolver</Button>
                  ) : null,
                },
              ]}
              rows={movementEquipQuery.data ?? []}
              rowKey={(row) => row.id}
              emptyMessage={selectedMovementId ? "Sin equipos asignados." : "Selecciona un movimiento."}
            />
          </CardContent>
        </Card>
      </div>

      <Dialog open={isCreateOpen} title="Nuevo equipo" description="Registra un equipo en el catalogo."
        onClose={() => setIsCreateOpen(false)}>
        <form className="space-y-4" onSubmit={handleCreate}>
          <label className="block space-y-2 text-sm text-foreground">
            <span>Nombre</span>
            <Input value={equipName} onChange={(e) => setEquipName(e.target.value)} required />
          </label>
          <label className="block space-y-2 text-sm text-foreground">
            <span>Tipo</span>
            <Input value={equipType} onChange={(e) => setEquipType(e.target.value)} placeholder="Bomba, manguera, etc" />
          </label>
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setIsCreateOpen(false)}>Cancelar</Button>
            <Button type="submit" disabled={createMutation.isPending}>Guardar</Button>
          </div>
        </form>
      </Dialog>

      <Dialog open={isAssignOpen} title="Asignar equipo a movimiento"
        description="Selecciona un equipo del catalogo."
        onClose={() => setIsAssignOpen(false)}>
        <form className="space-y-4" onSubmit={handleAssign}>
          <label className="block space-y-2 text-sm text-foreground">
            <span>Equipo</span>
            <Select value={assignEquipId} onChange={(value) => setAssignEquipId(value)} required
              placeholder="Selecciona equipo"
              options={(equipmentQuery.data ?? []).filter((e) => e.is_active).map((e) => ({ value: e.id, label: `${e.name} ${e.equipment_type ? `(${e.equipment_type})` : ""}` }))} />
          </label>
          <label className="block space-y-2 text-sm text-foreground">
            <span>Notas</span>
            <Input value={assignNotes} onChange={(e) => setAssignNotes(e.target.value)} />
          </label>
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setIsAssignOpen(false)}>Cancelar</Button>
            <Button type="submit" disabled={assignMutation.isPending}>Asignar</Button>
          </div>
        </form>
      </Dialog>
    </LogisticsSection>
  );
}
