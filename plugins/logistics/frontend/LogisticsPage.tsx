import { FormEvent, useRef, useState } from "react";
import { useMutation } from "../../../apps/web/src/lib/react-query";
import type { CustomerBrief } from "../../crm/frontend/types";
import { getMovement, listMovementItems } from "./api/movements";

import { Alert } from "../../../apps/web/src/shared/ui/alert";
import { Button } from "../../../apps/web/src/shared/ui/button";
import { Card, CardContent } from "../../../apps/web/src/shared/ui/card";
import { ConfirmDialog } from "../../../apps/web/src/shared/ui/confirm-dialog";
import { DataTable } from "../../../apps/web/src/shared/ui/data-table";
import { CustomerSearchDialog } from "../../crm/frontend/components/CustomerSearchDialog";
import { getProduct } from "../../productos/frontend/api";
import { getRealWarehouses } from "./api/warehouses";
import { CylinderStateBadge, getCylinderStateLabel } from "./CylinderStateBadge";
import { LogisticsSection } from "./components/LogisticsSection";
import { CylinderFiltersCard } from "./cylinders/components/CylinderFiltersCard";
import type { CylinderEntryMode, LogisticsCylinder } from "./api";
import {
  type CylinderFormState,
  type CylinderCreateMetaState,
  type HydrotestFormState,
  type WarrantyFormState,
  type RetimbradoFormState,
  type ServiceFormState,
  type PrintLabelFormState,
  type ScanFormState,
  EMPTY_CYLINDER_FORM,
  EMPTY_HYDROTEST_FORM,
  EMPTY_WARRANTY_FORM,
  EMPTY_RETIMBRADO_FORM,
  EMPTY_SERVICE_FORM,
  EMPTY_PRINT_LABEL_FORM,
  EMPTY_SCAN_FORM,
  EMPTY_CYLINDER_CREATE_META,
} from "./cylinders/forms/cylinder-form-state";
import {
  buildCylinderFormState,
  buildCylinderPayload,
  buildCreateCylinderPayload,
} from "./cylinders/forms/cylinder-payload";
import { formatDate } from "./cylinders/utils/formatters";
import { CreateCylinderDialog } from "./cylinders/dialogs/create-cylinder-dialog";
import { EditCylinderDialog } from "./cylinders/dialogs/edit-cylinder-dialog";
import { CylinderViewSectionDialog } from "./cylinders/dialogs/cylinder-view-section-dialog";
import { DetailMenuDialog } from "./cylinders/dialogs/DetailMenuDialog";
import { HydrotestDialog } from "./cylinders/dialogs/HydrotestDialog";
import { WarrantyDialog } from "./cylinders/dialogs/WarrantyDialog";
import { RetimbradoDialog } from "./cylinders/dialogs/RetimbradoDialog";
import { ServiceDialog } from "./cylinders/dialogs/ServiceDialog";
import { PrintLabelDialog } from "./cylinders/dialogs/PrintLabelDialog";
import { TransitionDialog } from "./cylinders/dialogs/TransitionDialog";
import { ScanDialog } from "./cylinders/dialogs/ScanDialog";
import { useCylinderPermissions } from "./cylinders/hooks/use-cylinder-permissions";
import { useCylinderData } from "./cylinders/hooks/use-cylinder-data";
import { useCylinderMutations } from "./cylinders/hooks/use-cylinder-mutations";
import { ContractFormDialog } from "./contracts/dialogs/contract-form-dialog";
import { EMPTY_CONTRACT_FORM, type ContractFormState } from "./contracts/forms/contract-form-state";
import { buildCreatePayload } from "./contracts/forms/contract-payload";
import { createContract, uploadContractFile } from "./api/contracts";

