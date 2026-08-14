import { describe, expect, it } from "vitest";

import {
  buildEditableLoadPlanItems,
  buildReconciliationCounts,
} from "../../../../../plugins/logistics/frontend/components/vehicle-sessions/session-console-view";

describe("buildEditableLoadPlanItems", () => {
  it("maps load plan items into editable rows", () => {
    const items = buildEditableLoadPlanItems({
      id: "plan-1",
      session_id: "session-1",
      status: "DRAFT",
      notes: null,
      planned_weight_kg: 10,
      items: [
        {
          id: "item-1",
          product_id: "prod-1",
          product_name: "Oxigeno",
          planned_quantity: 3.5,
          planned_weight_kg: 10,
          source_warehouse_id: "wh-1",
          notes: null,
          requires_serials: true,
          selected_serials_count: 2,
          serials_complete: false,
          created_at: "",
        },
      ],
    });

    expect(items).toEqual([
      {
        id: "item-1",
        product_id: "prod-1",
        product_name: "Oxigeno",
        planned_quantity: "3.5",
        source_warehouse_id: "wh-1",
        requires_serials: true,
        selected_serials_count: 2,
        serials_complete: false,
      },
    ]);
  });
});

describe("buildReconciliationCounts", () => {
  it("uses counted quantity when present and expected otherwise", () => {
    const counts = buildReconciliationCounts({
      id: null,
      session_id: "session-1",
      status: "OPEN",
      counted_by: null,
      counted_at: null,
      notes: null,
      can_close: false,
      discrepancies: [],
      lines: [
        {
          product_id: "prod-1",
          product_name: "Oxigeno",
          expected_quantity: 5,
          counted_quantity: 4,
          difference_quantity: -1,
        },
        {
          product_id: "prod-2",
          product_name: "Nitrogeno",
          expected_quantity: 2,
          counted_quantity: null,
          difference_quantity: null,
        },
      ],
    });

    expect(counts).toEqual({ "prod-1": "4", "prod-2": "2" });
  });
});
