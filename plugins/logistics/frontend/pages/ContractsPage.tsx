import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Alert } from "../../../../apps/web/src/shared/ui/alert";
import { Button } from "../../../../apps/web/src/shared/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../../../../apps/web/src/shared/ui/card";
import { ConfirmDialog } from "../../../../apps/web/src/shared/ui/confirm-dialog";
import { DataTable } from "../../../../apps/web/src/shared/ui/data-table";
import { Input } from "../../../../apps/web/src/shared/ui/input";
import { Select } from "../../../../apps/web/src/shared/ui/select";
import { Dialog } from "../../../../apps/web/src/shared/ui/dialog";
import { Badge } from "../../../../apps/web/src/shared/ui/badge";
import { EmptyState } from "../../../../apps/web/src/shared/ui/empty-state";
import { SearchDialog } from "../../../../apps/web/src/shared/ui/search-dialog";
import { ContractFormDialog } from "../contracts/dialogs/contract-form-dialog";
import { ContractStatusBadge } from "../contracts/components/contract-status-badge";
import {
  EMPTY_CONTRACT_FORM,
  EMPTY_CONTRACT_ITEM_FORM,
  EMPTY_TERMINATE_FORM,
  type ContractFormState,
  type ContractItemFormState,
  type TerminateFormState,
} from "../contracts/forms/contract-form-state";
import {
  buildCreatePayload,
  buildItemPayload,
  buildTerminatePayload,
  buildUpdatePayload,
} from "../contracts/forms/contract-payload";
import { formatDate, formatDateTime } from "../cylinders/utils/formatters";
import { useContractHistory, useContractList } from "../contracts/hooks/use-contract-data";
import {
  createContract,
  updateContract,
  activateContract,
  signContract,
  renewContract,
  terminateContract,
  cancelContract,
  uploadContractFile,
  addContractItem,
  deliverContractItem,
  returnContractItem,
  type LogisticsCylinderContract,
} from "../api/contracts";
import { listCylinders, type LogisticsCylinder } from "../api/cylinders";
import { useMutation } from "../../../../apps/web/src/lib/react-query";

