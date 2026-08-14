import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { useMutation, useQuery, useQueryClient } from "../../../../apps/web/src/lib/react-query";
import { ApiError } from "../../../../apps/web/src/shared/api/client";
import { Button } from "../../../../apps/web/src/shared/ui/button";
import { ConfirmDialog } from "../../../../apps/web/src/shared/ui/confirm-dialog";
import { ProductSearchDialog } from "../../../productos/frontend/components/ProductSearchDialog";
import {
  cancelSession,
  confirmAndReady,
  countSessionReconciliation,
  departSession,
  getSessionConsoleContext,
  logisticsKeys,
  markSessionReturning,
  returnRemaining,
  startLoadingSession,
  upsertLoadPlan,
} from "../api";
import {
  type EditableLoadPlanItem,
} from "../components/vehicle-sessions/SessionLoadTab";
import {
  buildEditableLoadPlanItems,
  buildReconciliationCounts,
} from "../components/vehicle-sessions/session-console-view";
import { VehicleSessionConsole } from "../components/vehicle-sessions/VehicleSessionConsole";
import { LoadModal } from "../components/vehicle-sessions/modals/LoadModal";
import { ReconciliationModal } from "../components/vehicle-sessions/modals/ReconciliationModal";
import { RouteModal } from "../components/vehicle-sessions/modals/RouteModal";
import {
  type SessionContextKey,
  STEPPER_ACTIONABLE_STATUSES,
} from "../components/vehicle-sessions/session-ui-map";
import { LogisticsSection } from "../components/LogisticsSection";

type VehicleSessionDetailPageProps = {
  sessionIdOverride?: string;
  embedded?: boolean;
  onClose?: () => void;
};

type SessionActionError = {
  type: "technical" | "business";
  message: string;
  scope: "stepper" | "cancel" | SessionContextKey;
};

