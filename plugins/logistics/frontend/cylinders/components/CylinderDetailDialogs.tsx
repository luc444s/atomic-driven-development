import type { LogisticsCylinder } from "../../api";
import { DetailMenuDialog } from "../dialogs/DetailMenuDialog";
import { EditCylinderDialog } from "../dialogs/edit-cylinder-dialog";
import { CylinderFillingDialog } from "../dialogs/CylinderFillingDialog";
import { CylinderViewSectionDialog } from "../dialogs/cylinder-view-section-dialog";
import { TransitionDialog } from "../dialogs/TransitionDialog";
import type { CylinderFormState } from "../forms/cylinder-form-state";
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

interface CylinderDetailDialogsProps {
  selectedViewSection: SelectedViewSection;
  selectedCylinderId: string;
  closeViewSectionAndGoBack: () => void;
  data: CylinderDataState;
  permissions: CylinderPermissionsState;
  selectedCylinder: LogisticsCylinder | null;
  detailError: string | null;
  warehouseOptions: Array<{ value: string; label: string; keywords: string[] }>;
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
  cylinderForm: CylinderFormState;
  handleCylinderFormChange: (next: CylinderFormState) => void;
  handleUpdateCylinder: (event: React.FormEvent<HTMLFormElement>) => void;
  isTransitionOpen: boolean;
  nextState: string;
  setNextState: (next: string) => void;
  handleTransition: () => void;
  getCylinderStateLabel: (state: string) => string;
  mutations: CylinderMutationsState;
}

export function CylinderDetailDialogs({
  selectedViewSection,
  selectedCylinderId,
  closeViewSectionAndGoBack,
  data,
  permissions,
  selectedCylinder,
  detailError,
  warehouseOptions,
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
  cylinderForm,
  handleCylinderFormChange,
  handleUpdateCylinder,
  isTransitionOpen,
  nextState,
  setNextState,
  handleTransition,
  getCylinderStateLabel,
  mutations,
}: CylinderDetailDialogsProps) {
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

      <CylinderFillingDialog
        open={isFillingOpen}
        mode={fillingMode}
        cylinder={selectedCylinder}
        form={fillingForm}
        warehouseOptions={warehouseOptions}
        error={detailError}
        isPending={
          fillingMode === "fill"
            ? mutations.fillMutation.isPending
            : mutations.vacateMutation.isPending
        }
        onOpenChange={setIsFillingOpen}
        onFormChange={setFillingForm}
        onSubmit={handleCylinderFilling}
      />

      <DetailMenuDialog
        selectedCylinder={selectedCylinder}
        isDetailMenuOpen={isDetailMenuOpen}
        detailError={detailError}
        productById={data.productById}
        gasById={data.gasById}
        brandById={data.brandById}
        canUpdate={permissions.canUpdate}
        canMaintenance={permissions.canMaintenance}
        canTransition={permissions.canTransition}
        canRetimbrado={permissions.canRetimbrado}
        canServiceManage={permissions.canServiceManage}
        canLabelPrint={permissions.canLabelPrint}
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
      />

      <EditCylinderDialog
        open={isEditOpen}
        onOpenChange={setIsEditOpen}
        cylinderForm={cylinderForm}
        onCylinderFormChange={handleCylinderFormChange}
        gasOptions={data.gasOptions}
        isPending={mutations.updateMutation.isPending}
        serial={selectedCylinder?.serial ?? ""}
        onSubmit={handleUpdateCylinder}
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
    </>
  );
}
