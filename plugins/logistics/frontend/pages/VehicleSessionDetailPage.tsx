import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { useMutation, useQuery, useQueryClient } from "../../../../apps/web/src/lib/react-query";
import { ApiError } from "../../../../apps/web/src/shared/api/client";
import { Button } from "../../../../apps/web/src/shared/ui/button";
import { Tabs } from "../../../../apps/web/src/shared/ui/tabs";
import { listBalances, stockKeys } from "../../../stock/frontend/api";
import { ProductSearchDialog } from "../../../productos/frontend/components/ProductSearchDialog";
import {
  closeVehicleSession,
  confirmLoad,
  countSessionReconciliation,
  departSession,
  getLoadPlan,
  getSessionReconciliation,
  getVehicleSession,
  logisticsKeys,
  markSessionReady,
  markSessionReturning,
  returnRemaining,
  startLoadingSession,
  upsertLoadPlan,
} from "../api";
import { SessionHistoryTab } from "../components/vehicle-sessions/SessionHistoryTab";
import {
  type EditableLoadPlanItem,
  SessionLoadTab,
} from "../components/vehicle-sessions/SessionLoadTab";
import { SessionReconciliationTab } from "../components/vehicle-sessions/SessionReconciliationTab";
import { SessionRouteTab } from "../components/vehicle-sessions/SessionRouteTab";
import { SessionStepper } from "../components/vehicle-sessions/SessionStepper";
import { SessionSummaryTab } from "../components/vehicle-sessions/SessionSummaryTab";
import { SessionWorkspaceHeader } from "../components/vehicle-sessions/SessionWorkspaceHeader";
import { LogisticsSection } from "../components/LogisticsSection";

type VehicleSessionDetailPageProps = {
  sessionIdOverride?: string;
  embedded?: boolean;
  onClose?: () => void;
};

