import { Alert } from "../../../../../apps/web/src/shared/ui/alert";
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
import { formatRouteIncidentType } from "./jornada-labels";

export type RouteSelectOption = {
  value: string;
  label: string;
};

export type RouteDraftItem = {
  product_id: string;
  product_name: string;
  quantity: string;
  direction: "OUT" | "IN";
};

export type RouteCorrectionContext = {
  incidentId: string;
  incidentType: string;
  stopLabel: string;
  relatedOperationLabel: string | null;
};

type Props = {
  canRegisterOperation: boolean;
  operationType: string;
  routeStopId: string;
  operationNotes: string;
  draftItems: RouteDraftItem[];
  stopOptions: RouteSelectOption[];
  operationOptions: RouteSelectOption[];
  directionOptions: RouteSelectOption[];
  correctionContext: RouteCorrectionContext | null;
  isPending: boolean;
  onOperationTypeChange: (value: string) => void;
  onRouteStopChange: (value: string) => void;
  onOperationNotesChange: (value: string) => void;
  onOpenProductSearch: (direction?: "OUT" | "IN") => void;
  onUpdateDraftItem: (index: number, patch: Partial<RouteDraftItem>) => void;
  onRemoveDraftItem: (index: number) => void;
  onCancelCorrection: () => void;
  onSubmit: () => void;
};

