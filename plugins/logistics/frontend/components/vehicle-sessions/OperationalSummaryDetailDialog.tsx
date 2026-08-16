import { Dialog } from "@systutor/shell/ui/dialog";
import type { SessionOperationalSummary } from "../../api";
import {
  formatDataCompleteness,
  formatHealthStatus,
  formatRouteIncidentType,
  formatStopOutcomeType,
  formatStopStatus,
  formatWaybillSyncStatus,
  STOP_STATUS_BORDER_COLORS,
} from "./jornada-labels";

const BLOCKING_REASON_LABELS: Record<string, string> = {
  FAILED_STOP: "Hay al menos una parada fallida.",
  WAYBILL_MISSING: "La carta porte todavia no existe donde ya deberia estar emitida.",
  NO_ROUTE_ASSIGNED: "La jornada ya requiere ruta, pero no tiene una asignada.",
};

const ATTENTION_REASON_LABELS: Record<string, string> = {
  PARTIAL_STOP: "Existen paradas parciales que requieren seguimiento.",
  OPEN_INCIDENT: "Existen incidencias abiertas pendientes de cierre o correccion.",
  WAYBILL_OUTDATED: "La carta porte esta desactualizada respecto de la realidad operativa.",
};

type Props = {
  open: boolean;
  summary: SessionOperationalSummary | null;
  onClose: () => void;
};

export function OperationalSummaryDetailDialog({ open, summary, onClose }: Props) {
  return (
    <Dialog
      open={open}
      onClose={onClose}
      title="Detalle operativo de jornada"
      description="Explica por que la jornada esta sana, en atencion o bloqueada."
      maxWidthClassName="max-w-4xl"
    >
      {!summary ? (
        <p className="text-sm text-muted-foreground">El resumen operativo todavia no esta disponible.</p>
      ) : (
        <div className="space-y-5">
          <section className="grid gap-3 md:grid-cols-3">
            <div className="rounded-xl border border-border p-4">
              <p className="text-xs uppercase tracking-wide text-muted-foreground">Salud</p>
              <p className="mt-1 text-lg font-semibold text-foreground">{formatHealthStatus(summary.health_status)}</p>
            </div>
            <div className="rounded-xl border border-border p-4">
              <p className="text-xs uppercase tracking-wide text-muted-foreground">Confiabilidad</p>
              <p className="mt-1 text-lg font-semibold text-foreground">{formatDataCompleteness(summary.data_completeness)}</p>
            </div>
            <div className="rounded-xl border border-border p-4">
              <p className="text-xs uppercase tracking-wide text-muted-foreground">Carta Porte</p>
              <p className="mt-1 text-lg font-semibold text-foreground">
                {formatWaybillSyncStatus(summary.waybill.sync_status)}
                {summary.waybill.active_version != null ? ` · v${summary.waybill.active_version}` : ""}
              </p>
            </div>
          </section>

          <section className="space-y-2">
            <p className="text-sm font-semibold text-foreground">Razones de bloqueo o atencion</p>
            {summary.blocking_reasons.length || summary.attention_reasons.length ? (
              <div className="space-y-2">
                {summary.blocking_reasons.map((reason) => (
                  <div key={reason} className="rounded-lg border border-rose-500/20 bg-rose-500/5 px-3 py-2 text-sm text-foreground">
                    <span className="font-medium">Bloqueo:</span> {BLOCKING_REASON_LABELS[reason] ?? reason}
                  </div>
                ))}
                {summary.attention_reasons.map((reason) => (
                  <div key={reason} className="rounded-lg border border-amber-500/20 bg-amber-500/5 px-3 py-2 text-sm text-foreground">
                    <span className="font-medium">Atencion:</span> {ATTENTION_REASON_LABELS[reason] ?? reason}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">Sin razones activas de bloqueo o atencion.</p>
            )}
          </section>

          <section className="space-y-2">
            <p className="text-sm font-semibold text-foreground">Paradas comprometidas</p>
            {summary.problematic_stops.length ? (
              <div className="space-y-2">
                {summary.problematic_stops.map((stop) => (
                  <div key={stop.route_stop_id} className={`rounded-lg border-r border-t border-b border-l-4 border-border ${STOP_STATUS_BORDER_COLORS[stop.progress_status] ?? "border-l-gray-400"} px-3 py-3 text-sm text-foreground`}>
                    <div className="font-medium">{stop.label}</div>
                    <div className="text-muted-foreground">
                      {formatStopStatus(stop.progress_status)} · Incidencias abiertas: {stop.open_incidents}
                      {stop.completion_percent != null ? ` · ${stop.completion_percent}%` : ""}
                      {stop.outcome_type ? ` · ${formatStopOutcomeType(stop.outcome_type)}` : ""}
                      {stop.last_operation_at ? ` · Última operación: ${new Date(stop.last_operation_at).toLocaleString()}` : ""}
                    </div>
                    {stop.driver_note ? <div className="mt-1 text-muted-foreground">{stop.driver_note}</div> : null}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">Sin paradas comprometidas.</p>
            )}
          </section>

          <section className="space-y-2">
            <p className="text-sm font-semibold text-foreground">Incidencias abiertas</p>
            {summary.open_incidents.length ? (
              <div className="space-y-2">
                {summary.open_incidents.map((incident) => (
                  <div key={incident.id} className="rounded-lg border border-border px-3 py-3 text-sm text-foreground">
                    <div className="font-medium">{formatRouteIncidentType(incident.type)}</div>
                    <div className="text-muted-foreground">
                      {incident.stop_label ?? "Sin parada"} · {new Date(incident.updated_at).toLocaleString()}
                    </div>
                    {incident.notes ? <div className="mt-1 text-muted-foreground">{incident.notes}</div> : null}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">Sin incidencias abiertas.</p>
            )}
          </section>

          <section className="grid gap-3 md:grid-cols-3">
            <div className="rounded-xl border border-border p-4">
              <p className="text-xs uppercase tracking-wide text-muted-foreground">Paradas</p>
              <p className="mt-1 text-sm text-foreground">
                {summary.stop_counters.completed}/{summary.stop_counters.total} completas · {summary.stop_counters.partial} parciales · {summary.stop_counters.failed} fallidas
              </p>
            </div>
            <div className="rounded-xl border border-border p-4">
              <p className="text-xs uppercase tracking-wide text-muted-foreground">Composición</p>
              <p className="mt-1 text-sm text-foreground">
                {summary.composition.total_products} prod · {summary.composition.total_units} und · {summary.composition.total_weight_kg ?? 0} kg
              </p>
            </div>
            <div className="rounded-xl border border-border p-4">
              <p className="text-xs uppercase tracking-wide text-muted-foreground">Última actividad</p>
              <p className="mt-1 text-sm text-foreground">
                {summary.route_activity.last_activity
                  ? `${summary.route_activity.last_activity.label} · ${new Date(summary.route_activity.last_activity.at).toLocaleString()}`
                  : "Sin actividad relevante todavía."}
              </p>
            </div>
          </section>
        </div>
      )}
    </Dialog>
  );
}
