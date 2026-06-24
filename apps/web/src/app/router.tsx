import { createBrowserRouter, Navigate } from "react-router-dom";

import { LoginPage } from "../features/auth/LoginPage";
import { PluginRouteBoundary } from "../features/plugins/PluginRouteBoundary";
import { listFrontendPluginRegistrations } from "../features/plugins/runtime";
import { RequireAuth } from "../features/auth/RequireAuth";
import { PermissionBoundary } from "../features/shell/PermissionBoundary";
import { SettingsPage } from "../features/settings/SettingsPage";
import { PluginsPage } from "../features/system/PluginsPage";
import { SystemDashboardPage } from "../features/system/SystemDashboardPage";
import { AppLayout } from "../shared/layout/AppLayout";
import { useAuthStore } from "../features/auth/store";

function RootRedirect() {
  const token = useAuthStore((state) => state.token);
  return <Navigate replace to={token ? "/app/system" : "/login"} />;
}

const pluginRoutes = listFrontendPluginRegistrations().flatMap((registration) =>
  registration.routes.map((route) => {
    const RouteComponent = route.component;

    return {
      path: route.path,
      element: (
        <PluginRouteBoundary
          pluginId={registration.pluginId}
          requiredPermissions={route.requiredPermissions}
        >
          <RouteComponent />
        </PluginRouteBoundary>
      ),
    };
  })
);

export const appRouter = createBrowserRouter([
  {
    path: "/",
    element: <RootRedirect />,
  },
  {
    path: "/login",
    element: <LoginPage />,
  },
  {
    path: "/app",
    element: <RequireAuth />,
    children: [
      {
        element: <AppLayout />,
        children: [
          {
            index: true,
            element: <Navigate replace to="system" />,
          },
          {
            path: "system",
            element: <SystemDashboardPage />,
          },
          {
            path: "plugins",
            element: (
              <PermissionBoundary requiredPermissions={["core.plugin.read"]}>
                <PluginsPage />
              </PermissionBoundary>
            ),
          },
          {
            path: "settings/users",
            element: (
              <PermissionBoundary requiredPermissions={["core.users.read"]}>
                <SettingsPage
                  title="Users"
                  description="Administracion tenant-aware de usuarios del core."
                />
              </PermissionBoundary>
            ),
          },
          {
            path: "settings/roles",
            element: (
              <PermissionBoundary requiredPermissions={["core.roles.read"]}>
                <SettingsPage
                  title="Roles"
                  description="Administracion tenant-aware de roles y permisos efectivos."
                />
              </PermissionBoundary>
            ),
          },
          {
            path: "settings/branches",
            element: (
              <PermissionBoundary requiredPermissions={["core.branches.manage"]}>
                <SettingsPage
                  title="Branches"
                  description="Administracion tenant-aware de sucursales disponibles."
                />
              </PermissionBoundary>
            ),
          },
          ...pluginRoutes,
        ],
      },
    ],
  },
]);
