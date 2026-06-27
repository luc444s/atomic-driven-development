import { useMutation, useQuery, useQueryClient } from "../../../../apps/web/src/lib/react-query";
import { FormEvent, useState } from "react";

import { createWarehouse, createZone, listWarehouses, listZones, logisticsKeys, updateWarehouse } from "../api";
import { LogisticsSection } from "../components/LogisticsSection";
import { Alert } from "../../../../apps/web/src/shared/ui/alert";
import { Button } from "../../../../apps/web/src/shared/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../../../apps/web/src/shared/ui/card";
import { DataTable } from "../../../../apps/web/src/shared/ui/data-table";
import { Dialog } from "../../../../apps/web/src/shared/ui/dialog";
import { Input } from "../../../../apps/web/src/shared/ui/input";

type WarehouseFormState = { id?: string; name: string; code: string; address: string; phone: string };
type ZoneFormState = { name: string; code: string };

const EMPTY_WAREHOUSE: WarehouseFormState = { name: "", code: "", address: "", phone: "" };
const EMPTY_ZONE: ZoneFormState = { name: "", code: "" };

export function WarehousesPage() {
  const queryClient = useQueryClient();
  const [warehouseForm, setWarehouseForm] = useState<WarehouseFormState>(EMPTY_WAREHOUSE);
  const [zoneForm, setZoneForm] = useState<ZoneFormState>(EMPTY_ZONE);
  const [isWarehouseOpen, setIsWarehouseOpen] = useState(false);
  const [isZoneOpen, setIsZoneOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const warehousesQuery = useQuery({ queryKey: logisticsKeys.warehouses(), queryFn: listWarehouses });
  const zonesQuery = useQuery({ queryKey: logisticsKeys.zones(), queryFn: listZones });

  const saveWarehouseMutation = useMutation({
    mutationFn: async (payload: WarehouseFormState) => {
      if (payload.id) {
        return updateWarehouse(payload.id, payload);
      }
      return createWarehouse(payload);
    },
    onSuccess: async () => {
      setIsWarehouseOpen(false);
      setWarehouseForm(EMPTY_WAREHOUSE);
      setError(null);
      await queryClient.invalidateQueries({ queryKey: logisticsKeys.warehouses() });
    },
  });

  const createZoneMutation = useMutation({
    mutationFn: createZone,
    onSuccess: async () => {
      setIsZoneOpen(false);
      setZoneForm(EMPTY_ZONE);
      setError(null);
      await queryClient.invalidateQueries({ queryKey: logisticsKeys.zones() });
    },
  });

  async function submitWarehouse(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    try {
      await saveWarehouseMutation.mutateAsync(warehouseForm);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "No se pudo guardar el almacén.");
    }
  }

  async function submitZone(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    try {
      await createZoneMutation.mutateAsync(zoneForm);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "No se pudo crear la zona.");
    }
  }

  return (
    <LogisticsSection
      title="Almacenes y zonas"
      description="Organiza la operación por puntos de salida."
      actions={
        <div className="flex gap-2">
          <Button variant="secondary" onClick={() => setIsZoneOpen(true)}>
            Nueva zona
          </Button>
          <Button onClick={() => setIsWarehouseOpen(true)}>Nuevo almacén</Button>
        </div>
      }
    >
      {error ? <Alert title="No se pudo completar la acción">{error}</Alert> : null}

      <div className="grid gap-6 xl:grid-cols-[1.4fr,1fr]">
        <Card>
          <CardHeader>
            <CardTitle>Almacenes</CardTitle>
            <CardDescription>Ubicaciones activas para salida, ingreso y control de envases.</CardDescription>
          </CardHeader>
          <CardContent>
            <DataTable
              columns={[
                { key: "name", header: "Nombre", render: (row) => row.name },
                { key: "code", header: "Código", render: (row) => row.code },
                { key: "address", header: "Dirección", render: (row) => row.address ?? "-" },
                {
                  key: "actions",
                  header: "Editar",
                  className: "w-32",
                  render: (row) => (
                    <Button
                      variant="secondary"
                      onClick={() => {
                        setWarehouseForm({
                          id: row.id,
                          name: row.name,
                          code: row.code,
                          address: row.address ?? "",
                          phone: row.phone ?? "",
                        });
                        setIsWarehouseOpen(true);
                      }}
                    >
                      Abrir
                    </Button>
                  ),
                },
              ]}
              rows={warehousesQuery.data ?? []}
              rowKey={(row) => row.id}
              emptyMessage="Aún no hay almacenes registrados."
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Zonas</CardTitle>
            <CardDescription>Áreas de entrega que ayudan a ordenar las rutas.</CardDescription>
          </CardHeader>
          <CardContent>
            <DataTable
              columns={[
                { key: "name", header: "Nombre", render: (row) => row.name },
                { key: "code", header: "Código", render: (row) => row.code },
              ]}
              rows={zonesQuery.data ?? []}
              rowKey={(row) => row.id}
              emptyMessage="Todavía no hay zonas registradas."
            />
          </CardContent>
        </Card>
      </div>

      <Dialog
        open={isWarehouseOpen}
        title={warehouseForm.id ? "Editar almacén" : "Nuevo almacén"}
        description="Guarda los datos base del punto de operación."
        onClose={() => {
          setIsWarehouseOpen(false);
          setWarehouseForm(EMPTY_WAREHOUSE);
        }}
      >
        <form className="space-y-4" onSubmit={submitWarehouse}>
          <label className="block space-y-2 text-sm text-slate-300">
            <span>Nombre</span>
            <Input value={warehouseForm.name} onChange={(event) => setWarehouseForm((current) => ({ ...current, name: event.target.value }))} />
          </label>
          <label className="block space-y-2 text-sm text-slate-300">
            <span>Código</span>
            <Input value={warehouseForm.code} onChange={(event) => setWarehouseForm((current) => ({ ...current, code: event.target.value }))} />
          </label>
          <label className="block space-y-2 text-sm text-slate-300">
            <span>Dirección</span>
            <Input value={warehouseForm.address} onChange={(event) => setWarehouseForm((current) => ({ ...current, address: event.target.value }))} />
          </label>
          <label className="block space-y-2 text-sm text-slate-300">
            <span>Teléfono</span>
            <Input value={warehouseForm.phone} onChange={(event) => setWarehouseForm((current) => ({ ...current, phone: event.target.value }))} />
          </label>
          <div className="flex justify-end gap-3">
            <Button type="button" variant="secondary" onClick={() => setIsWarehouseOpen(false)}>
              Cancelar
            </Button>
            <Button type="submit" disabled={saveWarehouseMutation.isPending}>
              Guardar
            </Button>
          </div>
        </form>
      </Dialog>

      <Dialog
        open={isZoneOpen}
        title="Nueva zona"
        description="Crea una zona breve para clasificar entregas."
        onClose={() => {
          setIsZoneOpen(false);
          setZoneForm(EMPTY_ZONE);
        }}
      >
        <form className="space-y-4" onSubmit={submitZone}>
          <label className="block space-y-2 text-sm text-slate-300">
            <span>Nombre</span>
            <Input value={zoneForm.name} onChange={(event) => setZoneForm((current) => ({ ...current, name: event.target.value }))} />
          </label>
          <label className="block space-y-2 text-sm text-slate-300">
            <span>Código</span>
            <Input value={zoneForm.code} onChange={(event) => setZoneForm((current) => ({ ...current, code: event.target.value }))} />
          </label>
          <div className="flex justify-end gap-3">
            <Button type="button" variant="secondary" onClick={() => setIsZoneOpen(false)}>
              Cancelar
            </Button>
            <Button type="submit" disabled={createZoneMutation.isPending}>
              Crear
            </Button>
          </div>
        </form>
      </Dialog>
    </LogisticsSection>
  );
}
