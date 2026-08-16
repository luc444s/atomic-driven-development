import { Dialog } from "@systutor/shell/ui/dialog";
import { SessionReconciliationTab } from "../SessionReconciliationTab";
import type { SessionReconciliation } from "../../../api";

type Props = {
  open: boolean;
  onClose: () => void;
  reconciliation: SessionReconciliation | undefined;
  counts: Record<string, string>;
  setCounts: React.Dispatch<React.SetStateAction<Record<string, string>>>;
  onSaveCount: () => void;
  isPending: boolean;
  error: string | null;
};

export function ReconciliationModal(props: Props) {
  const { open, onClose, ...contentProps } = props;

  return (
    <Dialog
      open={open}
      onClose={onClose}
      title="Conciliación operativa"
      description="Registra el conteo y valida diferencias sin abandonar la consola principal."
      maxWidthClassName="max-w-5xl"
    >
      <SessionReconciliationTab {...contentProps} />
    </Dialog>
  );
}
