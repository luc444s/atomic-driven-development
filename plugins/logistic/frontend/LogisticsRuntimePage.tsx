export function LogisticsRuntimePage() {
  return (
    <section className="space-y-6">
      <div className="space-y-2">
        <h1 className="text-2xl font-semibold text-white">Logistics Runtime</h1>
        <p className="text-sm text-slate-400">
          Ruta frontend registrada por el plugin `logistics` a traves del runtime persistente.
        </p>
      </div>

      <div className="rounded-xl border border-slate-800 bg-slate-950/70 p-5 text-sm text-slate-300">
        El modulo piloto todavia no expone operaciones de negocio completas, pero ya puede registrar
        rutas, navegacion y widgets condicionados por estado persistente y permisos.
      </div>
    </section>
  );
}
