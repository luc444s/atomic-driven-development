import type { LogisticsCylinder } from "../../api";
import { CylinderViewSectionDialog } from "../dialogs/cylinder-view-section-dialog";
import { CylinderDetailDialogs } from "./CylinderDetailDialogs";
import { CylinderEntryDialogs } from "./CylinderEntryDialogs";
import { CylinderMaintenanceDialogs } from "./CylinderMaintenanceDialogs";
import type {
  CylinderCreateMetaState,
  CylinderFormState,
  HydrotestFormState,
  PrintLabelFormState,
  RetimbradoFormState,
  ScanFormState,
  ServiceFormState,
  WarrantyFormState,
} from "../forms/cylinder-form-state";
import type {
  CylinderFillingFormState,
  CylinderFillingMode,
} from "../forms/cylinder-filling";
import type { useCylinderData } from "../hooks/use-cylinder-data";
import type { useCylinderMutations } from "../hooks/use-cylinder-mutations";
import type { useCylinderPermissions } from "../hooks/use-cylinder-permissions";

type SelectedViewSection =
  | "trace"
  | "ph"
  | "retimbrados"
  | "custody"
  | "services"
  | "label"
  | null;

type CylinderDataState = ReturnType<typeof useCylinderData>;
type CylinderMutationsState = ReturnType<typeof useCylinderMutations>;
type CylinderPermissionsState = ReturnType<typeof useCylinderPermissions>;

interface CylinderDialogsHostProps {
  selectedViewSection: SelectedViewSection;
  selectedCylinderId: string;
  closeViewSectionAndGoBack: () => void;
  data: CylinderDataState;
  permissions: CylinderPermissionsState;
  selectedCylinder: LogisticsCylinder | null;
  detailError: string | null;
  panelError: string | null;
  warehouseOptions: Array<{ value: string; label: string; keywords: string[] }>;
  resetCreateDialog: () => void;
  isCreateOpen: boolean;
  setIsCreateOpen: (open: boolean) => void;
  cylinderForm: CylinderFormState;
  handleCylinderFormChange: (next: CylinderFormState) => void;
  createMeta: CylinderCreateMetaState;
  setCreateMeta: (next: CylinderCreateMetaState) => void;
  handleCreateCylinder: (serials: string[]) => void;
  scanFallbackHint: string | null;
  isCryogenicFillingOpen: boolean;
  setIsCryogenicFillingOpen: (open: boolean) => void;
  isFillingOpen: boolean;
  fillingMode: CylinderFillingMode;
  fillingForm: CylinderFillingFormState;
  setIsFillingOpen: (open: boolean) => void;
  setFillingForm: (next: CylinderFillingFormState) => void;
  handleCylinderFilling: (event: React.FormEvent<HTMLFormElement>) => void;
  isDetailMenuOpen: boolean;
  openEditDialog: () => void;
  openFillingDialog: (mode: CylinderFillingMode) => void;
  setIsHydrotestOpen: (open: boolean) => void;
  setIsWarrantyOpen: (open: boolean) => void;
  setIsTransitionOpen: (open: boolean) => void;
  setIsRetimbradoOpen: (open: boolean) => void;
  setIsServiceOpen: (open: boolean) => void;
  setIsPrintLabelOpen: (open: boolean) => void;
  setIsScanOpen: (open: boolean) => void;
  openViewSection: (section: NonNullable<SelectedViewSection>) => void;
  closeDetailContext: () => void;
  formatDate: (value: string | null | undefined) => string;
  formatDateTime: (value: string | null | undefined) => string;
  isEditOpen: boolean;
  setIsEditOpen: (open: boolean) => void;
  handleUpdateCylinder: (event: React.FormEvent<HTMLFormElement>) => void;
  isHydrotestOpen: boolean;
  hydrotestForm: HydrotestFormState;
  setHydrotestForm: (next: HydrotestFormState) => void;
  handleHydrotest: (event: React.FormEvent<HTMLFormElement>) => void;
  isWarrantyOpen: boolean;
  warrantyForm: WarrantyFormState;
  setWarrantyForm: (next: WarrantyFormState | ((prev: WarrantyFormState) => WarrantyFormState)) => void;
  handleWarranty: (event: React.FormEvent<HTMLFormElement>) => void;
  isWarrantyCustomerSearchOpen: boolean;
  setIsWarrantyCustomerSearchOpen: (open: boolean) => void;
  isRetimbradoOpen: boolean;
  retimbradoForm: RetimbradoFormState;
  setRetimbradoForm: (next: RetimbradoFormState) => void;
  handleRetimbrado: (event: React.FormEvent<HTMLFormElement>) => void;
  isServiceOpen: boolean;
  serviceForm: ServiceFormState;
  setServiceForm: (next: ServiceFormState) => void;
  handleService: (event: React.FormEvent<HTMLFormElement>) => void;
  isPrintLabelOpen: boolean;
  printLabelForm: PrintLabelFormState;
  setPrintLabelForm: (next: PrintLabelFormState) => void;
  handlePrintLabel: (event: React.FormEvent<HTMLFormElement>) => void;
  isTransitionOpen: boolean;
  nextState: string;
  setNextState: (next: string) => void;
  handleTransition: () => void;
  getCylinderStateLabel: (state: string) => string;
  isScanOpen: boolean;
  scanForm: ScanFormState;
  setScanForm: (next: ScanFormState) => void;
  handleScan: (event: React.FormEvent<HTMLFormElement>) => void;
  scanFallbackAvailable: boolean;
  openScanFallbackCreate: () => void;
  confirmDelete: { id: string; onConfirm: () => void } | null;
  setConfirmDelete: (value: { id: string; onConfirm: () => void } | null) => void;
  mutations: CylinderMutationsState;
}

