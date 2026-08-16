import { Badge } from "@systutor/shell/ui/badge";

const STATUS_COLOR: Record<string, string> = {
  DRAFT: "bg-gray-100 text-gray-800",
  PENDING_SIGNATURE: "bg-amber-100 text-amber-800",
  ACTIVE: "bg-green-100 text-green-800",
  EXPIRED: "bg-red-100 text-red-800",
  CANCELLED: "bg-yellow-100 text-yellow-800",
  TERMINATED: "bg-red-100 text-red-800",
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
    <Badge className={STATUS_COLOR[status] || "bg-gray-100 text-gray-800"}>
      {STATUS_LABEL[status] || status}
    </Badge>
  );
}
