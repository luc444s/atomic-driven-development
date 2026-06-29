import type { PluginFrontendContext, PluginFrontendRegistration } from "@systutor/sdk/frontend";

import { CustomerDetailPage } from "./pages/CustomerDetailPage";
import { CustomerFormPage } from "./pages/CustomerFormPage";
import { CustomersListPage } from "./pages/CustomersListPage";

export { CustomerSearchDialog } from "./components/CustomerSearchDialog";

export function registerPlugin(ctx: PluginFrontendContext): PluginFrontendRegistration {
  return {
    pluginId: "crm",
    routes: [
      {
        path: "crm/customers",
        title: "Clientes",
        component: CustomersListPage,
        requiredPermissions: ["crm.customer.read"],
      },
      {
        path: "crm/customers/new",
        title: "Nuevo cliente",
        component: CustomerFormPage,
        requiredPermissions: ["crm.customer.create"],
      },
      {
        path: "crm/customers/:customerId",
        title: "Editar cliente",
        component: CustomerFormPage,
        requiredPermissions: ["crm.customer.update"],
      },
      {
        path: "crm/customers/:customerId/detail",
        title: "Detalle cliente",
        component: CustomerDetailPage,
        requiredPermissions: ["crm.customer.read"],
      },
    ],
    navigation: [
      {
        to: `${ctx.appBasePath}/crm/customers`,
        label: "Clientes",
        requiredPermissions: ["crm.customer.read"],
      },
    ],
    widgets: [],
  };
}
