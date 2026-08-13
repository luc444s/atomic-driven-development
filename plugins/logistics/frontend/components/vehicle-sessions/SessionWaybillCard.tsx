import { Alert } from "../../../../../apps/web/src/shared/ui/alert";
import { Button } from "../../../../../apps/web/src/shared/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "../../../../../apps/web/src/shared/ui/card";
import type { SessionWaybillState, SessionWaybillVersion } from "../../api";
import {
  formatWaybillChangeEvent,
  formatWaybillVersionStatus,
} from "./jornada-labels";
import { buildSessionWaybillHistoryLabel } from "./session-waybill-view";

type Props = {
  waybillState: SessionWaybillState | undefined;
  history: SessionWaybillVersion[];
  isLoading: boolean;
  canRegenerate: boolean;
  isRegenerating: boolean;
  canEmit: boolean;
  isEmitting: boolean;
  onRegenerate: () => void;
  onEmit: () => void;
  onViewDocument: () => void;
};

export function SessionWaybillCard({
  waybillState,
  history,
  isLoading,
  canRegenerate,
  isRegenerating,
  canEmit,
  isEmitting,
  onRegenerate,
  onEmit,
  onViewDocument,
}: Props) {
  const active = waybillState?.active;
  const issued = waybillState?.issued;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between gap-4">
          <div>
            <CardTitle>Carta Porte</CardTitle>
            <CardDescription>
              Preview viva para operación y documento oficial emitido para impresión legal.
            </CardDescription>
          </div>
          <div className="flex flex-wrap justify-end gap-2">
            <Button
              variant={waybillState?.sync_status === "OUTDATED" ? "default" : "secondary"}
              disabled={!canRegenerate || isRegenerating}
              onClick={onRegenerate}
            >
              {isRegenerating ? "Regenerando..." : active ? "Regenerar preview" : "Generar preview"}
            </Button>
            <Button disabled={!canEmit || isEmitting} onClick={onEmit}>
              {isEmitting ? "Emitiendo..." : issued ? "Reemitir" : "Emitir"}
            </Button>
            <Button variant="secondary" disabled={!issued} onClick={onViewDocument}>
              Ver documento
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {isLoading ? (
          <p className="text-sm text-muted-foreground">Cargando carta porte...</p>
        ) : null}

        {!isLoading && waybillState?.emit_block_reason ? (
          <Alert title="No se puede emitir la carta porte oficial">
            {waybillState.emit_block_reason}
          </Alert>
        ) : null}

        {!isLoading && !active ? (
          <div className="rounded-xl border border-dashed border-border p-4 text-sm text-muted-foreground">
            Todavía no existe preview viva para esta jornada.
          </div>
        ) : null}

        {issued ? (
          <div className="space-y-3 rounded-xl border border-border p-4">
            <p className="text-sm font-medium text-foreground">Documento oficial emitido</p>
            <div className="grid gap-3 text-sm text-foreground md:grid-cols-2">
              <div><span className="text-muted-foreground">Versión:</span> v{issued.version}</div>
              <div><span className="text-muted-foreground">Emitida:</span> {new Date(issued.generated_at).toLocaleString()}</div>
              <div><span className="text-muted-foreground">Fecha documento:</span> {issued.snapshot.issue_date}</div>
              <div><span className="text-muted-foreground">Conductor:</span> {issued.snapshot.driver_name}</div>
              <div><span className="text-muted-foreground">Expedidor:</span> {issued.snapshot.issuer.legal_name}</div>
              <div><span className="text-muted-foreground">Destinatario:</span> {issued.snapshot.consignee.legal_name ?? "-"}</div>
            </div>
          </div>
        ) : null}

        {active ? (
          <>
            {waybillState?.sync_status === "OUTDATED" ? (
              <Alert title="Carta porte desactualizada">
                La preview viva ya no coincide con el estado operativo actual. Regenera antes de emitir de nuevo.
              </Alert>
            ) : null}
            <div className="space-y-3 rounded-xl border border-border p-4">
              <p className="text-sm font-medium text-foreground">Preview viva</p>
              <div className="grid gap-3 text-sm text-foreground md:grid-cols-2">
                <div><span className="text-muted-foreground">Versión:</span> v{active.version}</div>
                <div><span className="text-muted-foreground">Generada:</span> {new Date(active.generated_at).toLocaleString()}</div>
                <div><span className="text-muted-foreground">Vehículo:</span> {active.snapshot.vehicle.plate}</div>
                <div><span className="text-muted-foreground">Conductor:</span> {active.snapshot.driver.name}</div>
                <div><span className="text-muted-foreground">Destino:</span> {active.snapshot.destination.name ?? "Sin destino"}</div>
                <div><span className="text-muted-foreground">Dirección:</span> {active.snapshot.destination.address ?? "Sin dirección"}</div>
              </div>
            </div>

            <div className="space-y-2">
              <p className="text-sm font-medium text-foreground">Productos transportados</p>
              <div className="space-y-2">
                {active.snapshot.transported_items.map((item) => (
                  <div key={`${item.product_id}-${item.product_name}`} className="rounded-lg border border-border px-3 py-2 text-sm">
                    <div className="font-medium text-foreground">{item.product_name}</div>
                    <div className="text-muted-foreground">
                      {`Cantidad: ${item.quantity} | Peso: ${item.weight_kg ?? "-"} kg | ADR: ${item.adr_points ?? "-"}`}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="grid gap-3 border-t border-border pt-3 text-sm text-muted-foreground md:grid-cols-3">
              <div>Total bultos: {active.snapshot.totals.total_packages ?? "-"}</div>
              <div>Peso total: {active.snapshot.totals.total_weight_kg ?? "-"} kg</div>
              <div>ADR total: {active.snapshot.totals.total_adr_points ?? "-"}</div>
            </div>
          </>
        ) : null}

        <div className="space-y-2 border-t border-border pt-3">
          <p className="text-sm font-medium text-foreground">Historial</p>
          {history.length ? (
            <div className="space-y-2">
              {history.map((version) => (
                <div key={version.id} className="rounded-lg border border-border px-3 py-2 text-sm text-foreground">
                  <div className="font-medium">{buildSessionWaybillHistoryLabel(version)} · {formatWaybillVersionStatus(version.status)}</div>
                  <div className="text-muted-foreground">
                    {formatWaybillChangeEvent(version.change_event)} · {version.change_reason}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">Sin versiones registradas.</p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
