import { LogisticsRuntimePage } from "./LogisticsRuntimePage";
import { LogisticsSummaryWidget } from "./LogisticsSummaryWidget";

import type {
  PluginFrontendContext,
  PluginFrontendRegistration,
} from "../../../apps/web/src/features/plugins/runtime";

export function registerPlugin(ctx: PluginFrontendContext): PluginFrontendRegistration {
  return {
    pluginId: "logistics",
    routes: [
      {
        path: "logistics",
        title: "Logistics",
        component: LogisticsRuntimePage,
        requiredPermissions: ["logistics.delivery.read"],
      },
    ],
    navigation: [
      {
        to: `${ctx.appBasePath}/logistics`,
        label: "Logistics",
        requiredPermissions: ["logistics.delivery.read"],
      },
    ],
    widgets: [
      {
        id: "logistics.runtime.summary",
        slot: "system.dashboard",
        title: "Logistics",
        component: LogisticsSummaryWidget,
        requiredPermissions: ["logistics.delivery.read"],
      },
    ],
  };
}
