import { FormEvent, useEffect, useRef, useState } from "react";
import { useMutation } from "../../../apps/web/src/lib/react-query";
import { getMovement, listMovementItems } from "./api/movements";

import { Alert } from "../../../apps/web/src/shared/ui/alert";
import { Button } from "../../../apps/web/src/shared/ui/button";
import { getProduct } from "../../productos/frontend/api";
import { getRealWarehouses } from "./api/warehouses";
import { getCylinderStateLabel } from "./CylinderStateBadge";
import { LogisticsSection } from "./components/LogisticsSection";
import { CylinderDialogsHost } from "./cylinders/components/CylinderDialogsHost";
import { CylinderFiltersCard } from "./cylinders/components/CylinderFiltersCard";
import { CylinderSummaryCards } from "./cylinders/components/CylinderSummaryCards";
import { CylinderTableSection } from "./cylinders/components/CylinderTableSection";
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
import {
  type CylinderFillingFormState,
  type CylinderFillingMode,
  EMPTY_CYLINDER_FILLING_FORM,
  buildCylinderFillingFormState,
} from "./cylinders/forms/cylinder-filling";
import { formatDate, formatDateTime } from "./cylinders/utils/formatters";
import { useCylinderPermissions } from "./cylinders/hooks/use-cylinder-permissions";
import { useCylinderData } from "./cylinders/hooks/use-cylinder-data";
import { useCylinderMutations } from "./cylinders/hooks/use-cylinder-mutations";