export function CylinderDialogsHost({
  selectedViewSection,
  selectedCylinderId,
  closeViewSectionAndGoBack,
  data,
  permissions,
  selectedCylinder,
  detailError,
  panelError,
  warehouseOptions,
  resetCreateDialog,
  isCreateOpen,
  setIsCreateOpen,
  cylinderForm,
  handleCylinderFormChange,
  createMeta,
  setCreateMeta,
  handleCreateCylinder,
  scanFallbackHint,
  isCryogenicFillingOpen,
  setIsCryogenicFillingOpen,
  isFillingOpen,
  fillingMode,
  fillingForm,
  setIsFillingOpen,
  setFillingForm,
  handleCylinderFilling,
  isDetailMenuOpen,
  openEditDialog,
  openFillingDialog,
  setIsHydrotestOpen,
  setIsWarrantyOpen,
  setIsTransitionOpen,
  setIsRetimbradoOpen,
  setIsServiceOpen,
  setIsPrintLabelOpen,
  setIsScanOpen,
  openViewSection,
  closeDetailContext,
  formatDate,
  formatDateTime,
  isEditOpen,
  setIsEditOpen,
  handleUpdateCylinder,
  isHydrotestOpen,
  hydrotestForm,
  setHydrotestForm,
  handleHydrotest,
  isWarrantyOpen,
  warrantyForm,
  setWarrantyForm,
  handleWarranty,
  isWarrantyCustomerSearchOpen,
  setIsWarrantyCustomerSearchOpen,
  isRetimbradoOpen,
  retimbradoForm,
  setRetimbradoForm,
  handleRetimbrado,
  isServiceOpen,
  serviceForm,
  setServiceForm,
  handleService,
  isPrintLabelOpen,
  printLabelForm,
  setPrintLabelForm,
  handlePrintLabel,
  isTransitionOpen,
  nextState,
  setNextState,
  handleTransition,
  getCylinderStateLabel,
  isScanOpen,
  scanForm,
  setScanForm,
  handleScan,
  scanFallbackAvailable,
  openScanFallbackCreate,
  confirmDelete,
  setConfirmDelete,
  mutations,
}: CylinderDialogsHostProps) {
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

      <CylinderEntryDialogs
        data={data}
        permissions={permissions}
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
        panelError={panelError}
        isCryogenicFillingOpen={isCryogenicFillingOpen}
        setIsCryogenicFillingOpen={setIsCryogenicFillingOpen}
        mutations={mutations}
      />

      <CylinderDetailDialogs
        selectedViewSection={selectedViewSection}
        selectedCylinderId={selectedCylinderId}
        closeViewSectionAndGoBack={closeViewSectionAndGoBack}
        data={data}
        permissions={permissions}
        selectedCylinder={selectedCylinder}
        detailError={detailError}
        warehouseOptions={warehouseOptions}
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
        cylinderForm={cylinderForm}
        handleCylinderFormChange={handleCylinderFormChange}
        handleUpdateCylinder={handleUpdateCylinder}
        isTransitionOpen={isTransitionOpen}
        nextState={nextState}
        setNextState={setNextState}
        handleTransition={handleTransition}
        getCylinderStateLabel={getCylinderStateLabel}
        mutations={mutations}
      />

      <CylinderMaintenanceDialogs
        data={data}
        isHydrotestOpen={isHydrotestOpen}
        setIsHydrotestOpen={setIsHydrotestOpen}
        hydrotestForm={hydrotestForm}
        setHydrotestForm={setHydrotestForm}
        handleHydrotest={handleHydrotest}
        isWarrantyOpen={isWarrantyOpen}
        setIsWarrantyOpen={setIsWarrantyOpen}
        warrantyForm={warrantyForm}
        setWarrantyForm={setWarrantyForm}
        handleWarranty={handleWarranty}
        isWarrantyCustomerSearchOpen={isWarrantyCustomerSearchOpen}
        setIsWarrantyCustomerSearchOpen={setIsWarrantyCustomerSearchOpen}
        isRetimbradoOpen={isRetimbradoOpen}
        setIsRetimbradoOpen={setIsRetimbradoOpen}
        retimbradoForm={retimbradoForm}
        setRetimbradoForm={setRetimbradoForm}
        handleRetimbrado={handleRetimbrado}
        isServiceOpen={isServiceOpen}
        setIsServiceOpen={setIsServiceOpen}
        serviceForm={serviceForm}
        setServiceForm={setServiceForm}
        handleService={handleService}
        isPrintLabelOpen={isPrintLabelOpen}
        setIsPrintLabelOpen={setIsPrintLabelOpen}
        printLabelForm={printLabelForm}
        setPrintLabelForm={setPrintLabelForm}
        handlePrintLabel={handlePrintLabel}
        isScanOpen={isScanOpen}
        setIsScanOpen={setIsScanOpen}
        scanForm={scanForm}
        setScanForm={setScanForm}
        handleScan={handleScan}
        scanFallbackAvailable={scanFallbackAvailable}
        scanFallbackHint={scanFallbackHint}
        openScanFallbackCreate={openScanFallbackCreate}
        confirmDelete={confirmDelete}
        setConfirmDelete={setConfirmDelete}
        mutations={mutations}
      />
    </>
  );
}
