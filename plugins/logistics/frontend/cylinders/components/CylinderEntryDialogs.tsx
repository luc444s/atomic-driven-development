import { CryogenicFillingDialog } from "../../cryogenic-filling/CryogenicFillingDialog";
import { CreateCylinderDialog } from "../dialogs/create-cylinder-dialog";
import type {
  CylinderCreateMetaState,
  CylinderFormState,
} from "../forms/cylinder-form-state";
import type { useCylinderData } from "../hooks/use-cylinder-data";
import type { useCylinderMutations } from "../hooks/use-cylinder-mutations";
import type { useCylinderPermissions } from "../hooks/use-cylinder-permissions";

type CylinderDataState = ReturnType<typeof useCylinderData>;
type CylinderMutationsState = ReturnType<typeof useCylinderMutations>;
type CylinderPermissionsState = ReturnType<typeof useCylinderPermissions>;

interface CylinderEntryDialogsProps {
  data: CylinderDataState;
  permissions: CylinderPermissionsState;
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
  panelError: string | null;
  isCryogenicFillingOpen: boolean;
  setIsCryogenicFillingOpen: (open: boolean) => void;
  mutations: CylinderMutationsState;
}

export function CylinderEntryDialogs({
  data,
  permissions,
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
  panelError,
  isCryogenicFillingOpen,
  setIsCryogenicFillingOpen,
  mutations,
}: CylinderEntryDialogsProps) {
  return (
    <>
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
        warehouseOptions={warehouseOptions}
        isPending={mutations.createMutation.isPending}
        error={panelError}
        onSubmit={handleCreateCylinder}
        compactMode={scanFallbackHint !== null}
        compactHint={scanFallbackHint}
      />

      <CryogenicFillingDialog
        open={isCryogenicFillingOpen}
        canFill={permissions.canUpdate}
        products={data.gasCatalogQuery.data ?? []}
        onOpenChange={setIsCryogenicFillingOpen}
      />
    </>
  );
}
