// Auto-generado por split-tsx.py (limpiado manualmente)
import { Alert } from "@systutor/shell/ui/alert";
import { Button } from "@systutor/shell/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@systutor/shell/ui/card";
import { Dialog } from "@systutor/shell/ui/dialog";
import { CylinderStateBadge } from "../../CylinderStateBadge";
import type { LogisticsCylinder } from "../../api";

type ViewSection = "trace" | "ph" | "retimbrados" | "custody" | "services" | "label";

interface ActionCardButtonProps {
  title: string;
  description: string;
  onClick: () => void;
}

function ActionCardButton({ title, description, onClick }: ActionCardButtonProps) {
  return (
    <Button
      type="button"
      variant="secondary"
      onClick={onClick}
      className="h-auto w-full flex-col items-start gap-1 rounded-lg border border-border bg-surface p-4 text-left"
    >
      <span className="text-sm font-medium text-foreground">{title}</span>
      <span className="text-xs text-muted-foreground">{description}</span>
    </Button>
  );
}

interface DetailMenuDialogProps {
  selectedCylinder: LogisticsCylinder | null;
  isDetailMenuOpen: boolean;
  detailError: string | null;
  productById: Map<string, string>;
  gasById: Map<string, string>;
  brandById: Map<string, string>;
  canUpdate: boolean;
  canMaintenance: boolean;
  canTransition: boolean;
  canRetimbrado: boolean;
  canServiceManage: boolean;
  canLabelPrint: boolean;
  openEditDialog: () => void;
  openFillingDialog: (mode: "fill" | "vacate") => void;
  setIsHydrotestOpen: (open: boolean) => void;
  setIsWarrantyOpen: (open: boolean) => void;
  setIsTransitionOpen: (open: boolean) => void;
  setIsRetimbradoOpen: (open: boolean) => void;
  setIsServiceOpen: (open: boolean) => void;
  setIsPrintLabelOpen: (open: boolean) => void;
  setIsScanOpen: (open: boolean) => void;
  openViewSection: (section: ViewSection) => void;
  closeDetailContext: () => void;
  formatDate: (date: string | null | undefined) => string;
  formatDateTime: (date: string | null | undefined) => string;
}

