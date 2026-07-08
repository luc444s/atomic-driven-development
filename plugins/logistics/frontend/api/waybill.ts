// Auto-generado por split_api.py
import { API_PREFIX, withQuery } from "./_shared";
import { LogisticsMovement } from "./movements";
import { apiRequest } from "../../../../apps/web/src/shared/api/client";

export type WaybillDetailItem = {
  product_id: string | null;
  product_name: string | null;
  quantity: number;
  unit_weight_kg: number | null;
  total_weight_kg: number | null;
  adr_points: number | null;
};

export type Waybill = {
  movement_id: string;
  movement_type: string;
  document: string | null;
  warehouse_id: string | null;
  warehouse_name: string | null;
  customer_id: string | null;
  customer_name: string | null;
  vehicle_id: string | null;
  vehicle_plate: string | null;
  driver_id: string | null;
  destination_place: string | null;
  destination_address: string | null;
  items: WaybillDetailItem[];
  total_packages: number;
  total_weight_kg: number;
  total_adr_points: number;
};

export type WaybillSummary = {
  movement_id: string;
  total_packages: number;
  total_weight_kg: number;
  total_adr_points: number;
};

export function getWaybill(movementId: string) {
  return apiRequest<Waybill>(`${API_PREFIX}/waybill/${movementId}`);
}

export function getWaybillSummary(movementId: string) {
  return apiRequest<WaybillSummary>(`${API_PREFIX}/waybill/${movementId}/summary`);
}

export function assignDispatchGuide(movementId: string, payload: { document_series: string }) {
  return apiRequest<LogisticsMovement>(`${API_PREFIX}/movements/${movementId}/guide`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function closeDispatch(movementId: string) {
  return apiRequest<LogisticsMovement>(`${API_PREFIX}/movements/${movementId}/close-dispatch`, {
    method: "POST",
  });
}

export function getDispatchReceipt(movementId: string) {
  return apiRequest<LogisticsMovement>(`${API_PREFIX}/movements/${movementId}/dispatch-receipt`);
}

export function vehicleReturn(movementId: string, payload: { cylinder_ids: string[]; notes?: string }) {
  return apiRequest<LogisticsMovement>(`${API_PREFIX}/movements/${movementId}/vehicle-return`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export type DispatchTicket = Waybill;

export type TransferAlbaran = Waybill;

export function getDispatchTicket(movementId: string) {
  return apiRequest<DispatchTicket>(`${API_PREFIX}/reports/dispatch-ticket/${movementId}`);
}

export function getTransferAlbaran(movementId: string) {
  return apiRequest<TransferAlbaran>(`${API_PREFIX}/reports/transfer-albaran/${movementId}`);
}

