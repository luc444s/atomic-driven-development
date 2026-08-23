import { apiRequest } from "@systutor/shell/api/client";

import { API_PREFIX } from "./_shared";

export type CustomerCylinderConditionSummary = {
  assigned: number;
  at_customer: number;
  pipeline: number;
  lost: number;
};

export type CustomerCylinderPipeline = {
  total: number;
  in_vehicle: number;
  in_transit: number;
  in_warehouse: number;
  unknown: number;
};

export type CustomerCylinderProductSummary = {
  product_id: string | null;
  product_name: string;
  contracted: number;
  assigned: number;
  at_customer: number;
  at_customer_unknown: number;
  pipeline: CustomerCylinderPipeline;
  lost: number;
  deviation: number;
  customer_address_id: string | null;
  address_label: string | null;
  by_condition: Record<string, CustomerCylinderConditionSummary>;
};

export type CustomerCylinderAlert = {
  severity: string;
  category: string;
  message: string;
};

export type CustomerCylinderContractSnapshot = {
  contract_id: string | null;
  status: string;
  active_contract_count: number;
  contract_ids: string[];
};

export type CustomerCylinderTotals = {
  contracted: number;
  assigned: number;
  at_customer: number;
  at_customer_unknown: number;
  pipeline: number;
  lost: number;
  deviation: number;
};

export type CustomerCylinderSummary = {
  customer_id: string;
  customer_name: string;
  contract: CustomerCylinderContractSnapshot;
  summary: CustomerCylinderTotals;
  by_product: CustomerCylinderProductSummary[];
  alerts: CustomerCylinderAlert[];
};

export function getCustomerCylinderSummary(customerId: string) {
  return apiRequest<CustomerCylinderSummary>(
    `${API_PREFIX}/customers/${customerId}/cylinders/summary`
  );
}
