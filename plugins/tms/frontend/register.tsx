// Tipos locales del plugin — sin dependencia del shell.
export interface PluginFrontendContext {
  pluginId: string;
}

export interface PluginFrontendRegistration {
  pluginId: string;
  routes: unknown[];
  navigation: unknown[];
  widgets: unknown[];
}

export function registerPlugin(_ctx: PluginFrontendContext): PluginFrontendRegistration {
  return {
    pluginId: "tms",
    routes: [],
    navigation: [],
    widgets: [],
  };
}
