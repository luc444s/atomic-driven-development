import type { LoadPlan } from "../../api/load-plans";
import type { SessionReconciliation } from "../../api/reconciliation";
import type { EditableLoadPlanItem } from "./SessionLoadTab";

export function buildEditableLoadPlanItems(loadPlan: LoadPlan): EditableLoadPlanItem[] {
  return loadPlan.items.map((item) => ({
    id: item.id,
    product_id: item.product_id,
    product_name: item.product_name,
    planned_quantity: String(item.planned_quantity),
    source_warehouse_id: item.source_warehouse_id,
    requires_serials: item.requires_serials,
    selected_serials_count: item.selected_serials_count,
    serials_complete: item.serials_complete,
  }));
}

export function buildReconciliationCounts(
  reconciliation: SessionReconciliation
): Record<string, string> {
  return Object.fromEntries(
    reconciliation.lines.map((line) => [
      line.product_id,
      line.counted_quantity != null
        ? String(line.counted_quantity)
        : String(line.expected_quantity),
    ])
  );
}
