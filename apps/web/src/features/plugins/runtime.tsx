import type { ComponentType } from "react";

import { useAuthStore } from "../auth/store";
import { hasRequiredPermissions } from "../shell/permissions";
import type { PluginRuntimeRecord } from "../../shared/api/client";

export type PluginFrontendRoute = {
  path: string;
  title: string;
  component: ComponentType;
  requiredPermissions?: string[];
};

export type PluginSidebarEntry = {
  to: string;
  label: string;
  requiredPermissions?: string[];
};

export type PluginWidget = {
  id: string;
  slot: "system.dashboard";
  title: string;
  component: ComponentType;
  requiredPermissions?: string[];
};

export type PluginFrontendRegistration = {
  pluginId: string;
  routes: PluginFrontendRoute[];
  navigation: PluginSidebarEntry[];
  widgets: PluginWidget[];
};

export type PluginFrontendContext = {
  appBasePath: string;
};

type FrontendPluginModule = {
  registerPlugin: (ctx: PluginFrontendContext) => PluginFrontendRegistration;
};

type FrontendRuntimeInput = {
  records: PluginRuntimeRecord[];
  registrations: PluginFrontendRegistration[];
  userPermissions: string[];
};

const EMPTY_PERMISSIONS: string[] = [];

const frontendPluginModules = import.meta.glob<FrontendPluginModule>(
  "../../../../../plugins/*/frontend/register.ts",
  { eager: true }
);

export function listFrontendPluginRegistrations(): PluginFrontendRegistration[] {
  return Object.values(frontendPluginModules)
    .map((module) => module.registerPlugin({ appBasePath: "/app" }))
    .sort((left, right) => left.pluginId.localeCompare(right.pluginId));
}

export function buildFrontendPluginRuntime({
  records,
  registrations,
  userPermissions,
}: FrontendRuntimeInput) {
  const recordsById = new Map(records.map((record) => [record.plugin_id, record]));

  const routes: Array<PluginFrontendRoute & { pluginId: string }> = [];
  const navigation: Array<PluginSidebarEntry & { pluginId: string }> = [];
  const widgets: Array<PluginWidget & { pluginId: string }> = [];

  for (const registration of registrations) {
    const record = recordsById.get(registration.pluginId);
    const isEnabled = record?.state === "enabled" && record.is_enabled;
    if (!isEnabled) {
      continue;
    }

    for (const route of registration.routes) {
      if (!hasRequiredPermissions(userPermissions, route.requiredPermissions)) {
        continue;
      }
      routes.push({ ...route, pluginId: registration.pluginId });
    }

    for (const navEntry of registration.navigation) {
      if (!hasRequiredPermissions(userPermissions, navEntry.requiredPermissions)) {
        continue;
      }
      navigation.push({ ...navEntry, pluginId: registration.pluginId });
    }

    for (const widget of registration.widgets) {
      if (!hasRequiredPermissions(userPermissions, widget.requiredPermissions)) {
        continue;
      }
      widgets.push({ ...widget, pluginId: registration.pluginId });
    }
  }

  return {
    recordsById,
    routes,
    navigation,
    widgets,
  };
}

export function usePluginFrontendRuntime() {
  const userPermissions = useAuthStore((state) => state.permissions ?? EMPTY_PERMISSIONS);
  const pluginRuntimeRecords = useAuthStore((state) => state.pluginRuntimeRecords);
  const registrations = listFrontendPluginRegistrations();
  const resolvedRuntime = buildFrontendPluginRuntime({
    records: pluginRuntimeRecords,
    registrations,
    userPermissions,
  });

  return {
    isLoading: false,
    error: null,
    registrations,
    ...resolvedRuntime,
  };
}
