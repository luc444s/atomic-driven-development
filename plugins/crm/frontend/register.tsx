import { useParams } from "../../../apps/web/src/lib/router";
import type { PluginFrontendContext, PluginFrontendRegistration } from "@systutor/sdk/frontend";

import { ModalDetalleCliente } from "./components/ModalDetalleCliente";
import { ModalNuevoCliente } from "./components/ModalNuevoCliente";
import { CustomersListPage } from "./pages/CustomersListPage";

export { CustomerSearchDialog } from "./components/CustomerSearchDialog";
export { ModalNuevoCliente, ModalDetalleCliente };

function NuevoClienteFallback() {
  return <ModalNuevoCliente open onClose={() => window.history.back()} asPage />;
}

function EditarClienteFallback() {
  const { customerId } = useParams();
  return <ModalNuevoCliente open customerId={customerId} onClose={() => window.history.back()} asPage />;
}

function DetalleClienteFallback() {
  const { customerId } = useParams();
  return <ModalDetalleCliente open customerId={customerId!} onClose={() => window.history.back()} asPage />;
}

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
        component: NuevoClienteFallback,
        requiredPermissions: ["crm.customer.create"],
      },
      {
        path: "crm/customers/:customerId",
        title: "Editar cliente",
        component: EditarClienteFallback,
        requiredPermissions: ["crm.customer.update"],
      },
      {
        path: "crm/customers/:customerId/detail",
        title: "Detalle cliente",
        component: DetalleClienteFallback,
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
