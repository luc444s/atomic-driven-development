import { API_PREFIX, withQuery } from "./_shared";
import { apiRequest } from "../../../../apps/web/src/shared/api/client";

export type LogisticsCylinderContract = {
  id: string;
  document_type_code: number;
  document_prefix: string;
  warehouse_id: string | null;
  series: string | null;
  number: number | null;
  contract_number: string | null;
  contract_type: string;
  status: string;
  customer_id: string;
  customer_name: string | null;
  start_date: string;
  end_date: string | null;
  renewal_type: string | null;
  cylinder_type_id: string | null;
  cylinder_condition: string | null;
  quantity: number;
  unit_price: number;
  signed_flag: boolean;
  signed_at: string | null;
  signed_by: string | null;
  signature_type: string | null;
  contract_file_path: string | null;
  notes: string | null;
  observations: string | null;
  excess_wait_days: number;
  auto_renew_on_excess: boolean;
  source_contract_id: string | null;
  created_at: string;
};

export type LogisticsContractType = {
  code: string;
  name: string;
  duration_unit: string;
  duration_value: number;
};

export type LogisticsContractHistory = {
  id: string;
  contract_id: string;
  event_type: string;
  description: string | null;
  occurred_at: string;
  created_by: string | null;
};

export type CoreDocumentVersion = {
  id: string;
  tenant_id: string;
  module: string;
  entity_type: string;
  entity_id: string;
  template_code: string;
  version_number: number;
  status: string;
  title: string | null;
  file_path: string;
  sha256: string;
  created_by: string | null;
  created_at: string;
};

export type CoreDocumentSignedDownload = {
  url: string;
  expires_at: string;
};

export type CoreSignatureSession = {
  id: string;
  tenant_id: string;
  document_version_id: string;
  signer_name: string | null;
  signer_email: string | null;
  signer_phone: string | null;
  signer_role: string | null;
  provider: string;
  status: string;
  verification_channel: string;
  verification_ref: string | null;
  completed_at: string | null;
  created_at: string;
};

export type CreateContractPayload = {
  contract_type: string;
  customer_id: string;
  warehouse_id: string;
  start_date: string;
  end_date?: string | null;
  renewal_type?: string | null;
  cylinder_type_id?: string | null;
  cylinder_condition?: string | null;
  quantity: number;
  unit_price: number;
  contract_file_path?: string | null;
  notes?: string | null;
  observations?: string | null;
  excess_wait_days?: number;
  auto_renew_on_excess?: boolean;
  source_contract_id?: string | null;
};

export type UpdateContractPayload = Partial<CreateContractPayload>;

export type ContractExcessPolicyPayload = {
  excess_wait_days?: number;
  auto_renew_on_excess?: boolean;
};

export type ContractExcessTracking = {
  id: string;
  customer_id: string;
  cylinder_type_id: string;
  product_name: string | null;
  excess_qty: number;
  first_detected_at: string;
  last_seen_at: string;
  excess_wait_days: number;
  auto_renew_on_excess: boolean;
  base_unit_price: number;
  base_contract_type: string;
  status: string;
  resolved_reason: string | null;
  created_contract_id: string | null;
  contract_number: string | null;
  days_pending: number | null;
};

export type TerminateContractPayload = {
  reason: string;
};

export type RenewContractPayload = {
  end_date: string;
  renewal_type?: string | null;
  notes?: string | null;
  observations?: string | null;
};

export type SignContractPayload = {
  signed_at?: string | null;
  signed_by?: string | null;
  signer_name?: string | null;
  signer_email?: string | null;
  signer_phone?: string | null;
  signature_type?: string | null;
  contract_file_path?: string | null;
};

export function listContractTypes() {
  return apiRequest<LogisticsContractType[]>(`${API_PREFIX}/cylinders/contracts/types`);
}

export function listContracts(filters: {
  customer_id?: string;
  status?: string;
  type?: string;
  date_from?: string;
  date_to?: string;
}) {
  return apiRequest<LogisticsCylinderContract[]>(
    withQuery(`${API_PREFIX}/cylinders/contracts`, {
      customer_id: filters.customer_id,
      status: filters.status,
      type: filters.type,
      date_from: filters.date_from,
      date_to: filters.date_to,
    })
  );
}

