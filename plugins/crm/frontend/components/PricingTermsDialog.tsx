import { Dialog } from "@systutor/shell/ui/dialog";
import { PricingTermsSection } from "./PricingTermsSection";

type PricingTermsDialogProps = {
  open: boolean;
  onClose: () => void;
  customerId: string;
};

export function PricingTermsDialog({ open, onClose, customerId }: PricingTermsDialogProps) {
  return (
    <Dialog
      open={open}
      title="Precios especiales"
      description="Condiciones comerciales del cliente. El precio base sigue viviendo en productos."
      onClose={onClose}
      maxWidthClassName="max-w-4xl"
    >
      <PricingTermsSection customerId={customerId} canManage />
    </Dialog>
  );
}
