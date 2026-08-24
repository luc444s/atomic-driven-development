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
  CreateOrderPayload,
  CreateSupplierPayload,
  PurchaseOrder,
  PurchaseOrderDetail,
  PurchaseOrderPage,
  ReceiveOrderPayload,
  Supplier,
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
