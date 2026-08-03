import { useCoreMutation } from "../../../../../apps/web/src/lib/use-core-mutation";
import { toast } from "../../../../../apps/web/src/shared/ui/toast";
import {
  createCylinder,
  fillCylinder,
  updateCylinder,
  transitionCylinder,
  vacateCylinder,
  createHydrotestFromForm,
  createWarrantyFromForm,
  createRetimbradoFromForm,
  createCylinderServiceFromForm,
  printLabelFromForm,
  processScanFromForm,
  updateCylinderService,
  deleteCylinderService,
  getCylinderQueryKeys,
  logisticsKeys,
} from "../../api";
import {
  type CylinderFormState,
  type CylinderCreateMetaState,
  type HydrotestFormState,
  type WarrantyFormState,
  type RetimbradoFormState,
  type ServiceFormState,
  type PrintLabelFormState,
  type ScanFormState,
  EMPTY_HYDROTEST_FORM,
  EMPTY_WARRANTY_FORM,
  EMPTY_RETIMBRADO_FORM,
  EMPTY_SERVICE_FORM,
  EMPTY_PRINT_LABEL_FORM,
  EMPTY_SCAN_FORM,
} from "../forms/cylinder-form-state";
import { buildCylinderPayload, buildCreateCylinderPayload } from "../forms/cylinder-payload";
import {
  type CylinderFillingFormState,
  EMPTY_CYLINDER_FILLING_FORM,
  buildFillCylinderPayload,
  buildVacateCylinderPayload,
} from "../forms/cylinder-filling";

export interface CylinderMutationActions {
  selectedCylinderId: string;
  setSelectedCylinder: (c: any) => void;
  setIsCreateOpen: (v: boolean) => void;
  setIsEditOpen: (v: boolean) => void;
  setIsHydrotestOpen: (v: boolean) => void;
  setIsWarrantyOpen: (v: boolean) => void;
  setIsRetimbradoOpen: (v: boolean) => void;
  setIsServiceOpen: (v: boolean) => void;
  setIsPrintLabelOpen: (v: boolean) => void;
  setIsScanOpen: (v: boolean) => void;
  setIsFillingOpen: (v: boolean) => void;
  setNextState: (v: string) => void;
  setHydrotestForm: (v: HydrotestFormState | ((prev: HydrotestFormState) => HydrotestFormState)) => void;
  setWarrantyForm: (v: WarrantyFormState | ((prev: WarrantyFormState) => WarrantyFormState)) => void;
  setRetimbradoForm: (v: RetimbradoFormState) => void;
  setServiceForm: (v: ServiceFormState) => void;
  setPrintLabelForm: (v: PrintLabelFormState) => void;
  setScanForm: (v: ScanFormState) => void;
  setFillingForm: (v: CylinderFillingFormState) => void;
  setCylinderForm: (v: CylinderFormState | ((prev: CylinderFormState) => CylinderFormState)) => void;
  setCreateMeta: (v: CylinderCreateMetaState | ((prev: CylinderCreateMetaState) => CylinderCreateMetaState)) => void;
  gasGroupIdRef: React.MutableRefObject<string>;
  resetCreateDialog: () => void;
  onCreateSuccess?: (cylinder: any) => void;
}

