import { Dialog } from "../../../../../apps/web/src/shared/ui/dialog";
import { ProductSearchDialog } from "../../../../productos/frontend/components/ProductSearchDialog";
import { LoadSerialsDialog } from "./LoadSerialsDialog";
import { RouteCompositionCard } from "./RouteCompositionCard";
import { RouteIncidentsPanel } from "./RouteIncidentsPanel";
import { RouteOperationForm } from "./RouteOperationForm";
import { RouteOperationsCard } from "./RouteOperationsCard";
import { RouteStopProgressCard } from "./RouteStopProgressCard";
import { RouteStopResultsPanel } from "./RouteStopResultsPanel";
import { useSessionRouteTabController } from "./useSessionRouteTabController";

type Props = {
  controller: ReturnType<typeof useSessionRouteTabController>;
};

export function SessionRouteTabDialogs({ controller }: Props) {
  return (
    <>
      <Dialog
        open={controller.eventModalOpen}
        onClose={controller.closeEventModal}
        title={controller.correctionContext ? "Corrección operativa" : "Registrar evento de ruta"}
        description={
          controller.correctionContext
            ? "Reconcilia la realidad actual sin editar la operación original."
            : "Captura el hecho real de calle y, si aplica, su desvío en un solo flujo."
        }
        maxWidthClassName="max-w-[1400px]"
        zIndexClassName="z-[60]"
      >
        <RouteOperationForm
          canRegisterOperation={controller.canRegisterOperation}
          operationType={controller.operationType}
          routeStopId={controller.routeStopId}
          contextType={controller.contextType}
          customerId={controller.contextCustomerId}
          warehouseId={controller.contextWarehouseId}
          operationNotes={controller.operationNotes}
          draftItems={controller.draftItems}
          stopOptions={controller.stopOptions}
          customerOptions={controller.customerOptions}
          warehouseOptions={controller.warehouseOptions}
          operationOptions={controller.operationOptions}
          directionOptions={controller.directionOptions}
          correctionContext={controller.correctionContext}
          composition={controller.composition?.product_lines ?? []}
          fastSerialInput={controller.fastSerialInput}
          fastSerialError={controller.fastSerialError}
          isPending={controller.isSubmittingRouteEvent}
          onOperationTypeChange={controller.setOperationType}
          onRouteStopChange={controller.handleRouteStopChange}
          onContextTypeChange={controller.handleContextTypeChange}
          onCustomerChange={controller.setContextCustomerId}
          onWarehouseChange={controller.setContextWarehouseId}
          onOperationNotesChange={controller.setOperationNotes}
          onOpenProductSearch={controller.handleOpenProductSearch}
          onOpenSerialScanner={controller.setSerialItemIndex}
          onUpdateDraftItem={controller.updateDraftItem}
          onRemoveDraftItem={controller.removeDraftItem}
          onCancelCorrection={controller.cancelCorrection}
          onSubmit={controller.submitRouteEvent}
          onAddDeliveryProduct={controller.addDeliveryProduct}
          onFastSerialChange={controller.setFastSerialInput}
          onFastSerialSubmit={controller.submitFastSerial}
        />
      </Dialog>

      <Dialog
        open={controller.incidentsModalOpen}
        onClose={controller.closeIncidentsModal}
        title="Incidencias"
        description="Seguimiento de desvíos registrados en calle y acceso a resolución o corrección."
        maxWidthClassName="max-w-[1200px]"
        zIndexClassName="z-[60]"
      >
        <RouteIncidentsPanel
          incidentStopId={controller.incidentStopId}
          incidentRelatedOperationId={controller.incidentRelatedOperationId}
          incidentType={controller.incidentType}
          incidentNotes={controller.incidentNotes}
          stopOptions={controller.stopOptions}
          incidentOptions={controller.incidentOptions}
          relatedOperationOptions={controller.routeOperationOptions}
          incidents={controller.routeIncidents}
          resolveIncidentId={controller.resolveIncidentId}
          resolveNotes={controller.resolveNotes}
          isCreatePending={controller.isCreatingIncident}
          isResolvePending={controller.isResolvingIncident}
          correctionIncidentId={controller.correctionIncidentId}
          onIncidentStopChange={controller.setIncidentStopId}
          onIncidentRelatedOperationChange={controller.setIncidentRelatedOperationId}
          onIncidentTypeChange={controller.setIncidentType}
          onIncidentNotesChange={controller.setIncidentNotes}
          onCreateIncident={controller.createIncident}
          onStartResolve={controller.startResolveIncident}
          onResolveNotesChange={controller.setResolveNotes}
          onCancelResolve={controller.cancelResolveIncident}
          onConfirmResolve={controller.confirmResolveIncident}
          onStartCorrection={controller.startCorrection}
        />
      </Dialog>

      <Dialog
        open={controller.stopResultsModalOpen}
        onClose={controller.closeStopResultsModal}
        title="Resultados de parada"
        description="Cierre semántico y notas breves por parada dentro de la jornada."
        maxWidthClassName="max-w-[1200px]"
        zIndexClassName="z-[60]"
      >
        <RouteStopResultsPanel
          canManage={controller.canRegisterOperation}
          stopOptions={controller.stopOptions}
          results={controller.routeStopResults}
          isPending={controller.isSavingStopResult}
          onSave={controller.saveStopResult}
        />
      </Dialog>

      <Dialog
        open={controller.operationsModalOpen}
        onClose={controller.closeOperationsModal}
        title="Operaciones confirmadas"
        description="Registro inmutable de lo que ya ocurrió en la calle."
        maxWidthClassName="max-w-[1200px]"
        zIndexClassName="z-[60]"
      >
        <RouteOperationsCard operations={controller.routeOperations} />
      </Dialog>

      <Dialog
        open={controller.stopProgressModalOpen}
        onClose={controller.closeStopProgressModal}
        title="Progreso de parada"
        description="Estado derivado y avance operativo de las paradas de la ruta."
        maxWidthClassName="max-w-[1200px]"
        zIndexClassName="z-[60]"
      >
        <RouteStopProgressCard stopOptions={controller.stopOptions} progress={controller.routeStopProgress} />
      </Dialog>

      <Dialog
        open={controller.compositionModalOpen}
        onClose={controller.closeCompositionModal}
        title="Composición vigente"
        description="Proyección operativa actual de lo que el vehículo transporta en este momento."
        maxWidthClassName="max-w-[1200px]"
        zIndexClassName="z-[60]"
      >
        <RouteCompositionCard composition={controller.composition} />
      </Dialog>

      <LoadSerialsDialog
        open={Boolean(controller.serialDialogItem)}
        sessionId={controller.sessionId}
        item={controller.serialDialogItem}
        selectionContext={controller.operationType === "DELIVERY" ? "LOAD_PLAN" : "ROUTE_PICKUP"}
        allowCreateFallback={false}
        onClose={controller.closeSerialDialog}
        onSelectionCountChange={(_productId, selectedCount) => controller.handleSerialSelectionCountChange(selectedCount)}
      />

      <ProductSearchDialog
        open={controller.showProductSearch}
        onOpenChange={controller.setShowProductSearch}
        onSelect={controller.handleProductSelected}
      />
    </>
  );
}