export function VehicleSessionDetailPage({
  sessionIdOverride,
  embedded = false,
  onClose,
}: VehicleSessionDetailPageProps = {}) {
  const { sessionId: routeSessionId = "" } = useParams();
  const sessionId = sessionIdOverride ?? routeSessionId;
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [activeModal, setActiveModal] = useState<SessionContextKey | null>(null);
  const [error, setError] = useState<SessionActionError | null>(null);
  const [cancelConfirmOpen, setCancelConfirmOpen] = useState(false);
  const [loadPlanItems, setLoadPlanItems] = useState<EditableLoadPlanItem[]>([]);
  const [showProductSearch, setShowProductSearch] = useState(false);
  const [counts, setCounts] = useState<Record<string, string>>({});

  const consoleContextQuery = useQuery({
    queryKey: logisticsKeys.vehicleSessions.consoleContext(sessionId),
    queryFn: () => getSessionConsoleContext(sessionId),
    enabled: Boolean(sessionId),
  });

  const context = consoleContextQuery.data;
  const session = context?.session;

  useEffect(() => {
    if (!context?.load_plan) {
      return;
    }
    setLoadPlanItems(buildEditableLoadPlanItems(context.load_plan));
  }, [context?.load_plan]);

  useEffect(() => {
    if (!context?.reconciliation) {
      return;
    }
    setCounts(buildReconciliationCounts(context.reconciliation));
  }, [context?.reconciliation]);

  async function invalidateAll() {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: logisticsKeys.vehicleSessions.all() }),
      queryClient.invalidateQueries({ queryKey: logisticsKeys.vehicleSessions.consoleContext(sessionId) }),
      queryClient.invalidateQueries({ queryKey: logisticsKeys.vehicleSessions.routeContext(sessionId) }),
    ]);
  }

  const startLoadingMutation = useMutation({
    mutationFn: () => startLoadingSession(sessionId),
    onSuccess: invalidateAll,
  });
  const departMutation = useMutation({
    mutationFn: () => departSession(sessionId),
    onSuccess: invalidateAll,
  });
  const returningMutation = useMutation({
    mutationFn: () => markSessionReturning(sessionId),
    onSuccess: invalidateAll,
  });
  const savePlanMutation = useMutation({
    mutationFn: () =>
      upsertLoadPlan(sessionId, {
        items: loadPlanItems.map((item) => ({
          product_id: item.product_id,
          planned_quantity: Number(item.planned_quantity || "0"),
          source_warehouse_id: item.source_warehouse_id || session?.origin_warehouse_id,
        })),
      }),
    onSuccess: invalidateAll,
  });
  const confirmLoadMutation = useMutation({
    mutationFn: () => confirmAndReady(sessionId),
    onSuccess: invalidateAll,
  });
  const returnMutation = useMutation({
    mutationFn: () => returnRemaining(sessionId),
    onSuccess: invalidateAll,
  });
  const countMutation = useMutation({
    mutationFn: () =>
      countSessionReconciliation(sessionId, {
        items: Object.entries(counts).map(([product_id, counted_quantity]) => ({
          product_id,
          counted_quantity: Number(counted_quantity || "0"),
        })),
      }),
    onSuccess: async (result) => {
      await invalidateAll();
      if (result.status !== "CLOSED") {
        return;
      }
      setActiveModal(null);
      if (embedded) {
        onClose?.();
        return;
      }
    },
  });
  const cancelMutation = useMutation({
    mutationFn: () => cancelSession(sessionId),
    onSuccess: async () => {
      setCancelConfirmOpen(false);
      setActiveModal(null);
      await invalidateAll();
    },
  });

  const mobileRows = context?.mobile_balances?.items ?? [];
  const originRows = context?.origin_balances?.items ?? [];
  const originSerializedRows = context?.origin_serialized ?? [];
  const isPending =
    startLoadingMutation.isPending ||
    departMutation.isPending ||
    returningMutation.isPending ||
    savePlanMutation.isPending ||
    confirmLoadMutation.isPending ||
    returnMutation.isPending ||
    countMutation.isPending ||
    cancelMutation.isPending;

  const TRANSITION_ACTIONS: Partial<Record<string, () => Promise<unknown>>> = {
    DRAFT: startLoadingMutation.mutateAsync,
    // TODO: reemplazar por evento GPS.
    READY_TO_DEPART: departMutation.mutateAsync,
    // TODO: reemplazar por evento GPS.
    OUTBOUND: returningMutation.mutateAsync,
    RETURNING: returnMutation.mutateAsync,
  };

  const isStepperActionStatus = session ? STEPPER_ACTIONABLE_STATUSES.has(session.status) : false;
  const stepperError = error?.scope === "stepper" ? error : null;
  const cancelError = error?.scope === "cancel" ? error.message : null;
  const loadPanelError = error?.scope === "load" ? error.message : null;
  const reconciliationPanelError =
    error?.scope === "reconciliation" ? error.message : null;

  async function runAction(action?: () => Promise<unknown>, scope: SessionActionError["scope"] = "stepper") {
    if (!action) {
      return;
    }
    setError(null);
    try {
      await action();
    } catch (cause) {
        if (cause instanceof ApiError) {
          setError({
            type: cause.status >= 500 ? "technical" : "business",
            message:
              cause.status >= 500 ? "Error del servidor. Intente nuevamente." : cause.message,
            scope,
          });
          return;
        }
      setError({
        type: "technical",
        message: "Error del servidor. Intente nuevamente.",
        scope,
      });
    }
  }

  function handleOpenContext(context: SessionContextKey) {
    setError(null);
    setActiveModal(context);
  }

  function handleCloseModal() {
    setActiveModal(null);
  }

  function handleOpenCancelConfirm() {
    setError(null);
    setCancelConfirmOpen(true);
  }

  function handleCloseCancelConfirm() {
    if (cancelMutation.isPending) {
      return;
    }
    setError(null);
    setCancelConfirmOpen(false);
  }

  function handleCloseLoadModal() {
    setShowProductSearch(false);
    handleCloseModal();
  }

  if (!session) {
    const loadingContent = null;
    if (embedded) {
      return loadingContent;
    }
    return (
      <LogisticsSection title="Jornada" description="Cargando jornada operativa...">
        {loadingContent}
      </LogisticsSection>
    );
  }

  const content = (
    <>
      <VehicleSessionConsole
        session={session}
        mobileRows={mobileRows}
        operationalSummary={context?.operational_summary ?? null}
        operationalSummaryLoading={consoleContextQuery.isLoading}
        cancellation={{
          canCancel: ["DRAFT", "LOADING", "READY_TO_DEPART"].includes(session.status),
          isPending: cancelMutation.isPending,
          onOpenConfirm: handleOpenCancelConfirm,
        }}
        stepper={{
          nextTransitionAllowed: session.next_transition_allowed,
          nextTransitionBlocker: session.next_transition_blocker,
          closedAt: session.closed_at,
          isPending,
          error: isStepperActionStatus ? stepperError : null,
          onNext: () => runAction(TRANSITION_ACTIONS[session.status], "stepper"),
          onOpenContext: handleOpenContext,
        }}
      />

      <LoadModal
        open={activeModal === "load"}
        onClose={handleCloseLoadModal}
        session={session}
        loadPlanItems={loadPlanItems}
        setLoadPlanItems={setLoadPlanItems}
        originRows={originRows}
        serializedRows={originSerializedRows}
        onOpenProductSearch={() => setShowProductSearch(true)}
        onSavePlan={() =>
          runAction(async () => {
            await savePlanMutation.mutateAsync();
            if (session.status !== "LOADING") {
              return;
            }
            await confirmLoadMutation.mutateAsync();
            handleCloseLoadModal();
          }, "load")
        }
        isPending={isPending}
        error={loadPanelError}
      />

      <RouteModal
        open={activeModal === "route"}
        onClose={handleCloseModal}
        sessionId={session.id}
        sessionStatus={session.status}
        routeId={session.route_id}
        routeDate={session.route_date}
        routeOriginLabel={session.route_origin_label}
        routeDestinationLabel={session.route_destination_label}
      />

      <ReconciliationModal
        open={activeModal === "reconciliation"}
        onClose={handleCloseModal}
        reconciliation={context?.reconciliation}
        counts={counts}
        setCounts={setCounts}
        onSaveCount={() => runAction(() => countMutation.mutateAsync(), "reconciliation")}
        isPending={isPending}
        error={reconciliationPanelError}
      />

      <ProductSearchDialog
        open={showProductSearch}
        onOpenChange={setShowProductSearch}
        onSelect={(product) => {
          setLoadPlanItems((current) => {
            if (current.some((item) => item.product_id === product.id)) {
              return current;
            }
            return [
              ...current,
              {
                product_id: product.id,
                product_name: `${product.sku} · ${product.name}`,
                planned_quantity: "1",
                source_warehouse_id: session.origin_warehouse_id,
                requires_serials: false,
                selected_serials_count: 0,
                serials_complete: true,
              },
            ];
          });
          setShowProductSearch(false);
        }}
      />

      <ConfirmDialog
        open={cancelConfirmOpen}
        onClose={handleCloseCancelConfirm}
        onConfirm={() => runAction(() => cancelMutation.mutateAsync(), "cancel")}
        title="Cancelar jornada"
        description={
          cancelError ??
          "La jornada quedará anulada y ya no podrá continuar su ciclo operativo. Esta acción solo aplica antes de salir a ruta."
        }
        confirmLabel="Sí, cancelar jornada"
        cancelLabel="Volver"
        destructive
        loading={cancelMutation.isPending}
      />
    </>
  );

  const backButton = !embedded ? (
    <Button
      variant="secondary"
      onClick={() => (onClose ? onClose() : navigate("/app/logistics/vehicle-sessions"))}
    >
      Volver
    </Button>
  ) : null;

  if (embedded) {
    return <div className="space-y-4">{content}</div>;
  }

  return (
    <LogisticsSection
      title={`Jornada ${session.vehicle_plate}`}
      description="Centro operativo de la jornada: carga, ruta, conciliación e historial."
      actions={backButton}
    >
      {content}
    </LogisticsSection>
  );
}
