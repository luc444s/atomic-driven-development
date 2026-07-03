import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../../../apps/web/src/shared/ui/card";
import { DataTable } from "../../../../apps/web/src/shared/ui/data-table";

type DeliveryPointSummary = {
  id: string;
  address: string;
  contact_name: string | null;
  phone: string | null;
  delivery_day: string | null;
  time_window: string | null;
  is_active: boolean;
};

type DeliveryPointsSectionProps = {
  points: DeliveryPointSummary[];
  isLoading?: boolean;
};

export function DeliveryPointsSection({ points, isLoading = false }: DeliveryPointsSectionProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Puntos de entrega</CardTitle>
        <CardDescription>Vista resumida de los puntos operativos mantenidos en logistics.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3 text-sm text-foreground">
        {isLoading ? <p>Cargando puntos de entrega...</p> : null}
        <DataTable
          columns={[
            { key: "address", header: "Dirección", render: (row) => row.address },
            { key: "contact", header: "Contacto", render: (row) => row.contact_name ?? "-" },
            { key: "phone", header: "Teléfono", render: (row) => row.phone ?? "-" },
            { key: "day", header: "Día", render: (row) => row.delivery_day ?? "-" },
            { key: "window", header: "Ventana", render: (row) => row.time_window ?? "-" },
            { key: "active", header: "Activo", render: (row) => (row.is_active ? "Sí" : "No") },
          ]}
          rows={points}
          rowKey={(row) => row.id}
          emptyMessage="No hay puntos de entrega asociados."
        />
      </CardContent>
    </Card>
  );
}
