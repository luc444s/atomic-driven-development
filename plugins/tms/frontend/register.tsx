import type { PluginFrontendContext, PluginFrontendRegistration } from "@systutor/sdk/frontend";

export function registerPlugin(_ctx: PluginFrontendContext): PluginFrontendRegistration {
  return {
    pluginId: "tms",
    routes: [],
    navigation: [],
    widgets: [],
  };
}
