import { useMutation, useQuery, useQueryClient } from "../../../../apps/web/src/lib/react-query";
import { FormEvent, useState } from "react";

import { createVehicle, listVehicles, listWarehouses, logisticsKeys, updateVehicle } from "../api";
import { getRealWarehouses } from "../api/warehouses";
import { LogisticsSection } from "../components/LogisticsSection";
import { Alert } from "@systutor/shell/ui/alert";
import { Button } from "@systutor/shell/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@systutor/shell/ui/card";
import { DataTable } from "@systutor/shell/ui/data-table";
import { Dialog } from "@systutor/shell/ui/dialog";
import { Input } from "@systutor/shell/ui/input";
import { Select } from "@systutor/shell/ui/select";

type VehicleFormState = {
  id?: string;
  plate: string;
  vehicle_type: string;
  brand: string;
  model: string;
  capacity_weight: string;
  warehouse_id: string;
};

const EMPTY_FORM: VehicleFormState = {
  plate: "",
  vehicle_type: "",
  brand: "",
  model: "",
  capacity_weight: "",
  warehouse_id: "",
};

export function VehiclesPage() {
  const queryClient = useQueryClient();
  const [formState, setFormState] = useState<VehicleFormState>(EMPTY_FORM);
  const [isOpen, setIsOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const vehiclesQuery = useQuery({ queryKey: logisticsKeys.vehicles(), queryFn: listVehicles });
  const warehousesQuery = useQuery({ queryKey: logisticsKeys.warehouses(), queryFn: listWarehouses });
  const realWarehouses = getRealWarehouses(warehousesQuery.data ?? []);

  const saveMutation = useMutation({
    mutationFn: async (payload: VehicleFormState) => {
      const normalized = {
        plate: payload.plate,
        vehicle_type: payload.vehicle_type || null,
        brand: payload.brand || null,
        model: payload.model || null,
        capacity_weight: payload.capacity_weight ? Number(payload.capacity_weight) : null,
        warehouse_id: payload.warehouse_id || null,
      };
      if (payload.id) {
        return updateVehicle(payload.id, normalized);
      }
      return createVehicle(normalized);
    },
    onSuccess: async () => {
      setIsOpen(false);
      setFormState(EMPTY_FORM);
      setError(null);
      await queryClient.invalidateQueries({ queryKey: logisticsKeys.vehicles() });
    },
  });

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    try {
      await saveMutation.mutateAsync(formState);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "No se pudo guardar el vehículo.");
    }
  }

  return (
    <LogisticsSection
      title="Vehículos (secundario)"
      description="Superficie reusable de soporte. En v1.1 la selección y creación principal de vehículos ocurre desde Jornadas."
      actions={<Button onClick={() => setIsOpen(true)}>Nuevo vehículo</Button>}
    >
      {error ? <Alert title="No se pudo completar la acción">{error}</Alert> : null}
      <Card>
        <CardHeader>
          <CardTitle>Flota</CardTitle>
          <CardDescription>Vista rápida de unidades disponibles y su almacén base.</CardDescription>
        </CardHeader>
        <CardContent>
          <DataTable
            columns={[
              { key: "plate", header: "Placa", render: (row) => row.plate },
              { key: "type", header: "Tipo", render: (row) => row.vehicle_type ?? "-" },
              { key: "brand", header: "Marca", render: (row) => row.brand ?? "-" },
              {
                key: "warehouse",
                header: "Base",
                render: (row) => warehousesQuery.data?.find((item) => item.id === row.warehouse_id)?.name ?? "-",
              },
              {
                key: "actions",
                header: "Editar",
                className: "w-32",
                render: (row) => (
                  <Button
                    variant="secondary"
                    onClick={() => {
                      setFormState({
                        id: row.id,
                        plate: row.plate,
                        vehicle_type: row.vehicle_type ?? "",
                        brand: row.brand ?? "",
                        model: row.model ?? "",
                        capacity_weight: row.capacity_weight ? String(row.capacity_weight) : "",
                        warehouse_id: row.warehouse_id ?? "",
                      });
                      setIsOpen(true);
                    }}
                  >
                    Abrir
                  </Button>
                ),
              },
            ]}
            rows={vehiclesQuery.data ?? []}
            rowKey={(row) => row.id}
            emptyMessage="No hay vehículos registrados todavía."
          />
        </CardContent>
      </Card>

      <Dialog
        open={isOpen}
        title={formState.id ? "Editar vehículo" : "Nuevo vehículo"}
        description="Guarda una unidad de trabajo con su información base."
        onClose={() => {
          setIsOpen(false);
          setFormState(EMPTY_FORM);
        }}
      >
        <form className="space-y-4" onSubmit={onSubmit}>
          <label className="block space-y-2 text-sm text-foreground">
            <span>Placa</span>
            <Input value={formState.plate} onChange={(event) => setFormState((current) => ({ ...current, plate: event.target.value }))} />
          </label>
          <div className="grid gap-4 md:grid-cols-2">
            <label className="block space-y-2 text-sm text-foreground">
              <span>Tipo</span>
              <Input value={formState.vehicle_type} onChange={(event) => setFormState((current) => ({ ...current, vehicle_type: event.target.value }))} />
            </label>
            <label className="block space-y-2 text-sm text-foreground">
              <span>Marca</span>
              <Input value={formState.brand} onChange={(event) => setFormState((current) => ({ ...current, brand: event.target.value }))} />
            </label>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <label className="block space-y-2 text-sm text-foreground">
              <span>Modelo</span>
              <Input value={formState.model} onChange={(event) => setFormState((current) => ({ ...current, model: event.target.value }))} />
            </label>
            <label className="block space-y-2 text-sm text-foreground">
              <span>Capacidad</span>
              <Input value={formState.capacity_weight} onChange={(event) => setFormState((current) => ({ ...current, capacity_weight: event.target.value }))} />
            </label>
          </div>
          <label className="block space-y-2 text-sm text-foreground">
            <span>Almacén base</span>
              <Select
                value={formState.warehouse_id}
                onChange={(value) => setFormState((current) => ({ ...current, warehouse_id: value }))}
                placeholder="Sin asignar"
                options={realWarehouses.map((warehouse) => ({ value: warehouse.id, label: warehouse.name }))} />
          </label>
          <div className="flex justify-end gap-3">
            <Button type="button" variant="secondary" onClick={() => setIsOpen(false)}>
              Cancelar
            </Button>
            <Button type="submit" disabled={saveMutation.isPending}>
              Guardar
            </Button>
          </div>
        </form>
      </Dialog>
    </LogisticsSection>
  );
}
