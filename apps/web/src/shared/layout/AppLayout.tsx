import { useQuery } from "@tanstack/react-query";
import { LogOut } from "./icons";
import { Outlet, useNavigate } from "react-router-dom";
import { useEffect } from "react";

import { getCurrentUser } from "../../features/auth/api";
import { useAuthStore } from "../../features/auth/store";
import { ApiError } from "../api/client";
import { Sidebar } from "./Sidebar";
import { Button } from "../ui/button";

export function AppLayout() {
  const navigate = useNavigate();
  const token = useAuthStore((state) => state.token);
  const user = useAuthStore((state) => state.user);
  const setUser = useAuthStore((state) => state.setUser);
  const logout = useAuthStore((state) => state.logout);

  const currentUserQuery = useQuery({
    queryKey: ["auth", "me", token],
    queryFn: getCurrentUser,
    enabled: Boolean(token),
  });

  useEffect(() => {
    if (currentUserQuery.data) {
      setUser(currentUserQuery.data);
    }
  }, [currentUserQuery.data, setUser]);

  useEffect(() => {
    if (currentUserQuery.error instanceof ApiError && currentUserQuery.error.status === 401) {
      logout();
      navigate("/login", { replace: true });
    }
  }, [currentUserQuery.error, logout, navigate]);

  const currentUser = currentUserQuery.data ?? user;

  return (
    <div className="grid min-h-screen lg:grid-cols-[280px_1fr]">
      <div className="hidden lg:block">
        <Sidebar />
      </div>

      <div className="flex min-h-screen flex-col">
        <header className="flex items-center justify-between border-b border-slate-800 bg-slate-950/70 px-4 py-4 backdrop-blur lg:px-6">
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Core shell</p>
            <h1 className="text-lg font-semibold text-white">Operacion base del sistema</h1>
          </div>

          <div className="flex items-center gap-3">
            <div className="hidden text-right sm:block">
              <p className="text-sm font-medium text-slate-200">
                {currentUser?.full_name ?? "Cargando usuario..."}
              </p>
              <p className="text-xs text-slate-500">{currentUser?.email ?? "Sesion activa"}</p>
            </div>
            <Button
              type="button"
              variant="secondary"
              onClick={() => {
                logout();
                navigate("/login", { replace: true });
              }}
            >
              <LogOut />
              Logout
            </Button>
          </div>
        </header>

        <div className="border-b border-slate-800 bg-slate-950/60 p-4 lg:hidden">
          <Sidebar />
        </div>

        <main className="flex-1 px-4 py-6 lg:px-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
