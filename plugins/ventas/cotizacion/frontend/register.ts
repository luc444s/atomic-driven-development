// ═══════════════════════════════════════════════════════════════════
// MODULO DESHABILITADO — La cotización queda fuera de servicio hasta
// que exista un módulo de ventas completo (facturación, pedidos,
// despacho). El registro de rutas se mantiene para que la página sea
// accesible vía URL directa durante desarrollo, pero la navegación
// del sidebar está suprimida.
// Fecha: 2026-08-06 — ver AGENTS.md memoria de sesión.
// ═══════════════════════════════════════════════════════════════════

import type {
  PluginFrontendContext,
  PluginFrontendRegistration,
} from "@systutor/sdk/frontend";

import { CotizacionPage } from "./pages/CotizacionPage";

export function registerPlugin(ctx: PluginFrontendContext): PluginFrontendRegistration {
  return {
    pluginId: "ventas",
    routes: [
      {
        path: "ventas/cotizacion",
        title: "Cotización",
        component: CotizacionPage,
        requiredPermissions: ["ventas.cotizacion.create"],
      },
    ],
    navigation: [
      // Suprimido: la cotización no tiene sentido sin módulo de ventas completo.
      // {
      //   to: `${ctx.appBasePath}/ventas/cotizacion`,
      //   label: "Cotización",
      //   requiredPermissions: ["ventas.cotizacion.create"],
      //   group: "Ventas",
      // },
    ],
    widgets: [],
  };
}
