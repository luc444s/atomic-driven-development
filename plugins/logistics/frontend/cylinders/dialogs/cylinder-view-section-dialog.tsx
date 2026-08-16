import { Button } from "@systutor/shell/ui/button";
import { Card, CardContent } from "@systutor/shell/ui/card";
import { DataTable } from "@systutor/shell/ui/data-table";
import { Dialog } from "@systutor/shell/ui/dialog";
import { CylinderTraceabilityTimeline } from "../../traceability/CylinderTraceabilityTimeline";
import { formatDate, formatDateTime, InfoBlock } from "../utils/formatters";
import type { LogisticsHydrostaticTest, LogisticsWarranty } from "../../api";
import type { LogisticsRetimbrado } from "../../api";
import type { LogisticsOwnership, LogisticsLabelHistory } from "../../api";
import type { LogisticsCylinderService, LogisticsScanLog } from "../../api";
import type { LogisticsLabelData } from "../../api";

type ViewSection = "trace" | "ph" | "retimbrados" | "custody" | "services" | "label";

type CylinderViewSectionDialogProps = {
  open: boolean;
  section: ViewSection | null;
  cylinderId: string;
  onBack: () => void;
  hydrotestsData: LogisticsHydrostaticTest[];
  warrantiesData: LogisticsWarranty[];
  retimbradosData: LogisticsRetimbrado[];
  ownershipData: LogisticsOwnership[];
  labelHistoryData: LogisticsLabelHistory[];
  servicesData: LogisticsCylinderService[];
  scanData: LogisticsScanLog[];
  labelData: LogisticsLabelData | null;
  serviceTypeById: Map<string, string>;
};

const TITLES: Record<ViewSection, { title: string; description: string }> = {
  trace: { title: "Trazabilidad de estado", description: "Transiciones registradas sobre el envase." },
  ph: { title: "PH y garantías", description: "Historial de mantenimiento legal y comercial." },
  retimbrados: { title: "Retimbrados", description: "Ficha técnica del reestampado del cilindro." },
  custody: { title: "Custodia e impresión", description: "Tenencia del envase y sus etiquetas impresas." },
  services: { title: "Servicios y escaneos", description: "Mantenimiento del envase y eventos de campo." },
  label: { title: "Etiqueta operativa", description: "Resumen rápido para impresión y verificación." },
};

