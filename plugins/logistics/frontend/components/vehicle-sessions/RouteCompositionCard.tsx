import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@systutor/shell/ui/card";
import type { CurrentComposition } from "../../api";

type Props = {
  composition: CurrentComposition | undefined;
};

export function RouteCompositionCard({ composition }: Props) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Composición vigente</CardTitle>
        <CardDescription>
          Proyección derivada de lo que el vehículo transporta ahora mismo.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {composition?.product_lines.length ? (
          <>
            <div className="space-y-2">
              {composition.product_lines.map((line) => (
                <div key={line.product_id} className="rounded-lg border border-border px-3 py-2 text-sm text-foreground">
                  <div className="font-medium">{line.product_name}</div>
                  <div className="text-muted-foreground">
                    Cantidad: {line.quantity} · Peso: {line.weight_kg ?? "-"} kg · ADR: {line.adr_points ?? "-"}
                  </div>
                </div>
              ))}
            </div>
            <div className="grid gap-3 border-t border-border pt-3 text-sm text-muted-foreground md:grid-cols-3">
              <div>Total bultos: {composition.totals.total_packages}</div>
              <div>Peso total: {composition.totals.total_weight_kg} kg</div>
              <div>ADR total: {composition.totals.total_adr_points}</div>
            </div>
          </>
        ) : (
          <p className="text-sm text-muted-foreground">Sin composición transportada vigente.</p>
        )}
      </CardContent>
    </Card>
  );
}
