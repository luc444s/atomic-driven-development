import { useQuery } from "@tanstack/react-query";

import { getPlugins } from "./api";
import { ApiError } from "../../shared/api/client";
import { Alert } from "../../shared/ui/alert";
import { Badge } from "../../shared/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../shared/ui/card";

export function PluginsPage() {
  const pluginsQuery = useQuery({
    queryKey: ["system", "plugins"],
    queryFn: getPlugins,
  });

  const error = pluginsQuery.error;

  return (
    <section className="space-y-6">
      <div className="space-y-2">
        <h1 className="text-2xl font-semibold text-white">Runtime de plugins</h1>
        <p className="text-sm text-slate-400">
          Vista inicial del runtime. Todavia no expone administracion completa de instalacion,
          habilitacion o migraciones.
        </p>
      </div>

      {error instanceof ApiError && error.status === 403 ? (
        <Alert title="Sin permiso para listar plugins">
          El backend requiere `core.plugin.read` para consultar el runtime de plugins.
        </Alert>
      ) : null}

      {error && !(error instanceof ApiError && error.status === 403) ? (
        <Alert title="No se pudo cargar la lista de plugins">
          Verifica la API o el estado de autenticacion actual.
        </Alert>
      ) : null}

      <div className="grid gap-4 xl:grid-cols-2">
        {pluginsQuery.data?.map((plugin) => (
          <Card key={plugin.id}>
            <CardHeader>
              <div className="flex items-center justify-between gap-3">
                <CardTitle>{plugin.name}</CardTitle>
                <Badge>{plugin.version}</Badge>
              </div>
              <CardDescription>{plugin.description}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4 text-sm text-slate-300">
              <div className="grid gap-2 rounded-md border border-slate-800 bg-slate-900/70 p-3">
                <InfoLine label="Plugin ID" value={plugin.id} />
                <InfoLine label="API version" value={plugin.api_version} />
                <InfoLine label="Backend entrypoint" value={plugin.backend_entrypoint} />
                <InfoLine label="Frontend entrypoint" value={plugin.frontend_entrypoint} />
              </div>

              <TagBlock label="Permisos" values={plugin.permissions} />
              <TagBlock label="Eventos" values={plugin.events} />
              <TagBlock label="Dependencias" values={plugin.requires} emptyLabel="Sin dependencias" />
            </CardContent>
          </Card>
        ))}
      </div>

      {pluginsQuery.isSuccess && pluginsQuery.data?.length === 0 ? (
        <Alert title="No se encontraron plugins declarados">
          El runtime backend no reporto manifiestos disponibles.
        </Alert>
      ) : null}
    </section>
  );
}

function InfoLine({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
      <span className="text-slate-400">{label}</span>
      <span className="break-all text-slate-200">{value}</span>
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
