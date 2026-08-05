import { describe, expect, it } from "vitest";

import {
  buildCryogenicFillPreview,
  buildCryogenicTankSourceCards,
  pickFillableSerialIds,
  resolveActiveCryogenicRecipe,
} from "../../../../../plugins/logistics/frontend/cryogenic-filling/helpers";

function makeRecipe(sourceProductId: string, liters: number) {
  return {
    id: "adr-1",
    product_id: "prod-1",
    source_product_id: sourceProductId,
    source_quantity_liters: liters,
    category: null,
    packaging_type: null,
    net_weight_kg: 3.8,
    net_volume_m3: 3.2,
    un_number: null,
    cargo_description: null,
    label: null,
    tunnel_restriction: null,
    subline_id: null,
    factor: null,
    points: null,
    unit_measure: null,
    valid_from: "2026-01-01",
    valid_to: null,
    created_by: "user-1",
    created_at: "2026-01-01T00:00:00Z",
  };
}

function makeTank(overrides: Record<string, unknown>) {
  return {
    id: "tank-1",
    tenant_id: "t1",
    branch_id: null,
    serial: "TK-LOX-001",
    container_type: "CRYOGENIC_TANK",
    description: "Tanque LOX planta norte",
    current_state: "EN_ALMACEN_VACIO",
    product_id: "lox-1",
    volume_m3: 5,
    warehouse_id: "wh-1",
    warehouse_name: "Piedra",
    is_active: true,
    ...overrides,
  };
}

function makeEmptyCylinder(productId: string, warehouseId: string, serial: string) {
  return {
    id: `cyl-${serial}`,
    serial,
    product_id: productId,
    warehouse_id: warehouseId,
    current_state: "EN_ALMACEN_VACIO",
    fill_status: "VACIO",
    container_type: "CYLINDER",
  };
}

describe("cryogenic filling helpers", () => {
  it("resolves the active cryogenic recipe with source product and metrics", () => {
    const recipe = resolveActiveCryogenicRecipe(
      {
        adr_configs: [
          {
            id: "adr-1",
            product_id: "prod-1",
            source_product_id: "src-1",
            source_quantity_liters: 3.798,
            category: null,
            packaging_type: null,
            net_weight_kg: 3.8,
            net_volume_m3: 3.2,
            un_number: null,
            cargo_description: null,
            label: null,
            tunnel_restriction: null,
            subline_id: null,
            factor: null,
            points: null,
            unit_measure: null,
            valid_from: "2026-01-01",
            valid_to: null,
            created_by: "user-1",
            created_at: "2026-01-01T00:00:00Z",
          },
        ],
      } as any,
      new Date("2026-08-04T00:00:00Z"),
    );

    expect(recipe?.source_product_id).toBe("src-1");
    expect(recipe?.source_quantity_liters).toBe(3.798);
  });

  it("calculates partial preview when available liters do not reach the full selection", () => {
    const preview = buildCryogenicFillPreview({
      selectedCount: 100,
      litersPerCylinder: 2.516,
      litersAvailable: 151,
    });

    expect(preview.fillableCount).toBe(60);
    expect(preview.isPartial).toBe(true);
    expect(preview.litersRequired).toBeCloseTo(251.6, 5);
    expect(preview.projectedBalance).toBeCloseTo(0.04, 5);
  });

  it("keeps only the serial ids that can really be filled", () => {
    expect(pickFillableSerialIds(["a", "b", "c", "d"], 2)).toEqual(["a", "b"]);
  });

  it("builds tank cards reading liters from the balance of the gas in the tank warehouse", () => {
    const cards = buildCryogenicTankSourceCards({
      tanks: [makeTank({}) as any],
      balances: [
        {
          product_id: "lox-1",
          warehouse_id: "wh-1",
          warehouse_code: "PIEDRA",
          warehouse_name: "Piedra",
          product_sku: "LOX",
          product_name: "Oxigeno Liquido",
          quantity: 1000,
        },
      ] as any,
      emptyResultCylinders: [
        makeEmptyCylinder("result-1", "wh-1", "2947prue"),
        makeEmptyCylinder("result-2", "wh-9", "OTRO"),
      ] as any,
      recipeByResultProductId: new Map([
        ["result-1", makeRecipe("lox-1", 1.899)],
        ["result-2", makeRecipe("lox-1", 1.899)],
      ]) as any,
      productsById: new Map([
        ["lox-1", { id: "lox-1", sku: "LOX", name: "Oxigeno Liquido" }],
      ]) as any,
    });

    expect(cards).toHaveLength(1);
    expect(cards[0].availableLiters).toBe(1000);
    expect(cards[0].sourceProductName).toBe("Oxigeno Liquido");
    expect(cards[0].nominalCapacityM3).toBe(5);
    expect(cards[0].eligibleEmptyCount).toBe(1);
    expect(cards[0].resultProductIds).toEqual(["result-1"]);
  });

  it("reports zero liters when the tank has no balance row for its gas", () => {
    const cards = buildCryogenicTankSourceCards({
      tanks: [makeTank({}) as any],
      balances: [],
      emptyResultCylinders: [makeEmptyCylinder("result-1", "wh-1", "2947prue")] as any,
      recipeByResultProductId: new Map([["result-1", makeRecipe("lox-1", 1.899)]]) as any,
      productsById: new Map() as any,
    });

    expect(cards).toHaveLength(1);
    expect(cards[0].availableLiters).toBe(0);
  });

  it("ignores tanks without a liquid gas product and empties of another warehouse", () => {
    const cards = buildCryogenicTankSourceCards({
      tanks: [
        makeTank({ product_id: null }),
        makeTank({ id: "tank-2", serial: "TK-LIN-001", product_id: "lin-1", warehouse_id: "wh-2" }),
      ] as any,
      balances: [
        {
          product_id: "lin-1",
          warehouse_id: "wh-2",
          warehouse_code: "LIN",
          warehouse_name: "Planta LIN",
          product_sku: "LIN",
          product_name: "Nitrogeno Liquido",
          quantity: 50,
        },
      ] as any,
      emptyResultCylinders: [makeEmptyCylinder("result-1", "wh-1", "2947prue")] as any,
      recipeByResultProductId: new Map([["result-1", makeRecipe("lin-1", 1.899)]]) as any,
      productsById: new Map() as any,
    });

    expect(cards).toHaveLength(1);
    expect(cards[0].serial).toBe("TK-LIN-001");
    expect(cards[0].availableLiters).toBe(50);
    expect(cards[0].eligibleEmptyCount).toBe(0);
  });
});
