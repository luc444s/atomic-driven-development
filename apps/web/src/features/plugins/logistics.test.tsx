import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";

import { buildCylinderFormState } from "../../../../../plugins/logistics/frontend/cylinders/forms/cylinder-payload";
import { CylinderStateBadge, getCylinderStateLabel } from "../../../../../plugins/logistics/frontend/CylinderStateBadge";

describe("logistics frontend helpers", () => {
  it("maps complete cylinder data into the edit form state", () => {
    const form = buildCylinderFormState({
      id: "cyl-1",
      tenant_id: "tenant-1",
      branch_id: null,
      serial: "GL-200001",
      description: "Envase piloto 10kg",
      barcode1: "BC-200001",
      barcode2: "MAT-200001",
      current_state: "EN_ALMACEN_VACIO",
      gas_group_id: "gas-1",
      product_id: "prod-1",
      content_kg: 10,
      volume_m3: 1.2,
      condition: "NUEVO",
      brand_id: "brand-1",
      cost: 120,
      price: 175,
      country_code: "PE",
      box_number: "LOTE-1",
      is_service: false,
      manufacturer_date: "2025-01-01",
      manufacturer_code: "FAB-01",
      manufacture_year: 2025,
      weight_origin: 12.5,
      weight_current: 12.4,
      average_weight_source: null,
      last_hydrotest_date: "2026-01-01",
      next_hydrotest_date: "2031-01-01",
      location: "Patio norte",
      location_context: null,
      warehouse_id: null,
      warehouse_name: null,
      fill_status: "CARGADO",
      last_fill_at: null,
      last_fill_operation_id: null,
      last_fill_mode: null,
      last_fill_warehouse_id: null,
      last_fill_warehouse_name: null,
      last_fill_source_product_id: null,
      last_fill_source_product_name: null,
      last_fill_source_quantity_liters: null,
      is_active: true,
      container_type: "CYLINDER",
      is_medical: false,
      medical_notes: null,
      created_at: "2026-06-27T00:00:00Z",
      updated_at: "2026-06-27T00:00:00Z",
    });

    expect(form.barcode2).toBe("MAT-200001");
    expect(form.gas_group_id).toBe("prod-1");
    expect(form.price).toBe("175");
    expect(form.location).toBe("Patio norte");
    expect(form.is_active).toBe(true);
  });

  it("keeps human labels for cylinder states", () => {
    expect(getCylinderStateLabel("EN_ALMACEN_VACIO")).toBe("Disponible");
    expect(getCylinderStateLabel("EN_CLIENTE_LLENO")).toBe("En cliente");
  });

  it("renders state badge with readable text", () => {
    const markup = renderToStaticMarkup(<CylinderStateBadge state="LLENADO_OK" />);

    expect(markup).toContain("Listo");
  });
});
