import { useMutation, useQuery, useQueryClient } from "../../../../apps/web/src/lib/react-query";
import { FormEvent, useState } from "react";
import type { CustomerBrief } from "../../../crm/frontend/types";

import { completeAgendaTask, createAgendaTask, listAgendaTasks, listTaskTypes, logisticsKeys } from "../api";
import { listCustomers } from "../../../crm/frontend/api";
import { CustomerSearchDialog } from "../../../crm/frontend/components/CustomerSearchDialog";
import { LogisticsSection } from "../components/LogisticsSection";
import { Alert } from "@systutor/shell/ui/alert";
import { Button } from "@systutor/shell/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@systutor/shell/ui/card";
import { DataTable } from "@systutor/shell/ui/data-table";
import { Dialog } from "@systutor/shell/ui/dialog";
import { Input } from "@systutor/shell/ui/input";
import { Select } from "@systutor/shell/ui/select";

type TaskFormState = {
  task_type: string;
  scheduled_date: string;
  customer_id: string;
  customer_name: string;
  description: string;
};

const EMPTY_FORM: TaskFormState = {
  task_type: "VISITA",
  scheduled_date: "",
  customer_id: "",
  customer_name: "",
  description: "",
};

export function AgendaPage() {
  const queryClient = useQueryClient();
  const [formState, setFormState] = useState<TaskFormState>(EMPTY_FORM);
  const [isOpen, setIsOpen] = useState(false);
  const [isCustomerSearchOpen, setIsCustomerSearchOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const tasksQuery = useQuery({ queryKey: logisticsKeys.agenda.list({}), queryFn: () => listAgendaTasks({}) });
  const taskTypesQuery = useQuery({ queryKey: logisticsKeys.taskTypes(), queryFn: listTaskTypes });
  const customersQuery = useQuery({
    queryKey: ["crm", "customers", "logistics-lookup"],
    queryFn: () => listCustomers({ limit: 200, offset: 0 }),
  });

  const createMutation = useMutation({
    mutationFn: createAgendaTask,
    onSuccess: async () => {
      setIsOpen(false);
      setFormState(EMPTY_FORM);
      setError(null);
      await queryClient.invalidateQueries({ queryKey: logisticsKeys.agenda.all() });
    },
  });
  const completeMutation = useMutation({
    mutationFn: completeAgendaTask,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: logisticsKeys.agenda.all() });
    },
  });

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    try {
      await createMutation.mutateAsync({
        task_type: formState.task_type,
        scheduled_date: formState.scheduled_date,
        customer_id: formState.customer_id,
        description: formState.description || null,
      });
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "No se pudo crear la tarea.");
    }
  }

  return (
    <LogisticsSection
      title="Agenda (transicion)"
      description="Superficie auxiliar mientras Jornadas absorbe el contexto operativo diario del repartidor."
      actions={<Button onClick={() => setIsOpen(true)}>Nueva tarea</Button>}
    >
      {error ? <Alert title="No se pudo completar la acción">{error}</Alert> : null}
      <Card>
        <CardHeader>
          <CardTitle>Tareas programadas</CardTitle>
          <CardDescription>Resumen por tipo, fecha y estado actual.</CardDescription>
        </CardHeader>
        <CardContent>
          <DataTable
            columns={[
              { key: "date", header: "Fecha", render: (row) => row.scheduled_date },
              { key: "type", header: "Tipo", render: (row) => row.task_type },
              {
                key: "customer",
                header: "Cliente",
                render: (row) =>
                  customersQuery.data?.items.find((item) => item.id === row.customer_id)?.commercial_name ??
                  customersQuery.data?.items.find((item) => item.id === row.customer_id)?.legal_name ??
                  row.customer_name ??
                  "-",
              },
              { key: "status", header: "Estado", render: (row) => row.status },
              {
                key: "actions",
                header: "Cerrar",
                className: "w-32",
                render: (row) => (
                  <Button variant="secondary" onClick={() => completeMutation.mutate(row.id)}>
                    Completar
                  </Button>
                ),
              },
            ]}
            rows={tasksQuery.data ?? []}
            rowKey={(row) => row.id}
            emptyMessage="No hay tareas programadas todavía."
          />
        </CardContent>
      </Card>

      <Dialog
        open={isOpen}
        title="Nueva tarea"
        description="Crea una actividad simple para el día."
        onClose={() => setIsOpen(false)}
      >
        <form className="space-y-4" onSubmit={onSubmit}>
          <label className="block space-y-2 text-sm text-foreground">
            <span>Tipo</span>
            <Select
              value={formState.task_type}
              onChange={(value) => setFormState((current) => ({ ...current, task_type: value }))}
              options={(taskTypesQuery.data ?? []).map((type) => ({ value: type.code, label: type.description }))} />
          </label>
          <label className="block space-y-2 text-sm text-foreground">
            <span>Fecha</span>
            <Input type="date" value={formState.scheduled_date} onChange={(event) => setFormState((current) => ({ ...current, scheduled_date: event.target.value }))} />
          </label>
          <div className="space-y-2 text-sm text-foreground">
            <span>Cliente</span>
            <Button type="button" variant="secondary" onClick={() => setIsCustomerSearchOpen(true)}>
              {formState.customer_name ? `${formState.customer_name} (${formState.customer_id})` : "Seleccionar cliente"}
            </Button>
          </div>
          <label className="block space-y-2 text-sm text-foreground">
            <span>Descripción</span>
            <Input value={formState.description} onChange={(event) => setFormState((current) => ({ ...current, description: event.target.value }))} />
          </label>
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
          setFormState((current) => ({ ...current, customer_id: customer.id, customer_name: customer.display_name }))
        }
      />
    </LogisticsSection>
  );
}
