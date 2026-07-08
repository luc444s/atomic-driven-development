// Auto-generado por split-tsx.py (limpiado manualmente)
import { Alert } from "../../../../../apps/web/src/shared/ui/alert";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../../../../apps/web/src/shared/ui/card";
import { Dialog } from "../../../../../apps/web/src/shared/ui/dialog";
import { CylinderStateBadge } from "../../CylinderStateBadge";
import type { LogisticsCylinder } from "../../api";
import type { LogisticsCylinderContract } from "../../api/contracts";
import { ContractStatusBadge } from "../../contracts/components/contract-status-badge";

interface DetailMenuDialogProps {
  selectedCylinder: LogisticsCylinder | null;
  isDetailMenuOpen: boolean;
  detailError: string | null;
  contractList: LogisticsCylinderContract[];
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

function isActiveContractForCylinder(contract: LogisticsCylinderContract, cylinderId: string) {
  if (contract.status === "CANCELLED" || contract.status === "EXPIRED") {
    return false;
  }
  return contract.items.some(
    (item) => item.cylinder_id === cylinderId && item.returned_at === null
  );
}

export function DetailMenuDialog({
  selectedCylinder,
  isDetailMenuOpen,
  detailError,
  contractList,
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
  const currentContract = selectedCylinder
    ? contractList.find((contract) =>
        isActiveContractForCylinder(contract, selectedCylinder.id)
      ) ?? null
    : null;
  const hasContractHistory = contractList.length > 0;

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
              <div><span className="text-muted-foreground">Contrato actual:</span>{' '}
                {currentContract === null ? (
                  <span className="text-muted-foreground">Sin contrato activo</span>
                ) : (
                  <span>
                    {currentContract.contract_number || "Sin Nro"}{" "}
                    <ContractStatusBadge status={currentContract.status} />
                  </span>
                )}
              </div>
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
                <CardTitle>Contrato asignado</CardTitle>
                <CardDescription>Relacion contractual actual del envase y su contexto historico.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {canContractView && currentContract ? (
                  <div className="rounded-lg border border-border bg-surface p-4 text-sm text-foreground">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-medium">{currentContract.contract_number || "Sin Nro"}</span>
                      <ContractStatusBadge status={currentContract.status} />
                    </div>
                    <div className="mt-2 grid gap-2 md:grid-cols-2">
                      <div><span className="text-muted-foreground">Tipo:</span> {currentContract.contract_type}</div>
                      <div><span className="text-muted-foreground">Cliente:</span> {currentContract.customer_name || currentContract.customer_id}</div>
                      <div><span className="text-muted-foreground">Inicio:</span> {formatDate(currentContract.start_date) || "-"}</div>
                      <div><span className="text-muted-foreground">Fin:</span> {formatDate(currentContract.end_date) || "-"}</div>
                    </div>
                  </div>
                ) : (
                  <div className="rounded-lg border border-dashed border-border bg-surface p-4 text-sm text-muted-foreground">
                    Este envase no tiene contrato activo asignado.
                  </div>
                )}

                {canContractView && hasContractHistory ? (
                  <p className="text-xs text-muted-foreground">
                    Historial contractual detectado: {contractList.length} registro(s) relacionado(s) con este envase.
                  </p>
                ) : null}

                {currentContract === null && canContractCreate ? (
                  <div className="flex justify-end">
                    <button
                      type="button"
                      onClick={openCreateContractDialog}
                      className="rounded-lg border border-border bg-surface px-4 py-2 text-sm text-foreground transition hover:border-ring hover:bg-surface-alt"
                    >
                      Crear contrato desde este envase
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
