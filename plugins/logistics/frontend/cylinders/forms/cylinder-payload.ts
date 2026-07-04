import type { LogisticsCylinder } from "../../api";
import { toNullable, toNumberOrNull, toIntegerOrNull } from "../utils/formatters";
import type { CylinderFormState, CylinderCreateMetaState } from "./cylinder-form-state";
import { EMPTY_CYLINDER_FORM } from "./cylinder-form-state";

export function buildCylinderFormState(cylinder?: LogisticsCylinder | null): CylinderFormState {
  if (!cylinder) {
    return EMPTY_CYLINDER_FORM;
  }
  return {
    serial: cylinder.serial,
    description: cylinder.description ?? "",
    barcode1: cylinder.barcode1 ?? "",
    barcode2: cylinder.barcode2 ?? "",
    gas_group_id: cylinder.product_id ?? cylinder.gas_group_id ?? "",
    content_kg: cylinder.content_kg?.toString() ?? "",
    volume_m3: cylinder.volume_m3?.toString() ?? "",
    condition: cylinder.condition ?? "",
    brand_id: cylinder.brand_id ?? "",
    cost: cylinder.cost?.toString() ?? "",
    price: cylinder.price?.toString() ?? "",
    country_code: cylinder.country_code ?? "",
    box_number: cylinder.box_number ?? "",
    is_service: cylinder.is_service,
    is_medical: cylinder.is_medical,
    medical_notes: cylinder.medical_notes ?? "",
    manufacturer_date: cylinder.manufacturer_date ?? "",
    manufacturer_code: cylinder.manufacturer_code ?? "",
    manufacture_year: cylinder.manufacture_year?.toString() ?? "",
    weight_origin: cylinder.weight_origin?.toString() ?? "",
    weight_current: cylinder.weight_current?.toString() ?? "",
    last_hydrotest_date: cylinder.last_hydrotest_date ?? "",
    next_hydrotest_date: cylinder.next_hydrotest_date ?? "",
    adr_category: cylinder.adr_category ?? "",
    adr_un_number: cylinder.adr_un_number ?? "",
    adr_label: cylinder.adr_label ?? "",
    adr_package_type: cylinder.adr_package_type ?? "",
    adr_weight_kg: cylinder.adr_weight_kg?.toString() ?? "",
    adr_merchandise: cylinder.adr_merchandise ?? "",
    adr_tunnel: cylinder.adr_tunnel ?? "",
    adr_subline: cylinder.adr_subline ?? "",
    adr_factor: cylinder.adr_factor?.toString() ?? "",
    adr_points: cylinder.adr_points?.toString() ?? "",
    adr_unit_measure: cylinder.adr_unit_measure ?? "",
    location: cylinder.location ?? "",
    is_active: cylinder.is_active,
  };
}

export function buildCylinderPayload(form: CylinderFormState) {
  return {
    serial: form.serial,
    description: toNullable(form.description),
    barcode1: toNullable(form.barcode1),
    barcode2: toNullable(form.barcode2),
    product_id: toNullable(form.gas_group_id),
    content_kg: toNumberOrNull(form.content_kg),
    volume_m3: toNumberOrNull(form.volume_m3),
    condition: toNullable(form.condition),
    brand_id: toNullable(form.brand_id),
    cost: toNumberOrNull(form.cost),
    price: toNumberOrNull(form.price),
    country_code: toNullable(form.country_code),
    box_number: toNullable(form.box_number),
    is_service: form.is_service,
    is_medical: form.is_medical,
    medical_notes: toNullable(form.medical_notes),
    manufacturer_date: toNullable(form.manufacturer_date),
    manufacturer_code: toNullable(form.manufacturer_code),
    manufacture_year: toIntegerOrNull(form.manufacture_year),
    weight_origin: toNumberOrNull(form.weight_origin),
    weight_current: toNumberOrNull(form.weight_current),
    last_hydrotest_date: toNullable(form.last_hydrotest_date),
    next_hydrotest_date: toNullable(form.next_hydrotest_date),
    adr_category: toNullable(form.adr_category),
    adr_un_number: toNullable(form.adr_un_number),
    adr_label: toNullable(form.adr_label),
    adr_package_type: toNullable(form.adr_package_type),
    adr_weight_kg: toNumberOrNull(form.adr_weight_kg),
    adr_merchandise: toNullable(form.adr_merchandise),
    adr_tunnel: toNullable(form.adr_tunnel),
    adr_subline: toNullable(form.adr_subline),
    adr_factor: toNumberOrNull(form.adr_factor),
    adr_points: toIntegerOrNull(form.adr_points),
    adr_unit_measure: toNullable(form.adr_unit_measure),
    location: toNullable(form.location),
    is_active: form.is_active,
  };
}

export function buildCreateCylinderPayload(form: CylinderFormState, meta: CylinderCreateMetaState) {
  return {
    ...buildCylinderPayload(form),
    entry_mode: meta.entry_mode,
    document_type: toNullable(meta.document_type),
    document_number: toNullable(meta.document_number),
    customer_id:
      meta.entry_mode === "EMPTY_FROM_CUSTOMER" ? toNullable(meta.customer_id) : null,
  };
}
