import { Alert } from "../../../../../apps/web/src/shared/ui/alert";
import { Badge } from "../../../../../apps/web/src/shared/ui/badge";
import { Button } from "../../../../../apps/web/src/shared/ui/button";
import { cn } from "../../../../../apps/web/src/shared/ui/cn";
import {
  AUTO_ACTION_HINTS,
  MANUAL_ACTION_LABELS,
  type SessionContextKey,
  SESSION_STEPS,
  STATUS_PHRASE,
  STEPPER_ACTIONABLE_STATUSES,
} from "./session-ui-map";

type SessionStepperProps = {
  status: string;
  nextTransitionAllowed: boolean;
  nextTransitionBlocker: string | null;
  closedAt: string | null;
  isPending: boolean;
  error: { type: "technical" | "business"; message: string } | null;
  onNext: () => void;
  onOpenContext: (context: SessionContextKey) => void;
};

function getCurrentStepIndex(status: string) {
  if (status === "CLOSED") {
    return SESSION_STEPS.length - 1;
  }
  return Math.max(
    SESSION_STEPS.findIndex((step) => step.status === status),
    0
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
  onOpenContext,
}: SessionStepperProps) {
  const currentIndex = getCurrentStepIndex(status);
  const isClosed = status === "CLOSED";
  const isCancelled = status === "CANCELLED";
  const canTriggerManually = STEPPER_ACTIONABLE_STATUSES.has(status);
  const currentLabel =
    status === "CLOSED"
      ? "Cerrada"
      : status === "CANCELLED"
        ? "Cancelada"
        : (SESSION_STEPS[currentIndex]?.label ?? status);

  return (
    <div className="space-y-6 rounded-2xl border bg-card p-5 shadow-sm sm:p-6">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-muted-foreground">
            Ciclo operativo
          </p>
          <p className="text-sm text-muted-foreground sm:text-base">
            El estado real y sus bloqueos vienen del backend.
          </p>
        </div>
        {isCancelled ? (
          <Badge className="border-destructive/30 bg-destructive/10 text-destructive">
            Cancelada
          </Badge>
        ) : null}
      </div>

      <div className="overflow-x-auto pb-1">
        <div className="flex min-w-max items-start gap-0 px-1">
          {SESSION_STEPS.map((step, index) => {
            const isCompleted = isClosed || index < currentIndex;
            const isCurrent = !isClosed && index === currentIndex;
            const isReachable = isClosed || index <= currentIndex;

            return (
              <div key={step.status} className="flex min-w-[144px] flex-1 items-start sm:min-w-[156px]">
                <button
                  type="button"
                  onClick={() => {
                    if (!isReachable) {
                      return;
                    }
                    onOpenContext(step.context);
                  }}
                  disabled={!isReachable}
                  className={cn(
                    "flex flex-col items-center gap-2 rounded-xl px-2 py-1 text-center transition",
                    isReachable ? "hover:bg-accent/50" : "cursor-not-allowed opacity-70"
                  )}
                >
                  <span
                    className={cn(
                      "flex h-10 w-10 items-center justify-center rounded-full text-sm font-bold transition sm:h-11 sm:w-11",
                      isCompleted && "bg-green-500 text-white",
                      isCurrent && "bg-primary text-primary-foreground ring-4 ring-primary/20",
                      !isCompleted && !isCurrent && "bg-muted text-muted-foreground"
                    )}
                  >
                    {index + 1}
                  </span>
                  <span
                    className={cn(
                      "max-w-[112px] text-sm font-semibold leading-tight",
                      !isCompleted && !isCurrent && "text-muted-foreground"
                    )}
                  >
                    {step.label}
                  </span>
                  <span className="max-w-[128px] text-[11px] leading-tight text-muted-foreground sm:text-xs">
                    {STATUS_PHRASE[step.status]}
                  </span>
                </button>
                {index < SESSION_STEPS.length - 1 ? (
                  <div
                    className={cn(
                      "mt-5 h-0.5 min-w-6 flex-1",
                      isClosed || index < currentIndex ? "bg-green-500" : "bg-muted"
                    )}
                  />
                ) : null}
              </div>
            );
          })}
        </div>
      </div>

      <div className="rounded-2xl bg-muted/35 px-4 py-4 text-center sm:px-5">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-muted-foreground">
          Estado actual
        </p>
        <p className="mt-1 text-xl font-semibold tracking-tight text-foreground">
          {currentLabel}
        </p>
        <p className="mt-2 text-sm text-muted-foreground sm:text-base">
          {AUTO_ACTION_HINTS[status] ?? STATUS_PHRASE[status]}
        </p>
      </div>

      {status === "CLOSED" ? (
        <p className="text-center text-sm text-muted-foreground">
          Jornada finalizada el {closedAt ? new Date(closedAt).toLocaleString() : "sin fecha registrada"}
        </p>
      ) : !canTriggerManually ? (
        <p className="text-center text-sm text-muted-foreground">
          {AUTO_ACTION_HINTS[status] ?? STATUS_PHRASE[status]}
        </p>
      ) : (
        <div className="flex justify-center">
          <Button
            disabled={isPending || isCancelled || !nextTransitionAllowed}
            onClick={onNext}
            title={nextTransitionBlocker ?? undefined}
            className="px-5 py-2.5 text-sm sm:px-6 sm:py-3 sm:text-base"
          >
            {isPending ? <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-current border-t-transparent" /> : null}
            {MANUAL_ACTION_LABELS[status] ?? "Estado no soportado"}
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
