import { apiRequest } from "@systutor/shell/api/client";
import { API_PREFIX, withQuery } from "./_shared";
import type { LogisticsCylinder } from "./cylinders";

export interface CylinderListFilters {
  search?: string;
  state?: string;
  active?: boolean;
  is_medical?: boolean;
  page?: number;
  per_page?: number;
}

export interface CylinderListPage {
  items: LogisticsCylinder[];
  pagination: {
    page: number;
    per_page: number;
    total: number;
    total_pages: number;
  };
}

export function listCylindersWithFilters(filters: CylinderListFilters) {
  return apiRequest<CylinderListPage>(
    withQuery(`${API_PREFIX}/cylinders/page`, {
      search: filters.search,
      state: filters.state,
      active: filters.active,
      is_medical: filters.is_medical,
      page: filters.page,
      per_page: filters.per_page,
    })
  );
}
