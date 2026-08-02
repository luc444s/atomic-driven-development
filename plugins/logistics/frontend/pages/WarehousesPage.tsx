import { useMutation, useQuery, useQueryClient } from "../../../../apps/web/src/lib/react-query";
import { FormEvent, useState } from "react";

import { createWarehouse, listWarehouses, logisticsKeys, setPrimaryWarehouse, updateWarehouse } from "../api";
import { LogisticsSection } from "../components/LogisticsSection";
import { Alert } from "../../../../apps/web/src/shared/ui/alert";
import { Button } from "../../../../apps/web/src/shared/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../../../apps/web/src/shared/ui/card";
import { PaginatedDataTable } from "../../../../apps/web/src/shared/ui/paginated-data-table";
import { Dialog } from "../../../../apps/web/src/shared/ui/dialog";
import { Input } from "../../../../apps/web/src/shared/ui/input";
import { LocationPicker } from "../../../../apps/web/src/shared/ui/location-picker";

type WarehouseFormState = {
  id?: string;
  name: string;
  code: string;
  address: string;
  phone: string;
  latitude: string;
  longitude: string;
  formatted_address: string;
  place_id: string;
};
const EMPTY_WAREHOUSE: WarehouseFormState = { name: "", code: "", address: "", phone: "", latitude: "", longitude: "", formatted_address: "", place_id: "" };

export function WarehousesPage() {
  const queryClient = useQueryClient();
  const [warehouseForm, setWarehouseForm] = useState<WarehouseFormState>(EMPTY_WAREHOUSE);
  const [isWarehouseOpen, setIsWarehouseOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const warehousesQuery = useQuery({ queryKey: logisticsKeys.warehouses(), queryFn: listWarehouses });

  const saveWarehouseMutation = useMutation({
    mutationFn: async (payload: WarehouseFormState) => {
      const body = {
        name: payload.name,
        code: payload.code,
        address: payload.address,
        phone: payload.phone,
        latitude: payload.latitude ? Number(payload.latitude) : null,
        longitude: payload.longitude ? Number(payload.longitude) : null,
        formatted_address: payload.formatted_address || null,
        place_id: payload.place_id || null,
      };
      if (payload.id) {
        return updateWarehouse(payload.id, body);
      }
      return createWarehouse(body);
    },
    onSuccess: async () => {
      setIsWarehouseOpen(false);
      setWarehouseForm(EMPTY_WAREHOUSE);
      setError(null);
      await queryClient.invalidateQueries({ queryKey: logisticsKeys.warehouses() });
    },
  });

  const setPrimaryMutation = useMutation({
    mutationFn: setPrimaryWarehouse,
    onSuccess: async () => {
      setError(null);
      await queryClient.invalidateQueries({ queryKey: logisticsKeys.warehouses() });
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

  return (
    <LogisticsSection
      title="Almacenes y zonas"
      description="Organiza la operación por puntos de salida."
      actions={
        <div className="flex gap-2">
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
            <PaginatedDataTable
              columns={[
                {
                  key: "name",
                  header: "Nombre",
                  render: (row) => (
                    <span className="inline-flex items-center gap-2">
                      {row.name}
                      {row.is_primary ? (
                        <span className="rounded-full bg-primary/15 px-2 py-0.5 text-xs font-medium text-primary">
                          Principal
                        </span>
                      ) : null}
                    </span>
                  ),
                },
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
                          latitude: row.latitude != null ? String(row.latitude) : "",
                          longitude: row.longitude != null ? String(row.longitude) : "",
                          formatted_address: row.formatted_address ?? "",
                          place_id: row.place_id ?? "",
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
              pageSize={10}
              label="almacenes"
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
          <label className="block space-y-2 text-sm text-foreground">
            <span>Nombre</span>
            <Input value={warehouseForm.name} onChange={(event) => setWarehouseForm((current) => ({ ...current, name: event.target.value }))} />
          </label>
          <label className="block space-y-2 text-sm text-foreground">
            <span>Código</span>
            <Input value={warehouseForm.code} onChange={(event) => setWarehouseForm((current) => ({ ...current, code: event.target.value }))} />
          </label>
          <label className="block space-y-2 text-sm text-foreground">
            <span>Dirección</span>
            <Input value={warehouseForm.address} onChange={(event) => setWarehouseForm((current) => ({ ...current, address: event.target.value }))} />
          </label>
          <label className="block space-y-2 text-sm text-foreground">
            <span>Teléfono</span>
            <Input value={warehouseForm.phone} onChange={(event) => setWarehouseForm((current) => ({ ...current, phone: event.target.value }))} />
          </label>
          <div className="space-y-2">
            <span className="block text-sm text-foreground">Ubicación del punto de origen</span>
            <LocationPicker
              value={
                warehouseForm.latitude && warehouseForm.longitude
                  ? { lat: Number(warehouseForm.latitude), lng: Number(warehouseForm.longitude) }
                  : null
              }
              onChange={(location) =>
                setWarehouseForm((current) => ({
                  ...current,
                  latitude: String(location.lat),
                  longitude: String(location.lng),
                }))
              }
              height={200}
            />
            {warehouseForm.formatted_address ? (
              <p className="text-xs text-muted-foreground">{warehouseForm.formatted_address}</p>
            ) : null}
          </div>
          {warehouseForm.id ? (
            <label className="flex items-center gap-3 rounded-md border border-border bg-surface px-3 py-2 text-sm text-foreground">
              <input
                type="checkbox"
                checked={
                  warehousesQuery.data?.find((warehouse) => warehouse.id === warehouseForm.id)
                    ?.is_primary ?? false
                }
                onChange={(event) => {
                  if (event.target.checked && warehouseForm.id) {
                    setPrimaryMutation.mutate(warehouseForm.id);
                  }
                }}
              />
              <span>Almacén principal</span>
              <span className="text-xs text-muted-foreground">
                Los balances por defecto y el stock consolidado se refieren a este almacén.
              </span>
            </label>
          ) : null}
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

    </LogisticsSection>
  );
}