export function CylinderViewSectionDialog({
  open,
  section,
  cylinderId,
  onBack,
  hydrotestsData,
  warrantiesData,
  retimbradosData,
  ownershipData,
  labelHistoryData,
  servicesData,
  scanData,
  labelData,
  serviceTypeById,
}: CylinderViewSectionDialogProps) {
  if (!section) {
    return null;
  }

  const titles = TITLES[section];

  return (
    <Dialog open={open} title={titles.title} description={titles.description} maxWidthClassName="max-w-5xl" onClose={onBack}>
      <div className="space-y-4">
        <Button variant="secondary" onClick={onBack}>
          ← Volver al menú
        </Button>

        {section === "trace" ? (
          <Card>
            <CardContent className="pt-6">
              <CylinderTraceabilityTimeline cylinderId={cylinderId} />
            </CardContent>
          </Card>
        ) : null}

        {section === "ph" ? (
          <div className="grid gap-4 lg:grid-cols-2">
            <Card>
              <CardContent className="pt-6">
                <DataTable
                  columns={[
                    { key: "test_date", header: "PH", render: (row) => row.test_date },
                    { key: "status", header: "Estado", render: (row) => row.status || "-" },
                    { key: "notes", header: "Notas", render: (row) => row.notes || "-" },
                  ]}
                  rows={hydrotestsData}
                  rowKey={(row) => row.id}
                  emptyMessage="Sin PH registradas."
                />
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <DataTable
                  columns={[
                    { key: "customer", header: "Cliente", render: (row) => (row as LogisticsWarranty).customer_name },
                    { key: "type", header: "Tipo", render: (row) => (row as LogisticsWarranty).warranty_type },
                    { key: "status", header: "Estado", render: (row) => (row as LogisticsWarranty).status },
                  ]}
                  rows={warrantiesData}
                  rowKey={(row) => row.id}
                  emptyMessage="Sin garantías registradas."
                />
              </CardContent>
            </Card>
          </div>
        ) : null}

        {section === "retimbrados" ? (
          <Card>
            <CardContent className="pt-6">
              <DataTable
                columns={[
                  { key: "date", header: "Fecha", render: (row) => (row as LogisticsRetimbrado).retimbrado_date },
                  { key: "approval", header: "Aprobación", render: (row) => (row as LogisticsRetimbrado).approval_number || "-" },
                  { key: "pressure", header: "Presión prueba", render: (row) => (row as LogisticsRetimbrado).test_pressure?.toString() || "-" },
                  { key: "onu", header: "ONU", render: (row) => (row as LogisticsRetimbrado).un_number || "-" },
                ]}
                rows={retimbradosData}
                rowKey={(row) => row.id}
                emptyMessage="Sin retimbrados registrados."
              />
            </CardContent>
          </Card>
        ) : null}

        {section === "custody" ? (
          <div className="grid gap-4 lg:grid-cols-2">
            <Card>
              <CardContent className="pt-6">
                <DataTable
                  columns={[
                    { key: "date", header: "Fecha", render: (row) => formatDateTime((row as LogisticsOwnership).change_date) },
                    { key: "customer", header: "Custodio", render: (row) => (row as LogisticsOwnership).customer_name || "-" },
                    { key: "condition", header: "Condición", render: (row) => (row as LogisticsOwnership).condition || "-" },
                  ]}
                  rows={ownershipData}
                  rowKey={(row) => row.id}
                  emptyMessage="Sin cambios de custodia."
                />
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <DataTable
                  columns={[
                    { key: "date", header: "Fecha", render: (row) => formatDateTime((row as LogisticsLabelHistory).printed_at) },
                    { key: "origin", header: "Origen", render: (row) => (row as LogisticsLabelHistory).origin },
                    { key: "copies", header: "Copias", render: (row) => (row as LogisticsLabelHistory).copies },
                    { key: "reason", header: "Motivo", render: (row) => (row as LogisticsLabelHistory).reason || "-" },
                  ]}
                  rows={labelHistoryData}
                  rowKey={(row) => row.id}
                  emptyMessage="Sin impresiones registradas."
                />
              </CardContent>
            </Card>
          </div>
        ) : null}

        {section === "services" ? (
          <div className="grid gap-4 lg:grid-cols-2">
            <Card>
              <CardContent className="pt-6">
                <DataTable
                  columns={[
                    { key: "service", header: "Servicio", render: (row) => serviceTypeById.get((row as LogisticsCylinderService).service_type_id) || "-" },
                    { key: "status", header: "Estado", render: (row) => (row as LogisticsCylinderService).status },
                    { key: "total", header: "Total", render: (row) => (row as LogisticsCylinderService).total_amount?.toString() || "-" },
                  ]}
                  rows={servicesData}
                  rowKey={(row) => row.id}
                  emptyMessage="Sin servicios registrados."
                />
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <DataTable
                  columns={[
                    { key: "date", header: "Fecha", render: (row) => formatDateTime((row as LogisticsScanLog).scanned_at) },
                    { key: "service", header: "Servicio", render: (row) => (row as LogisticsScanLog).service_type },
                    { key: "result", header: "Resultado", render: (row) => (row as LogisticsScanLog).result },
                    {
                      key: "gps",
                      header: "GPS",
                      render: (row) =>
                        (row as LogisticsScanLog).gps_lat !== null && (row as LogisticsScanLog).gps_lng !== null
                          ? `${(row as LogisticsScanLog).gps_lat}, ${(row as LogisticsScanLog).gps_lng}`
                          : "-",
                    },
                  ]}
                  rows={scanData}
                  rowKey={(row) => row.id}
                  emptyMessage="Sin escaneos registrados."
                />
              </CardContent>
            </Card>
          </div>
        ) : null}

        {section === "label" ? (
          <Card>
            <CardContent className="pt-6 grid gap-4 grid-cols-1 sm:grid-cols-2 md:grid-cols-3 xl:grid-cols-6">
              <InfoBlock label="Gas" value={labelData?.gas_product_name ?? null} />
              <InfoBlock label="Marca" value={labelData?.brand_name ?? null} />
              <InfoBlock label="Aprobación" value={labelData?.approval_number ?? null} />
              <InfoBlock label="Clase peligro" value={labelData?.danger_class ?? null} />
              <InfoBlock label="Nro ONU" value={labelData?.un_number ?? null} />
              <InfoBlock label="Última impresión" value={labelData?.label_origin ?? null} />
            </CardContent>
          </Card>
        ) : null}
      </div>
    </Dialog>
  );
}
