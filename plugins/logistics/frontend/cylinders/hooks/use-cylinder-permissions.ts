import { useAuthStore } from "../../../../../apps/web/src/features/auth/store";

export interface CylinderPermissions {
  canCreate: boolean;
  canUpdate: boolean;
  canTransition: boolean;
  canTrace: boolean;
  canMaintenance: boolean;
  canRetimbrado: boolean;
  canLabelPrint: boolean;
  canServiceManage: boolean;
  canServiceRead: boolean;
  canScan: boolean;
  canScanRead: boolean;
  canOwnershipRead: boolean;
  canWarehouseRead: boolean;
}

export function useCylinderPermissions(): CylinderPermissions {
  const permissions = useAuthStore((state) => state.permissions);

  return {
    canCreate: permissions.includes("logistics.cylinder.create"),
    canUpdate: permissions.includes("logistics.cylinder.update"),
    canTransition: permissions.includes("logistics.cylinder.transition"),
    canTrace: permissions.includes("logistics.cylinder.trace"),
    canMaintenance: permissions.includes("logistics.maintenance.manage"),
    canRetimbrado: permissions.includes("logistics.retimbrado.manage"),
    canLabelPrint: permissions.includes("logistics.label.print"),
    canServiceManage: permissions.includes("logistics.service.manage"),
    canServiceRead: permissions.includes("logistics.service.read"),
    canScan: permissions.includes("logistics.scan.execute"),
    canScanRead: permissions.includes("logistics.scan.read"),
    canOwnershipRead: permissions.includes("logistics.cylinder.ownership.read"),
    canWarehouseRead: permissions.includes("logistics.warehouse.read"),
  };
}
