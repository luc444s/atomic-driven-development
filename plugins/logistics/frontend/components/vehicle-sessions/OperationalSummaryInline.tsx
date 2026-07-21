import { Badge } from "../../../../../apps/web/src/shared/ui/badge";
import { cn } from "../../../../../apps/web/src/shared/ui/cn";

import {
  type SessionOperationalSummary,
  VEHICLE_SESSION_STATUS_LABELS,
  type VehicleSessionDetail,
} from "../../api";
import { formatWaybillSyncStatus } from "./jornada-labels";
import { VehicleSessionStatusBadge } from "./VehicleSessionStatusBadge";

type Props = {
  session: VehicleSessionDetail;
  summary: SessionOperationalSummary | null;
  isLoading: boolean;
};

function SummaryToneBadge({ label, tone }: { label: string; tone: "healthy" | "attention" | "blocked" | "neutral" }) {
  return (
    <Badge
      className={cn(
        tone === "healthy" && "border-emerald-500/30 bg-emerald-500/10 text-emerald-700 dark:text-emerald-200",
        tone === "attention" && "border-amber-500/30 bg-amber-500/10 text-amber-700 dark:text-amber-200",
        tone === "blocked" && "border-rose-500/30 bg-rose-500/10 text-rose-700 dark:text-rose-200",
        tone === "neutral" && "border-slate-500/30 bg-slate-500/10 text-slate-700 dark:text-slate-200"
      )}
    >
      {label}
    </Badge>
  );
}

export function OperationalSummaryInline({ session, summary, isLoading }: Props) {
  const items = [
    { label: "Conductor", value: session.driver_name },
    { label: "Ruta", value: session.route_id ?? "Sin ruta" },
    { label: "Apertura", value: new Date(session.opened_at).toLocaleString() },
    { label: "Peso planificado", value: `${session.planned_weight_kg ?? 0} kg` },
    { label: "Peso confirmado", value: `${session.loaded_weight_kg ?? 0} kg` },
    summary
      ? {
          label: "Paradas",
          value: `${summary.stop_counters.completed}/${summary.stop_counters.total} completas · ${summary.stop_counters.partial} parciales · ${summary.stop_counters.failed} fallidas`,
        }
      : { label: "Paradas", value: isLoading ? "Cargando..." : "Sin pulso operativo" },
    summary
      ? {
          label: "Incidencias abiertas",
          value: `${summary.incidents.open_total} activas · ${summary.incidents.corrected_total} corregidas`,
        }
      : { label: "Incidencias abiertas", value: isLoading ? "Cargando..." : "Sin pulso operativo" },
    summary
      ? {
          label: "Carga actual",
          value: `${summary.composition.total_products} productos · ${summary.composition.total_units} unidades · ${summary.composition.total_weight_kg ?? 0} kg`,
        }
      : { label: "Carga actual", value: isLoading ? "Cargando..." : "Sin pulso operativo" },
    summary
      ? {
          label: "Carta Porte",
          value:
            summary.waybill.active_version != null
              ? `${formatWaybillSyncStatus(summary.waybill.sync_status)} · v${summary.waybill.active_version}`
              : formatWaybillSyncStatus(summary.waybill.sync_status),
        }
      : { label: "Carta Porte", value: isLoading ? "Cargando..." : "Sin pulso operativo" },
    summary
      ? {
          label: "Última actividad",
          value: summary.route_activity.last_activity
            ? `${summary.route_activity.last_activity.label} · ${new Date(summary.route_activity.last_activity.at).toLocaleString()}`
            : "Sin actividad relevante todavía.",
        }
      : { label: "Última actividad", value: session.last_activity ?? "Sin actividad aún" },
  ];

  return (
    <div className="space-y-3 rounded-2xl bg-muted/35 px-4 py-4 sm:px-5">
      <div className="flex flex-wrap items-center gap-3">
        <p className="text-lg font-semibold tracking-tight text-foreground">{session.vehicle_plate}</p>
        <VehicleSessionStatusBadge status={session.status} />
        {summary ? (
          <SummaryToneBadge
            label={summary.health_status === "HEALTHY" ? "Jornada sana" : summary.health_status === "ATTENTION" ? "Jornada en atención" : "Jornada bloqueada"}
            tone={summary.health_status === "HEALTHY" ? "healthy" : summary.health_status === "ATTENTION" ? "attention" : "blocked"}
          />
        ) : null}
        {summary ? (
          <SummaryToneBadge
            label={summary.data_completeness === "FULL" ? "Lectura completa" : "Lectura parcial"}
            tone={summary.data_completeness === "FULL" ? "neutral" : "attention"}
          />
        ) : null}
      </div>
      <p className="text-sm text-muted-foreground sm:text-base">
        {summary
          ? `${VEHICLE_SESSION_STATUS_LABELS[session.status] ?? session.status} · ${summary.route_activity.confirmed_operations} operaciones confirmadas`
          : "Leyendo el pulso operativo derivado de la jornada..."}
      </p>
      <div className="grid gap-x-6 gap-y-3 text-sm sm:grid-cols-2 xl:grid-cols-4">
        {items.map((item) => (
          <div key={item.label} className="min-w-0">
            <p className="text-[11px] uppercase tracking-wide text-muted-foreground">{item.label}</p>
            <p className="font-medium text-foreground">{item.value}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
