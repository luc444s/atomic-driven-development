import { Alert } from "@systutor/shell/ui/alert";
import { Button } from "@systutor/shell/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@systutor/shell/ui/card";
import { Input } from "@systutor/shell/ui/input";
import { Select } from "@systutor/shell/ui/select";
import { formatRouteIncidentType } from "./jornada-labels";

export type RouteSelectOption = {
  value: string;
  label: string;
};

export type RouteContextType = "STOP" | "CUSTOMER" | "WAREHOUSE";
export type RouteDraftItem = {
  product_id: string;
  product_name: string;
  quantity: string;
  direction: "OUT" | "IN";
  selected_serials_count: number;
};

export type RouteCorrectionContext = {
  incidentId: string;
  incidentType: string;
  stopLabel: string;
  relatedOperationLabel: string | null;
};

type CompositionLine = {
  product_id: string;
  product_name: string;
  quantity: number;
  address_label?: string | null;
};

type Props = {
  canRegisterOperation: boolean;
  operationType: string;
  routeStopId: string;
  contextType: RouteContextType;
  customerId: string;
  warehouseId: string;
  operationNotes: string;
  draftItems: RouteDraftItem[];
  stopOptions: RouteSelectOption[];
  customerOptions: RouteSelectOption[];
  warehouseOptions: RouteSelectOption[];
  operationOptions: RouteSelectOption[];
  directionOptions: RouteSelectOption[];
  correctionContext: RouteCorrectionContext | null;
  composition: CompositionLine[];
  customerCylinders: CompositionLine[];
  stopAddressLabel: string | null;
  fastSerialInput: string;
  fastSerialError: string | null;
  isPending: boolean;
  onOperationTypeChange: (value: string) => void;
  onRouteStopChange: (value: string) => void;
  onContextTypeChange: (value: RouteContextType) => void;
  onCustomerChange: (value: string) => void;
  onWarehouseChange: (value: string) => void;
  onOperationNotesChange: (value: string) => void;
  onOpenProductSearch: (direction?: "OUT" | "IN") => void;
  onOpenSerialScanner: (index: number) => void;
  onUpdateDraftItem: (index: number, patch: Partial<RouteDraftItem>) => void;
  onRemoveDraftItem: (index: number) => void;
  onCancelCorrection: () => void;
  onSubmit: () => void;
  onAddDeliveryProduct: (product: { product_id: string; product_name: string; available: number; serial?: string }) => void;
  onAddPickupProduct: (product: { product_id: string; product_name: string; available: number; serial?: string }) => void;
  onFastSerialChange: (value: string) => void;
  onFastSerialSubmit: () => void;
};