export function ContractsPage() {
  const navigate = useNavigate();
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [isDetailOpen, setIsDetailOpen] = useState(false);
  const [isTerminateOpen, setIsTerminateOpen] = useState(false);
  const [isRenewOpen, setIsRenewOpen] = useState(false);
  const [isAddItemOpen, setIsAddItemOpen] = useState(false);
  const [isCylinderSearchOpen, setIsCylinderSearchOpen] = useState(false);
  const [selectedContract, setSelectedContract] = useState<LogisticsCylinderContract | null>(null);
  const [contractForm, setContractForm] = useState<ContractFormState>(EMPTY_CONTRACT_FORM);
  const [itemForm, setItemForm] = useState<ContractItemFormState>(EMPTY_CONTRACT_ITEM_FORM);
  const [newContractCylinderId, setNewContractCylinderId] = useState("");
  const [newContractCylinderSerial, setNewContractCylinderSerial] = useState("");
  const [selectedContractFile, setSelectedContractFile] = useState<File | null>(null);
  const [terminateForm, setTerminateForm] = useState<TerminateFormState>(EMPTY_TERMINATE_FORM);
  const [renewEndDate, setRenewEndDate] = useState("");
  const [error, setError] = useState<string | null>(null);

  const { data: contracts = [], isLoading, refetch } = useContractList({
    status: statusFilter || undefined,
    type: typeFilter || undefined,
  });
  const contractHistoryQuery = useContractHistory(selectedContract?.id ?? null);

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

  const addItemMutation = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: ReturnType<typeof buildItemPayload> }) =>
      addContractItem(id, payload),
    onSuccess: () => { setIsAddItemOpen(false); refetch(); },
    onError: (e: Error) => setError(e.message),
  });

  const deliverItemMutation = useMutation({
    mutationFn: ({ cid, iid }: { cid: string; iid: string }) => deliverContractItem(cid, iid),
    onSuccess: () => refetch(),
  });

  const returnItemMutation = useMutation({
    mutationFn: ({ cid, iid }: { cid: string; iid: string }) => returnContractItem(cid, iid),
    onSuccess: () => refetch(),
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
      if (newContractCylinderId) {
        await addContractItem(created.id, {
          cylinder_id: newContractCylinderId,
          serial: newContractCylinderSerial || undefined,
          quantity: Number(contractForm.quantity || "1"),
          unit_price: Number(contractForm.unit_price || "0"),
        });
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

  const handleAddItem = (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    if (!selectedContract) return;
    addItemMutation.mutate({
      id: selectedContract.id,
      payload: buildItemPayload(itemForm),
    });
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
        <Button onClick={() => { setContractForm(EMPTY_CONTRACT_FORM); setNewContractCylinderId(""); setNewContractCylinderSerial(""); setSelectedContractFile(null); setError(null); setIsCreateOpen(true); }}>
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
        onCylinderSelect={(id, serial) => { setNewContractCylinderId(id); setNewContractCylinderSerial(serial); }}
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
        onCylinderSelect={() => {}}
        onFileSelect={setSelectedContractFile}
      />

      <Dialog
        open={isDetailOpen}
        title={`Contrato ${selectedContract?.contract_number || "(borrador)"}`}
        maxWidthClassName="max-w-2xl"
        onClose={() => setIsDetailOpen(false)}
      >
        {selectedContract && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div><span className="font-medium">Estado:</span> <ContractStatusBadge status={selectedContract.status} /></div>
              <div><span className="font-medium">Tipo:</span> {typeLabel(selectedContract.contract_type)}</div>
              <div><span className="font-medium">Cliente:</span> {selectedContract.customer_name || "-"}</div>
              <div><span className="font-medium">Serie:</span> {selectedContract.series || "-"}</div>
              <div><span className="font-medium">Inicio:</span> {formatDate(selectedContract.start_date)}</div>
              <div><span className="font-medium">Fin:</span> {selectedContract.end_date ? formatDate(selectedContract.end_date) : "-"}</div>
              <div><span className="font-medium">Cantidad:</span> {selectedContract.quantity}</div>
              <div><span className="font-medium">Precio unitario:</span> {selectedContract.unit_price?.toFixed(2)}</div>
              <div><span className="font-medium">Firmado:</span> {selectedContract.signed_flag ? "Si" : "No"}</div>
              {selectedContract.contract_file_path && (
                <div className="col-span-2"><span className="font-medium">Archivo:</span> {selectedContract.contract_file_path}</div>
              )}
              {selectedContract.notes && (
                <div className="col-span-2"><span className="font-medium">Notas:</span> {selectedContract.notes}</div>
              )}
              {selectedContract.observations && (
                <div className="col-span-2"><span className="font-medium">Observaciones:</span> {selectedContract.observations}</div>
              )}
            </div>

            <div className="border-t pt-3">
              <div className="flex items-center justify-between mb-2">
                <h4 className="font-medium">Cilindros asignados</h4>
                {selectedContract.status !== "EXPIRED" && selectedContract.status !== "CANCELLED" && (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => {
                      setItemForm(EMPTY_CONTRACT_ITEM_FORM);
                      setIsAddItemOpen(true);
                    }}
                  >
                    Agregar
                  </Button>
                )}
              </div>
              {selectedContract.items.length === 0 ? (
                <p className="text-sm text-muted-foreground">Sin cilindros asignados.</p>
              ) : (
                <div className="space-y-1">
                  {selectedContract.items.map((item) => (
                    <div key={item.id} className="flex items-center justify-between rounded border p-2 text-sm">
                      {item.serial ? (
                        <Button size="sm" variant="link" className="h-auto p-0 text-sm font-normal" onClick={() => navigate(`/app/logistics/cylinders?search=${encodeURIComponent(item.serial)}`)}>
                          {item.serial}
                        </Button>
                      ) : (
                        <span className="text-sm text-muted-foreground">-</span>
                      )}
                      <div className="flex items-center gap-2">
                        {item.delivered_at ? (
                          <Badge className="bg-blue-100 text-blue-800">
                            Entregado {formatDate(item.delivered_at)}
                          </Badge>
                        ) : (
                          <Button
                            size="sm"
                            variant="ghost"
                            className="text-blue-600"
                            onClick={() =>
                              deliverItemMutation.mutate({
                                cid: selectedContract.id,
                                iid: item.id,
                              })
                            }
                          >
                            Marcar entregado
                          </Button>
                        )}
                        {item.returned_at ? (
                          <Badge className="bg-gray-100 text-gray-800">
                            Devuelto {formatDate(item.returned_at)}
                          </Badge>
                        ) : item.delivered_at ? (
                          <Button
                            size="sm"
                            variant="ghost"
                            className="text-orange-600"
                            onClick={() =>
                              returnItemMutation.mutate({
                                cid: selectedContract.id,
                                iid: item.id,
                              })
                            }
                          >
                            Marcar devuelto
                          </Button>
                        ) : null}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="border-t pt-3">
              <h4 className="mb-2 font-medium">Historial</h4>
              {contractHistoryQuery.isLoading ? (
                <p className="text-sm text-muted-foreground">Cargando historial...</p>
              ) : (contractHistoryQuery.data?.length ?? 0) === 0 ? (
                <p className="text-sm text-muted-foreground">Sin eventos registrados.</p>
              ) : (
                <div className="space-y-1 text-sm">
                  {contractHistoryQuery.data?.map((event) => (
                    <div key={event.id} className="rounded border p-2">
                      <div className="font-medium">{event.event_type}</div>
                      <div className="text-muted-foreground">{formatDateTime(event.occurred_at)}</div>
                      {event.description ? <div>{event.description}</div> : null}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </Dialog>

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

      <Dialog
        open={isAddItemOpen}
        title="Agregar cilindro"
        maxWidthClassName="max-w-sm"
        onClose={() => setIsAddItemOpen(false)}
      >
        <form className="space-y-3" onSubmit={handleAddItem}>
          <div>
            <div className="text-sm font-medium mb-1">Cilindro</div>
            <div className="flex gap-2">
              <Input
                value={itemForm.serial}
                onChange={(e) => setItemForm({ ...itemForm, serial: e.target.value })}
                placeholder="Numero de serie..."
                className="flex-1"
              />
              <Button type="button" variant="outline" onClick={() => setIsCylinderSearchOpen(true)}>
                Buscar
              </Button>
            </div>
          </div>
          <div>
            <div className="text-sm font-medium mb-1">Cantidad</div>
            <Input
              type="number"
              value={itemForm.quantity}
              onChange={(e) => setItemForm({ ...itemForm, quantity: e.target.value })}
              min="1"
            />
          </div>
          <div>
            <div className="text-sm font-medium mb-1">Precio unitario</div>
            <Input
              type="number"
              value={itemForm.unit_price}
              onChange={(e) => setItemForm({ ...itemForm, unit_price: e.target.value })}
              step="0.01"
            />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" onClick={() => setIsAddItemOpen(false)}>
              Cancelar
            </Button>
            <Button type="submit" disabled={addItemMutation.isPending}>
              Agregar
            </Button>
          </div>
        </form>
      </Dialog>

      <SearchDialog<LogisticsCylinder>
        open={isCylinderSearchOpen}
        onOpenChange={setIsCylinderSearchOpen}
        title="Buscar cilindro"
        placeholder="Número de serie..."
        columns={[
          { key: "serial", header: "Serie", render: (cyl: LogisticsCylinder) => cyl.serial },
          { key: "gas", header: "Gas", render: (cyl: LogisticsCylinder) => cyl.gas_group_id ?? "-" },
          { key: "state", header: "Estado", render: (cyl: LogisticsCylinder) => cyl.current_state },
        ]}
        fetchFn={(q) => listCylinders({ search: q || undefined, active: undefined })}
        onSelect={(cyl) => {
          setItemForm({ ...itemForm, cylinder_id: cyl.id, serial: cyl.serial });
        }}
        getRowId={(cyl) => cyl.id}
      />

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
