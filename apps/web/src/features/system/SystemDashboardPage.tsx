import { useQuery } from "@tanstack/react-query";

import { usePluginFrontendRuntime } from "../plugins/runtime";
import { getSystemHealth, getSystemReady } from "./api";
import { Alert } from "@systutor/shell/ui/alert";
import { Badge } from "@systutor/shell/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@systutor/shell/ui/card";

export function SystemDashboardPage() {
  const healthQuery = useQuery({
    queryKey: ["system", "health"],
    queryFn: getSystemHealth,
  });
  const pluginRuntime = usePluginFrontendRuntime();

  const readyQuery = useQuery({
    queryKey: ["system", "ready"],
    queryFn: getSystemReady,
  });

  const hasError = healthQuery.error || readyQuery.error;

  return (
    <section className="space-y-6">
      <div className="space-y-2">
        <h1 className="text-2xl font-semibold text-foreground">Dashboard del sistema</h1>
        <p className="text-sm text-muted-foreground">
          Shell base del core para revisar salud, readiness y estado general del backend.
        </p>
      </div>

      {hasError ? (
        <Alert title="No se pudo cargar el estado del sistema">
          Revisa que el backend este levantado y que `VITE_API_BASE_URL` apunte al host correcto.
        </Alert>
      ) : null}

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Estado</CardTitle>
            <CardDescription>Estado basico de la API.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <MetricRow label="Estado" value={healthQuery.data?.status ?? "cargando"} />
            <MetricRow label="Servicio" value={healthQuery.data?.service ?? "-"} />
            <MetricRow label="Versión" value={healthQuery.data?.version ?? "-"} />
            <MetricRow label="Entorno" value={healthQuery.data?.env ?? "-"} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Listo</CardTitle>
            <CardDescription>Conectividad y runtime inicial del core.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <MetricRow label="Base de datos" value={boolLabel(readyQuery.data?.database_connected)} />
            <MetricRow label="Redis" value={boolLabel(readyQuery.data?.redis_configured)} />
            <MetricRow label="Plugins cargados" value={String(readyQuery.data?.plugins_loaded ?? 0)} />
            <MetricRow
              label="BD configurada"
              value={boolLabel(readyQuery.data?.database_configured)}
            />
          </CardContent>
        </Card>
      </div>

      {pluginRuntime.widgets.length > 0 ? (
        <div className="space-y-3">
          <div className="space-y-1">
            <h2 className="text-lg font-semibold text-foreground">Widgets de plugins</h2>
            <p className="text-sm text-muted-foreground">
              Componentes habilitados por el runtime persistente segun estado y permisos.
            </p>
          </div>

          <div className="grid gap-4 lg:grid-cols-2">
            {pluginRuntime.widgets.map((widget) => {
              const WidgetComponent = widget.component;

              return (
                <Card key={widget.id}>
                  <CardHeader>
                    <CardTitle>{widget.title}</CardTitle>
                    <CardDescription>{widget.pluginId}</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <WidgetComponent />
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>
      ) : null}
    </section>
  );
}

function MetricRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between rounded-md border border-border bg-muted/70 px-3 py-2">
      <span className="text-sm text-muted-foreground">{label}</span>
      <Badge>{value}</Badge>
    </div>
  );
}

function boolLabel(value: boolean | undefined) {
  if (value === undefined) {
    return "cargando";
  }

  return value ? "ok" : "no";
}
