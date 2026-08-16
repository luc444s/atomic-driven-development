import { FormEvent, useState } from "react";
import { Alert } from "@systutor/shell/ui/alert";
import { Button } from "@systutor/shell/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@systutor/shell/ui/card";
import { ConfirmDialog } from "@systutor/shell/ui/confirm-dialog";
import { DataTable } from "@systutor/shell/ui/data-table";
import { Input } from "@systutor/shell/ui/input";
import { Select } from "@systutor/shell/ui/select";
import { Dialog } from "@systutor/shell/ui/dialog";
import { EmptyState } from "@systutor/shell/ui/empty-state";
import { ContractDetailDialog } from "../contracts/components/contract-detail-dialog";
import { ContractFormDialog } from "../contracts/dialogs/contract-form-dialog";
import { ContractStatusBadge } from "../contracts/components/contract-status-badge";
import {
  EMPTY_CONTRACT_FORM,
  EMPTY_TERMINATE_FORM,
  type ContractFormState,
  type TerminateFormState,
} from "../contracts/forms/contract-form-state";
import {
  buildCreatePayload,
  buildTerminatePayload,
  buildUpdatePayload,
} from "../contracts/forms/contract-payload";
import { formatDate } from "../cylinders/utils/formatters";
import { useContractList } from "../contracts/hooks/use-contract-data";
import {
  createContract,
  updateContract,
  activateContract,
  signContract,
  renewContract,
  terminateContract,
  cancelContract,
  uploadContractFile,
  type LogisticsCylinderContract,
} from "../api/contracts";
import { useMutation } from "../../../../apps/web/src/lib/react-query";

