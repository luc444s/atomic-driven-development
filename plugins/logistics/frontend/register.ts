import type {
  PluginFrontendContext,
  PluginFrontendRegistration,
} from "@systutor/sdk/frontend";

import { AgendaPage } from "./pages/AgendaPage";
import { CylindersPage } from "./pages/CylindersPage";
import { DeliveryPointsPage } from "./pages/DeliveryPointsPage";
import { LoadsPage } from "./pages/LoadsPage";
import { MovementsPage } from "./pages/MovementsPage";
import { OrdersPage } from "./pages/OrdersPage";
import { RoutesPage } from "./pages/RoutesPage";
import { VehiclesPage } from "./pages/VehiclesPage";
import { WarehousesPage } from "./pages/WarehousesPage";
import { LogisticsPage } from "./LogisticsPage";
import { LogisticsSummaryWidget } from "./LogisticsSummaryWidget";

export function registerPlugin(ctx: PluginFrontendContext): PluginFrontendRegistration {
  return {
    pluginId: "logistics",
    routes: [
      {
        path: "logistics",
        title: "Logistics",
        component: LogisticsPage,
        requiredPermissions: ["logistics.cylinder.read"],
      },
      {
        path: "logistics/cylinders",
        title: "Envases",
        component: CylindersPage,
        requiredPermissions: ["logistics.cylinder.read"],
      },
      {
        path: "logistics/orders",
        title: "Pedidos",
        component: OrdersPage,
        requiredPermissions: ["logistics.order.read"],
      },
      {
        path: "logistics/routes",
        title: "Rutas",
        component: RoutesPage,
        requiredPermissions: ["logistics.route.read"],
      },
      {
        path: "logistics/loads",
        title: "Carga",
        component: LoadsPage,
        requiredPermissions: ["logistics.load.manage"],
      },
      {
        path: "logistics/movements",
        title: "Movimientos",
        component: MovementsPage,
        requiredPermissions: ["logistics.movement.read"],
      },
      {
        path: "logistics/agenda",
        title: "Agenda",
        component: AgendaPage,
        requiredPermissions: ["logistics.agenda.read"],
      },
      {
        path: "logistics/warehouses",
        title: "Almacenes",
        component: WarehousesPage,
        requiredPermissions: ["logistics.warehouse.read"],
      },
      {
        path: "logistics/vehicles",
        title: "Vehículos",
        component: VehiclesPage,
        requiredPermissions: ["logistics.vehicle.read"],
      },
      {
        path: "logistics/delivery-points",
        title: "Puntos de entrega",
        component: DeliveryPointsPage,
        requiredPermissions: ["logistics.route.read"],
      },
    ],
    navigation: [
      {
        to: `${ctx.appBasePath}/logistics`,
        label: "Logistics",
        requiredPermissions: ["logistics.cylinder.read"],
      },
    ],
    widgets: [
      {
        id: "logistics.runtime.summary",
        slot: "system.dashboard",
        title: "Logistics",
        component: LogisticsSummaryWidget,
        requiredPermissions: ["logistics.cylinder.read"],
      },
    ],
  };
}
