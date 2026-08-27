import { apiRequest } from "@systutor/shell/api/client";

function buildQuery(params: Record<string, unknown>) {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null || value === "") continue;
    query.set(key, String(value));
  }
  const qs = query.toString();
  return qs ? `?${qs}` : "";
}
import type {
  CommercialClosePayload,
  CreateClaimPayload,
  CreateInvoicePayload,
  CreateOrderPayload,
  CreateSupplierPayload,
  PurchaseOrder,
  PurchaseOrderDetail,
  PurchaseOrderPage,
  ReceiveOrderPayload,
  Reconciliation,
  Supplier,
  SupplierClaim,
  SupplierClaimDetail,
  SupplierInvoice,
  UpdateOrderPayload,
  UpdateSupplierPayload,
} from "./types";

const BASE = "/api/v1/plugins/compras/purchase";

// ── Suppliers ──

export function listSuppliers(search?: string) {
  return apiRequest<Supplier[]>(`${BASE}/suppliers${buildQuery({ search })}`);
}

export function createSupplier(payload: CreateSupplierPayload) {
  return apiRequest<Supplier>(`${BASE}/suppliers`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateSupplier(id: string, payload: UpdateSupplierPayload) {
  return apiRequest<Supplier>(`${BASE}/suppliers/${id}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function disableSupplier(id: string) {
  return apiRequest<Supplier>(`${BASE}/suppliers/${id}/disable`, { method: "POST" });
}

export function addSupplierAddress(supplierId: string, payload: { line1: string; label?: string | null; district?: string | null; city?: string | null; latitude?: number | null; longitude?: number | null }) {
  return apiRequest<Supplier>(`${BASE}/suppliers/${supplierId}/addresses`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function removeSupplierAddress(supplierId: string, addressId: string) {
  return apiRequest<Supplier>(`${BASE}/suppliers/${supplierId}/addresses/${addressId}`, {
    method: "DELETE",
  });
}

export function addSupplierContact(supplierId: string, payload: { full_name?: string | null; role?: string | null; phone?: string | null; email?: string | null }) {
  return apiRequest<Supplier>(`${BASE}/suppliers/${supplierId}/contacts`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function removeSupplierContact(supplierId: string, contactId: string) {
  return apiRequest<Supplier>(`${BASE}/suppliers/${supplierId}/contacts/${contactId}`, {
    method: "DELETE",
  });
}

export function addSupplierBankAccount(supplierId: string, payload: { bank_name: string; account_holder: string; iban: string; bic_swift?: string | null }) {
  return apiRequest<Supplier>(`${BASE}/suppliers/${supplierId}/bank-accounts`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function removeSupplierBankAccount(supplierId: string, accountId: string) {
  return apiRequest<Supplier>(`${BASE}/suppliers/${supplierId}/bank-accounts/${accountId}`, {
    method: "DELETE",
  });
}

export function listTanks(productId?: string) {
  return apiRequest<Array<{ id: string; serial: string; description: string; product_id: string; content_kg: number; volume_m3: number }>>(
    `${BASE}/tanks${productId ? `?product_id=${productId}` : ""}`
  );
}

// ── Orders ──

export function listOrders(params: Record<string, unknown> = {}) {
  return apiRequest<PurchaseOrderPage>(`${BASE}/orders${buildQuery(params)}`);
}

export function getOrder(id: string) {
  return apiRequest<PurchaseOrderDetail>(`${BASE}/orders/${id}`);
}

export function createOrder(payload: CreateOrderPayload) {
  return apiRequest<PurchaseOrder>(`${BASE}/orders`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateOrder(id: string, payload: UpdateOrderPayload) {
  return apiRequest<PurchaseOrder>(`${BASE}/orders/${id}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function confirmOrder(id: string) {
  return apiRequest<PurchaseOrder>(`${BASE}/orders/${id}/confirm`, { method: "POST" });
}

export function cancelOrder(id: string, reason?: string) {
  return apiRequest<PurchaseOrder>(`${BASE}/orders/${id}/cancel`, {
    method: "POST",
    body: JSON.stringify(reason ? { reason } : {}),
  });
}

export function closeOrder(id: string, reason: string) {
  return apiRequest<PurchaseOrder>(`${BASE}/orders/${id}/close`, {
    method: "POST",
    body: JSON.stringify({ reason }),
  });
}

export function receiveOrder(id: string, payload: ReceiveOrderPayload) {
  return apiRequest<PurchaseOrder>(`${BASE}/orders/${id}/receive`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function commercialCloseReceipt(receiptId: string, payload: CommercialClosePayload) {
  return apiRequest<PurchaseOrder>(`${BASE}/receipts/${receiptId}/commercial-close`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function createInvoice(orderId: string, payload: CreateInvoicePayload) {
  return apiRequest<SupplierInvoice>(`${BASE}/orders/${orderId}/invoices`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function listInvoices(orderId: string) {
  return apiRequest<SupplierInvoice[]>(`${BASE}/orders/${orderId}/invoices`);
}

export function getReconciliation(orderId: string) {
  return apiRequest<Reconciliation>(`${BASE}/orders/${orderId}/reconciliation`);
}

export function cancelInvoice(invoiceId: string) {
  return apiRequest<SupplierInvoice>(`${BASE}/invoices/${invoiceId}/cancel`, {
    method: "POST",
  });
}

// ── Claims (reclamaciones al proveedor) ──

export function listClaims(orderId: string) {
  return apiRequest<SupplierClaim[]>(`${BASE}/orders/${orderId}/claims`);
}

export function getClaim(orderId: string, claimId: string) {
  return apiRequest<SupplierClaimDetail>(`${BASE}/orders/${orderId}/claims/${claimId}`);
}

export function createClaim(orderId: string, payload: CreateClaimPayload) {
  return apiRequest<SupplierClaim>(`${BASE}/orders/${orderId}/claims`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function startClaim(orderId: string, claimId: string) {
  return apiRequest<SupplierClaim>(`${BASE}/orders/${orderId}/claims/${claimId}/start`, {
    method: "POST",
  });
}

export function resolveClaim(orderId: string, claimId: string, resolutionNotes: string) {
  return apiRequest<SupplierClaim>(`${BASE}/orders/${orderId}/claims/${claimId}/resolve`, {
    method: "POST",
    body: JSON.stringify({ resolution_notes: resolutionNotes }),
  });
}

export function annulClaim(orderId: string, claimId: string, reason: string) {
  return apiRequest<SupplierClaim>(`${BASE}/orders/${orderId}/claims/${claimId}/annul`, {
    method: "POST",
    body: JSON.stringify({ reason }),
  });
}

// ── Dispatches ──

export function listDispatches(params: Record<string, unknown> = {}) {
  return apiRequest<import("./types").DispatchPage>(`${BASE}/dispatches${buildQuery(params)}`);
}

export function getDispatch(id: string) {
  return apiRequest<import("./types").Dispatch>(`${BASE}/dispatches/${id}`);
}

export function createDispatch(payload: Record<string, unknown>) {
  return apiRequest<import("./types").Dispatch>(`${BASE}/dispatches`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function confirmDispatch(id: string) {
  return apiRequest<import("./types").Dispatch>(`${BASE}/dispatches/${id}/confirm`, { method: "POST" });
}

export function cancelDispatch(id: string) {
  return apiRequest<import("./types").Dispatch>(`${BASE}/dispatches/${id}/cancel`, { method: "POST" });
}

export function listSupplierCustody(supplierId: string, params: Record<string, unknown> = {}) {
  return apiRequest<import("./types").CustodyEntry[]>(
    `${BASE}/dispatches/suppliers/${supplierId}/custody${buildQuery(params)}`
  );
}

export function registerDispatchReturn(id: string, cylinderIds: string[], notes?: string) {
  return apiRequest<import("./types").Dispatch>(`${BASE}/dispatches/${id}/return`, {
    method: "POST",
    body: JSON.stringify({ cylinders: cylinderIds.map(c => ({ cylinder_id: c })), notes: notes ?? null }),
  });
}
