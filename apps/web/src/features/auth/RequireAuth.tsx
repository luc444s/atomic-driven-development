import { Navigate, Outlet, useLocation } from "react-router-dom";

import { useAuthStore } from "./store";

export function RequireAuth() {
  const token = useAuthStore((state) => state.token);
  const location = useLocation();

  if (!token) {
    return <Navigate replace to="/login" state={{ from: location }} />;
  }

  return <Outlet />;
}
