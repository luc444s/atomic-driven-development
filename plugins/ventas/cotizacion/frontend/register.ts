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
      {
        to: `${ctx.appBasePath}/ventas/cotizacion`,
        label: "Cotización",
        requiredPermissions: ["ventas.cotizacion.create"],
        group: "Ventas",
      },
    ],
    widgets: [],
  };
}
