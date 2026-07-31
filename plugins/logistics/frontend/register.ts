import type {
  PluginFrontendContext,
  PluginFrontendRegistration,
} from "@systutor/sdk/frontend";

import { AgendaPage } from "./pages/AgendaPage";
import { CylindersPage } from "./pages/CylindersPage";
import { EquipmentPage } from "./pages/EquipmentPage";
import { LoadsPage } from "./pages/LoadsPage";
import { MovementsPage } from "./pages/MovementsPage";
import { OrdersPage } from "./pages/OrdersPage";
import { PlanningPage } from "./pages/PlanningPage";
import { ReceptionPage } from "./pages/ReceptionPage";
import { RoutesPage } from "./pages/RoutesPage";
import { VehiclesPage } from "./pages/VehiclesPage";
import { WarehousesPage } from "./pages/WarehousesPage";
import { ContractsPage } from "./pages/ContractsPage";
import { VehicleSessionDetailPage } from "./pages/VehicleSessionDetailPage";
import { VehicleSessionsPage } from "./pages/VehicleSessionsPage";
import { LogisticsSummaryWidget } from "./LogisticsSummaryWidget";

export function registerPlugin(ctx: PluginFrontendContext): PluginFrontendRegistration {
  return {
    pluginId: "logistics",
    routes: [
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
        path: "logistics/planning",
        title: "Planificación",
        component: PlanningPage,
        requiredPermissions: ["logistics.order.read"],
      },
      {
        path: "logistics/reception",
        title: "Recepción",
        component: ReceptionPage,
        requiredPermissions: ["logistics.movement.read"],
      },
      {
        path: "logistics/equipment",
        title: "Equipos",
        component: EquipmentPage,
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
        path: "logistics/contracts",
        title: "Contratos",
        component: ContractsPage,
        requiredPermissions: ["logistics.contract.view"],
      },
      {
        path: "logistics/vehicle-sessions",
        title: "Jornadas",
        component: VehicleSessionsPage,
        requiredPermissions: ["logistics.session.read"],
      },
      {
        path: "logistics/vehicle-sessions/:sessionId",
        title: "Detalle de jornada",
        component: VehicleSessionDetailPage,
        requiredPermissions: ["logistics.session.read"],
      },
    ],
    navigation: [
      { to: `${ctx.appBasePath}/logistics/vehicle-sessions`, label: "Jornadas", requiredPermissions: ["logistics.session.read"], group: "Logistics" },
      { to: `${ctx.appBasePath}/logistics/cylinders`, label: "Envases", requiredPermissions: ["logistics.cylinder.read"], group: "Logistics" },
      { to: `${ctx.appBasePath}/logistics/equipment`, label: "Equipos", requiredPermissions: ["logistics.movement.read"], group: "Logistics" },
      { to: `${ctx.appBasePath}/logistics/warehouses`, label: "Almacenes", requiredPermissions: ["logistics.warehouse.read"], group: "Logistics" },
      { to: `${ctx.appBasePath}/logistics/contracts`, label: "Contratos", requiredPermissions: ["logistics.contract.view"], group: "Logistics" },
      { to: `${ctx.appBasePath}/logistics/planning`, label: "Planificacion", requiredPermissions: ["logistics.order.read"], group: "Logistics" },
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
