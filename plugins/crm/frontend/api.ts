import { apiRequest } from "../../../apps/web/src/shared/api/client";

import type {
  Customer,
  CustomerAddress,
  CustomerAddressPayload,
  CustomerBrief,
  CustomerContact,
  CustomerContactPayload,
  CustomerPage,
  CustomerPayload,
  DocumentType,
  GeographyItem,
  PaymentTerm,
} from "./types";

const CRM_BASE = "/api/v1/plugins/crm";

export const crmKeys = {
  all: ["crm"] as const,
  customers: {
    all: ["crm", "customers"] as const,
    list: (params: Record<string, unknown>) => ["crm", "customers", params] as const,
    detail: (customerId: string) => ["crm", "customers", customerId] as const,
    addresses: (customerId: string) => ["crm", "customers", customerId, "addresses"] as const,
    contacts: (customerId: string) => ["crm", "customers", customerId, "contacts"] as const,
    search: (query: string) => ["crm", "customers", "search", query] as const,
  },
  catalogs: {
    documentTypes: (countryCode: string | null) => ["crm", "catalog", "document-types", countryCode] as const,
    paymentTerms: ["crm", "catalog", "payment-terms"] as const,
  },
  geography: {
    countries: ["crm", "geography", "countries"] as const,
    departments: (countryCode: string) => ["crm", "geography", "departments", countryCode] as const,
    provinces: (departmentId: string) => ["crm", "geography", "provinces", departmentId] as const,
    districts: (provinceId: string) => ["crm", "geography", "districts", provinceId] as const,
  },
};

function buildQuery(params: Record<string, unknown>) {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null || value === "") {
      continue;
    }
    query.set(key, String(value));
  }
  const stringified = query.toString();
  return stringified ? `?${stringified}` : "";
}

export async function listCustomers(params: Record<string, unknown>): Promise<CustomerPage> {
  return apiRequest<CustomerPage>(`${CRM_BASE}/customers${buildQuery(params)}`);
}

export async function searchCustomers(query: string, limit = 20): Promise<CustomerBrief[]> {
  return apiRequest<CustomerBrief[]>(
    `${CRM_BASE}/customers/search${buildQuery({ query, limit })}`
  );
}

export async function getCustomer(customerId: string): Promise<Customer> {
  return apiRequest<Customer>(`${CRM_BASE}/customers/${customerId}`);
}

export async function createCustomer(payload: CustomerPayload): Promise<Customer> {
  return apiRequest<Customer>(`${CRM_BASE}/customers`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateCustomer(customerId: string, payload: Partial<CustomerPayload>): Promise<Customer> {
  return apiRequest<Customer>(`${CRM_BASE}/customers/${customerId}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export async function toggleCustomer(customerId: string, isActive: boolean, reason?: string | null): Promise<Customer> {
  return apiRequest<Customer>(`${CRM_BASE}/customers/${customerId}/toggle-active`, {
    method: "PATCH",
    body: JSON.stringify({ is_active: isActive, reason: reason ?? null }),
  });
}

export async function listCustomerAddresses(customerId: string): Promise<CustomerAddress[]> {
  return apiRequest<CustomerAddress[]>(`${CRM_BASE}/customers/${customerId}/addresses`);
}

export async function createCustomerAddress(customerId: string, payload: CustomerAddressPayload): Promise<CustomerAddress> {
  return apiRequest<CustomerAddress>(`${CRM_BASE}/customers/${customerId}/addresses`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateCustomerAddress(addressId: string, payload: Partial<CustomerAddressPayload> & { is_active?: boolean }): Promise<CustomerAddress> {
  return apiRequest<CustomerAddress>(`${CRM_BASE}/addresses/${addressId}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export async function setFiscalAddress(customerId: string, addressId: string): Promise<{ customer_id: string; fiscal_address_id: string }> {
  return apiRequest(`${CRM_BASE}/customers/${customerId}/fiscal-address/${addressId}`, {
    method: "PUT",
  });
}

export async function deleteCustomerAddress(addressId: string): Promise<void> {
  await apiRequest(`${CRM_BASE}/addresses/${addressId}`, { method: "DELETE" });
}

export async function listCustomerContacts(customerId: string): Promise<CustomerContact[]> {
  return apiRequest<CustomerContact[]>(`${CRM_BASE}/customers/${customerId}/contacts`);
}

export async function createCustomerContact(customerId: string, payload: CustomerContactPayload): Promise<CustomerContact> {
  return apiRequest<CustomerContact>(`${CRM_BASE}/customers/${customerId}/contacts`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function deleteCustomerContact(contactId: string): Promise<void> {
  await apiRequest(`${CRM_BASE}/contacts/${contactId}`, { method: "DELETE" });
}

export async function listDocumentTypes(countryCode?: string | null): Promise<DocumentType[]> {
  return apiRequest<DocumentType[]>(`${CRM_BASE}/catalog/document-types${buildQuery({ country_code: countryCode ?? null })}`);
}

export async function listPaymentTerms(): Promise<PaymentTerm[]> {
  return apiRequest<PaymentTerm[]>(`${CRM_BASE}/catalog/payment-terms`);
}

export async function listCountries(): Promise<GeographyItem[]> {
  return apiRequest<GeographyItem[]>(`${CRM_BASE}/geography/countries`);
}

export async function listDepartments(countryCode: string): Promise<GeographyItem[]> {
  return apiRequest<GeographyItem[]>(`${CRM_BASE}/geography/departments${buildQuery({ country_code: countryCode })}`);
}

export async function listProvinces(departmentId: string): Promise<GeographyItem[]> {
  return apiRequest<GeographyItem[]>(`${CRM_BASE}/geography/provinces${buildQuery({ department_id: departmentId })}`);
}

export async function listDistricts(provinceId: string): Promise<GeographyItem[]> {
  return apiRequest<GeographyItem[]>(`${CRM_BASE}/geography/districts${buildQuery({ province_id: provinceId })}`);
}
