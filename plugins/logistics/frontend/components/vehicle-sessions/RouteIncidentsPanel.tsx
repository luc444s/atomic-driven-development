import { Button } from "../../../../../apps/web/src/shared/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "../../../../../apps/web/src/shared/ui/card";
import { Input } from "../../../../../apps/web/src/shared/ui/input";
import { Select } from "../../../../../apps/web/src/shared/ui/select";
import type { RouteIncident } from "../../api";
import { formatRouteIncidentStatus, formatRouteIncidentType } from "./jornada-labels";
import type { RouteSelectOption } from "./RouteOperationForm";

const RECONCILABLE_INCIDENT_TYPES = new Set([
  "QUANTITY_MISMATCH",
  "WRONG_PRODUCT",
  "EXCESS_DELIVERY",
  "MISSING_PICKUP",
]);

type Props = {
  incidentStopId: string;
  incidentRelatedOperationId: string;
  incidentType: string;
  incidentNotes: string;
  stopOptions: RouteSelectOption[];
  incidentOptions: RouteSelectOption[];
  relatedOperationOptions: RouteSelectOption[];
  incidents: RouteIncident[];
  resolveIncidentId: string | null;
  resolveNotes: string;
  isCreatePending: boolean;
  isResolvePending: boolean;
  correctionIncidentId: string | null;
  onIncidentStopChange: (value: string) => void;
  onIncidentRelatedOperationChange: (value: string) => void;
  onIncidentTypeChange: (value: string) => void;
  onIncidentNotesChange: (value: string) => void;
  onCreateIncident: () => void;
  onStartResolve: (incidentId: string) => void;
  onResolveNotesChange: (value: string) => void;
  onCancelResolve: () => void;
  onConfirmResolve: (incidentId: string) => void;
  onStartCorrection: (incident: RouteIncident) => void;
};

export function RouteIncidentsPanel({
  incidentStopId,
  incidentRelatedOperationId,
  incidentType,
  incidentNotes,
  stopOptions,
  incidentOptions,
  relatedOperationOptions,
  incidents,
  resolveIncidentId,
  resolveNotes,
  isCreatePending,
  isResolvePending,
  correctionIncidentId,
  onIncidentStopChange,
  onIncidentRelatedOperationChange,
  onIncidentTypeChange,
  onIncidentNotesChange,
  onCreateIncident,
  onStartResolve,
  onResolveNotesChange,
  onCancelResolve,
  onConfirmResolve,
  onStartCorrection,
}: Props) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Incidencias</CardTitle>
        <CardDescription>
          Seguimiento de desvíos ya registrados en calle. La corrección sigue entrando como operación nueva.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-4 md:grid-cols-3">
          <label className="space-y-2 text-sm text-foreground">
            <span>Parada</span>
            <Select value={incidentStopId} onChange={onIncidentStopChange} options={stopOptions} placeholder="Sin parada" />
          </label>
          <label className="space-y-2 text-sm text-foreground">
            <span>Operación relacionada</span>
            <Select
              value={incidentRelatedOperationId}
              onChange={onIncidentRelatedOperationChange}
              options={relatedOperationOptions}
              placeholder="Sin operación"
            />
          </label>
          <label className="space-y-2 text-sm text-foreground">
            <span>Tipo</span>
            <Select value={incidentType} onChange={onIncidentTypeChange} options={incidentOptions} />
          </label>
        </div>
        <label className="space-y-2 text-sm text-foreground">
          <span>Notas</span>
          <Input value={incidentNotes} onChange={(event) => onIncidentNotesChange(event.target.value)} placeholder="Describe el desvío detectado" />
        </label>
        <div className="flex justify-end">
          <Button disabled={isCreatePending} onClick={onCreateIncident}>
            {isCreatePending ? "Registrando..." : "Registrar incidencia"}
          </Button>
        </div>

        <div className="space-y-2 border-t border-border pt-3">
          {incidents.length ? (
            incidents.map((incident) => {
              const stopLabel = incident.route_stop_id
                ? stopOptions.find((option) => option.value === incident.route_stop_id)?.label ?? incident.route_stop_id
                : "Sin parada";
              const relatedOperationLabel = incident.related_operation_id
                ? relatedOperationOptions.find((option) => option.value === incident.related_operation_id)?.label ?? incident.related_operation_id
                : null;
              const correctiveOperationLabel = incident.corrective_operation_id
                ? relatedOperationOptions.find((option) => option.value === incident.corrective_operation_id)?.label ?? incident.corrective_operation_id
                : null;
              const canCorrect = incident.status === "OPEN" && RECONCILABLE_INCIDENT_TYPES.has(incident.type);
              const isResolving = resolveIncidentId === incident.id;
              const isCorrectionActive = correctionIncidentId === incident.id;
              return (
                <div key={incident.id} className="rounded-lg border border-border px-3 py-2 text-sm text-foreground">
                  <div className="flex items-start justify-between gap-3">
                    <div className="space-y-1">
                      <div className="font-medium">
                        {formatRouteIncidentType(incident.type)} · {formatRouteIncidentStatus(incident.status)}
                      </div>
                      <div className="text-muted-foreground">{stopLabel}</div>
                      {relatedOperationLabel ? (
                        <div className="text-muted-foreground">Operación original: {relatedOperationLabel}</div>
                      ) : null}
                      {correctiveOperationLabel ? (
                        <div className="text-muted-foreground">Operación correctiva: {correctiveOperationLabel}</div>
                      ) : null}
                      {incident.notes ? <div className="mt-1 text-muted-foreground">{incident.notes}</div> : null}
                    </div>
                    {incident.status === "OPEN" ? (
                      <div className="flex flex-wrap gap-2">
                        <Button
                          variant="secondary"
                          disabled={isResolvePending}
                          onClick={() => onStartResolve(incident.id)}
                        >
                          Resolver
                        </Button>
                        {canCorrect ? (
                          <Button
                            variant={isCorrectionActive ? "default" : "secondary"}
                            onClick={() => onStartCorrection(incident)}
                          >
                            Corregir
                          </Button>
                        ) : null}
                      </div>
                    ) : null}
                  </div>

                  {isResolving ? (
                    <div className="mt-3 space-y-2 border-t border-border pt-3">
                      <label className="space-y-2 text-sm text-foreground">
                        <span>Notas de resolución</span>
                        <Input
                          value={resolveNotes}
                          onChange={(event) => onResolveNotesChange(event.target.value)}
                          placeholder="Cierra la incidencia sin compensación operativa"
                        />
                      </label>
                      <div className="flex justify-end gap-2">
                        <Button type="button" variant="secondary" onClick={onCancelResolve}>
                          Cancelar
                        </Button>
                        <Button disabled={isResolvePending} onClick={() => onConfirmResolve(incident.id)}>
                          {isResolvePending ? "Resolviendo..." : "Confirmar resolución"}
                        </Button>
                      </div>
                    </div>
                  ) : null}
                </div>
              );
            })
          ) : (
            <p className="text-sm text-muted-foreground">Sin incidencias registradas.</p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