export function useCylinderMutations(actions: CylinderMutationActions) {
  const {
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
    resetCreateDialog,
    onCreateSuccess,
  } = actions;

  const createMutation = useCoreMutation(
    (payload: ReturnType<typeof buildCreateCylinderPayload>) => createCylinder(payload),
    {
      successMessage: "Envase creado",
      onSuccess: (cylinder: any) => {
        setSelectedCylinder(cylinder);
        setIsCreateOpen(false);
        resetCreateDialog();
        onCreateSuccess?.(cylinder);
      },
      invalidate: (cylinder: any) => getCylinderQueryKeys(cylinder.id),
    },
  );

  const updateMutation = useCoreMutation(
    ({ cylinderId, payload }: { cylinderId: string; payload: ReturnType<typeof buildCylinderPayload> }) =>
      updateCylinder(cylinderId, payload),
    {
      successMessage: "Envase actualizado",
      onSuccess: (cylinder: any) => {
        setSelectedCylinder(cylinder);
        setIsEditOpen(false);
      },
      invalidate: (cylinder: any) => getCylinderQueryKeys(cylinder.id),
    },
  );

  const transitionMutation = useCoreMutation(
    ({ cylinderId, toState }: { cylinderId: string; toState: string }) =>
      transitionCylinder(cylinderId, { to_state: toState }),
    {
      successMessage: "Transición aplicada",
      onSuccess: (cylinder: any) => {
        setSelectedCylinder(cylinder);
        setNextState("");
      },
      invalidate: (cylinder: any) => getCylinderQueryKeys(cylinder.id),
    },
  );

  const fillMutation = useCoreMutation(
    (form: CylinderFillingFormState) =>
      fillCylinder(selectedCylinderId, buildFillCylinderPayload(form)),
    {
      successMessage: "Llenado registrado",
      onSuccess: (cylinder: any) => {
        setSelectedCylinder(cylinder);
        setIsFillingOpen(false);
        setFillingForm(EMPTY_CYLINDER_FILLING_FORM);
      },
      invalidate: (cylinder: any) => getCylinderQueryKeys(cylinder.id),
    },
  );

  const vacateMutation = useCoreMutation(
    (form: CylinderFillingFormState) =>
      vacateCylinder(selectedCylinderId, buildVacateCylinderPayload(form)),
    {
      successMessage: "Vaciado registrado",
      onSuccess: (cylinder: any) => {
        setSelectedCylinder(cylinder);
        setIsFillingOpen(false);
        setFillingForm(EMPTY_CYLINDER_FILLING_FORM);
      },
      invalidate: (cylinder: any) => getCylinderQueryKeys(cylinder.id),
    },
  );

  const hydrotestMutation = useCoreMutation(
    (form: HydrotestFormState) => createHydrotestFromForm(selectedCylinderId, form),
    {
      successMessage: "Prueba hidráulica registrada",
      onSuccess: () => {
        setIsHydrotestOpen(false);
        setHydrotestForm(EMPTY_HYDROTEST_FORM);
      },
      invalidate: () => getCylinderQueryKeys(selectedCylinderId),
    },
  );

  const warrantyMutation = useCoreMutation(
    (form: WarrantyFormState) => createWarrantyFromForm(selectedCylinderId, form),
    {
      successMessage: "Garantía registrada",
      onSuccess: () => {
        setIsWarrantyOpen(false);
        setWarrantyForm(EMPTY_WARRANTY_FORM);
      },
      invalidate: () => getCylinderQueryKeys(selectedCylinderId),
    },
  );

  const retimbradoMutation = useCoreMutation(
    (form: RetimbradoFormState) => createRetimbradoFromForm(selectedCylinderId, form),
    {
      successMessage: "Retimbrado registrado",
      onSuccess: () => {
        setIsRetimbradoOpen(false);
        setRetimbradoForm(EMPTY_RETIMBRADO_FORM);
      },
      invalidate: () => getCylinderQueryKeys(selectedCylinderId),
    },
  );

  const serviceMutation = useCoreMutation(
    (form: ServiceFormState) => createCylinderServiceFromForm(selectedCylinderId, form),
    {
      successMessage: "Servicio registrado",
      onSuccess: () => {
        setIsServiceOpen(false);
        setServiceForm(EMPTY_SERVICE_FORM);
      },
      invalidate: () => getCylinderQueryKeys(selectedCylinderId),
    },
  );

  const serviceStatusMutation = useCoreMutation(
    ({ serviceId, status }: { serviceId: string; status: string }) =>
      updateCylinderService(selectedCylinderId, serviceId, { status }),
    {
      successMessage: "Servicio completado",
      invalidate: () => getCylinderQueryKeys(selectedCylinderId),
      onError: (err) => {
        toast.error(err instanceof Error ? err.message : "Error al completar servicio");
      },
    },
  );

  const deleteServiceMutation = useCoreMutation(
    (serviceId: string) => deleteCylinderService(selectedCylinderId, serviceId),
    {
      successMessage: "Servicio eliminado",
      invalidate: () => getCylinderQueryKeys(selectedCylinderId),
      onError: (err) => {
        toast.error(err instanceof Error ? err.message : "Error al eliminar servicio");
      },
    },
  );

  const printLabelMutation = useCoreMutation(
    (form: PrintLabelFormState) => printLabelFromForm(selectedCylinderId, form),
    {
      successMessage: "Impresión registrada",
      onSuccess: () => {
        setIsPrintLabelOpen(false);
        setPrintLabelForm(EMPTY_PRINT_LABEL_FORM);
      },
      invalidate: () => getCylinderQueryKeys(selectedCylinderId),
    },
  );

  const scanMutation = useCoreMutation(
    (form: ScanFormState) => processScanFromForm(form),
    {
      successMessage: "Escaneo procesado",
      onSuccess: (log: any) => {
        setIsScanOpen(false);
        setScanForm(EMPTY_SCAN_FORM);
      },
      invalidate: (log: any) => [
        ...getCylinderQueryKeys(log.cylinder_id ?? selectedCylinderId),
        logisticsKeys.scans.all(),
      ],
    },
  );

  return {
    createMutation,
    updateMutation,
    transitionMutation,
    fillMutation,
    vacateMutation,
    hydrotestMutation,
    warrantyMutation,
    retimbradoMutation,
    serviceMutation,
    serviceStatusMutation,
    deleteServiceMutation,
    printLabelMutation,
    scanMutation,
  };
}
