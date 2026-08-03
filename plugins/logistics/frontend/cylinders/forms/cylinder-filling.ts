import type {
  FillCylinderPayload,
  LogisticsCylinder,
  VacateCylinderPayload,
} from "../../api";
import { toNullable, toNumberOrNull } from "../utils/formatters";

export type CylinderFillingMode = "fill" | "vacate";

export type CylinderFillingFormState = {
  warehouse_id: string;
  content_kg: string;
  volume_m3: string;
  weight_current: string;
  notes: string;
};

export const EMPTY_CYLINDER_FILLING_FORM: CylinderFillingFormState = {
  warehouse_id: "",
  content_kg: "",
  volume_m3: "",
  weight_current: "",
  notes: "",
};

export function buildCylinderFillingFormState(
  cylinder: LogisticsCylinder | null,
  mode: CylinderFillingMode,
): CylinderFillingFormState {
  if (!cylinder) {
    return EMPTY_CYLINDER_FILLING_FORM;
  }
  return {
    warehouse_id: cylinder.warehouse_id ?? "",
    content_kg: "",
    volume_m3: "",
    weight_current:
      mode === "vacate" ? cylinder.weight_origin?.toString() ?? "" : "",
    notes: "",
  };
}

export function buildFillCylinderPayload(
  form: CylinderFillingFormState,
): FillCylinderPayload {
  return {
    warehouse_id: toNullable(form.warehouse_id),
    content_kg: toNumberOrNull(form.content_kg),
    volume_m3: toNumberOrNull(form.volume_m3),
    weight_current: toNumberOrNull(form.weight_current),
    notes: toNullable(form.notes),
  };
}

export function buildVacateCylinderPayload(
  form: CylinderFillingFormState,
): VacateCylinderPayload {
  return {
    warehouse_id: toNullable(form.warehouse_id),
    weight_current: toNumberOrNull(form.weight_current),
    notes: toNullable(form.notes),
  };
}