export function LogisticsPage() {
  const permissions = useCylinderPermissions();
  const [search, setSearch] = useState("");
  const [stateFilter, setStateFilter] = useState("");
  const [medicalOnly, setMedicalOnly] = useState(false);
  const [selectedCylinder, setSelectedCylinder] = useState<LogisticsCylinder | null>(null);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isCreateContractOpen, setIsCreateContractOpen] = useState(false);
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [isHydrotestOpen, setIsHydrotestOpen] = useState(false);
  const [isWarrantyOpen, setIsWarrantyOpen] = useState(false);
  const [isCreateCustomerSearchOpen, setIsCreateCustomerSearchOpen] = useState(false);
  const [isWarrantyCustomerSearchOpen, setIsWarrantyCustomerSearchOpen] = useState(false);
  const [isRetimbradoOpen, setIsRetimbradoOpen] = useState(false);
  const [isServiceOpen, setIsServiceOpen] = useState(false);
  const [isTransitionOpen, setIsTransitionOpen] = useState(false);
  const [isPrintLabelOpen, setIsPrintLabelOpen] = useState(false);
  const [isScanOpen, setIsScanOpen] = useState(false);
  const [isDetailMenuOpen, setIsDetailMenuOpen] = useState(false);
  const [selectedViewSection, setSelectedViewSection] = useState<"trace" | "ph" | "retimbrados" | "custody" | "services" | "label" | null>(null);
  const [nextState, setNextState] = useState("");
  const [cylinderForm, setCylinderForm] = useState<CylinderFormState>(EMPTY_CYLINDER_FORM);
  const [createMeta, setCreateMeta] = useState<CylinderCreateMetaState>(EMPTY_CYLINDER_CREATE_META);
  const [hydrotestForm, setHydrotestForm] = useState<HydrotestFormState>(EMPTY_HYDROTEST_FORM);
  const [warrantyForm, setWarrantyForm] = useState<WarrantyFormState>(EMPTY_WARRANTY_FORM);
  const [retimbradoForm, setRetimbradoForm] = useState<RetimbradoFormState>(EMPTY_RETIMBRADO_FORM);
  const [serviceForm, setServiceForm] = useState<ServiceFormState>(EMPTY_SERVICE_FORM);
  const [printLabelForm, setPrintLabelForm] = useState<PrintLabelFormState>(EMPTY_PRINT_LABEL_FORM);
  const [scanForm, setScanForm] = useState<ScanFormState>(EMPTY_SCAN_FORM);
  const [contractForm, setContractForm] = useState<ContractFormState>(EMPTY_CONTRACT_FORM);
  const [selectedContractFile, setSelectedContractFile] = useState<File | null>(null);
  const [panelError, setPanelError] = useState<string | null>(null);
  const [detailError, setDetailError] = useState<string | null>(null);
  const [confirmDelete, setConfirmDelete] = useState<{ id: string; onConfirm: () => void } | null>(null);
  const [scanFallbackHint, setScanFallbackHint] = useState<string | null>(null);
  const [scanFallbackAvailable, setScanFallbackAvailable] = useState(false);

  const selectedCylinderId = selectedCylinder?.id ?? "";

  const data = useCylinderData({
    search,
    stateFilter,
    medicalOnly,
    selectedCylinderId,
    selectedCylinder,
    permissions,
  });

  const warehouseOptions = getRealWarehouses(data.warehousesQuery.data ?? []).map((warehouse) => ({
    value: warehouse.id,
    label: `${warehouse.code} · ${warehouse.name}`,
    keywords: [warehouse.code, warehouse.name, warehouse.address ?? ""],
  }));

  const createContractMutation = useMutation({
    mutationFn: async () => {
      const created = await createContract(buildCreatePayload(contractForm));
      if (selectedContractFile) {
        await uploadContractFile(created.id, selectedContractFile);
      }
      return created;
    },
    onSuccess: async () => {
      setIsCreateContractOpen(false);
      if (selectedCylinder) {
        setIsDetailMenuOpen(true);
      }
      setSelectedContractFile(null);
    },
    onError: (error: Error) => {
      setDetailError(error.message);
    },
  });

  const gasGroupIdRef = useRef(cylinderForm.gas_group_id);

  function resetCreateDialog() {
    setCylinderForm(EMPTY_CYLINDER_FORM);
    gasGroupIdRef.current = "";
    setCreateMeta(EMPTY_CYLINDER_CREATE_META);
    setPanelError(null);
    setScanFallbackHint(null);
    setScanFallbackAvailable(false);
    setIsCreateCustomerSearchOpen(false);
  }

  const mutations = useCylinderMutations({
    selectedCylinderId,
    setSelectedCylinder,
    setIsCreateOpen,
    setIsEditOpen,
    setIsHydrotestOpen,
    setIsWarrantyOpen,
    setIsRetimbradoOpen,
    setIsServiceOpen,
    setIsPrintLabelOpen,
    setIsScanOpen,
    setNextState,
    setHydrotestForm,
    setWarrantyForm,
    setRetimbradoForm,
    setServiceForm,
    setPrintLabelForm,
    setScanForm,
    setCylinderForm,
    setCreateMeta,
    gasGroupIdRef,
    resetCreateDialog,
    onCreateSuccess: () => {
      if (scanFallbackHint) {
        setScanFallbackHint(null);
        setScanFallbackAvailable(false);
        setIsScanOpen(true);
      }
    },
  });

  async function handleCreateCylinder(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPanelError(null);
    try {
      await mutations.createMutation.mutateAsync(buildCreateCylinderPayload(cylinderForm, createMeta));
    } catch (error) {
      setPanelError(error instanceof Error ? error.message : "No se pudo crear el envase.");
    }
  }

  async function handleUpdateCylinder(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedCylinder) {
      return;
    }
    setDetailError(null);
    try {
      const payload = buildCylinderPayload(cylinderForm);
      await mutations.updateMutation.mutateAsync({
        cylinderId: selectedCylinder.id,
        payload,
      });
    } catch (error) {
      setDetailError(error instanceof Error ? error.message : "No se pudo actualizar el envase.");
    }
  }

  async function handleTransition() {
    if (!selectedCylinder || !nextState) {
      return;
    }
    setDetailError(null);
    try {
      await mutations.transitionMutation.mutateAsync({ cylinderId: selectedCylinder.id, toState: nextState });
    } catch (error) {
      setDetailError(error instanceof Error ? error.message : "No se pudo aplicar la transición.");
    }
  }

  async function handleHydrotest(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setDetailError(null);
    try {
      await mutations.hydrotestMutation.mutateAsync(hydrotestForm);
    } catch (error) {
      setDetailError(error instanceof Error ? error.message : "No se pudo registrar la PH.");
    }
  }

  async function handleWarranty(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setDetailError(null);
    try {
      await mutations.warrantyMutation.mutateAsync(warrantyForm);
    } catch (error) {
      setDetailError(error instanceof Error ? error.message : "No se pudo registrar la garantía.");
    }
  }

  async function handleRetimbrado(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setDetailError(null);
    try {
      await mutations.retimbradoMutation.mutateAsync(retimbradoForm);
    } catch (error) {
      setDetailError(error instanceof Error ? error.message : "No se pudo registrar el retimbrado.");
    }
  }

  async function handleService(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setDetailError(null);
    try {
      await mutations.serviceMutation.mutateAsync(serviceForm);
    } catch (error) {
      setDetailError(error instanceof Error ? error.message : "No se pudo registrar el servicio.");
    }
  }

  async function handlePrintLabel(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setDetailError(null);
    try {
      await mutations.printLabelMutation.mutateAsync(printLabelForm);
    } catch (error) {
      setDetailError(error instanceof Error ? error.message : "No se pudo registrar la impresión.");
    }
  }

  async function handleScan(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setDetailError(null);
    try {
      await mutations.scanMutation.mutateAsync(scanForm);
    } catch (error) {
      const message = error instanceof Error ? error.message : "No se pudo procesar el escaneo.";
      setDetailError(message);
      const isUnknownCylinder =
        message.toLowerCase().includes("envase no encontrado") ||
        message.toLowerCase().includes("cylinder not found");
      setScanFallbackAvailable(isUnknownCylinder);
      if (!isUnknownCylinder) {
        return;
      }

      const normalizedSerial = scanForm.barcode_serial.trim().toUpperCase();
      let inferredProductId = "";
      let inferredCustomerId = "";
      let inferredCustomerName = "";
      let inferredWarehouseId = "";
      let inferredEntryMode: CylinderEntryMode = "FULL_FROM_SUPPLIER";

      if (scanForm.movement_id) {
        try {
          const [movement, items] = await Promise.all([
            getMovement(scanForm.movement_id),
            listMovementItems(scanForm.movement_id),
          ]);
          inferredWarehouseId = movement.warehouse_id ?? "";
          inferredCustomerId = movement.customer_id ?? "";
          inferredCustomerName = movement.customer_name ?? "";
          inferredEntryMode = movement.movement_type === "IC" ? "EMPTY_FROM_CUSTOMER" : "FULL_FROM_SUPPLIER";
          const movementProductIds = Array.from(new Set(items.map((item) => item.product_id).filter(Boolean)));
          inferredProductId = movementProductIds.length === 1 ? movementProductIds[0] ?? "" : "";
        } catch {
          // Keep the minimal fallback even if contextual inference fails.
        }
      }

      gasGroupIdRef.current = inferredProductId;
      setCylinderForm((current) => ({
        ...current,
        serial: normalizedSerial,
        barcode2: normalizedSerial,
        gas_group_id: inferredProductId,
      }));
      setCreateMeta((current) => ({
        ...current,
        entry_mode: inferredEntryMode,
        warehouse_id: inferredWarehouseId,
        customer_id: inferredCustomerId,
        customer_name: inferredCustomerName,
      }));
      setScanFallbackHint(
        inferredProductId
          ? "Envase no registrado. Completa el alta mínima y luego vuelve a procesar el escaneo."
          : "Envase no registrado. Completa serial y barcode; si el producto no pudo inferirse, termínalo luego desde Envases."
      );
    }
  }

  function openScanFallbackCreate() {
    if (!scanFallbackAvailable) {
      return;
    }
    setIsScanOpen(false);
    setIsCreateOpen(true);
  }

  function openDetail(cylinder: LogisticsCylinder) {
    setSelectedCylinder(cylinder);
    const raw = cylinder.product_id ?? cylinder.gas_group_id ?? "";
    const mapped = cylinder.product_id ?? data.productIdByGasId.get(raw) ?? (data.validGasIds.has(raw) ? raw : "");
    gasGroupIdRef.current = mapped;
    setCylinderForm({
      ...buildCylinderFormState(cylinder),
      gas_group_id: mapped,
    });
    setNextState("");
    setDetailError(null);
    setIsDetailMenuOpen(true);
    setScanForm({
      ...EMPTY_SCAN_FORM,
      barcode_serial: cylinder.barcode2 || cylinder.barcode1 || cylinder.serial,
    });
  }

  function openEditDialog() {
    const raw = selectedCylinder.product_id ?? selectedCylinder.gas_group_id ?? "";
    const mapped = selectedCylinder.product_id ?? data.productIdByGasId.get(raw) ?? (data.validGasIds.has(raw) ? raw : "");
    const form = {
      ...buildCylinderFormState(selectedCylinder),
      gas_group_id: mapped,
    };
    gasGroupIdRef.current = form.gas_group_id;
    setCylinderForm(form);
    setIsEditOpen(true);
  }

  function closeDetailContext() {
    setSelectedCylinder(null);
    setDetailError(null);
    setIsEditOpen(false);
    setIsDetailMenuOpen(false);
    setIsCreateContractOpen(false);
    setSelectedViewSection(null);
  }

  function openCreateContractDialog() {
    if (!selectedCylinder) {
      return;
    }
    const today = new Date().toISOString().slice(0, 10);
    setContractForm({
      ...EMPTY_CONTRACT_FORM,
      warehouse_id: "",
      start_date: today,
      cylinder_type_id: selectedCylinder.product_id ?? selectedCylinder.gas_group_id ?? "",
      cylinder_condition: selectedCylinder.condition ?? "",
      quantity: "1",
    });
    setSelectedContractFile(null);
    setDetailError(null);
    setIsDetailMenuOpen(false);
    setIsCreateContractOpen(true);
  }

  function closeCreateContractDialog(open: boolean) {
    setIsCreateContractOpen(open);
    if (!open) {
      setSelectedContractFile(null);
      if (selectedCylinder) {
        setIsDetailMenuOpen(true);
      }
    }
  }

  function openViewSection(section: NonNullable<typeof selectedViewSection>) {
    setIsDetailMenuOpen(false);
    setSelectedViewSection(section);
  }

  function closeViewSection() {
    setSelectedViewSection(null);
    if (selectedCylinder) {
      setIsDetailMenuOpen(true);
    }
  }

  function closeViewSectionAndGoBack() {
    setSelectedViewSection(null);
    setIsDetailMenuOpen(true);
  }

  function handleCylinderFormChange(next: CylinderFormState) {
    const prevGasId = gasGroupIdRef.current;
    setCylinderForm(next);
    if (next.gas_group_id && next.gas_group_id !== prevGasId) {
      gasGroupIdRef.current = next.gas_group_id;
      getProduct(next.gas_group_id).then((product) => {
        setCylinderForm((current) => ({
          ...current,
          brand_id: data.lgBrandIdByProdBrandId.get(product.brand_id ?? "") ?? current.brand_id,
          adr_subline: product.subline_name ?? current.adr_subline,
        }));
      }).catch(() => {});
    }
  }

  return (
    <>
      <CylinderViewSectionDialog
        open={selectedViewSection !== null}
        section={selectedViewSection}
        cylinderId={selectedCylinderId}
        onBack={closeViewSectionAndGoBack}
        hydrotestsData={data.hydrotestsQuery.data ?? []}
        warrantiesData={data.warrantiesQuery.data ?? []}
        retimbradosData={data.retimbradosQuery.data ?? []}
        ownershipData={data.ownershipQuery.data ?? []}
        labelHistoryData={data.labelHistoryQuery.data ?? []}
        servicesData={data.servicesQuery.data ?? []}
        scanData={data.filteredScans}
        labelData={data.labelDataQuery.data ?? null}
        serviceTypeById={data.serviceTypeById}
      />
      <ContractFormDialog
        open={isCreateContractOpen}
        onOpenChange={closeCreateContractDialog}
        title={selectedCylinder ? `Nuevo contrato para ${selectedCylinder.serial}` : "Nuevo contrato"}
        form={contractForm}
        onFormChange={setContractForm}
        isPending={createContractMutation.isPending}
        error={detailError}
        onSubmit={(event) => {
          event.preventDefault();
          setDetailError(null);
          createContractMutation.mutate();
        }}
        onFileSelect={setSelectedContractFile}
        showNotes={false}
      />
      <LogisticsSection
      title="Control de envases"
      description="Ficha completa del cilindro, trazabilidad, retimbrados, etiquetas, servicios y escaneo en campo."
      actions={permissions.canCreate ? <Button onClick={() => setIsCreateOpen(true)}>Nuevo envase</Button> : null}
    >
      {data.hasMainError ? (
        <Alert title="No se pudo cargar la vista principal">
          Revisa permisos o conectividad con el backend del plugin.
        </Alert>
      ) : null}

      <div className="overflow-x-auto">
        <div className="flex min-w-max gap-3">
          {[
            "CREADO_VACIO",
            "EN_ALMACEN_VACIO",
            "LLENADO_OK",
            "EN_RUTA",
            "EN_CLIENTE_LLENO",
            "OBSERVADO",
          ].map((state) => (
            <Card key={state} className="min-w-40">
              <CardContent className="space-y-2 p-4">
                <CylinderStateBadge state={state} />
                <p className="text-2xl font-semibold text-foreground">{data.summaryByState.get(state) ?? 0}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      <CylinderFiltersCard
        search={search}
        stateFilter={stateFilter}
        medicalOnly={medicalOnly}
        stateOptions={(data.statesQuery.data ?? []).map((state) => ({ value: state.code, label: getCylinderStateLabel(state.code) }))}
        onSearchChange={setSearch}
        onStateFilterChange={setStateFilter}
        onMedicalOnlyChange={setMedicalOnly}
        onReset={() => {
          setSearch("");
          setStateFilter("");
          setMedicalOnly(false);
        }}
      />

      <DataTable
        columns={[
          {
            key: "serial",
            header: "Envase",
            render: (row) => (
              <div className="space-y-1">
                <button
                  type="button"
                  onClick={() => openDetail(row)}
                  className="text-left font-medium text-cyan-300 hover:text-cyan-200"
                >
                  {row.serial}
                </button>
                <p className="text-xs text-muted-foreground">{row.description || "Sin descripción"}</p>
                <p className="text-xs text-muted-foreground">{row.barcode2 || row.barcode1 || "Sin barcode"}</p>
              </div>
            ),
          },
          {
            key: "gas",
            header: "Gas / marca",
            render: (row) => (
              <div className="space-y-1 text-sm text-foreground">
                <p>{data.productById.get(row.product_id ?? "") || data.gasById.get(row.gas_group_id ?? "") || "Sin gas"}</p>
                <p className="text-xs text-muted-foreground">{data.brandById.get(row.brand_id ?? "") || "Sin marca"}</p>
              </div>
            ),
          },
          {
            key: "state",
            header: "Estado",
            render: (row) => <CylinderStateBadge state={row.current_state} />,
          },
          {
            key: "ph",
            header: "PH / ADR",
            render: (row) => (
              <div className="space-y-1 text-xs text-muted-foreground">
                <p>PH: {formatDate(row.next_hydrotest_date)}</p>
                <p>ADR: {row.adr_un_number || "-"}</p>
                {row.is_medical ? <p className="font-medium text-amber-500">MEDICINAL</p> : null}
              </div>
            ),
          },
          {
            key: "location",
            header: "Ubicación",
            render: (row) => <span className="text-sm text-foreground">{row.location || "-"}</span>,
          },
          {
            key: "actions",
            header: "Acciones",
            render: (row) => (
              <div className="flex gap-2">
                <Button variant="secondary" onClick={() => openDetail(row)}>
                  Ver ficha
                </Button>
              </div>
            ),
          },
        ]}
        rows={data.cylindersQuery.data ?? []}
        rowKey={(row) => row.id}
        emptyMessage="Aún no hay envases registrados."
      />

      <CreateCylinderDialog
        open={isCreateOpen}
        onOpenChange={(open) => {
          setIsCreateOpen(open);
          if (!open) {
            resetCreateDialog();
          }
        }}
        cylinderForm={cylinderForm}
        onCylinderFormChange={handleCylinderFormChange}
        createMeta={createMeta}
        onCreateMetaChange={setCreateMeta}
        gasOptions={data.gasOptions}
        brandOptions={data.brandOptions}
        warehouseOptions={warehouseOptions}
        sublineOptions={data.sublineOptions}
        conditions={data.conditionsQuery.data ?? []}
        isPending={mutations.createMutation.isPending}
        error={panelError}
        onSubmit={handleCreateCylinder}
        onCustomerSearchClick={() => setIsCreateCustomerSearchOpen(true)}
        compactMode={scanFallbackHint !== null}
        compactHint={scanFallbackHint}
      />

      <CustomerSearchDialog
        open={isCreateCustomerSearchOpen}
        onOpenChange={setIsCreateCustomerSearchOpen}
        onSelect={(customer: CustomerBrief) =>
          setCreateMeta((current) => ({
            ...current,
            customer_id: customer.id,
            customer_name: customer.display_name,
          }))
        }
      />

      <DetailMenuDialog
        selectedCylinder={selectedCylinder}
        isDetailMenuOpen={isDetailMenuOpen}
        detailError={detailError}
        productById={data.productById}
        gasById={data.gasById}
        brandById={data.brandById}
        canContractView={permissions.canContractView}
        canContractCreate={permissions.canContractCreate}
        canUpdate={permissions.canUpdate}
        canMaintenance={permissions.canMaintenance}
        canTransition={permissions.canTransition}
        canRetimbrado={permissions.canRetimbrado}
        canServiceManage={permissions.canServiceManage}
        canLabelPrint={permissions.canLabelPrint}
        canScan={permissions.canScan}
        openEditDialog={openEditDialog}
        setIsHydrotestOpen={setIsHydrotestOpen}
        setIsWarrantyOpen={setIsWarrantyOpen}
        setIsTransitionOpen={setIsTransitionOpen}
        setIsRetimbradoOpen={setIsRetimbradoOpen}
        setIsServiceOpen={setIsServiceOpen}
        setIsPrintLabelOpen={setIsPrintLabelOpen}
        setIsScanOpen={setIsScanOpen}
        openViewSection={openViewSection}
        openCreateContractDialog={openCreateContractDialog}
        closeDetailContext={closeDetailContext}
        formatDate={formatDate}
      />

      <EditCylinderDialog
        open={isEditOpen}
        onOpenChange={setIsEditOpen}
        cylinderForm={cylinderForm}
        onCylinderFormChange={handleCylinderFormChange}
        gasOptions={data.gasOptions}
        brandOptions={data.brandOptions}
        sublineOptions={data.sublineOptions}
        conditions={data.conditionsQuery.data ?? []}
        isPending={mutations.updateMutation.isPending}
        serial={selectedCylinder?.serial ?? ""}
        onSubmit={handleUpdateCylinder}
      />

      <HydrotestDialog
        isHydrotestOpen={isHydrotestOpen}
        setIsHydrotestOpen={setIsHydrotestOpen}
        hydrotestForm={hydrotestForm}
        setHydrotestForm={setHydrotestForm}
        handleHydrotest={handleHydrotest}
        hydrotestMutation={mutations.hydrotestMutation}
      />

      <WarrantyDialog
        isWarrantyOpen={isWarrantyOpen}
        setIsWarrantyOpen={setIsWarrantyOpen}
        warrantyForm={warrantyForm}
        setWarrantyForm={setWarrantyForm}
        handleWarranty={handleWarranty}
        warrantyMutation={mutations.warrantyMutation}
        setIsWarrantyCustomerSearchOpen={setIsWarrantyCustomerSearchOpen}
      />

      <CustomerSearchDialog
        open={isWarrantyCustomerSearchOpen}
        onOpenChange={setIsWarrantyCustomerSearchOpen}
        onSelect={(customer: CustomerBrief) =>
          setWarrantyForm((current) => ({ ...current, customer_id: customer.id, customer_name: customer.display_name }))
        }
      />

      <RetimbradoDialog
        isRetimbradoOpen={isRetimbradoOpen}
        setIsRetimbradoOpen={setIsRetimbradoOpen}
        retimbradoForm={retimbradoForm}
        setRetimbradoForm={setRetimbradoForm}
        handleRetimbrado={handleRetimbrado}
        retimbradoMutation={mutations.retimbradoMutation}
      />

      <ServiceDialog
        isServiceOpen={isServiceOpen}
        setIsServiceOpen={setIsServiceOpen}
        serviceForm={serviceForm}
        setServiceForm={setServiceForm}
        handleService={handleService}
        serviceMutation={mutations.serviceMutation}
        serviceTypesQuery={data.serviceTypesQuery}
      />

      <PrintLabelDialog
        isPrintLabelOpen={isPrintLabelOpen}
        setIsPrintLabelOpen={setIsPrintLabelOpen}
        printLabelForm={printLabelForm}
        setPrintLabelForm={setPrintLabelForm}
        handlePrintLabel={handlePrintLabel}
        printLabelMutation={mutations.printLabelMutation}
      />

      <TransitionDialog
        isTransitionOpen={isTransitionOpen}
        setIsTransitionOpen={setIsTransitionOpen}
        nextState={nextState}
        setNextState={setNextState}
        handleTransition={handleTransition}
        transitionMutation={mutations.transitionMutation}
        transitionsQuery={data.transitionsQuery}
        getCylinderStateLabel={getCylinderStateLabel}
      />

      <ScanDialog
        isScanOpen={isScanOpen}
        setIsScanOpen={setIsScanOpen}
        scanForm={scanForm}
        setScanForm={setScanForm}
        handleScan={handleScan}
        scanMutation={mutations.scanMutation}
        fallbackMessage={scanFallbackAvailable ? scanFallbackHint : null}
        onOpenRegisterFallback={scanFallbackAvailable ? openScanFallbackCreate : undefined}
      />

      <ConfirmDialog
        open={confirmDelete !== null}
        onClose={() => setConfirmDelete(null)}
        onConfirm={() => {
          confirmDelete?.onConfirm();
          setConfirmDelete(null);
        }}
        title="Confirmar eliminación"
        description="¿Estás seguro de eliminar este servicio?"
        destructive
        confirmLabel="Eliminar"
      />
    </LogisticsSection>
    </>
  );
}
