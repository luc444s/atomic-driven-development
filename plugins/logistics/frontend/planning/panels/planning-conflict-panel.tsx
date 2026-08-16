import { Alert } from "@systutor/shell/ui/alert";

type Props = {
  reason: string | null;
};

export function PlanningConflictPanel({ reason }: Props) {
  if (!reason) {
    return null;
  }

  return <Alert title="Conflicto operativo">{reason}</Alert>;
}
