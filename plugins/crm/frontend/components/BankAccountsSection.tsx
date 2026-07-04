import { FormEvent, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "../../../../apps/web/src/lib/react-query";
import { Button } from "../../../../apps/web/src/shared/ui/button";
import { ConfirmDialog } from "../../../../apps/web/src/shared/ui/confirm-dialog";
import { DataTable } from "../../../../apps/web/src/shared/ui/data-table";
import { Input } from "../../../../apps/web/src/shared/ui/input";
import { toast } from "../../../../apps/web/src/shared/ui/toast";
import {
  createCustomerBankAccount,
  crmKeys,
  deleteCustomerBankAccount,
  listCustomerBankAccounts,
  updateCustomerBankAccount,
} from "../api";
import type { CustomerBankAccount, CustomerBankAccountPayload } from "../types";

type BankAccountsSectionProps = {
  customerId: string;
  canManage?: boolean;
};

const EMPTY_BANK_ACCOUNT: CustomerBankAccountPayload = {
  bank_name: "",
  account_holder: "",
  iban: "",
  bic_swift: null,
  is_primary: false,
  notes: null,
};

export function BankAccountsSection({ customerId, canManage = false }: BankAccountsSectionProps) {
  const queryClient = useQueryClient();
  const [form, setForm] = useState<CustomerBankAccountPayload>(EMPTY_BANK_ACCOUNT);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);

  const query = useQuery({
    queryKey: crmKeys.customers.bankAccounts(customerId),
    queryFn: () => listCustomerBankAccounts(customerId),
  });

  const createMutation = useMutation({
    mutationFn: () => createCustomerBankAccount(customerId, form),
    onSuccess: async () => {
      toast.success("Cuenta bancaria creada");
      setForm(EMPTY_BANK_ACCOUNT);
      await queryClient.invalidateQueries({ queryKey: crmKeys.customers.bankAccounts(customerId) });
    },
  });

  const updateMutation = useMutation({
    mutationFn: () => updateCustomerBankAccount(editingId!, form),
    onSuccess: async () => {
      toast.success("Cuenta bancaria actualizada");
      setForm(EMPTY_BANK_ACCOUNT);
      setEditingId(null);
      await queryClient.invalidateQueries({ queryKey: crmKeys.customers.bankAccounts(customerId) });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (bankAccountId: string) => deleteCustomerBankAccount(bankAccountId),
    onSuccess: async () => {
      toast.success("Cuenta bancaria eliminada");
      await queryClient.invalidateQueries({ queryKey: crmKeys.customers.bankAccounts(customerId) });
    },
  });

  async function submitForm(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (editingId) {
      await updateMutation.mutateAsync();
    } else {
      await createMutation.mutateAsync();
    }
  }

  function startEdit(row: CustomerBankAccount) {
    setEditingId(row.id);
    setForm({
      bank_name: row.bank_name,
      account_holder: row.account_holder,
      iban: row.iban,
      bic_swift: row.bic_swift,
      is_primary: row.is_primary,
      notes: row.notes,
    });
  }

  function cancelEdit() {
    setEditingId(null);
    setForm(EMPTY_BANK_ACCOUNT);
  }

  const isPending = createMutation.isPending || updateMutation.isPending;

  return (
    <div className="space-y-4">
      <DataTable
        dense
        columns={[
          { key: "bank_name", header: "Banco", render: (row: CustomerBankAccount) => row.bank_name },
          { key: "account_holder", header: "Titular", render: (row: CustomerBankAccount) => row.account_holder },
          { key: "iban", header: "IBAN", render: (row: CustomerBankAccount) => row.iban },
          { key: "bic", header: "BIC/SWIFT", render: (row: CustomerBankAccount) => row.bic_swift ?? "-" },
          { key: "primary", header: "Principal", render: (row: CustomerBankAccount) => (row.is_primary ? "Sí" : "No") },
          {
            key: "actions",
            header: "",
            render: (row: CustomerBankAccount) =>
              canManage ? (
                <Button
                  variant="secondary"
                  className="h-7 w-7 px-0 py-0"
                  aria-label="Eliminar cuenta bancaria"
                  onClick={(event) => {
                    event.stopPropagation();
                    setConfirmDeleteId(row.id);
                  }}
                >
                  x
                </Button>
              ) : null,
          },
        ]}
        rows={query.data ?? []}
        rowKey={(row) => row.id}
        emptyMessage="No hay cuentas bancarias cargadas."
        onRowClick={canManage ? startEdit : undefined}
      />

      <ConfirmDialog
        open={confirmDeleteId !== null}
        onClose={() => setConfirmDeleteId(null)}
        onConfirm={() => {
          if (confirmDeleteId) deleteMutation.mutate(confirmDeleteId);
          setConfirmDeleteId(null);
        }}
        title="Eliminar cuenta bancaria"
        description="¿Estás seguro de eliminar esta cuenta bancaria?"
        destructive
        confirmLabel="Eliminar"
      />

      {canManage ? (
        <form className="space-y-3 rounded-md border border-border p-4" onSubmit={submitForm}>
          <div>
            <p className="text-sm font-medium text-foreground">
              {editingId ? "Editar cuenta bancaria" : "Nueva cuenta bancaria"}
            </p>
            <p className="text-xs text-muted-foreground">
              Datos bancarios del cliente para domiciliaciones, transferencias y remesas.
            </p>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <label className="block space-y-2 text-sm text-foreground">
              <span>Banco</span>
              <Input
                value={form.bank_name}
                onChange={(event) => setForm((current) => ({ ...current, bank_name: event.target.value }))}
                placeholder="Ej. Banco Santander"
              />
            </label>
            <label className="block space-y-2 text-sm text-foreground">
              <span>Titular</span>
              <Input
                value={form.account_holder}
                onChange={(event) => setForm((current) => ({ ...current, account_holder: event.target.value }))}
                placeholder="Nombre del titular"
              />
            </label>
            <label className="block space-y-2 text-sm text-foreground">
              <span>IBAN</span>
              <Input
                value={form.iban}
                onChange={(event) => setForm((current) => ({ ...current, iban: event.target.value }))}
                placeholder="ES00 0000 0000 0000 0000 0000"
              />
            </label>
            <label className="block space-y-2 text-sm text-foreground">
              <span>BIC/SWIFT</span>
              <Input
                value={form.bic_swift ?? ""}
                onChange={(event) => setForm((current) => ({ ...current, bic_swift: event.target.value || null }))}
                placeholder="Opcional"
              />
            </label>
            <label className="block space-y-2 text-sm text-foreground md:col-span-2">
              <span>Notas</span>
              <Input
                value={form.notes ?? ""}
                onChange={(event) => setForm((current) => ({ ...current, notes: event.target.value || null }))}
                placeholder="Opcional"
              />
            </label>
          </div>
          <label className="flex items-center gap-2 text-sm text-foreground">
            <input
              type="checkbox"
              checked={form.is_primary}
              onChange={(event) => setForm((current) => ({ ...current, is_primary: event.target.checked }))}
            />
            <span>Marcar como cuenta principal</span>
          </label>
          <div className="flex justify-end gap-2">
            {editingId ? (
              <Button variant="secondary" type="button" onClick={cancelEdit}>
                Cancelar
              </Button>
            ) : null}
            <Button type="submit" disabled={isPending}>
              {editingId ? "Guardar cambios" : "Agregar cuenta"}
            </Button>
          </div>
        </form>
      ) : null}
    </div>
  );
}
