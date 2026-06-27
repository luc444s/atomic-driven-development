import { useMutation, useQuery, useQueryClient } from "../../../../apps/web/src/lib/react-query";
import { FormEvent, useState } from "react";

import { completeAgendaTask, createAgendaTask, listAgendaTasks, listTaskTypes, logisticsKeys } from "../api";
import { LogisticsSection } from "../components/LogisticsSection";
import { Alert } from "../../../../apps/web/src/shared/ui/alert";
import { Button } from "../../../../apps/web/src/shared/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../../../apps/web/src/shared/ui/card";
import { DataTable } from "../../../../apps/web/src/shared/ui/data-table";
import { Dialog } from "../../../../apps/web/src/shared/ui/dialog";
import { Input } from "../../../../apps/web/src/shared/ui/input";

type TaskFormState = {
  task_type: string;
  scheduled_date: string;
  customer_name: string;
  description: string;
};

const EMPTY_FORM: TaskFormState = {
  task_type: "VISITA",
  scheduled_date: "",
  customer_name: "",
  description: "",
};

export function AgendaPage() {
  const queryClient = useQueryClient();
  const [formState, setFormState] = useState<TaskFormState>(EMPTY_FORM);
  const [isOpen, setIsOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const tasksQuery = useQuery({ queryKey: logisticsKeys.agenda.list({}), queryFn: () => listAgendaTasks({}) });
  const taskTypesQuery = useQuery({ queryKey: logisticsKeys.taskTypes(), queryFn: listTaskTypes });

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
        customer_name: formState.customer_name || null,
        description: formState.description || null,
      });
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "No se pudo crear la tarea.");
    }
  }

  return (
    <LogisticsSection
      title="Agenda"
      description="Lleva control del día con tareas simples y cierres rápidos."
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
              { key: "customer", header: "Cliente", render: (row) => row.customer_name ?? "-" },
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
          <label className="block space-y-2 text-sm text-slate-300">
            <span>Tipo</span>
            <select
              value={formState.task_type}
              onChange={(event) => setFormState((current) => ({ ...current, task_type: event.target.value }))}
              className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-200"
            >
              {(taskTypesQuery.data ?? []).map((type) => (
                <option key={type.code} value={type.code}>
                  {type.description}
                </option>
              ))}
            </select>
          </label>
          <label className="block space-y-2 text-sm text-slate-300">
            <span>Fecha</span>
            <Input type="date" value={formState.scheduled_date} onChange={(event) => setFormState((current) => ({ ...current, scheduled_date: event.target.value }))} />
          </label>
          <label className="block space-y-2 text-sm text-slate-300">
            <span>Cliente</span>
            <Input value={formState.customer_name} onChange={(event) => setFormState((current) => ({ ...current, customer_name: event.target.value }))} />
          </label>
          <label className="block space-y-2 text-sm text-slate-300">
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
    </LogisticsSection>
  );
}
