import { Button } from "../../../../../apps/web/src/shared/ui/button";
import { Input } from "../../../../../apps/web/src/shared/ui/input";
import { Select } from "../../../../../apps/web/src/shared/ui/select";
import type { LogisticsVehicle, RoutingCalculationResponse, VehicleSession } from "../../api";
import { LocationSearch } from "../../../../../apps/web/src/shared/ui/location-search";
import { type RouteStopDraft } from "./useRouteBuilder";

type Props = {
  phase: "idle" | "picking_start" | "picking_end" | "picking_stops";
  startPoint: RouteStopDraft | null;
  endPoint: RouteStopDraft | null;
  stops: RouteStopDraft[];
  routeDate: string;
  vehicleId: string;
  customName: string;
  isSaving: boolean;
  isCalculating: boolean;
  vehicles: LogisticsVehicle[];
  sessions: VehicleSession[];
  selectedSessionId: string;
  preview: RoutingCalculationResponse | null;
  onRemoveStart: () => void;
  onRemoveEnd: () => void;
  onRemoveStop: (index: number) => void;
  onReorderStop: (fromIndex: number, toIndex: number) => void;
  onRouteDateChange: (value: string) => void;
  onVehicleChange: (value: string) => void;
  onCustomNameChange: (value: string) => void;
  onSessionChange: (value: string) => void;
  onAssignSession: () => void;
  onCalculate: () => void;
  onClearPreview: () => void;
  onCancel: () => void;
  onSave: () => void;
  onSearchSelect: (lat: number, lng: number) => void;
  onAddStopManual: () => void;
  compact?: boolean;
};

