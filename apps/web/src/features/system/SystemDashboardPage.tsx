import { useQuery } from "@tanstack/react-query";

import { getSystemHealth, getSystemReady } from "./api";
import { Alert } from "../../shared/ui/alert";
import { Badge } from "../../shared/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../shared/ui/card";

export function SystemDashboardPage() {
  const healthQuery = useQuery({
    queryKey: ["system", "health"],
    queryFn: getSystemHealth,
  });

  const readyQuery = useQuery({
    queryKey: ["system", "ready"],
    queryFn: getSystemReady,
  });

  const hasError = healthQuery.error || readyQuery.error;

  return (
    <section className="space-y-6">
      <div className="space-y-2">
        <h1 className="text-2xl font-semibold text-white">Dashboard del sistema</h1>
        <p className="text-sm text-slate-400">
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
            <CardTitle>Health</CardTitle>
            <CardDescription>Estado basico de la API.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <MetricRow label="Status" value={healthQuery.data?.status ?? "cargando"} />
            <MetricRow label="Service" value={healthQuery.data?.service ?? "-"} />
            <MetricRow label="Version" value={healthQuery.data?.version ?? "-"} />
            <MetricRow label="Environment" value={healthQuery.data?.env ?? "-"} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Ready</CardTitle>
            <CardDescription>Conectividad y runtime inicial del core.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <MetricRow label="Database" value={boolLabel(readyQuery.data?.database_connected)} />
            <MetricRow label="Redis" value={boolLabel(readyQuery.data?.redis_configured)} />
            <MetricRow label="Plugins loaded" value={String(readyQuery.data?.plugins_loaded ?? 0)} />
            <MetricRow
              label="Database configured"
              value={boolLabel(readyQuery.data?.database_configured)}
            />
          </CardContent>
        </Card>
      </div>
    </section>
  );
}

function MetricRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between rounded-md border border-slate-800 bg-slate-900/70 px-3 py-2">
      <span className="text-sm text-slate-400">{label}</span>
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