type StepperError = {
  type: "technical" | "business";
  message: string;
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
  const [tab, setTab] = useState("summary");
  const [error, setError] = useState<StepperError | null>(null);
  const [loadPlanItems, setLoadPlanItems] = useState<EditableLoadPlanItem[]>([]);
  const [showProductSearch, setShowProductSearch] = useState(false);
  const [counts, setCounts] = useState<Record<string, string>>({});

  const sessionQuery = useQuery({
    queryKey: logisticsKeys.vehicleSessions.detail(sessionId),
    queryFn: () => getVehicleSession(sessionId),
    enabled: Boolean(sessionId),
  });
  const loadPlanQuery = useQuery({
    queryKey: logisticsKeys.loadPlans.detail(sessionId),
    queryFn: () => getLoadPlan(sessionId),
    enabled: Boolean(sessionId),
  });
  const reconciliationQuery = useQuery({
    queryKey: logisticsKeys.reconciliation.detail(sessionId),
    queryFn: () => getSessionReconciliation(sessionId),
    enabled: Boolean(sessionId),
  });

  const session = sessionQuery.data;

  const originBalancesKey = session?.origin_warehouse_id
    ? stockKeys.balances.list({ warehouse_id: session.origin_warehouse_id, limit: "200" })
    : ["stock", "origin-none"];
  const mobileBalancesKey = session?.mobile_warehouse_id
    ? stockKeys.balances.list({ warehouse_id: session.mobile_warehouse_id, limit: "200" })
    : ["stock", "mobile-none"];

  const originBalancesQuery = useQuery({
    queryKey: originBalancesKey,
    queryFn: () => listBalances({ warehouse_id: session!.origin_warehouse_id, limit: "200" }),
    enabled: Boolean(session?.origin_warehouse_id),
  });
  const mobileBalancesQuery = useQuery({
    queryKey: mobileBalancesKey,
    queryFn: () => listBalances({ warehouse_id: session!.mobile_warehouse_id, limit: "200" }),
    enabled: Boolean(session?.mobile_warehouse_id),
  });

  useEffect(() => {
    if (!loadPlanQuery.data) {
      return;
    }
    setLoadPlanItems(
      loadPlanQuery.data.items.map((item) => ({
        product_id: item.product_id,
        product_name: item.product_name,
        planned_quantity: String(item.planned_quantity),
      }))
    );
  }, [loadPlanQuery.data]);

  useEffect(() => {
    if (!reconciliationQuery.data) {
      return;
    }
    setCounts(
      Object.fromEntries(
        reconciliationQuery.data.lines.map((line) => [
          line.product_id,
          line.counted_quantity != null
            ? String(line.counted_quantity)
            : String(line.expected_quantity),
        ])
      )
    );
  }, [reconciliationQuery.data]);

  async function invalidateAll() {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: logisticsKeys.vehicleSessions.detail(sessionId) }),
      queryClient.invalidateQueries({ queryKey: logisticsKeys.vehicleSessions.all() }),
      queryClient.invalidateQueries({ queryKey: logisticsKeys.loadPlans.detail(sessionId) }),
      queryClient.invalidateQueries({ queryKey: logisticsKeys.reconciliation.detail(sessionId) }),
      queryClient.invalidateQueries({ queryKey: mobileBalancesKey }),
      queryClient.invalidateQueries({ queryKey: originBalancesKey }),
    ]);
  }

  const startLoadingMutation = useMutation({
    mutationFn: () => startLoadingSession(sessionId),
    onSuccess: invalidateAll,
  });
  const readyMutation = useMutation({
    mutationFn: () => markSessionReady(sessionId),
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
          source_warehouse_id: session?.origin_warehouse_id,
        })),
      }),
    onSuccess: invalidateAll,
  });
  const confirmLoadMutation = useMutation({
    mutationFn: () => confirmLoad(sessionId),
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
    onSuccess: invalidateAll,
  });
  const closeMutation = useMutation({
    mutationFn: () => closeVehicleSession(sessionId),
    onSuccess: async () => {
      await invalidateAll();
      if (embedded) {
        onClose?.();
        return;
      }
      navigate("/app/logistics/vehicle-sessions");
    },
  });

  const mobileRows = mobileBalancesQuery.data?.items ?? [];
  const isPending =
    startLoadingMutation.isPending ||
    readyMutation.isPending ||
    departMutation.isPending ||
    returningMutation.isPending ||
    savePlanMutation.isPending ||
    confirmLoadMutation.isPending ||
    returnMutation.isPending ||
    countMutation.isPending ||
    closeMutation.isPending;

  const TRANSITION_ACTIONS: Partial<Record<string, () => Promise<unknown>>> = {
    DRAFT: startLoadingMutation.mutateAsync,
    LOADING: readyMutation.mutateAsync,
    READY_TO_DEPART: departMutation.mutateAsync,
    OUTBOUND: returningMutation.mutateAsync,
    RETURNING: returnMutation.mutateAsync,
    AWAITING_RECONCILIATION: closeMutation.mutateAsync,
  };

  async function runAction(action?: () => Promise<unknown>) {
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
        });
        return;
      }
      setError({ type: "technical", message: "Error del servidor. Intente nuevamente." });
    }
  }

  function handleStepperTabNavigation(targetTab: string) {
    setTab(targetTab);
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
      <div className="grid gap-4 xl:grid-cols-2 xl:items-start">
        <SessionWorkspaceHeader session={session} />

        <SessionStepper
          status={session.status}
          nextTransitionAllowed={session.next_transition_allowed}
          nextTransitionBlocker={session.next_transition_blocker}
          closedAt={session.closed_at}
          isPending={isPending}
          error={error}
          onNext={() => runAction(TRANSITION_ACTIONS[session.status])}
          onNavigateTab={handleStepperTabNavigation}
        />
      </div>

      <Tabs
        value={tab}
        onChange={setTab}
        tabs={[
          {
            value: "summary",
            label: "Resumen",
            content: <SessionSummaryTab session={session} mobileRows={mobileRows} />,
          },
          {
            value: "load",
            label: "Carga",
            content: (
              <SessionLoadTab
                session={session}
                loadPlanItems={loadPlanItems}
                setLoadPlanItems={setLoadPlanItems}
                originRows={originBalancesQuery.data?.items ?? []}
                onOpenProductSearch={() => setShowProductSearch(true)}
                onSavePlan={() => runAction(() => savePlanMutation.mutateAsync())}
                onConfirmLoad={() => runAction(() => confirmLoadMutation.mutateAsync())}
              />
            ),
          },
          {
            value: "route",
            label: "Ruta",
            content: <SessionRouteTab routeId={session.route_id} />,
          },
          {
            value: "reconciliation",
            label: "Conciliación",
            content: (
              <SessionReconciliationTab
                reconciliation={reconciliationQuery.data}
                counts={counts}
                setCounts={setCounts}
                onSaveCount={() => runAction(() => countMutation.mutateAsync())}
                onCloseSession={() => runAction(() => closeMutation.mutateAsync())}
              />
            ),
          },
          {
            value: "history",
            label: "Historial",
            content: <SessionHistoryTab history={session.history} />,
          },
        ]}
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
              },
            ];
          });
          setShowProductSearch(false);
        }}
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