export function LogisticsPage() {
  const permissions = useCylinderPermissions();
  const [search, setSearch] = useState("");
  const [stateFilter, setStateFilter] = useState("");
  const [medicalOnly, setMedicalOnly] = useState(false);
  const [page, setPage] = useState(1);
  const [selectedCylinder, setSelectedCylinder] = useState<LogisticsCylinder | null>(null);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [isHydrotestOpen, setIsHydrotestOpen] = useState(false);
  const [isWarrantyOpen, setIsWarrantyOpen] = useState(false);
  const [isWarrantyCustomerSearchOpen, setIsWarrantyCustomerSearchOpen] = useState(false);
  const [isRetimbradoOpen, setIsRetimbradoOpen] = useState(false);
  const [isServiceOpen, setIsServiceOpen] = useState(false);
  const [isTransitionOpen, setIsTransitionOpen] = useState(false);
  const [isPrintLabelOpen, setIsPrintLabelOpen] = useState(false);
  const [isScanOpen, setIsScanOpen] = useState(false);
  const [isFillingOpen, setIsFillingOpen] = useState(false);
  const [isCryogenicFillingOpen, setIsCryogenicFillingOpen] = useState(false);
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
  const [fillingMode, setFillingMode] = useState<CylinderFillingMode>("fill");
  const [fillingForm, setFillingForm] = useState<CylinderFillingFormState>(
    EMPTY_CYLINDER_FILLING_FORM,
  );
  const [panelError, setPanelError] = useState<string | null>(null);
  const [detailError, setDetailError] = useState<string | null>(null);
  const [confirmDelete, setConfirmDelete] = useState<{ id: string; onConfirm: () => void } | null>(null);
  const [scanFallbackHint, setScanFallbackHint] = useState<string | null>(null);
  const [scanFallbackAvailable, setScanFallbackAvailable] = useState(false);

  const selectedCylinderId = selectedCylinder?.id ?? "";

  useEffect(() => {
    setPage(1);
  }, [search, stateFilter, medicalOnly]);

  const data = useCylinderData({
    search,
    stateFilter,
    medicalOnly,
    page,
    perPage: 10,
    selectedCylinderId,
    selectedCylinder,
    permissions,
  });

  const warehouseOptions = getRealWarehouses(data.warehousesQuery.data ?? []).map((warehouse) => ({
    value: warehouse.id,
    label: `${warehouse.code} · ${warehouse.name}`,
    keywords: [warehouse.code, warehouse.name, warehouse.address ?? ""],
  }));

  const gasGroupIdRef = useRef(cylinderForm.gas_group_id);

  function resetCreateDialog() {
    setCylinderForm(EMPTY_CYLINDER_FORM);
    gasGroupIdRef.current = "";
    setCreateMeta(EMPTY_CYLINDER_CREATE_META);
    setPanelError(null);
    setScanFallbackHint(null);
    setScanFallbackAvailable(false);
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
    setIsFillingOpen,
    setNextState,
    setHydrotestForm,
    setWarrantyForm,
    setRetimbradoForm,
    setServiceForm,
    setPrintLabelForm,
    setScanForm,
    setFillingForm,
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

  async function handleCreateCylinder(serials: string[]) {
    setPanelError(null);
    let lastError: string | null = null;
    for (const serial of serials) {
      try {
        const formWithSerial = { ...cylinderForm, serial };
        await mutations.createMutation.mutateAsync(buildCreateCylinderPayload(formWithSerial, createMeta));
      } catch (error) {
        lastError = error instanceof Error ? error.message : `Error al crear ${serial}`;
      }
    }
    if (serials.length > 1 && !lastError) {
      onCylinderFormChange({ ...cylinderForm, serial: "" });
      setTimeout(() => {
        const input = document.querySelector<HTMLInputElement>('input[placeholder="Nro. de serie del cilindro"]');
        input?.focus();
      }, 0);
    } else if (lastError) {
      setPanelError(lastError);
    } else {
      setIsCreateOpen(false);
      resetCreateDialog();
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

  async function handleCylinderFilling(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setDetailError(null);
    try {
      if (fillingMode === "fill") {
        await mutations.fillMutation.mutateAsync(fillingForm);
      } else {
        await mutations.vacateMutation.mutateAsync(fillingForm);
      }
    } catch (error) {
      setDetailError(
        error instanceof Error
          ? error.message
          : fillingMode === "fill"
            ? "No se pudo registrar el llenado."
            : "No se pudo registrar el vaciado.",
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

  function openFillingDialog(mode: CylinderFillingMode) {
    setFillingMode(mode);
    setFillingForm(buildCylinderFillingFormState(selectedCylinder, mode));
    setDetailError(null);
    setIsFillingOpen(true);
  }

  function closeDetailContext() {
    setSelectedCylinder(null);
    setDetailError(null);
    setIsEditOpen(false);
    setIsDetailMenuOpen(false);
    setSelectedViewSection(null);
    setIsFillingOpen(false);
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
      <LogisticsSection
        title="Control de envases"
        description="Ficha completa del cilindro, trazabilidad, retimbrados, etiquetas, servicios y escaneo en campo."
        actions={
          <div className="flex items-center gap-3">
            {permissions.canUpdate ? (
              <Button onClick={() => setIsCryogenicFillingOpen(true)}>Llenado</Button>
            ) : null}
            {permissions.canCreate ? (
              <Button variant="secondary" onClick={() => setIsCreateOpen(true)}>
                Nuevo envase
              </Button>
            ) : null}
          </div>
        }
      >
      {data.hasMainError ? (
        <Alert title="No se pudo cargar la vista principal">
          Revisa permisos o conectividad con el backend del plugin.
        </Alert>
      ) : null}

      <CylinderSummaryCards summaryByState={data.summaryByState} />

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

      <CylinderTableSection
        rows={data.cylindersQuery.data?.items ?? []}
        total={data.cylindersQuery.data?.pagination.total}
        page={data.cylindersQuery.data?.pagination.page ?? page}
        totalPages={data.cylindersQuery.data?.pagination.total_pages ?? 1}
        productById={data.productById}
        gasById={data.gasById}
        brandById={data.brandById}
        onOpenDetail={openDetail}
        onPageChange={setPage}
        formatDate={formatDate}
      />

      <CylinderDialogsHost
        selectedViewSection={selectedViewSection}
        selectedCylinderId={selectedCylinderId}
        closeViewSectionAndGoBack={closeViewSectionAndGoBack}
        data={data}
        permissions={permissions}
        selectedCylinder={selectedCylinder}
        detailError={detailError}
        panelError={panelError}
        warehouseOptions={warehouseOptions}
        resetCreateDialog={resetCreateDialog}
        isCreateOpen={isCreateOpen}
        setIsCreateOpen={setIsCreateOpen}
        cylinderForm={cylinderForm}
        handleCylinderFormChange={handleCylinderFormChange}
        createMeta={createMeta}
        setCreateMeta={setCreateMeta}
        handleCreateCylinder={handleCreateCylinder}
        scanFallbackHint={scanFallbackHint}
        isCryogenicFillingOpen={isCryogenicFillingOpen}
        setIsCryogenicFillingOpen={setIsCryogenicFillingOpen}
        isFillingOpen={isFillingOpen}
        fillingMode={fillingMode}
        fillingForm={fillingForm}
        setIsFillingOpen={setIsFillingOpen}
        setFillingForm={setFillingForm}
        handleCylinderFilling={handleCylinderFilling}
        isDetailMenuOpen={isDetailMenuOpen}
        openEditDialog={openEditDialog}
        openFillingDialog={openFillingDialog}
        setIsHydrotestOpen={setIsHydrotestOpen}
        setIsWarrantyOpen={setIsWarrantyOpen}
        setIsTransitionOpen={setIsTransitionOpen}
        setIsRetimbradoOpen={setIsRetimbradoOpen}
        setIsServiceOpen={setIsServiceOpen}
        setIsPrintLabelOpen={setIsPrintLabelOpen}
        setIsScanOpen={setIsScanOpen}
        openViewSection={openViewSection}
        closeDetailContext={closeDetailContext}
        formatDate={formatDate}
        formatDateTime={formatDateTime}
        isEditOpen={isEditOpen}
        setIsEditOpen={setIsEditOpen}
        handleUpdateCylinder={handleUpdateCylinder}
        isHydrotestOpen={isHydrotestOpen}
        hydrotestForm={hydrotestForm}
        setHydrotestForm={setHydrotestForm}
        handleHydrotest={handleHydrotest}
        isWarrantyOpen={isWarrantyOpen}
        warrantyForm={warrantyForm}
        setWarrantyForm={setWarrantyForm}
        handleWarranty={handleWarranty}
        isWarrantyCustomerSearchOpen={isWarrantyCustomerSearchOpen}
        setIsWarrantyCustomerSearchOpen={setIsWarrantyCustomerSearchOpen}
        isRetimbradoOpen={isRetimbradoOpen}
        retimbradoForm={retimbradoForm}
        setRetimbradoForm={setRetimbradoForm}
        handleRetimbrado={handleRetimbrado}
        isServiceOpen={isServiceOpen}
        serviceForm={serviceForm}
        setServiceForm={setServiceForm}
        handleService={handleService}
        isPrintLabelOpen={isPrintLabelOpen}
        printLabelForm={printLabelForm}
        setPrintLabelForm={setPrintLabelForm}
        handlePrintLabel={handlePrintLabel}
        isTransitionOpen={isTransitionOpen}
        nextState={nextState}
        setNextState={setNextState}
        handleTransition={handleTransition}
        getCylinderStateLabel={getCylinderStateLabel}
        isScanOpen={isScanOpen}
        scanForm={scanForm}
        setScanForm={setScanForm}
        handleScan={handleScan}
        scanFallbackAvailable={scanFallbackAvailable}
        openScanFallbackCreate={openScanFallbackCreate}
        confirmDelete={confirmDelete}
        setConfirmDelete={setConfirmDelete}
        mutations={mutations}
      />

      </LogisticsSection>
    </>
  );
}
