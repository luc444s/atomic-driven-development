import type { PluginFrontendContext, PluginFrontendRegistration } from "@systutor/sdk/frontend";
import { PurchaseOrdersPage } from "./pages/PurchaseOrdersPage";
import { DispatchesPage } from "./pages/DispatchesPage";

export function registerPlugin(ctx: PluginFrontendContext): PluginFrontendRegistration {
  return {
    pluginId: "compras",
    routes: [
      {
        path: "commerce/purchase-orders",
        title: "Compras",
        component: PurchaseOrdersPage,
        requiredPermissions: ["compras.order.read"],
      },
      {
        path: "commerce/dispatches",
        title: "Despachos",
        component: DispatchesPage,
        requiredPermissions: ["compras.dispatch.read"],
      },
    ],
    navigation: [
      {
        to: `${ctx.appBasePath}/commerce/purchase-orders`,
        label: "Compras",
        requiredPermissions: ["compras.order.read"],
        group: "Gestión Comercial",
      },
      {
        to: `${ctx.appBasePath}/commerce/dispatches`,
        label: "Despachos",
        requiredPermissions: ["compras.dispatch.read"],
        group: "Gestión Comercial",
      },
    ],
    widgets: [],
  };
}
