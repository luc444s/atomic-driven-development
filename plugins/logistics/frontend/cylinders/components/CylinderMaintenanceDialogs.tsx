import type { CustomerBrief } from "../../../../crm/frontend/types";
import { CustomerSearchDialog } from "../../../../crm/frontend/components/CustomerSearchDialog";
import { ConfirmDialog } from "../../../../../apps/web/src/shared/ui/confirm-dialog";
import { HydrotestDialog } from "../dialogs/HydrotestDialog";
import { PrintLabelDialog } from "../dialogs/PrintLabelDialog";
import { RetimbradoDialog } from "../dialogs/RetimbradoDialog";
import { ScanDialog } from "../dialogs/ScanDialog";
import { ServiceDialog } from "../dialogs/ServiceDialog";
import { WarrantyDialog } from "../dialogs/WarrantyDialog";
import type {
  HydrotestFormState,
  PrintLabelFormState,
  RetimbradoFormState,
  ScanFormState,
  ServiceFormState,
  WarrantyFormState,
} from "../forms/cylinder-form-state";
import type { useCylinderData } from "../hooks/use-cylinder-data";
import type { useCylinderMutations } from "../hooks/use-cylinder-mutations";

type CylinderDataState = ReturnType<typeof useCylinderData>;
type CylinderMutationsState = ReturnType<typeof useCylinderMutations>;

interface CylinderMaintenanceDialogsProps {
  data: CylinderDataState;
  isHydrotestOpen: boolean;
  setIsHydrotestOpen: (open: boolean) => void;
  hydrotestForm: HydrotestFormState;
  setHydrotestForm: (next: HydrotestFormState) => void;
  handleHydrotest: (event: React.FormEvent<HTMLFormElement>) => void;
  isWarrantyOpen: boolean;
  setIsWarrantyOpen: (open: boolean) => void;
  warrantyForm: WarrantyFormState;
  setWarrantyForm: (next: WarrantyFormState | ((prev: WarrantyFormState) => WarrantyFormState)) => void;
  handleWarranty: (event: React.FormEvent<HTMLFormElement>) => void;
  isWarrantyCustomerSearchOpen: boolean;
  setIsWarrantyCustomerSearchOpen: (open: boolean) => void;
  isRetimbradoOpen: boolean;
  setIsRetimbradoOpen: (open: boolean) => void;
  retimbradoForm: RetimbradoFormState;
  setRetimbradoForm: (next: RetimbradoFormState) => void;
  handleRetimbrado: (event: React.FormEvent<HTMLFormElement>) => void;
  isServiceOpen: boolean;
  setIsServiceOpen: (open: boolean) => void;
  serviceForm: ServiceFormState;
  setServiceForm: (next: ServiceFormState) => void;
  handleService: (event: React.FormEvent<HTMLFormElement>) => void;
  isPrintLabelOpen: boolean;
  setIsPrintLabelOpen: (open: boolean) => void;
  printLabelForm: PrintLabelFormState;
  setPrintLabelForm: (next: PrintLabelFormState) => void;
  handlePrintLabel: (event: React.FormEvent<HTMLFormElement>) => void;
  isScanOpen: boolean;
  setIsScanOpen: (open: boolean) => void;
  scanForm: ScanFormState;
  setScanForm: (next: ScanFormState) => void;
  handleScan: (event: React.FormEvent<HTMLFormElement>) => void;
  scanFallbackAvailable: boolean;
  scanFallbackHint: string | null;
  openScanFallbackCreate: () => void;
  confirmDelete: { id: string; onConfirm: () => void } | null;
  setConfirmDelete: (value: { id: string; onConfirm: () => void } | null) => void;
  mutations: CylinderMutationsState;
}

export function CylinderMaintenanceDialogs({
  data,
  isHydrotestOpen,
  setIsHydrotestOpen,
  hydrotestForm,
  setHydrotestForm,
  handleHydrotest,
  isWarrantyOpen,
  setIsWarrantyOpen,
  warrantyForm,
  setWarrantyForm,
  handleWarranty,
  isWarrantyCustomerSearchOpen,
  setIsWarrantyCustomerSearchOpen,
  isRetimbradoOpen,
  setIsRetimbradoOpen,
  retimbradoForm,
  setRetimbradoForm,
  handleRetimbrado,
  isServiceOpen,
  setIsServiceOpen,
  serviceForm,
  setServiceForm,
  handleService,
  isPrintLabelOpen,
  setIsPrintLabelOpen,
  printLabelForm,
  setPrintLabelForm,
  handlePrintLabel,
  isScanOpen,
  setIsScanOpen,
  scanForm,
  setScanForm,
  handleScan,
  scanFallbackAvailable,
  scanFallbackHint,
  openScanFallbackCreate,
  confirmDelete,
  setConfirmDelete,
  mutations,
}: CylinderMaintenanceDialogsProps) {
  return (
    <>
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
          setWarrantyForm((current) => ({
            ...current,
            customer_id: customer.id,
            customer_name: customer.display_name,
          }))
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
    </>
  );
}
