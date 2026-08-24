import type { PluginFrontendContext, PluginFrontendRegistration } from "@systutor/sdk/frontend";
import { PurchaseOrdersPage } from "./pages/PurchaseOrdersPage";
import { SuppliersPage } from "./pages/SuppliersPage";

export function registerPlugin(ctx: PluginFrontendContext): PluginFrontendRegistration {
  return {
    pluginId: "compras",
    routes: [
      {
        path: "commerce/suppliers",
        title: "Proveedores",
        component: SuppliersPage,
        requiredPermissions: ["compras.supplier.read"],
      },
      {
        path: "commerce/purchase-orders",
        title: "Órdenes de compra",
        component: PurchaseOrdersPage,
        requiredPermissions: ["compras.order.read"],
      },
    ],
    navigation: [
      {
        to: `${ctx.appBasePath}/commerce/suppliers`,
        label: "Compras",
        requiredPermissions: ["compras.supplier.read"],
        group: "Gestión Comercial",
      },
    ],
    widgets: [],
  };
}