export function getContract(contractId: string) {
  return apiRequest<LogisticsCylinderContract>(
    `${API_PREFIX}/cylinders/contracts/${contractId}`
  );
}

export function createContract(payload: CreateContractPayload) {
  return apiRequest<LogisticsCylinderContract>(
    `${API_PREFIX}/cylinders/contracts`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    }
  );
}

export function updateContract(contractId: string, payload: UpdateContractPayload) {
  return apiRequest<LogisticsCylinderContract>(
    `${API_PREFIX}/cylinders/contracts/${contractId}`,
    {
      method: "PATCH",
      body: JSON.stringify(payload),
    }
  );
}

export function activateContract(contractId: string) {
  return apiRequest<LogisticsCylinderContract>(
    `${API_PREFIX}/cylinders/contracts/${contractId}/issue`,
    { method: "POST", body: JSON.stringify({}) }
  );
}

export function signContract(contractId: string, payload: SignContractPayload = {}) {
  return apiRequest<LogisticsCylinderContract>(
    `${API_PREFIX}/cylinders/contracts/${contractId}/sign`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    }
  );
}

export function uploadContractFile(contractId: string, file: File) {
  const form = new FormData();
  form.append("file", file);
  return apiRequest<LogisticsCylinderContract>(
    `${API_PREFIX}/cylinders/contracts/${contractId}/file`,
    {
      method: "POST",
      body: form,
    }
  );
}

export function terminateContract(contractId: string, payload: TerminateContractPayload) {
  return apiRequest<LogisticsCylinderContract>(
    `${API_PREFIX}/cylinders/contracts/${contractId}/terminate`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    }
  );
}

export function cancelContract(contractId: string) {
  return apiRequest<LogisticsCylinderContract>(
    `${API_PREFIX}/cylinders/contracts/${contractId}/cancel`,
    { method: "POST" }
  );
}

export function renewContract(contractId: string, payload: RenewContractPayload) {
  return apiRequest<LogisticsCylinderContract>(
    `${API_PREFIX}/cylinders/contracts/${contractId}/renew`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    }
  );
}

export function listContractHistory(contractId: string) {
  return apiRequest<LogisticsContractHistory[]>(
    `${API_PREFIX}/cylinders/contracts/${contractId}/history`
  );
}

export function getCoreDocumentDownloadUrl(documentVersionId: string) {
  return `/api/v1/core/documents/${documentVersionId}/download`;
}

export function getCoreDocumentSignedDownload(documentVersionId: string) {
  return apiRequest<CoreDocumentSignedDownload>(
    `/api/v1/core/documents/${documentVersionId}/signed-url`
  );
}

export function listCoreDocumentVersionsForContract(contractId: string) {
  return apiRequest<CoreDocumentVersion[]>(
    withQuery(`/api/v1/core/documents/by-entity`, {
      module: "logistics",
      entity_type: "cylinder_contract",
      entity_id: contractId,
    })
  );
}

export function listCoreSignatureSessionsForContract(contractId: string) {
  return apiRequest<CoreSignatureSession[]>(
    withQuery(`/api/v1/core/signatures/sessions/by-entity`, {
      module: "logistics",
      entity_type: "cylinder_contract",
      entity_id: contractId,
    })
  );
}

export function updateContractExcessPolicy(contractId: string, payload: ContractExcessPolicyPayload) {
  return apiRequest<LogisticsCylinderContract>(
    `${API_PREFIX}/cylinders/contracts/${contractId}/excess-policy`,
    { method: "PATCH", body: JSON.stringify(payload) }
  );
}

export function listCustomerExcessTracking(customerId: string) {
  return apiRequest<ContractExcessTracking[]>(
    `${API_PREFIX}/customers/${customerId}/excess-tracking`
  );
}

export function resolveExcessTracking(trackingId: string, reason: string) {
  return apiRequest<ContractExcessTracking>(
    `${API_PREFIX}/excess-tracking/${trackingId}/resolve`,
    { method: "POST", body: JSON.stringify({ reason }) }
  );
}
