import { Alert } from "../../../../../apps/web/src/shared/ui/alert";
import { Badge } from "../../../../../apps/web/src/shared/ui/badge";
import { Button } from "../../../../../apps/web/src/shared/ui/button";
import { cn } from "../../../../../apps/web/src/shared/ui/cn";

type SessionStepperProps = {
  status: string;
  nextTransitionAllowed: boolean;
  nextTransitionBlocker: string | null;
  closedAt: string | null;
  isPending: boolean;
  error: { type: "technical" | "business"; message: string } | null;
  onNext: () => void;
  onNavigateTab: (tab: string) => void;
};

const STEPS = [
  { status: "DRAFT", label: "Borrador", tab: "load" },
  { status: "LOADING", label: "Cargando", tab: "load" },
  { status: "READY_TO_DEPART", label: "Listo para salir", tab: "load" },
  { status: "OUTBOUND", label: "En ruta", tab: "route" },
  { status: "RETURNING", label: "De regreso", tab: "route" },
  { status: "AWAITING_RECONCILIATION", label: "Pend. conciliación", tab: "reconciliation" },
] as const;

const NEXT_LABELS: Record<string, string> = {
  DRAFT: "Siguiente: Cargando",
  LOADING: "Siguiente: Listo para salir",
  READY_TO_DEPART: "Siguiente: En ruta",
  OUTBOUND: "Siguiente: De regreso",
  RETURNING: "Siguiente: Pend. conciliación",
  AWAITING_RECONCILIATION: "Siguiente: Cerrar jornada",
  CANCELLED: "Jornada cancelada",
};

function getCurrentStepIndex(status: string) {
  return Math.max(
    STEPS.findIndex((step) => step.status === status),
    status === "CLOSED" || status === "CANCELLED" ? 0 : 0
  );
}

export function SessionStepper({
  status,
  nextTransitionAllowed,
  nextTransitionBlocker,
  closedAt,
  isPending,
  error,
  onNext,
  onNavigateTab,
}: SessionStepperProps) {
  const currentIndex = getCurrentStepIndex(status);
  const isClosed = status === "CLOSED";
  const isCancelled = status === "CANCELLED";

  return (
    <div className="space-y-4 rounded-lg border bg-card p-4">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-sm font-medium">Ciclo operativo</p>
          <p className="text-xs text-muted-foreground">El avance y sus bloqueos vienen del backend.</p>
        </div>
        {isCancelled ? (
          <Badge className="border-destructive/30 bg-destructive/10 text-destructive">
            Cancelada
          </Badge>
        ) : null}
      </div>

      <div className="overflow-x-auto pb-1">
        <div className="flex min-w-max items-start gap-0">
          {STEPS.map((step, index) => {
            const isCompleted = isClosed || index < currentIndex;
            const isCurrent = !isClosed && index === currentIndex;

            return (
              <div key={step.status} className="flex min-w-[116px] flex-1 items-start">
                <button
                  type="button"
                  onClick={() => onNavigateTab(step.tab)}
                  className="flex flex-col items-center gap-2 text-center"
                >
                  <span
                    className={cn(
                      "flex h-8 w-8 items-center justify-center rounded-full text-sm font-bold transition",
                      isCompleted && "bg-green-500 text-white",
                      isCurrent && "bg-primary text-primary-foreground ring-2 ring-primary/40",
                      !isCompleted && !isCurrent && "bg-muted text-muted-foreground"
                    )}
                  >
                    {index + 1}
                  </span>
                  <span
                    className={cn(
                      "max-w-[96px] text-xs font-medium leading-tight",
                      !isCompleted && !isCurrent && "text-muted-foreground"
                    )}
                  >
                    {step.label}
                  </span>
                </button>
                {index < STEPS.length - 1 ? (
                  <div
                    className={cn(
                      "mt-4 h-0.5 min-w-4 flex-1",
                      isClosed || index < currentIndex ? "bg-green-500" : "bg-muted"
                    )}
                  />
                ) : null}
              </div>
            );
          })}
        </div>
      </div>

      {status === "CLOSED" ? (
        <p className="text-center text-sm text-muted-foreground">
          Jornada finalizada el {closedAt ? new Date(closedAt).toLocaleString() : "sin fecha registrada"}
        </p>
      ) : (
        <div className="flex justify-center">
          <Button
            disabled={isPending || isCancelled || !nextTransitionAllowed}
            onClick={onNext}
            title={nextTransitionBlocker ?? undefined}
          >
            {isPending ? <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-current border-t-transparent" /> : null}
            {NEXT_LABELS[status] ?? "Estado no soportado"}
          </Button>
        </div>
      )}

      {error ? (
        <Alert title={error.type === "business" ? "No se pudo avanzar" : "Error del servidor"}>
          {error.message}
        </Alert>
      ) : null}
    </div>
  );
}
