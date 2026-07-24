import { Alert } from "../../../../../apps/web/src/shared/ui/alert";

type Props = {
  reason: string | null;
};

export function PlanningConflictPanel({ reason }: Props) {
  if (!reason) {
    return null;
  }

  return <Alert title="Conflicto operativo">{reason}</Alert>;
}
