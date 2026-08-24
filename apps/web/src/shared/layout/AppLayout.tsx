import { LogOut } from "./icons";
import { Outlet } from "react-router-dom";

import { useAuthBootstrap } from "../../features/auth/useAuthBootstrap";
import { useLogoutAction } from "../../features/auth/useLogoutAction";
import { useAuthStore } from "../../features/auth/store";
import { Sidebar } from "./Sidebar";
import { ShellHeader } from "./ShellHeader";
import { Button } from "@systutor/shell/ui/button";
import { ThemeToggle } from "./theme-toggle";

export function AppLayout() {
  const token = useAuthStore((state) => state.token);
  const user = useAuthStore((state) => state.user);
  const currentTenant = useAuthStore((state) => state.currentTenant);
  const currentBranch = useAuthStore((state) => state.currentBranch);
  const logout = useLogoutAction();
  const bootstrap = useAuthBootstrap();

  if (token && bootstrap.isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center text-sm text-muted-foreground">
        Cargando contexto del tenant...
      </div>
    );
  }

  return (
    <div className="flex h-screen overflow-hidden">
      <div className="h-screen w-60 shrink-0">
        <Sidebar />
      </div>

      <div className="flex h-screen min-w-0 flex-1 flex-col overflow-y-auto">
        <header className="flex items-center justify-between border-b border-border bg-surface/70 px-4 py-4 backdrop-blur lg:px-6">
          <ShellHeader
            tenantName={currentTenant?.name ?? null}
            branchName={currentBranch?.name ?? null}
            userName={user?.full_name ?? null}
            userEmail={user?.email ?? null}
          />

          <div className="flex items-center gap-3">
            <div className="hidden text-right sm:block">
              <p className="text-sm font-medium text-foreground">{user?.full_name ?? "Cargando usuario..."}</p>
              <p className="text-xs text-muted-foreground">{user?.email ?? "Sesion activa"}</p>
            </div>
            <Button type="button" variant="secondary" onClick={logout}>
              <LogOut />
              Cerrar sesión
            </Button>
          </div>
        </header>

        <main className="flex-1 px-4 py-6 lg:px-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
