import { apiRequest } from "@systutor/shell/api/client";

import type {
  CommercialUserOption,
  Customer,
  CustomerAddress,
  CustomerAddressPayload,
  CustomerBankAccount,
  CustomerBankAccountPayload,
  CustomerBrief,
  CustomerCommercialAssignment,
  CustomerCommercialAssignmentPayload,
  CustomerContact,
  CustomerContactPayload,
  CustomerPage,
  CustomerPayload,
  CustomerPricingTerm,
  CustomerPricingTermPayload,
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
    commercialAssignments: (customerId: string) => ["crm", "customers", customerId, "commercial-assignments"] as const,
    bankAccounts: (customerId: string) => ["crm", "customers", customerId, "bank-accounts"] as const,
    pricingTerms: (customerId: string) => ["crm", "customers", customerId, "pricing-terms"] as const,
    search: (query: string) => ["crm", "customers", "search", query] as const,
  },
  commercial: {
    users: ["crm", "commercial", "users"] as const,
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

export async function searchCustomers(query: string, limit = 10): Promise<CustomerBrief[]> {
  if (!query.trim()) return [];
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

export async function listCustomerAddressesWithGps(): Promise<CustomerAddress[]> {
  return apiRequest<CustomerAddress[]>(`${CRM_BASE}/customers/addresses-gps`);
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

export async function updateCustomerContact(contactId: string, payload: Partial<CustomerContactPayload> & { is_active?: boolean }): Promise<CustomerContact> {
  return apiRequest<CustomerContact>(`${CRM_BASE}/contacts/${contactId}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export async function deleteCustomerContact(contactId: string): Promise<void> {
  await apiRequest(`${CRM_BASE}/contacts/${contactId}`, { method: "DELETE" });
}

export async function listCommercialUsers(): Promise<CommercialUserOption[]> {
  return apiRequest<CommercialUserOption[]>(`${CRM_BASE}/commercial/users`);
}

export async function listCustomerCommercialAssignments(customerId: string): Promise<CustomerCommercialAssignment[]> {
  return apiRequest<CustomerCommercialAssignment[]>(`${CRM_BASE}/customers/${customerId}/commercial-assignments`);
}

export async function createCustomerCommercialAssignment(
  customerId: string,
  payload: CustomerCommercialAssignmentPayload
): Promise<CustomerCommercialAssignment> {
  return apiRequest<CustomerCommercialAssignment>(`${CRM_BASE}/customers/${customerId}/commercial-assignments`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateCustomerCommercialAssignment(
  assignmentId: string,
  payload: Partial<CustomerCommercialAssignmentPayload>
): Promise<CustomerCommercialAssignment> {
  return apiRequest<CustomerCommercialAssignment>(`${CRM_BASE}/commercial-assignments/${assignmentId}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export async function deleteCustomerCommercialAssignment(assignmentId: string): Promise<void> {
  await apiRequest(`${CRM_BASE}/commercial-assignments/${assignmentId}`, { method: "DELETE" });
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

export async function listCustomerBankAccounts(customerId: string): Promise<CustomerBankAccount[]> {
  return apiRequest<CustomerBankAccount[]>(`${CRM_BASE}/customers/${customerId}/bank-accounts`);
}

export async function createCustomerBankAccount(
  customerId: string,
  payload: CustomerBankAccountPayload
): Promise<CustomerBankAccount> {
  return apiRequest<CustomerBankAccount>(`${CRM_BASE}/customers/${customerId}/bank-accounts`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateCustomerBankAccount(
  bankAccountId: string,
  payload: Partial<CustomerBankAccountPayload> & { is_active?: boolean }
): Promise<CustomerBankAccount> {
  return apiRequest<CustomerBankAccount>(`${CRM_BASE}/bank-accounts/${bankAccountId}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export async function deleteCustomerBankAccount(bankAccountId: string): Promise<void> {
  await apiRequest(`${CRM_BASE}/bank-accounts/${bankAccountId}`, { method: "DELETE" });
}

export async function listCustomerPricingTerms(customerId: string): Promise<CustomerPricingTerm[]> {
  return apiRequest<CustomerPricingTerm[]>(`${CRM_BASE}/customers/${customerId}/pricing-terms`);
}

export async function createCustomerPricingTerm(
  customerId: string,
  payload: CustomerPricingTermPayload
): Promise<CustomerPricingTerm> {
  return apiRequest<CustomerPricingTerm>(`${CRM_BASE}/customers/${customerId}/pricing-terms`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateCustomerPricingTerm(
  pricingTermId: string,
  payload: Partial<CustomerPricingTermPayload> & { is_active?: boolean }
): Promise<CustomerPricingTerm> {
  return apiRequest<CustomerPricingTerm>(`${CRM_BASE}/pricing-terms/${pricingTermId}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export async function deleteCustomerPricingTerm(pricingTermId: string): Promise<void> {
  await apiRequest(`${CRM_BASE}/pricing-terms/${pricingTermId}`, { method: "DELETE" });
}
