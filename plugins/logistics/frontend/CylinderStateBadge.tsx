import { Badge } from "../../../apps/web/src/shared/ui/badge";

const STATE_CLASSNAMES: Record<string, string> = {
  EN_ALMACEN_VACIO: "border-slate-400 dark:border-slate-600 bg-slate-100 dark:bg-slate-900 text-slate-700 dark:text-slate-100",
  LLENADO_OK: "border-emerald-400 dark:border-emerald-700 bg-emerald-50 dark:bg-emerald-500/10 text-emerald-700 dark:text-emerald-200",
  CARGA_EN_VEHICULO: "border-cyan-400 dark:border-cyan-700 bg-cyan-50 dark:bg-cyan-500/10 text-cyan-700 dark:text-cyan-200",
  EN_RUTA: "border-amber-400 dark:border-amber-700 bg-amber-50 dark:bg-amber-500/10 text-amber-700 dark:text-amber-100",
  EN_CLIENTE_LLENO: "border-blue-400 dark:border-blue-700 bg-blue-50 dark:bg-blue-500/10 text-blue-700 dark:text-blue-200",
  EN_CLIENTE_VACIO: "border-indigo-400 dark:border-indigo-700 bg-indigo-50 dark:bg-indigo-500/10 text-indigo-700 dark:text-indigo-200",
  EN_MANTENIMIENTO: "border-orange-400 dark:border-orange-700 bg-orange-50 dark:bg-orange-500/10 text-orange-700 dark:text-orange-200",
  PARA_REPARACION: "border-orange-400 dark:border-orange-700 bg-orange-50 dark:bg-orange-500/10 text-orange-700 dark:text-orange-200",
  OBSERVADO: "border-rose-400 dark:border-rose-700 bg-rose-50 dark:bg-rose-500/10 text-rose-700 dark:text-rose-200",
  BLOQUEADO: "border-rose-400 dark:border-rose-700 bg-rose-50 dark:bg-rose-500/10 text-rose-700 dark:text-rose-200",
  DE_BAJA: "border-slate-400 dark:border-slate-600 bg-slate-200 dark:bg-slate-950 text-slate-600 dark:text-slate-300",
  PERDIDO: "border-slate-400 dark:border-slate-600 bg-slate-200 dark:bg-slate-950 text-slate-600 dark:text-slate-300",
};

const STATE_LABELS: Record<string, string> = {
  CREADO_VACIO: "Nuevo",
  EN_ALMACEN_VACIO: "Vacío",
  EN_LLENADO: "En llenado",
  LLENADO_OK: "Lleno",
  CARGA_EN_VEHICULO: "Cargado",
  EN_RUTA: "En camino",
  EN_CLIENTE_LLENO: "En cliente",
  EN_CLIENTE_VACIO: "Por devolver",
  VACIO_EN_ALMACEN: "Devuelto",
  DESCARGADO_POR_RECEPCIONAR: "Pendiente",
  RECEPCIONADO: "Recibido",
  EN_MANTENIMIENTO: "Mantenimiento",
  PARA_REPARACION: "Reparacion",
  PARA_TRASLADO: "Traslado",
  OBSERVADO: "Observado",
  BLOQUEADO: "Bloqueado",
  DE_BAJA: "Baja",
  PERDIDO: "Perdido",
};

export function getCylinderStateLabel(state: string) {
  return STATE_LABELS[state] ?? state;
}

export function CylinderStateBadge({ state }: { state: string }) {
  return <Badge className={STATE_CLASSNAMES[state]}>{getCylinderStateLabel(state)}</Badge>;
}
