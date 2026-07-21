import { useEffect, useState } from "react";

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
import type { RouteStopResult } from "../../api";
import { formatStopOutcomeType, formatStopStatus } from "./jornada-labels";
import type { RouteSelectOption } from "./RouteOperationForm";

const STATUS_OPTIONS: RouteSelectOption[] = [
  { value: "PENDING", label: "Pendiente" },
  { value: "IN_PROGRESS", label: "En progreso" },
  { value: "PARTIAL", label: "Parcial" },
  { value: "COMPLETED", label: "Completada" },
  { value: "FAILED", label: "Fallida" },
];

const OUTCOME_OPTIONS: RouteSelectOption[] = [
  { value: "NORMAL", label: "Normal" },
  { value: "CUSTOMER_ABSENT", label: "Cliente ausente" },
  { value: "FAILED_DELIVERY", label: "Entrega fallida" },
  { value: "PARTIAL_ATTENDED", label: "Atención parcial" },
  { value: "UNPLANNED_RETURN", label: "Retorno no planificado" },
  { value: "OTHER", label: "Otro" },
];

type Props = {
  canManage: boolean;
  stopOptions: RouteSelectOption[];
  results: RouteStopResult[];
  isPending: boolean;
  onSave: (routeStopId: string, payload: {
    status: string;
    completion_percent: number;
    outcome_type: string;
    driver_note?: string | null;
  }) => void;
};

export function RouteStopResultsPanel({ canManage, stopOptions, results, isPending, onSave }: Props) {
  const [routeStopId, setRouteStopId] = useState("");
  const [status, setStatus] = useState("PENDING");
  const [completionPercent, setCompletionPercent] = useState("0");
  const [outcomeType, setOutcomeType] = useState("NORMAL");
  const [driverNote, setDriverNote] = useState("");

  useEffect(() => {
    if (!routeStopId && stopOptions.length) {
      setRouteStopId(stopOptions[0].value);
    }
  }, [routeStopId, stopOptions]);

  useEffect(() => {
    const current = results.find((result) => result.route_stop_id === routeStopId);
    if (!current) {
      setStatus("PENDING");
      setCompletionPercent("0");
      setOutcomeType("NORMAL");
      setDriverNote("");
      return;
    }
    setStatus(current.status);
    setCompletionPercent(String(current.completion_percent));
    setOutcomeType(current.outcome_type);
    setDriverNote(current.driver_note ?? "");
  }, [routeStopId, results]);

  const existingSummary = results.length
    ? results.map((result) => {
        const stopLabel = stopOptions.find((option) => option.value === result.route_stop_id)?.label ?? result.route_stop_id;
        return {
          ...result,
          stopLabel,
        };
      })
    : [];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Resultado de parada</CardTitle>
        <CardDescription>
          Cierra semánticamente la parada con porcentaje de cumplimiento y nota operativa del conductor.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {!canManage ? (
          <p className="text-sm text-muted-foreground">
            El resultado de parada se registra mientras la jornada sigue operativa en ruta o retorno.
          </p>
        ) : (
          <>
            <div className="grid gap-4 md:grid-cols-2">
              <label className="space-y-2 text-sm text-foreground">
                <span>Parada</span>
                <Select value={routeStopId} onChange={setRouteStopId} options={stopOptions} placeholder="Selecciona parada" />
              </label>
              <label className="space-y-2 text-sm text-foreground">
                <span>Estado</span>
                <Select value={status} onChange={setStatus} options={STATUS_OPTIONS} />
              </label>
              <label className="space-y-2 text-sm text-foreground">
                <span>Porcentaje</span>
                <Input
                  type="number"
                  min="0"
                  max="100"
                  step="1"
                  value={completionPercent}
                  onChange={(event) => setCompletionPercent(event.target.value)}
                />
              </label>
              <label className="space-y-2 text-sm text-foreground">
                <span>Desenlace</span>
                <Select value={outcomeType} onChange={setOutcomeType} options={OUTCOME_OPTIONS} />
              </label>
            </div>

            <label className="space-y-2 text-sm text-foreground">
              <span>Nota del conductor</span>
              <Input
                value={driverNote}
                onChange={(event) => setDriverNote(event.target.value)}
                placeholder="Explica como terminó realmente la parada"
              />
            </label>

            <div className="flex justify-end">
              <Button
                disabled={isPending || !routeStopId}
                onClick={() =>
                  onSave(routeStopId, {
                    status,
                    completion_percent: Number(completionPercent || "0"),
                    outcome_type: outcomeType,
                    driver_note: driverNote || null,
                  })
                }
              >
                {isPending ? "Guardando..." : "Guardar resultado"}
              </Button>
            </div>
          </>
        )}

        <div className="space-y-2 border-t border-border pt-3">
          <p className="text-sm font-medium text-foreground">Resultados registrados</p>
          {existingSummary.length ? (
            <div className="space-y-2">
              {existingSummary.map((result) => (
                <div key={result.id} className="rounded-lg border border-border px-3 py-3 text-sm text-foreground">
                  <div className="font-medium">{result.stopLabel}</div>
                  <div className="text-muted-foreground">
                    {formatStopStatus(result.status)} · {result.completion_percent}% · {formatStopOutcomeType(result.outcome_type)}
                  </div>
                  {result.driver_note ? <div className="mt-1 text-muted-foreground">{result.driver_note}</div> : null}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">Sin resultados de parada registrados.</p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
