import { describe, expect, it } from "vitest";

import {
  buildCylinderFillingFormState,
  buildFillCylinderPayload,
  buildVacateCylinderPayload,
} from "../../../../../plugins/logistics/frontend/cylinders/forms/cylinder-filling";

describe("cylinder filling payloads", () => {
  it("builds fill payloads using only the technical fields provided", () => {
    const payload = buildFillCylinderPayload({
      warehouse_id: "wh-1",
      content_kg: "10.50",
      volume_m3: "",
      weight_current: "50.50",
      notes: "Llenado de prueba",
    });

    expect(payload).toEqual({
      warehouse_id: "wh-1",
      content_kg: 10.5,
      volume_m3: null,
      weight_current: 50.5,
      notes: "Llenado de prueba",
    });
  });

  it("prefills vacate form with current warehouse and tare weight", () => {
    const form = buildCylinderFillingFormState(
      {
        warehouse_id: "wh-2",
        weight_origin: 42,
      } as any,
      "vacate",
    );

    expect(form).toEqual({
      warehouse_id: "wh-2",
      content_kg: "",
      volume_m3: "",
      weight_current: "42",
      notes: "",
    });
    expect(buildVacateCylinderPayload(form)).toEqual({
      warehouse_id: "wh-2",
      weight_current: 42,
      notes: null,
    });
  });
});