export function RouteOperationForm({
  canRegisterOperation,
  operationType,
  routeStopId,
  contextType,
  customerId,
  warehouseId,
  operationNotes,
  draftItems,
  stopOptions,
  customerOptions,
  warehouseOptions,
  operationOptions,
  directionOptions,
  correctionContext,
  composition,
  customerCylinders,
  stopAddressLabel,
  fastSerialInput,
  fastSerialError,
  isPending,
  onOperationTypeChange,
  onRouteStopChange,
  onContextTypeChange,
  onCustomerChange,
  onWarehouseChange,
  onOperationNotesChange,
  onOpenProductSearch,
  onOpenSerialScanner,
  onUpdateDraftItem,
  onRemoveDraftItem,
  onCancelCorrection,
  onSubmit,
  onAddDeliveryProduct,
  onAddPickupProduct,
  onFastSerialChange,
  onFastSerialSubmit,
}: Props) {
  const usesStopContext = Boolean(routeStopId);
  const showCustomerContext = !usesStopContext && contextType === "CUSTOMER";
  const showWarehouseContext = !usesStopContext && contextType === "WAREHOUSE";

  return (
    <Card>
      <CardHeader>
        <CardTitle>{correctionContext ? "Corrección operativa" : "Registrar evento de ruta"}</CardTitle>
        <CardDescription>
          {correctionContext
            ? "La operación original no se edita. Esta nueva operación reconcilia la realidad actual."
            : "Captura el hecho real de calle en un solo flujo. Si hubo desvío, puedes vincular la incidencia desde aquí."}
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
              <label className="block space-y-2 text-sm text-foreground">
                <span>Tipo</span>
                <Select value={operationType} onChange={onOperationTypeChange} options={operationOptions} />
              </label>
              <label className="block space-y-2 text-sm text-foreground">
                <span>Parada</span>
                <Select value={routeStopId} onChange={onRouteStopChange} options={stopOptions} placeholder="Sin parada" />
              </label>
            </div>

            {usesStopContext ? (
              <div className="rounded-md border border-border p-4">
                <p className="mb-3 text-sm font-medium text-foreground">Contexto operativo</p>
                <p className="text-sm text-muted-foreground">
                  La operación queda vinculada a la parada seleccionada. El cliente se deriva automáticamente desde ese punto de entrega.
                </p>
                <p className="mt-2 text-sm text-foreground">
                  Dirección:{" "}
                  <span className={stopAddressLabel ? "font-medium" : "text-muted-foreground"}>
                    {stopAddressLabel ?? "sin dirección específica"}
                  </span>
                </p>
              </div>
            ) : (
              <div className="rounded-md border border-border p-4 space-y-4">
                <p className="mb-3 text-sm font-medium text-foreground">Contexto operativo</p>
                <div className="grid gap-4 md:grid-cols-2">
                  <label className="block space-y-2 text-sm text-foreground">
                    <span>Contexto</span>
                    <Select
                      value={contextType}
                      onChange={(value) => onContextTypeChange(value as RouteContextType)}
                      options={[
                        { value: "CUSTOMER", label: "Cliente" },
                        { value: "WAREHOUSE", label: "Almacén" },
                      ]}
                    />
                  </label>
                  {showCustomerContext ? (
                    <label className="block space-y-2 text-sm text-foreground">
                      <span>Cliente</span>
                      <Select
                        value={customerId}
                        onChange={onCustomerChange}
                        options={customerOptions}
                        placeholder="Seleccionar cliente"
                      />
                    </label>
                  ) : null}
                  {showWarehouseContext ? (
                    <label className="block space-y-2 text-sm text-foreground">
                      <span>Almacén</span>
                      <Select
                        value={warehouseId}
                        onChange={onWarehouseChange}
                        options={warehouseOptions}
                        placeholder="Seleccionar almacén"
                      />
                    </label>
                  ) : null}
                </div>
              </div>
            )}

            <label className="block space-y-2 text-sm text-foreground">
              <span>Notas</span>
              <Input
                value={operationNotes}
                onChange={(event) => onOperationNotesChange(event.target.value)}
                placeholder={correctionContext ? "Describe la reconciliación controlada" : "Entrega parcial, recojo de vacíos, contingencia..."}
              />
            </label>

            <div className="space-y-3 rounded-xl border border-border p-3">
              {operationType === "DELIVERY" ? (
                <>
                  <div className="flex items-center gap-2">
                    <Input
                      value={fastSerialInput}
                      onChange={(event) => onFastSerialChange(event.target.value)}
                      onKeyDown={(event) => { if (event.key === "Enter") onFastSerialSubmit(); }}
                      placeholder="Escanear o escribir serial"
                      className="flex-1"
                    />
                    <Button type="button" variant="secondary" onClick={onFastSerialSubmit} disabled={!fastSerialInput.trim()}>
                      Agregar
                    </Button>
                  </div>
                  {fastSerialError ? (
                    <p className="text-sm text-destructive">{fastSerialError}</p>
                  ) : null}

                  {composition.length > 0 ? (
                    <div className="flex flex-wrap gap-2">
                      {composition.map((line) => (
                        <button
                          key={line.product_id}
                          type="button"
                          className="flex min-w-[120px] flex-col items-center rounded-lg border border-border px-3 py-2 text-center transition hover:border-primary hover:bg-accent"
                          onClick={() =>
                            onAddDeliveryProduct({
                              product_id: line.product_id,
                              product_name: line.product_name,
                              available: line.quantity,
                            })
                          }
                        >
                          <span className="text-xs font-medium text-foreground">{line.product_name}</span>
                          <span className="text-xs text-muted-foreground">{line.quantity} disponibles</span>
                        </button>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground">Sin carga en el camion.</p>
                  )}

                  {draftItems.length ? (
                    <div className="space-y-2 border-t border-border pt-3">
                      <p className="text-sm font-medium text-foreground">Entregado</p>
                      {draftItems.map((item, index) => (
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
                          <div className="md:col-span-3 flex items-center justify-between gap-2">
                            <Button type="button" variant="secondary" onClick={() => onOpenSerialScanner(index)}>
                              Seriales
                            </Button>
                            <span className="text-xs text-muted-foreground">
                              {item.selected_serials_count}/{Number(item.quantity || "0") || 0}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground">Sin lineas para entregar.</p>
                  )}
                </>
              ) : operationType === "EXCHANGE" ? (
                <>
                  <div className="flex flex-wrap items-center gap-2">
                    <Button type="button" variant="secondary" onClick={() => onOpenProductSearch("OUT")}>
                      Agregar entregado
                    </Button>
                    <Button type="button" variant="secondary" onClick={() => onOpenProductSearch("IN")}>
                      Agregar recogido
                    </Button>
                  </div>
                  {draftItems.length ? (
                    <div className="space-y-2">
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
                                  <div className="md:col-span-3 flex items-center justify-between gap-2">
                                    <Button type="button" variant="secondary" onClick={() => onOpenSerialScanner(index)}>
                                      Escanear seriales
                                    </Button>
                                    <span className="text-xs text-muted-foreground">
                                      {item.selected_serials_count}/{Number(item.quantity || "0") || 0}
                                    </span>
                                  </div>
                                </div>
                              ))
                          ) : (
                            <p className="text-sm text-muted-foreground">Sin lineas entregadas.</p>
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
                            <p className="text-sm text-muted-foreground">Sin lineas recogidas.</p>
                          )}
                        </div>
                      </div>
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground">Sin lineas todavia.</p>
                  )}
                </>
              ) : operationType === "PICKUP" ? (
                <>
                  <div className="flex items-center gap-2">
                    <Input
                      value={fastSerialInput}
                      onChange={(event) => onFastSerialChange(event.target.value)}
                      onKeyDown={(event) => { if (event.key === "Enter") onFastSerialSubmit(); }}
                      placeholder="Escanear o escribir serial"
                      className="flex-1"
                    />
                    <Button type="button" variant="secondary" onClick={onFastSerialSubmit} disabled={!fastSerialInput.trim()}>
                      Agregar
                    </Button>
                  </div>
                  {fastSerialError ? (
                    <p className="text-sm text-destructive">{fastSerialError}</p>
                  ) : null}

                  {customerCylinders.length > 0 ? (
                    <div className="flex flex-wrap gap-2">
                      {customerCylinders.map((line) => (
                        <button
                          key={line.product_id}
                          type="button"
                          className="flex min-w-[120px] flex-col items-center rounded-lg border border-border px-3 py-2 text-center transition hover:border-primary hover:bg-accent"
                          onClick={() =>
                            onAddPickupProduct({
                              product_id: line.product_id,
                              product_name: line.product_name,
                              available: line.quantity,
                            })
                          }
                        >
                          <span className="text-xs font-medium text-foreground">{line.product_name}</span>
                          <span className="text-xs text-muted-foreground">{line.quantity} en cliente</span>
                          {line.address_label ? (
                            <span className="text-xs text-foreground">{line.address_label}</span>
                          ) : (
                            <span className="text-xs text-muted-foreground">sin dirección específica</span>
                          )}
                        </button>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground">Selecciona una parada con cliente para ver sus envases.</p>
                  )}

                  {draftItems.length ? (
                    <div className="space-y-2 border-t border-border pt-3">
                      <p className="text-sm font-medium text-foreground">Recogido</p>
                      {draftItems.map((item, index) => (
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
                          <div className="md:col-span-3 flex items-center justify-between gap-2">
                            <Button type="button" variant="secondary" onClick={() => onOpenSerialScanner(index)}>
                              Seriales
                            </Button>
                            <span className="text-xs text-muted-foreground">
                              {item.selected_serials_count}/{Number(item.quantity || "0") || 0}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground">Sin lineas para recoger.</p>
                  )}
                </>
              ) : null}
            </div>

            <div className="flex justify-end">
              <Button disabled={isPending || draftItems.length === 0} onClick={onSubmit}>
                {isPending
                  ? correctionContext
                    ? "Confirmando corrección..."
                    : "Confirmando..."
                  : correctionContext
                    ? "Confirmar corrección"
                    : "Confirmar evento"}
              </Button>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}
