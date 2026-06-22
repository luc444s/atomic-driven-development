import { createBrowserRouter, Navigate } from "react-router-dom";

import { LoginPage } from "../features/auth/LoginPage";
import { RequireAuth } from "../features/auth/RequireAuth";
import { PluginsPage } from "../features/system/PluginsPage";
import { SystemDashboardPage } from "../features/system/SystemDashboardPage";
import { AppLayout } from "../shared/layout/AppLayout";
import { useAuthStore } from "../features/auth/store";

function RootRedirect() {
  const token = useAuthStore((state) => state.token);
  return <Navigate replace to={token ? "/app/system" : "/login"} />;
}

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
            element: <PluginsPage />,
          },
        ],
      },
    ],
  },
]);
