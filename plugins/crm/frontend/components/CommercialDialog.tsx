import { FormEvent } from "react";
import { Button } from "../../../../apps/web/src/shared/ui/button";
import { Combobox } from "../../../../apps/web/src/shared/ui/combobox";
import { DataTable } from "../../../../apps/web/src/shared/ui/data-table";
import { Dialog } from "../../../../apps/web/src/shared/ui/dialog";
import { Input } from "../../../../apps/web/src/shared/ui/input";
import type { CustomerCommercialAssignmentPayload } from "../types";

type CommercialDialogProps = {
  open: boolean;
  onClose: () => void;
  assignments: Array<Record<string, unknown>>;
  addresses: Array<Record<string, unknown>>;
  users: Array<Record<string, unknown>>;
  form: CustomerCommercialAssignmentPayload;
  onFormChange: (form: CustomerCommercialAssignmentPayload) => void;
  editingId: string | null;
  onEditingIdChange: (id: string | null) => void;
  onCancelEdit: () => void;
  onSubmit: (e: FormEvent<HTMLFormElement>) => Promise<void>;
  isCreatePending: boolean;
  isUpdatePending: boolean;
  onEdit: (id: string, data: CustomerCommercialAssignmentPayload) => void;
  onDelete: (id: string) => void;
};

export function CommercialDialog({
  open,
  onClose,
  assignments,
  addresses,
  users,
  form,
  onFormChange,
  editingId,
  onEditingIdChange,
  onCancelEdit,
  onSubmit,
  isCreatePending,
  isUpdatePending,
  onEdit,
  onDelete,
}: CommercialDialogProps) {
  return (
    <Dialog
      open={open}
      title="Gestión comercial"
      description="Asigna agente y supervisor comercial a nivel cliente o sede, sin mezclarlo con contactos externos ni operación diaria."
      onClose={onClose}
      maxWidthClassName="max-w-4xl"
    >
      <div className="space-y-4 text-sm text-foreground">
        <DataTable
          dense
          columns={[
            { key: "role", header: "Rol", render: (row) => row.assignment_role as string },
            { key: "user", header: "Usuario", render: (row) => row.user_display_name as string },
            { key: "email", header: "Email", render: (row) => row.user_email as string },
            {
              key: "address",
              header: "Sede",
              render: (row) => {
                if (!row.address_id) return "Cliente general";
                const addr = addresses.find((a) => a.id === row.address_id);
                return addr ? `${addr.line1} (${addr.address_type})` : "-";
              },
            },
            { key: "primary", header: "Principal", render: (row) => (row.is_primary ? "Sí" : "No") },
            {
              key: "actions",
              header: "Acciones",
              render: (row) => (
                <div className="flex flex-wrap gap-2">
                  <Button
                    variant="secondary"
                    onClick={() => {
                      onEdit(row.id as string, {
                        address_id: (row.address_id as string) || null,
                        user_id: (row.user_id as string) || "",
                        assignment_role: (row.assignment_role as string) || "AGENT",
                        notes: (row.notes as string) || null,
                        is_primary: (row.is_primary as boolean) || false,
                      });
                    }}
                  >
                    Editar
                  </Button>
                  <Button
                    variant="secondary"
                    className="h-7 w-7 px-0 py-0"
                    aria-label="Eliminar asignación comercial"
                    onClick={() => onDelete(row.id as string)}
                  >
                    x
                  </Button>
                </div>
              ),
            },
          ]}
          rows={assignments}
          rowKey={(row) => row.id as string}
          emptyMessage="No hay asignaciones comerciales cargadas."
        />

        <form className="space-y-3 rounded-md border border-border p-4" onSubmit={onSubmit}>
          <div>
            <p className="font-medium text-foreground">{editingId ? "Editar asignación comercial" : "Nueva asignación comercial"}</p>
            <p className="text-xs text-muted-foreground">Define ownership comercial interno por cliente o por sede.</p>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <label className="block space-y-2 text-sm text-foreground">
              <span>Rol comercial</span>
              <Combobox
                value={form.assignment_role}
                onChange={(v) => onFormChange({ ...form, assignment_role: v || "AGENT" })}
                options={[
                  { value: "AGENT", label: "Agente" },
                  { value: "SUPERVISOR", label: "Supervisor" },
                ]}
                placeholder="Seleccionar rol"
                searchPlaceholder="Buscar rol..."
              />
            </label>
            <label className="block space-y-2 text-sm text-foreground">
              <span>Usuario interno</span>
              <Combobox
                value={form.user_id}
                onChange={(v) => onFormChange({ ...form, user_id: v || "" })}
                options={users.map((u) => ({
                  value: u.id as string,
                  label: `${u.full_name} (${u.email})`,
                  keywords: [u.full_name as string, u.email as string],
                }))}
                placeholder="Seleccionar usuario"
                searchPlaceholder="Buscar usuario..."
              />
            </label>
            <label className="block space-y-2 text-sm text-foreground">
              <span>Sede vinculada</span>
              <Combobox
                value={form.address_id ?? ""}
                onChange={(v) => onFormChange({ ...form, address_id: v || null })}
                options={[
                  { value: "", label: "Cliente general", keywords: ["general", "cliente"] },
                  ...addresses.map((addr) => ({
                    value: addr.id as string,
                    label: `${addr.line1}${addr.city ? `, ${addr.city}` : ""} (${addr.address_type})`,
                    keywords: [addr.line1 as string, (addr.city as string) ?? "", addr.address_type as string],
                  })),
                ]}
                placeholder="Cliente general"
                searchPlaceholder="Buscar sede..."
              />
            </label>
            <label className="block space-y-2 text-sm text-foreground">
              <span>Notas</span>
              <Input value={form.notes ?? ""} onChange={(e) => onFormChange({ ...form, notes: e.target.value || null })} />
            </label>
          </div>
          <label className="flex items-center gap-2 text-sm text-foreground">
            <input
              type="checkbox"
              checked={form.is_primary}
              onChange={(e) => onFormChange({ ...form, is_primary: e.target.checked })}
            />
            <span>Marcar como principal</span>
          </label>
          <div className="flex justify-end gap-2">
            {editingId ? (
              <Button variant="secondary" type="button" onClick={onCancelEdit}>
                Cancelar
              </Button>
            ) : null}
            <Button type="submit" disabled={isCreatePending || isUpdatePending}>
              {editingId ? "Guardar cambios" : "Agregar asignación"}
            </Button>
          </div>
        </form>
      </div>
    </Dialog>
  );
}