export function RouteOperationForm({
  canRegisterOperation,
  operationType,
  routeStopId,
  operationNotes,
  draftItems,
  stopOptions,
  operationOptions,
  directionOptions,
  correctionContext,
  isPending,
  onOperationTypeChange,
  onRouteStopChange,
  onOperationNotesChange,
  onOpenProductSearch,
  onUpdateDraftItem,
  onRemoveDraftItem,
  onCancelCorrection,
  onSubmit,
}: Props) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{correctionContext ? "Corrección operativa" : "Operación de ruta"}</CardTitle>
        <CardDescription>
          {correctionContext
            ? "La operación original no se edita. Esta nueva operación reconcilia la realidad actual."
            : "La calle se registra aquí. La composición vigente y la carta porte salen de estas operaciones confirmadas."}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {!canRegisterOperation ? (
          <p className="text-sm text-muted-foreground">
            Las operaciones de ruta solo pueden registrarse cuando la jornada está en ruta o retorno.
          </p>
        ) : (
          <>
            {correctionContext ? (
              <Alert title={`Reconciliando incidencia ${correctionContext.incidentId}`}>
                <div className="space-y-2 text-sm">
                  <div>Tipo: {formatRouteIncidentType(correctionContext.incidentType)}</div>
                  <div>Parada: {correctionContext.stopLabel}</div>
                  {correctionContext.relatedOperationLabel ? (
                    <div>Operación original: {correctionContext.relatedOperationLabel}</div>
                  ) : null}
                </div>
                <div className="mt-3 flex justify-end">
                  <Button type="button" variant="secondary" onClick={onCancelCorrection}>
                    Cancelar corrección
                  </Button>
                </div>
              </Alert>
            ) : null}

            <div className="grid gap-4 md:grid-cols-2">
              <label className="space-y-2 text-sm text-foreground">
                <span>Tipo</span>
                <Select value={operationType} onChange={onOperationTypeChange} options={operationOptions} />
              </label>
              <label className="space-y-2 text-sm text-foreground">
                <span>Parada</span>
                <Select value={routeStopId} onChange={onRouteStopChange} options={stopOptions} placeholder="Sin parada" />
              </label>
            </div>

            <label className="space-y-2 text-sm text-foreground">
              <span>Notas</span>
              <Input
                value={operationNotes}
                onChange={(event) => onOperationNotesChange(event.target.value)}
                placeholder={correctionContext ? "Describe la reconciliación controlada" : "Entrega parcial, recojo de vacíos..."}
              />
            </label>

            <div className="space-y-2 rounded-xl border border-border p-3">
              <div className="flex flex-wrap items-center gap-2">
                {operationType === "EXCHANGE" ? (
                  <>
                    <Button type="button" variant="secondary" onClick={() => onOpenProductSearch("OUT")}>
                      Agregar entregado
                    </Button>
                    <Button type="button" variant="secondary" onClick={() => onOpenProductSearch("IN")}>
                      Agregar recogido
                    </Button>
                  </>
                ) : (
                  <Button type="button" variant="secondary" onClick={() => onOpenProductSearch()}>
                    Agregar producto
                  </Button>
                )}
              </div>
              {draftItems.length ? (
                <div className="space-y-2">
                  {operationType === "EXCHANGE" ? (
                    <div className="grid gap-4 md:grid-cols-2">
                      <div className="space-y-2">
                        <p className="text-sm font-medium text-foreground">Entregado</p>
                        {draftItems.filter((item) => item.direction === "OUT").length ? (
                          draftItems
                            .map((item, index) => ({ item, index }))
                            .filter(({ item }) => item.direction === "OUT")
                            .map(({ item, index }) => (
                              <div key={`${item.product_id}-${index}`} className="grid gap-2 rounded-lg border border-border p-3 md:grid-cols-[1.2fr_0.8fr_auto]">
                                <div className="text-sm text-foreground">{item.product_name}</div>
                                <Input
                                  type="number"
                                  min="0"
                                  step="0.001"
                                  value={item.quantity}
                                  onChange={(event) => onUpdateDraftItem(index, { quantity: event.target.value })}
                                />
                                <Button type="button" variant="secondary" onClick={() => onRemoveDraftItem(index)}>
                                  Quitar
                                </Button>
                              </div>
                            ))
                        ) : (
                          <p className="text-sm text-muted-foreground">Sin líneas entregadas.</p>
                        )}
                      </div>
                      <div className="space-y-2">
                        <p className="text-sm font-medium text-foreground">Recogido</p>
                        {draftItems.filter((item) => item.direction === "IN").length ? (
                          draftItems
                            .map((item, index) => ({ item, index }))
                            .filter(({ item }) => item.direction === "IN")
                            .map(({ item, index }) => (
                              <div key={`${item.product_id}-${index}`} className="grid gap-2 rounded-lg border border-border p-3 md:grid-cols-[1.2fr_0.8fr_auto]">
                                <div className="text-sm text-foreground">{item.product_name}</div>
                                <Input
                                  type="number"
                                  min="0"
                                  step="0.001"
                                  value={item.quantity}
                                  onChange={(event) => onUpdateDraftItem(index, { quantity: event.target.value })}
                                />
                                <Button type="button" variant="secondary" onClick={() => onRemoveDraftItem(index)}>
                                  Quitar
                                </Button>
                              </div>
                            ))
                        ) : (
                          <p className="text-sm text-muted-foreground">Sin líneas recogidas.</p>
                        )}
                      </div>
                    </div>
                  ) : (
                    draftItems.map((item, index) => (
                      <div key={`${item.product_id}-${index}`} className="grid gap-2 rounded-lg border border-border p-3 md:grid-cols-[1.4fr_0.8fr_0.8fr_auto]">
                        <div className="text-sm text-foreground">{item.product_name}</div>
                        <Select
                          value={operationType === "DELIVERY" ? "OUT" : operationType === "PICKUP" ? "IN" : item.direction}
                          onChange={(value) => onUpdateDraftItem(index, { direction: value as "OUT" | "IN" })}
                          options={directionOptions}
                        />
                        <Input
                          type="number"
                          min="0"
                          step="0.001"
                          value={item.quantity}
                          onChange={(event) => onUpdateDraftItem(index, { quantity: event.target.value })}
                        />
                        <Button type="button" variant="secondary" onClick={() => onRemoveDraftItem(index)}>
                          Quitar
                        </Button>
                      </div>
                    ))
                  )}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">Sin líneas todavía.</p>
              )}
            </div>

            <div className="flex justify-end">
              <Button disabled={isPending || draftItems.length === 0} onClick={onSubmit}>
                {isPending
                  ? correctionContext
                    ? "Confirmando corrección..."
                    : "Confirmando..."
                  : correctionContext
                    ? "Confirmar corrección"
                    : "Confirmar operación"}
              </Button>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}
