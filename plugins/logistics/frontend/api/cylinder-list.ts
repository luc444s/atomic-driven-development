import { apiRequest } from "../../../../apps/web/src/shared/api/client";
import { API_PREFIX, withQuery } from "./_shared";
import type { LogisticsCylinder } from "./cylinders";

export interface CylinderListFilters {
  search?: string;
  state?: string;
  active?: boolean;
  is_medical?: boolean;
}

export function listCylindersWithFilters(filters: CylinderListFilters) {
  return apiRequest<LogisticsCylinder[]>(
    withQuery(`${API_PREFIX}/cylinders`, {
      search: filters.search,
      state: filters.state,
      active: filters.active,
      is_medical: filters.is_medical,
    })
  );
}