export function ContractsPage() {
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [isDetailOpen, setIsDetailOpen] = useState(false);
  const [isTerminateOpen, setIsTerminateOpen] = useState(false);
  const [isRenewOpen, setIsRenewOpen] = useState(false);
  const [selectedContract, setSelectedContract] = useState<LogisticsCylinderContract | null>(null);
  const [contractForm, setContractForm] = useState<ContractFormState>(EMPTY_CONTRACT_FORM);
  const [selectedContractFile, setSelectedContractFile] = useState<File | null>(null);
  const [terminateForm, setTerminateForm] = useState<TerminateFormState>(EMPTY_TERMINATE_FORM);
  const [renewEndDate, setRenewEndDate] = useState("");
  const [error, setError] = useState<string | null>(null);

  const { data: contracts = [], isLoading, refetch } = useContractList({
    status: statusFilter || undefined,
    type: typeFilter || undefined,
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: ReturnType<typeof buildUpdatePayload> }) =>
      updateContract(id, payload),
    onError: (e: Error) => setError(e.message),
  });

  const activateMutation = useMutation({
    mutationFn: (id: string) => activateContract(id),
    onSuccess: () => refetch(),
    onError: (e: Error) => setError(e.message),
  });

  const signMutation = useMutation({
    mutationFn: (id: string) => signContract(id, {}),
    onSuccess: () => refetch(),
    onError: (e: Error) => setError(e.message),
  });

  const renewMutation = useMutation({
    mutationFn: ({ id, endDate }: { id: string; endDate: string }) => renewContract(id, { end_date: endDate }),
    onSuccess: () => { setIsRenewOpen(false); refetch(); },
    onError: (e: Error) => setError(e.message),
  });

  const terminateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: ReturnType<typeof buildTerminatePayload> }) =>
      terminateContract(id, payload),
    onSuccess: () => { setIsTerminateOpen(false); refetch(); },
    onError: (e: Error) => setError(e.message),
  });

  const cancelMutation = useMutation({
    mutationFn: (id: string) => cancelContract(id),
    onSuccess: () => refetch(),
    onError: (e: Error) => setError(e.message),
  });

  const handleCreate = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsCreating(true);
    try {
      const created = await createContract(buildCreatePayload(contractForm));
      if (selectedContractFile) {
        await uploadContractFile(created.id, selectedContractFile);
      }
      setIsCreateOpen(false);
      setSelectedContractFile(null);
      refetch();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setIsCreating(false);
    }
  };

  const handleEdit = (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    if (!selectedContract) return;
    updateMutation.mutate(
      {
        id: selectedContract.id,
        payload: buildUpdatePayload(contractForm),
      },
      {
        onSuccess: async (updated) => {
          if (selectedContractFile) {
            try {
              await uploadContractFile(updated.id, selectedContractFile);
            } catch (err) {
              setError((err as Error).message);
              return;
            }
          }
          setSelectedContractFile(null);
          setIsEditOpen(false);
          refetch();
        },
      }
    );
  };

  const openEdit = (c: LogisticsCylinderContract) => {
    setSelectedContract(c);
    setContractForm({
      contract_type: c.contract_type,
      customer_id: c.customer_id,
      customer_name: c.customer_name || "",
      warehouse_id: c.warehouse_id || "",
      start_date: c.start_date,
      end_date: c.end_date || "",
      renewal_type: c.renewal_type || "",
      cylinder_type_id: c.cylinder_type_id || "",
      cylinder_condition: c.cylinder_condition || "",
      quantity: String(c.quantity),
      unit_price: String(c.unit_price),
      contract_file_path: c.contract_file_path || "",
      notes: c.notes || "",
      observations: c.observations || "",
      excess_wait_days: String(c.excess_wait_days ?? 3),
      auto_renew_on_excess: c.auto_renew_on_excess ?? true,
    });
    setSelectedContractFile(null);
    setIsEditOpen(true);
  };

  const openDetail = (c: LogisticsCylinderContract) => {
    setSelectedContract(c);
    setIsDetailOpen(true);
  };

  const filtered = contracts.filter((c) => {
    if (search && !c.contract_number?.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  const typeLabel = (value: string) => ({ DAILY: "Diario", MONTHLY: "Mensual", ANNUAL: "Anual" }[value] || value);

  return (
    <div className="space-y-4 p-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Contratos de envases</h1>
        <Button onClick={() => { setContractForm(EMPTY_CONTRACT_FORM); setSelectedContractFile(null); setError(null); setIsCreateOpen(true); }}>
          Nuevo contrato
        </Button>
      </div>

      {error && (
        <Alert variant="error" onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Filtros</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-3">
          <Input
            placeholder="Buscar por numero..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="max-w-xs"
          />
          <Select
            value={statusFilter}
            onChange={setStatusFilter}
            options={[
              { value: "", label: "Todos los estados" },
              { value: "DRAFT", label: "Borrador" },
              { value: "PENDING_SIGNATURE", label: "Por firmar" },
              { value: "ACTIVE", label: "Vigente" },
              { value: "EXPIRED", label: "Vencido" },
              { value: "CANCELLED", label: "Anulado" },
            ]}
          />
          <Select
            value={typeFilter}
            onChange={setTypeFilter}
            options={[
              { value: "", label: "Todos los tipos" },
              { value: "DAILY", label: "Diario" },
              { value: "MONTHLY", label: "Mensual" },
              { value: "ANNUAL", label: "Anual" },
            ]}
          />
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-4 text-center text-muted-foreground">Cargando...</div>
          ) : filtered.length === 0 ? (
            <EmptyState
              title="Sin contratos"
              description="No se encontraron contratos con los filtros actuales."
            />
          ) : (
            <DataTable
              columns={[
                { key: "contract_number", header: "Numero", render: (row) => row.contract_number || "-" },
                {
                  key: "contract_type",
                  header: "Tipo",
                  render: (row) => typeLabel(row.contract_type),
                },
                {
                  key: "status",
                  header: "Estado",
                  render: (row) => <ContractStatusBadge status={row.status} />,
                },
                {
                  key: "customer_name",
                  header: "Cliente",
                  render: (row) => row.customer_name || row.customer_id,
                },
                {
                  key: "quantity",
                  header: "Cant.",
                  render: (row) => `${row.quantity} x`,
                },
                {
                  key: "start_date",
                  header: "Inicio",
                  render: (row) => formatDate(row.start_date),
                },
                {
                  key: "actions",
                  header: "",
                  render: (row) => (
                    <div className="flex gap-1">
                      <Button size="sm" variant="ghost" onClick={() => openDetail(row)}>
                        Ver
                      </Button>
                      {row.status === "DRAFT" && (
                        <>
                          <Button size="sm" variant="ghost" onClick={() => openEdit(row)}>
                            Editar
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            className="text-green-600"
                            onClick={() => activateMutation.mutate(row.id)}
                          >
                            Emitir
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            className="text-yellow-600"
                            onClick={() => cancelMutation.mutate(row.id)}
                          >
                            Cancelar
                          </Button>
                        </>
                      )}
                      {row.status === "PENDING_SIGNATURE" && (
                        <Button size="sm" variant="ghost" className="text-blue-600" onClick={() => signMutation.mutate(row.id)}>
                          Firmar
                        </Button>
                      )}
                      {row.status !== "DRAFT" && row.status !== "CANCELLED" && (
                        <>
                          <Button
                            size="sm"
                            variant="ghost"
                            className="text-indigo-600"
                            onClick={() => {
                              setSelectedContract(row);
                              setRenewEndDate(row.end_date || "");
                              setIsRenewOpen(true);
                            }}
                          >
                            Renovar
                          </Button>
                          {row.status !== "EXPIRED" && (
                            <Button
                              size="sm"
                              variant="ghost"
                              className="text-red-600"
                              onClick={() => {
                                setSelectedContract(row);
                                setTerminateForm(EMPTY_TERMINATE_FORM);
                                setIsTerminateOpen(true);
                              }}
                            >
                              Vencer
                            </Button>
                          )}
                        </>
                      )}
                    </div>
                  ),
                },
              ]}
              rows={filtered}
              rowKey={(row) => row.id}
              emptyMessage="No se encontraron contratos."
            />
          )}
        </CardContent>
      </Card>

      <ContractFormDialog
        open={isCreateOpen}
        onOpenChange={setIsCreateOpen}
        title="Nuevo contrato"
        form={contractForm}
        onFormChange={setContractForm}
        isPending={isCreating}
        error={error}
        onSubmit={handleCreate}
        onFileSelect={setSelectedContractFile}
        showNotes={false}
      />

      <ContractFormDialog
        open={isEditOpen}
        onOpenChange={setIsEditOpen}
        title="Editar contrato"
        form={contractForm}
        onFormChange={setContractForm}
        isPending={updateMutation.isPending}
        error={error}
        onSubmit={handleEdit}
        onFileSelect={setSelectedContractFile}
      />

      {selectedContract ? (
        <ContractDetailDialog
          contract={selectedContract}
          open={isDetailOpen}
          onClose={() => setIsDetailOpen(false)}
        />
      ) : null}

      <Dialog
        open={isRenewOpen}
        title={`Renovar contrato ${selectedContract?.contract_number || ""}`}
        maxWidthClassName="max-w-sm"
        onClose={() => setIsRenewOpen(false)}
      >
        <form
          className="space-y-3"
          onSubmit={(e) => {
            e.preventDefault();
            if (!selectedContract || !renewEndDate) return;
            renewMutation.mutate({ id: selectedContract.id, endDate: renewEndDate });
          }}
        >
          <div>
            <div className="mb-1 text-sm font-medium">Nueva fecha fin</div>
            <Input type="date" value={renewEndDate} onChange={(e) => setRenewEndDate(e.target.value)} />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" onClick={() => setIsRenewOpen(false)}>
              Cancelar
            </Button>
            <Button type="submit" disabled={renewMutation.isPending || !renewEndDate}>
              Renovar
            </Button>
          </div>
        </form>
      </Dialog>

      <ConfirmDialog
        open={isTerminateOpen}
        title="Marcar contrato como vencido"
        onConfirm={() => {
          if (selectedContract) {
            terminateMutation.mutate({
              id: selectedContract.id,
              payload: buildTerminatePayload(terminateForm),
            });
          }
        }}
        onCancel={() => setIsTerminateOpen(false)}
        confirmLabel="Marcar vencido"
      >
        <div className="space-y-3">
          <p>Ingrese el motivo para marcar el contrato como vencido:</p>
          <Input
            value={terminateForm.reason}
            onChange={(e) => setTerminateForm({ reason: e.target.value })}
            placeholder="Motivo..."
          />
        </div>
      </ConfirmDialog>
    </div>
  );
}
