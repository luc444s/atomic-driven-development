import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "../../../../../apps/web/src/shared/ui/card";
import type { RouteOperation } from "../../api";
import {
  formatMovementDirection,
  formatRouteOperationStatus,
  formatRouteOperationType,
} from "./jornada-labels";

type Props = {
  operations: RouteOperation[];
};

export function RouteOperationsCard({ operations }: Props) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Operaciones confirmadas</CardTitle>
        <CardDescription>
          Registro inmutable de lo que ya ocurrió en la calle.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-2">
        {operations.length ? (
          operations.map((operation) => (
            <div key={operation.id} className="rounded-lg border border-border px-3 py-2 text-sm text-foreground">
              <div className="font-medium">
                {formatRouteOperationType(operation.operation_type)} · {formatRouteOperationStatus(operation.status)}
              </div>
              <div className="text-muted-foreground">
                {operation.items
                  .map((item) => `${formatMovementDirection(item.direction)} ${item.product_name} ${item.quantity}`)
                  .join(" · ")}
              </div>
            </div>
          ))
        ) : (
          <p className="text-sm text-muted-foreground">Sin operaciones registradas todavía.</p>
        )}
      </CardContent>
    </Card>
  );
}