export function RouteBuilderPanel({
  phase,
  startPoint,
  endPoint,
  stops,
  routeDate,
  vehicleId,
  customName,
  isSaving,
  isCalculating,
  vehicles,
  sessions,
  selectedSessionId,
  preview,
  onRemoveStart,
  onRemoveEnd,
  onRemoveStop,
  onReorderStop,
  onRouteDateChange,
  onVehicleChange,
  onCustomNameChange,
  onSessionChange,
  onAssignSession,
  onCalculate,
  onClearPreview,
  onCancel,
  onSave,
  onSearchSelect,
  onAddStopManual,
  compact = false,
}: Props) {
  const isBuilding = phase !== "idle";
  const canSave = startPoint && endPoint && !isSaving && isBuilding;
  const canCalculate = Boolean(startPoint && endPoint && vehicleId && !isCalculating && isBuilding);

  const vehicleOptions = vehicles.map((v) => ({ value: v.id, label: v.plate }));
  const sessionOptions = sessions
    .filter((s) => ["OUTBOUND", "RETURNING"].includes(s.status))
    .map((s) => ({ value: s.id, label: `${s.vehicle_plate} · ${s.status}` }));

  return (
    <div className="space-y-4">
      {isBuilding ? (
        <>
          <LocationSearch
            phase={phase}
            onSelect={onSearchSelect}
            onAddStop={onAddStopManual}
          />

          {startPoint ? (
            <div className="flex items-center gap-2 rounded-lg border border-border px-3 py-2">
              <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-green-500 text-xs font-bold text-white">P</span>
              <div className="min-w-0 flex-1 text-sm">
                <p className="font-medium text-foreground">{startPoint.name}</p>
                <p className="text-xs text-muted-foreground">
                  {startPoint.lat.toFixed(5)}, {startPoint.lng.toFixed(5)}
                </p>
              </div>
              <Button variant="secondary" onClick={onRemoveStart}>×</Button>
            </div>
          ) : (
            <div className="rounded-lg border border-dashed border-border px-3 py-2 text-sm text-muted-foreground">
              Haz clic en el mapa para elegir la partida
            </div>
          )}

          {endPoint ? (
            <div className="flex items-center gap-2 rounded-lg border border-border px-3 py-2">
              <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-red-500 text-xs font-bold text-white">D</span>
              <div className="min-w-0 flex-1 text-sm">
                <p className="font-medium text-foreground">{endPoint.name}</p>
                <p className="text-xs text-muted-foreground">
                  {endPoint.lat.toFixed(5)}, {endPoint.lng.toFixed(5)}
                </p>
              </div>
              <Button variant="secondary" onClick={onRemoveEnd}>×</Button>
            </div>
          ) : (
            <div className="rounded-lg border border-dashed border-border px-3 py-2 text-sm text-muted-foreground">
              {startPoint ? "Haz clic para elegir el destino" : "Elige primero la partida"}
            </div>
          )}

          {stops.length > 0 ? (
            <div className="space-y-2">
              <p className="text-xs font-medium text-foreground">Paradas ({stops.length})</p>
              {stops.map((stop, index) => (
                <div key={`${stop.lat}-${stop.lng}-${index}`} className="flex items-center gap-2 rounded-lg border border-border px-3 py-2">
                  <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-blue-500 text-xs font-bold text-white">
                    {index + 1}
                  </span>
                  <div className="min-w-0 flex-1 text-sm">
                    <p className="font-medium text-foreground">{stop.name}</p>
                    <p className="text-xs text-muted-foreground">
                      {stop.lat.toFixed(5)}, {stop.lng.toFixed(5)}
                    </p>
                  </div>
                  <Button variant="secondary" disabled={index === 0} onClick={() => onReorderStop(index, index - 1)}>↑</Button>
                  <Button variant="secondary" disabled={index === stops.length - 1} onClick={() => onReorderStop(index, index + 1)}>↓</Button>
                  <Button variant="secondary" onClick={() => onRemoveStop(index)}>×</Button>
                </div>
              ))}
            </div>
          ) : null}

          <div className="border-t border-border pt-3 space-y-3">
            <label className="block space-y-2 text-sm text-foreground">
              <span>Nombre</span>
              <Input
                value={customName}
                onChange={(e) => onCustomNameChange(e.target.value)}
                placeholder="Partida → Destino"
              />
            </label>
            <div className={`grid gap-3 ${compact ? "grid-cols-1" : "grid-cols-2"}`}>
              <label className="block space-y-2 text-sm text-foreground">
                <span>Fecha</span>
                <Input type="date" value={routeDate} onChange={(e) => onRouteDateChange(e.target.value)} />
              </label>
              {!compact ? (
                <label className="block space-y-2 text-sm text-foreground">
                  <span>Vehículo</span>
                  <Select value={vehicleId} onChange={onVehicleChange} options={vehicleOptions} placeholder="Sin asignar" />
                </label>
              ) : null}
            </div>

            {!compact && sessionOptions.length > 0 ? (
              <div className="flex items-end gap-2">
                <label className="block min-w-0 flex-1 space-y-2 text-sm text-foreground">
                  <span>Asignar a sesión</span>
                  <Select value={selectedSessionId} onChange={onSessionChange} options={sessionOptions} placeholder="Seleccionar" />
                </label>
                <Button disabled={!selectedSessionId} onClick={onAssignSession}>Asignar</Button>
              </div>
            ) : null}

            {preview ? (
              <div className="rounded-md border border-border p-3 text-sm text-foreground space-y-1">
                <p>Preview: {preview.totals.distance_m} m · {preview.totals.travel_seconds}s</p>
                <p>Paradas optimizadas: {preview.ordered_stops.length}</p>
                {preview.violations.length ? <p>Violaciones: {preview.violations.join(", ")}</p> : null}
              </div>
            ) : null}
          </div>

          <div className="flex justify-end gap-3">
            <Button variant="secondary" disabled={!canCalculate} onClick={onCalculate}>
              {isCalculating ? "Calculando..." : "Calcular ruta"}
            </Button>
            {preview ? <Button variant="secondary" onClick={onClearPreview}>Limpiar preview</Button> : null}
            <Button variant="secondary" onClick={onCancel}>Cancelar</Button>
            <Button disabled={!canSave} onClick={onSave}>
              {isSaving ? "Guardando..." : "Guardar ruta"}
            </Button>
          </div>
        </>
      ) : (
        <div className="rounded-lg border border-dashed border-border p-6 text-center">
          <p className="text-sm text-muted-foreground">
            Selecciona una ruta o crea una nueva para empezar a armar el recorrido sobre el mapa.
          </p>
        </div>
      )}
    </div>
  );
}