export function DetailMenuDialog({
  selectedCylinder,
  isDetailMenuOpen,
  detailError,
  productById,
  gasById,
  brandById,
  canUpdate,
  canMaintenance,
  canTransition,
  canRetimbrado,
  canServiceManage,
  canLabelPrint,
  openEditDialog,
  openFillingDialog,
  setIsHydrotestOpen,
  setIsWarrantyOpen,
  setIsTransitionOpen,
  setIsRetimbradoOpen,
  setIsServiceOpen,
  setIsPrintLabelOpen,
  setIsScanOpen,
  openViewSection,
  closeDetailContext,
  formatDate,
  formatDateTime,
}: DetailMenuDialogProps) {
  return (
    <Dialog
      open={isDetailMenuOpen && selectedCylinder !== null}
      title={selectedCylinder ? `Ficha del envase ${selectedCylinder.serial}` : "Ficha del envase"}
      maxWidthClassName="max-w-[1600px]"
      onClose={closeDetailContext}
    >
      {selectedCylinder ? (
        <div className="space-y-4">
          {detailError ? <Alert title="Operación no completada">{detailError}</Alert> : null}

          <Card>
            <CardHeader>
              <CardTitle>Datos generales</CardTitle>
              <CardDescription>Resumen corto del envase antes de entrar a una función.</CardDescription>
            </CardHeader>
            <CardContent className="grid gap-3 grid-cols-1 sm:grid-cols-2 md:grid-cols-3 xl:grid-cols-5 2xl:grid-cols-6 text-sm text-foreground">
              <div><span className="text-muted-foreground">Serial:</span> {selectedCylinder.serial}</div>
              <div><span className="text-muted-foreground">Tipo:</span> {selectedCylinder.container_type === "CRYOGENIC_TANK" ? "Criogénico (tanque)" : "Estándar"}</div>
              <div><span className="text-muted-foreground">Estado:</span> <CylinderStateBadge state={selectedCylinder.current_state} /></div>
              <div><span className="text-muted-foreground">Gas:</span> {productById.get(selectedCylinder.product_id ?? "") || gasById.get(selectedCylinder.gas_group_id ?? "") || "-"}</div>
              <div><span className="text-muted-foreground">Marca:</span> {brandById.get(selectedCylinder.brand_id ?? "") || "-"}</div>
              <div><span className="text-muted-foreground">Matrícula:</span> {selectedCylinder.barcode2 || "-"}</div>
              <div><span className="text-muted-foreground">Condición:</span> {selectedCylinder.condition || "-"}</div>
              <div><span className="text-muted-foreground">Ubicación:</span> {selectedCylinder.location_context || selectedCylinder.warehouse_name || selectedCylinder.location || "-"}</div>
              <div><span className="text-muted-foreground">Lectura material:</span> {selectedCylinder.fill_status || "-"}</div>
              <div><span className="text-muted-foreground">Contenido kg:</span> {selectedCylinder.content_kg?.toString() || "-"}</div>
              {selectedCylinder.container_type === "CRYOGENIC_TANK" && selectedCylinder.content_kg != null && selectedCylinder.content_kg > 0 ? (
                <div><span className="text-muted-foreground">Contenido L:</span> {(selectedCylinder.content_kg / ((selectedCylinder.average_weight_source?.weight_kg ?? 1141) / 1000)).toFixed(0)} L</div>
              ) : null}
              <div><span className="text-muted-foreground">Peso:</span> {selectedCylinder.weight_current?.toString() || selectedCylinder.weight_origin?.toString() || (selectedCylinder.average_weight_source?.weight_kg?.toString() ?? "-")}{!selectedCylinder.weight_current && !selectedCylinder.weight_origin && selectedCylinder.average_weight_source ? <span className="ml-1 text-xs italic text-muted-foreground">(peso por defecto de producto)</span> : !selectedCylinder.weight_current && !selectedCylinder.weight_origin ? <span className="ml-1 text-xs italic text-muted-foreground">(sin peso real)</span> : null}</div>
              <div><span className="text-muted-foreground">Volumen m3:</span> {selectedCylinder.volume_m3?.toString() || "-"}</div>
              <div><span className="text-muted-foreground">Último llenado:</span> {formatDateTime(selectedCylinder.last_fill_at)}{selectedCylinder.last_fill_warehouse_name ? ` · ${selectedCylinder.last_fill_warehouse_name}` : ""}</div>
              <div><span className="text-muted-foreground">Costo:</span> {selectedCylinder.cost?.toString() || "-"}</div>
              <div><span className="text-muted-foreground">Precio:</span> {selectedCylinder.price?.toString() || "-"}</div>
              <div><span className="text-muted-foreground">PH siguiente:</span> {formatDate(selectedCylinder.next_hydrotest_date) || "-"}</div>
              <div>{selectedCylinder.is_medical ? <span className="font-medium text-amber-500">&bull; Medicinal</span> : null}</div>
            </CardContent>
          </Card>

          {selectedCylinder.is_medical ? (
            <Alert title="Uso medicinal">Este envase está marcado para uso medicinal. La trazabilidad debe ser completa y auditable.</Alert>
          ) : null}

          <Card>
            <CardHeader>
              <CardTitle>Operativa</CardTitle>
              <CardDescription>Acciones para trabajar el envase.</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
                {canUpdate ? <ActionCardButton title="Editar ficha" description="Actualiza los datos principales." onClick={openEditDialog} /> : null}
                {canMaintenance ? <ActionCardButton title="Registrar PH" description="Nueva prueba hidrostática." onClick={() => setIsHydrotestOpen(true)} /> : null}
                {canMaintenance ? <ActionCardButton title="Registrar garantía" description="Asocia una garantía comercial." onClick={() => setIsWarrantyOpen(true)} /> : null}
                {canTransition ? <ActionCardButton title="Corrección de estado" description="Solo para regularización o corrección excepcional." onClick={() => setIsTransitionOpen(true)} /> : null}
                {canRetimbrado ? <ActionCardButton title="Registrar retimbrado" description="Carga la ficha técnica del reestampado." onClick={() => setIsRetimbradoOpen(true)} /> : null}
                {canServiceManage ? <ActionCardButton title="Agregar servicio" description="Registra un servicio operativo." onClick={() => setIsServiceOpen(true)} /> : null}
                {canLabelPrint ? <ActionCardButton title="Imprimir etiqueta" description="Genera el registro de impresión." onClick={() => setIsPrintLabelOpen(true)} /> : null}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Vista</CardTitle>
              <CardDescription>Abre una tabla específica con un clic.</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                <ActionCardButton title="Trazabilidad de estado" description="Transiciones registradas." onClick={() => openViewSection("trace")} />
                <ActionCardButton title="PH y garantías" description="Mantenimiento legal y comercial." onClick={() => openViewSection("ph")} />
                <ActionCardButton title="Retimbrados" description="Ficha técnica del reestampado." onClick={() => openViewSection("retimbrados")} />
                <ActionCardButton title="Custodia e impresión" description="Tenencia y etiquetas impresas." onClick={() => openViewSection("custody")} />
                <ActionCardButton title="Servicios y escaneos" description="Mantenimiento y eventos de campo." onClick={() => openViewSection("services")} />
                <ActionCardButton title="Etiqueta operativa" description="Resumen rápido para impresión." onClick={() => openViewSection("label")} />
              </div>
            </CardContent>
          </Card>
        </div>
      ) : null}
    </Dialog>
  );
}
