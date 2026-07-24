import type { PlanningExpectedLoadSummary } from "../../api";

export type PlanningReservationProductLine = {
  product_id: string;
  product_name: string;
  sku: string;
  quantity: string;
  unit_weight_kg: number | null;
};

export function createEmptyPlanningProductLine(): PlanningReservationProductLine {
  return {
    product_id: "",
    product_name: "",
    sku: "",
    quantity: "1",
    unit_weight_kg: null,
  };
}

export function summarizePlanningProductLines(
  lines: PlanningReservationProductLine[],
): PlanningExpectedLoadSummary {
  const normalizedItems = lines
    .filter((line) => line.product_id)
    .map((line) => {
      const quantity = Number(line.quantity || 0);
      const total_weight_kg =
        line.unit_weight_kg != null ? Number((line.unit_weight_kg * quantity).toFixed(3)) : null;
      return {
        product_id: line.product_id,
        product_name: line.product_name,
        sku: line.sku || null,
        quantity,
        unit_weight_kg: line.unit_weight_kg,
        total_weight_kg,
      };
    });

  const total_units = normalizedItems.reduce((sum, item) => sum + item.quantity, 0);
  const total_products = normalizedItems.length;
  const hasMissingWeight = normalizedItems.some((item) => item.unit_weight_kg == null);
  const total_weight_kg = hasMissingWeight
    ? null
    : Number(
        normalizedItems.reduce((sum, item) => sum + (item.total_weight_kg ?? 0), 0).toFixed(3),
      );

  return {
    items: normalizedItems,
    total_products,
    total_units,
    total_weight_kg,
  };
}

export function buildPlanningProductLinesFromSummary(
  summary: PlanningExpectedLoadSummary | null | undefined,
): PlanningReservationProductLine[] {
  if (!summary?.items.length) {
    return [createEmptyPlanningProductLine()];
  }
  return summary.items.map((item) => ({
    product_id: item.product_id,
    product_name: item.product_name,
    sku: item.sku ?? "",
    quantity: String(item.quantity),
    unit_weight_kg: item.unit_weight_kg,
  }));
}
