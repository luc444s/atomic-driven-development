import type { PluginFrontendContext, PluginFrontendRegistration } from "@systutor/sdk/frontend";
import { PurchaseOrdersPage } from "./pages/PurchaseOrdersPage";

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
    ],
    navigation: [
      {
        to: `${ctx.appBasePath}/commerce/purchase-orders`,
        label: "Compras",
        requiredPermissions: ["compras.order.read"],
        group: "Gestión Comercial",
      },
    ],
    widgets: [],
  };
}
