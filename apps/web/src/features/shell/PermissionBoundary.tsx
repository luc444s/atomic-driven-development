import { ReactNode } from "react";
import { Navigate } from "react-router-dom";

import { useAuthStore } from "../auth/store";
import { hasRequiredPermissions } from "./permissions";

type PermissionBoundaryProps = {
  requiredPermissions?: string[];
  children: ReactNode;
};

export function PermissionBoundary({ requiredPermissions, children }: PermissionBoundaryProps) {
  const permissions = useAuthStore((state) => state.permissions);

  if (!hasRequiredPermissions(permissions, requiredPermissions)) {
    return <Navigate replace to="/app/system" />;
  }

  return <>{children}</>;
}
