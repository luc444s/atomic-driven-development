import { Badge } from "../../../apps/web/src/shared/ui/badge";

const STATE_CLASSNAMES: Record<string, string> = {
  EN_ALMACEN_VACIO: "border-slate-600 bg-slate-900 text-slate-100",
  LLENADO_OK: "border-emerald-700 bg-emerald-500/10 text-emerald-200",
  CARGA_EN_VEHICULO: "border-cyan-700 bg-cyan-500/10 text-cyan-200",
  EN_RUTA: "border-amber-700 bg-amber-500/10 text-amber-100",
  EN_CLIENTE_LLENO: "border-blue-700 bg-blue-500/10 text-blue-200",
  EN_CLIENTE_VACIO: "border-indigo-700 bg-indigo-500/10 text-indigo-200",
  EN_MANTENIMIENTO: "border-orange-700 bg-orange-500/10 text-orange-200",
  PARA_REPARACION: "border-orange-700 bg-orange-500/10 text-orange-200",
  OBSERVADO: "border-rose-700 bg-rose-500/10 text-rose-200",
  BLOQUEADO: "border-rose-700 bg-rose-500/10 text-rose-200",
  DE_BAJA: "border-slate-600 bg-slate-950 text-slate-300",
  PERDIDO: "border-slate-600 bg-slate-950 text-slate-300",
};

const STATE_LABELS: Record<string, string> = {
  CREADO_VACIO: "Nuevo",
  EN_ALMACEN_VACIO: "Disponible",
  EN_LLENADO: "En llenado",
  LLENADO_OK: "Listo",
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
