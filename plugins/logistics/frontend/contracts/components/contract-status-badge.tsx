import { Badge } from "@systutor/shell/ui/badge";

const STATUS_COLOR: Record<string, string> = {
  DRAFT: "border-border bg-muted text-muted-foreground",
  PENDING_SIGNATURE: "border-warning/30 bg-warning/10 text-warning",
  ACTIVE: "border-success/30 bg-success/10 text-success",
  EXPIRED: "border-destructive/30 bg-destructive/10 text-destructive",
  CANCELLED: "border-destructive/30 bg-destructive/10 text-destructive",
  TERMINATED: "border-destructive/30 bg-destructive/10 text-destructive",
};

const STATUS_LABEL: Record<string, string> = {
  DRAFT: "Borrador",
  PENDING_SIGNATURE: "Por firmar",
  ACTIVE: "Vigente",
  EXPIRED: "Vencido",
  CANCELLED: "Anulado",
  TERMINATED: "Terminado",
};

export function ContractStatusBadge({ status }: { status: string }) {
  return (
    <Badge className={STATUS_COLOR[status] || "border-border bg-muted text-muted-foreground"}>
      {STATUS_LABEL[status] || status}
    </Badge>
  );
}
