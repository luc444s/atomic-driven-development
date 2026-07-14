// Auto-generado por split-tsx.py (limpiado manualmente)
import { Alert } from "../../../../../apps/web/src/shared/ui/alert";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../../../../apps/web/src/shared/ui/card";
import { Dialog } from "../../../../../apps/web/src/shared/ui/dialog";
import { CylinderStateBadge } from "../../CylinderStateBadge";
import type { LogisticsCylinder } from "../../api";

interface DetailMenuDialogProps {
  selectedCylinder: LogisticsCylinder | null;
  isDetailMenuOpen: boolean;
  detailError: string | null;
  productById: Map<string, string>;
  gasById: Map<string, string>;
  brandById: Map<string, string>;
  canContractView: boolean;
  canContractCreate: boolean;
  canUpdate: boolean;
  canMaintenance: boolean;
  canTransition: boolean;
  canRetimbrado: boolean;
  canServiceManage: boolean;
  canLabelPrint: boolean;
  canScan: boolean;
  openEditDialog: () => void;
  setIsHydrotestOpen: (open: boolean) => void;
  setIsWarrantyOpen: (open: boolean) => void;
  setIsTransitionOpen: (open: boolean) => void;
  setIsRetimbradoOpen: (open: boolean) => void;
  setIsServiceOpen: (open: boolean) => void;
  setIsPrintLabelOpen: (open: boolean) => void;
  setIsScanOpen: (open: boolean) => void;
  openViewSection: (section: string) => void;
  openCreateContractDialog: () => void;
  closeDetailContext: () => void;
  formatDate: (date: string | null | undefined) => string;
}

