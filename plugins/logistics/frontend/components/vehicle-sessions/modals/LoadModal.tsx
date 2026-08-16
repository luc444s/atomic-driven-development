import { Dialog } from "@systutor/shell/ui/dialog";
import {
  type EditableLoadPlanItem,
  SessionLoadTab,
} from "../SessionLoadTab";
import type { SerializedCylinderSummary, VehicleSessionDetail } from "../../../api";
import type { StockBalanceItem } from "../../../../../stock/frontend/types";

type Props = {
  open: boolean;
  onClose: () => void;
  session: VehicleSessionDetail;
  loadPlanItems: EditableLoadPlanItem[];
  setLoadPlanItems: React.Dispatch<React.SetStateAction<EditableLoadPlanItem[]>>;
  originRows: StockBalanceItem[];
  serializedRows: SerializedCylinderSummary[];
  onOpenProductSearch: () => void;
  onSavePlan: () => void;
  isPending: boolean;
  error: string | null;
};

export function LoadModal(props: Props) {
  const { open, onClose, ...contentProps } = props;

  return (
    <Dialog
      open={open}
      onClose={onClose}
      title="Carga operativa"
      description="Edita y valida la carga sin perder el contexto de la jornada."
      maxWidthClassName="max-w-5xl"
    >
      <SessionLoadTab {...contentProps} />
    </Dialog>
  );
}
