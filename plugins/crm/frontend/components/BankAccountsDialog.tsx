import { Dialog } from "@systutor/shell/ui/dialog";
import { BankAccountsSection } from "./BankAccountsSection";

type BankAccountsDialogProps = {
  open: boolean;
  onClose: () => void;
  customerId: string;
};

export function BankAccountsDialog({ open, onClose, customerId }: BankAccountsDialogProps) {
  return (
    <Dialog
      open={open}
      title="Cuentas bancarias"
      description="Gestiona IBAN, titular y banco del cliente para domiciliaciones y remesas."
      onClose={onClose}
      maxWidthClassName="max-w-4xl"
    >
      <BankAccountsSection customerId={customerId} canManage />
    </Dialog>
  );
}