export function DetailMenuDialog({
  selectedCylinder,
  isDetailMenuOpen,
  detailError,
  productById,
  gasById,
  brandById,
  canContractView,
  canContractCreate,
  canUpdate,
  canMaintenance,
  canTransition,
  canRetimbrado,
  canServiceManage,
  canLabelPrint,
  canScan,
  openEditDialog,
  setIsHydrotestOpen,
  setIsWarrantyOpen,
  setIsTransitionOpen,
  setIsRetimbradoOpen,
  setIsServiceOpen,
  setIsPrintLabelOpen,
  setIsScanOpen,
  openViewSection,
  openCreateContractDialog,
  closeDetailContext,
  formatDate,
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
              <div><span className="text-muted-foreground">Estado:</span> <CylinderStateBadge state={selectedCylinder.current_state} /></div>
              <div><span className="text-muted-foreground">Gas:</span> {productById.get(selectedCylinder.product_id ?? "") || gasById.get(selectedCylinder.gas_group_id ?? "") || "-"}</div>
              <div><span className="text-muted-foreground">Marca:</span> {brandById.get(selectedCylinder.brand_id ?? "") || "-"}</div>
              <div><span className="text-muted-foreground">Barcode producto:</span> {selectedCylinder.barcode1 || "-"}</div>
              <div><span className="text-muted-foreground">Matrícula:</span> {selectedCylinder.barcode2 || "-"}</div>
              <div><span className="text-muted-foreground">Condición:</span> {selectedCylinder.condition || "-"}</div>
              <div><span className="text-muted-foreground">Ubicación:</span> {selectedCylinder.location || "-"}</div>
              <div><span className="text-muted-foreground">Contenido kg:</span> {selectedCylinder.content_kg?.toString() || "-"}</div>
              <div><span className="text-muted-foreground">Peso:</span> {selectedCylinder.weight_current?.toString() || selectedCylinder.weight_origin?.toString() || (selectedCylinder.average_weight_source?.weight_kg?.toString() ?? "-")}{!selectedCylinder.weight_current && !selectedCylinder.weight_origin && selectedCylinder.average_weight_source ? <span className="ml-1 text-xs italic text-muted-foreground">(peso por defecto de producto)</span> : !selectedCylinder.weight_current && !selectedCylinder.weight_origin ? <span className="ml-1 text-xs italic text-muted-foreground">(sin peso real)</span> : null}</div>
              <div><span className="text-muted-foreground">Volumen m3:</span> {selectedCylinder.volume_m3?.toString() || "-"}</div>
              <div><span className="text-muted-foreground">Costo:</span> {selectedCylinder.cost?.toString() || "-"}</div>
              <div><span className="text-muted-foreground">Precio:</span> {selectedCylinder.price?.toString() || "-"}</div>
              <div><span className="text-muted-foreground">PH siguiente:</span> {formatDate(selectedCylinder.next_hydrotest_date) || "-"}</div>
              <div><span className="text-muted-foreground">ADR UN:</span> {selectedCylinder.adr_un_number || "-"}</div>
              <div><span className="text-muted-foreground">ADR etiqueta:</span> {selectedCylinder.adr_label || "-"}</div>
              <div><span className="text-muted-foreground">ADR mercancía:</span> {selectedCylinder.adr_merchandise || "-"}</div>
              <div>{selectedCylinder.is_medical ? <span className="font-medium text-amber-500">&bull; Medicinal</span> : null}</div>
            </CardContent>
          </Card>

          {!selectedCylinder.barcode2 ? (
            <Alert title="Falta matrícula de etiqueta">Este envase aún no tiene `barcode2` para etiqueta y escaneo.</Alert>
          ) : null}

          {selectedCylinder.is_medical ? (
            <Alert title="Uso medicinal">Este envase está marcado para uso medicinal. La trazabilidad debe ser completa y auditable.</Alert>
          ) : null}

          {canContractView || canContractCreate ? (
            <Card>
              <CardHeader>
                <CardTitle>Contrato de envases</CardTitle>
                <CardDescription>Los contratos definen cantidades por producto; la asignacion real se deriva de movimientos SC/IC.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="rounded-lg border border-dashed border-border bg-surface p-4 text-sm text-muted-foreground">
                  Este envase no se vincula manualmente a un contrato. Usa movimientos confirmados para reflejar la posesion operativa del cliente.
                </div>

                {canContractCreate ? (
                  <div className="flex justify-end">
                    <button
                      type="button"
                      onClick={openCreateContractDialog}
                      className="rounded-lg border border-border bg-surface px-4 py-2 text-sm text-foreground transition hover:border-ring hover:bg-surface-alt"
                    >
                      Crear contrato con este tipo de envase
                    </button>
                  </div>
                ) : null}
              </CardContent>
            </Card>
          ) : null}

          <Card>
            <CardHeader>
              <CardTitle>Operativa</CardTitle>
              <CardDescription>Acciones para trabajar el envase.</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
                {canUpdate ? <button type="button" onClick={openEditDialog} className="rounded-lg border border-border bg-surface p-4 text-left transition hover:border-ring hover:bg-surface-alt"><p className="text-sm font-medium text-foreground">Editar ficha</p><p className="mt-1 text-xs text-muted-foreground">Actualiza los datos principales.</p></button> : null}
                {canMaintenance ? <button type="button" onClick={() => setIsHydrotestOpen(true)} className="rounded-lg border border-border bg-surface p-4 text-left transition hover:border-ring hover:bg-surface-alt"><p className="text-sm font-medium text-foreground">Registrar PH</p><p className="mt-1 text-xs text-muted-foreground">Nueva prueba hidrostática.</p></button> : null}
                {canMaintenance ? <button type="button" onClick={() => setIsWarrantyOpen(true)} className="rounded-lg border border-border bg-surface p-4 text-left transition hover:border-ring hover:bg-surface-alt"><p className="text-sm font-medium text-foreground">Registrar garantía</p><p className="mt-1 text-xs text-muted-foreground">Asocia una garantía comercial.</p></button> : null}
                {canTransition ? <button type="button" onClick={() => setIsTransitionOpen(true)} className="rounded-lg border border-border bg-surface p-4 text-left transition hover:border-ring hover:bg-surface-alt"><p className="text-sm font-medium text-foreground">Transición operativa</p><p className="mt-1 text-xs text-muted-foreground">Cambia el estado del envase.</p></button> : null}
                {canRetimbrado ? <button type="button" onClick={() => setIsRetimbradoOpen(true)} className="rounded-lg border border-border bg-surface p-4 text-left transition hover:border-ring hover:bg-surface-alt"><p className="text-sm font-medium text-foreground">Registrar retimbrado</p><p className="mt-1 text-xs text-muted-foreground">Carga la ficha técnica del reestampado.</p></button> : null}
                {canServiceManage ? <button type="button" onClick={() => setIsServiceOpen(true)} className="rounded-lg border border-border bg-surface p-4 text-left transition hover:border-ring hover:bg-surface-alt"><p className="text-sm font-medium text-foreground">Agregar servicio</p><p className="mt-1 text-xs text-muted-foreground">Registra un servicio operativo.</p></button> : null}
                {canLabelPrint ? <button type="button" onClick={() => setIsPrintLabelOpen(true)} className="rounded-lg border border-border bg-surface p-4 text-left transition hover:border-ring hover:bg-surface-alt"><p className="text-sm font-medium text-foreground">Imprimir etiqueta</p><p className="mt-1 text-xs text-muted-foreground">Genera el registro de impresión.</p></button> : null}
                {canScan ? <button type="button" onClick={() => setIsScanOpen(true)} className="rounded-lg border border-border bg-surface p-4 text-left transition hover:border-ring hover:bg-surface-alt"><p className="text-sm font-medium text-foreground">Escanear</p><p className="mt-1 text-xs text-muted-foreground">Procesa validación con GPS.</p></button> : null}
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
                <button type="button" onClick={() => openViewSection("trace")} className="rounded-lg border border-border bg-surface p-4 text-left transition hover:border-ring hover:bg-surface-alt"><p className="text-sm font-medium text-foreground">Trazabilidad de estado</p><p className="mt-1 text-xs text-muted-foreground">Transiciones registradas.</p></button>
                <button type="button" onClick={() => openViewSection("ph")} className="rounded-lg border border-border bg-surface p-4 text-left transition hover:border-ring hover:bg-surface-alt"><p className="text-sm font-medium text-foreground">PH y garantías</p><p className="mt-1 text-xs text-muted-foreground">Mantenimiento legal y comercial.</p></button>
                <button type="button" onClick={() => openViewSection("retimbrados")} className="rounded-lg border border-border bg-surface p-4 text-left transition hover:border-ring hover:bg-surface-alt"><p className="text-sm font-medium text-foreground">Retimbrados</p><p className="mt-1 text-xs text-muted-foreground">Ficha técnica del reestampado.</p></button>
                <button type="button" onClick={() => openViewSection("custody")} className="rounded-lg border border-border bg-surface p-4 text-left transition hover:border-ring hover:bg-surface-alt"><p className="text-sm font-medium text-foreground">Custodia e impresión</p><p className="mt-1 text-xs text-muted-foreground">Tenencia y etiquetas impresas.</p></button>
                <button type="button" onClick={() => openViewSection("services")} className="rounded-lg border border-border bg-surface p-4 text-left transition hover:border-ring hover:bg-surface-alt"><p className="text-sm font-medium text-foreground">Servicios y escaneos</p><p className="mt-1 text-xs text-muted-foreground">Mantenimiento y eventos de campo.</p></button>
                <button type="button" onClick={() => openViewSection("label")} className="rounded-lg border border-border bg-surface p-4 text-left transition hover:border-ring hover:bg-surface-alt"><p className="text-sm font-medium text-foreground">Etiqueta operativa</p><p className="mt-1 text-xs text-muted-foreground">Resumen rápido para impresión.</p></button>
              </div>
            </CardContent>
          </Card>
        </div>
      ) : null}
    </Dialog>
  );
}
