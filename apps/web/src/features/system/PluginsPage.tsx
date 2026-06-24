import { usePluginFrontendRuntime } from "../plugins/runtime";
import { useAuthStore } from "../auth/store";
import { Alert } from "../../shared/ui/alert";
import { Badge } from "../../shared/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../shared/ui/card";

export function PluginsPage() {
  const frontendRuntime = usePluginFrontendRuntime();
  const pluginRuntimeRecords = useAuthStore((state) => state.pluginRuntimeRecords);

  return (
    <section className="space-y-6">
      <div className="space-y-2">
        <h1 className="text-2xl font-semibold text-white">Runtime de plugins</h1>
        <p className="text-sm text-slate-400">
          Estado persistente del runtime, incluyendo lifecycle, version de migracion y
          capacidades frontend visibles para el usuario actual.
        </p>
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        {pluginRuntimeRecords.map((plugin) => (
          <Card key={plugin.id}>
            <CardHeader>
              <div className="flex items-center justify-between gap-3">
                <CardTitle>{plugin.name}</CardTitle>
                <div className="flex items-center gap-2">
                  <Badge>{plugin.version}</Badge>
                  <Badge>{plugin.state}</Badge>
                </div>
              </div>
              <CardDescription>{plugin.description}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4 text-sm text-slate-300">
              <div className="grid gap-2 rounded-md border border-slate-800 bg-slate-900/70 p-3">
                <InfoLine label="Plugin ID" value={plugin.plugin_id} />
                <InfoLine label="API version" value={plugin.api_version} />
                <InfoLine label="Backend entrypoint" value={plugin.backend_entrypoint} />
                <InfoLine label="Frontend entrypoint" value={plugin.frontend_entrypoint} />
                <InfoLine label="Migration version" value={plugin.migration_version ?? "-"} />
                <InfoLine label="Enabled" value={plugin.is_enabled ? "si" : "no"} />
              </div>

              <TagBlock label="Permisos" values={plugin.permissions_json} />
              <TagBlock label="Eventos" values={plugin.events_json} />
              <TagBlock
                label="Dependencias"
                values={plugin.requires_json}
                emptyLabel="Sin dependencias"
              />

              <div className="grid gap-2 rounded-md border border-slate-800 bg-slate-900/70 p-3">
                <InfoLine
                  label="Rutas frontend visibles"
                  value={String(
                    frontendRuntime.routes.filter((route) => route.pluginId === plugin.plugin_id)
                      .length
                  )}
                />
                <InfoLine
                  label="Entradas sidebar visibles"
                  value={String(
                    frontendRuntime.navigation.filter((entry) => entry.pluginId === plugin.plugin_id)
                      .length
                  )}
                />
                <InfoLine
                  label="Widgets visibles"
                  value={String(
                    frontendRuntime.widgets.filter((widget) => widget.pluginId === plugin.plugin_id)
                      .length
                  )}
                />
              </div>

              {plugin.last_error ? <Alert title="Ultimo error">{plugin.last_error}</Alert> : null}
            </CardContent>
          </Card>
        ))}
      </div>

      {pluginRuntimeRecords.length === 0 ? (
        <Alert title="No se encontraron plugins declarados">
          El contexto actual no expone plugins persistidos para esta sesion.
        </Alert>
      ) : null}
    </section>
  );
}

function InfoLine({ label, value }: { label: string; value: string | null }) {
  return (
    <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
      <span className="text-slate-400">{label}</span>
      <span className="break-all text-slate-200">{value ?? "-"}</span>
    </div>
  );
}

function TagBlock({
  label,
  values,
  emptyLabel = "Sin datos",
}: {
  label: string;
  values: string[];
  emptyLabel?: string;
}) {
  return (
    <div className="space-y-2">
      <h2 className="text-xs font-semibold uppercase tracking-wide text-slate-400">{label}</h2>
      <div className="flex flex-wrap gap-2">
        {values.length > 0 ? (
          values.map((value) => <Badge key={value}>{value}</Badge>)
        ) : (
          <span className="text-sm text-slate-500">{emptyLabel}</span>
        )}
      </div>
    </div>
  );
}
