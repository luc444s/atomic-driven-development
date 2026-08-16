import { Card, CardContent } from "@systutor/shell/ui/card";
import { CylinderStateBadge } from "../../CylinderStateBadge";

const SUMMARY_STATES = [
  "CREADO_VACIO",
  "EN_ALMACEN_VACIO",
  "LLENADO_OK",
  "EN_RUTA",
  "EN_CLIENTE_LLENO",
  "OBSERVADO",
] as const;

interface CylinderSummaryCardsProps {
  summaryByState: Map<string, number>;
}

export function CylinderSummaryCards({ summaryByState }: CylinderSummaryCardsProps) {
  return (
    <div className="overflow-x-auto">
      <div className="flex min-w-max gap-3">
        {SUMMARY_STATES.map((state) => (
          <Card key={state} className="min-w-40">
            <CardContent className="space-y-2 p-4">
              <CylinderStateBadge state={state} />
              <p className="text-2xl font-semibold text-foreground">
                {summaryByState.get(state) ?? 0}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
