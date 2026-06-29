import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../../../apps/web/src/shared/ui/card";

type DeliveryPointSummary = {
  id: string;
  address: string;
  delivery_day: string | null;
  time_window: string | null;
  is_active: boolean;
};

type DeliveryPointsSectionProps = {
  points: DeliveryPointSummary[];
};

export function DeliveryPointsSection({ points }: DeliveryPointsSectionProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Puntos de entrega</CardTitle>
        <CardDescription>Vista resumida de los puntos operativos mantenidos en logistics.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3 text-sm text-slate-300">
        {points.length === 0 ? <p>No hay puntos de entrega asociados.</p> : null}
        {points.map((point) => (
          <div key={point.id} className="rounded-md border border-slate-800 p-3">
            <p className="font-medium text-slate-100">{point.address}</p>
            <p>Día: {point.delivery_day ?? "-"}</p>
            <p>Ventana: {point.time_window ?? "-"}</p>
            <p>Activo: {point.is_active ? "Sí" : "No"}</p>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
