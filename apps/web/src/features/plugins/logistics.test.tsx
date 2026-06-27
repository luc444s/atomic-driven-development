import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";

import { buildCylinderFormState } from "../../../../../plugins/logistics/frontend/LogisticsPage";
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
      last_hydrotest_date: "2026-01-01",
      next_hydrotest_date: "2031-01-01",
      adr_category: "2F",
      adr_un_number: "1047",
      adr_label: "GLP",
      adr_package_type: "CIL",
      adr_weight_kg: 22.5,
      adr_merchandise: "Gas licuado de petroleo",
      adr_tunnel: "B/D",
      adr_subline: "GLP",
      adr_factor: 1,
      adr_points: 3,
      adr_unit_measure: "KG",
      location: "Patio norte",
      is_active: true,
      created_at: "2026-06-27T00:00:00Z",
      updated_at: "2026-06-27T00:00:00Z",
    });

    expect(form.barcode2).toBe("MAT-200001");
    expect(form.gas_group_id).toBe("gas-1");
    expect(form.price).toBe("175");
    expect(form.adr_package_type).toBe("CIL");
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
