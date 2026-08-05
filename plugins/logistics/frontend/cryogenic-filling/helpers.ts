import type { Product, ProductAdr } from "../../../productos/frontend/types";
import type { ProductListItem } from "../../../productos/frontend/types";
import type { StockBalanceItem } from "../../../stock/frontend/types";
import type { LogisticsCylinder } from "../api";

export type CryogenicFillPreview = {
  selectedCount: number;
  fillableCount: number;
  litersPerCylinder: number;
  litersRequired: number;
  litersAvailable: number;
  litersConsumed: number;
  projectedBalance: number;
  isPartial: boolean;
};

export type CryogenicTankSourceCard = {
  key: string;
  tankId: string;
  serial: string;
  description: string | null;
  warehouseId: string | null;
  warehouseCode: string | null;
  warehouseName: string | null;
  sourceProductId: string;
  sourceProductSku: string;
  sourceProductName: string;
  availableLiters: number;
  nominalCapacityM3: number | null;
  currentState: string;
  eligibleEmptyCount: number;
  resultProductIds: string[];
};

export function buildCryogenicTankSourceCards(input: {
  tanks: LogisticsCylinder[];
  balances: StockBalanceItem[];
  emptyResultCylinders: LogisticsCylinder[];
  recipeByResultProductId: Map<string, ProductAdr>;
  productsById: Map<string, ProductListItem>;
}): CryogenicTankSourceCard[] {
  const balanceByKey = new Map(
    input.balances
      .filter((item) => item.quantity > 0)
      .map((item) => [`${item.warehouse_id}:${item.product_id}`, item] as const),
  );

  const cards: CryogenicTankSourceCard[] = [];
  for (const tank of input.tanks) {
    if (tank.product_id === null) {
      continue;
    }
    const warehouseId = tank.warehouse_id;
    const balance =
      warehouseId !== null
        ? balanceByKey.get(`${warehouseId}:${tank.product_id}`)
        : undefined;
    const sourceProduct = input.productsById.get(tank.product_id);

    let eligibleEmptyCount = 0;
    const resultProductIds = new Set<string>();
    for (const cylinder of input.emptyResultCylinders) {
      if (cylinder.warehouse_id === null || cylinder.warehouse_id !== warehouseId) {
        continue;
      }
      const recipe = input.recipeByResultProductId.get(cylinder.product_id ?? "");
      if (!recipe || recipe.source_product_id !== tank.product_id) {
        continue;
      }
      eligibleEmptyCount += 1;
      resultProductIds.add(cylinder.product_id as string);
    }

    cards.push({
      key: tank.id,
      tankId: tank.id,
      serial: tank.serial,
      description: tank.description,
      warehouseId,
      warehouseCode: balance?.warehouse_code ?? null,
      warehouseName: balance?.warehouse_name ?? tank.warehouse_name ?? null,
      sourceProductId: tank.product_id,
      sourceProductSku: sourceProduct?.sku ?? tank.product_id,
      sourceProductName: sourceProduct?.name ?? tank.product_id,
      availableLiters: balance?.quantity ?? 0,
      nominalCapacityM3: tank.volume_m3,
      currentState: tank.current_state,
      eligibleEmptyCount,
      resultProductIds: Array.from(resultProductIds),
    });
  }

  return cards.sort((left, right) => left.serial.localeCompare(right.serial));
}

export function resolveActiveCryogenicRecipe(
  product: Product | null | undefined,
  today = new Date(),
): ProductAdr | null {
  if (!product) {
    return null;
  }

  const currentDate = today.toISOString().slice(0, 10);
  return (
    product.adr_configs.find(
      (adr) =>
        adr.source_product_id !== null &&
        adr.source_quantity_liters !== null &&
        adr.source_quantity_liters > 0 &&
        adr.net_volume_m3 !== null &&
        adr.net_volume_m3 > 0 &&
        adr.net_weight_kg !== null &&
        adr.net_weight_kg > 0 &&
        adr.valid_from <= currentDate &&
        (adr.valid_to === null || adr.valid_to >= currentDate),
    ) ?? null
  );
}

export function buildCryogenicFillPreview(input: {
  selectedCount: number;
  litersPerCylinder: number | null;
  litersAvailable: number | null;
}): CryogenicFillPreview {
  const selectedCount = Math.max(0, input.selectedCount);
  const litersPerCylinder = input.litersPerCylinder ?? 0;
  const litersAvailable = input.litersAvailable ?? 0;
  const fillableCount =
    litersPerCylinder > 0
      ? Math.min(selectedCount, Math.max(0, Math.floor(litersAvailable / litersPerCylinder)))
      : 0;
  const litersRequired = selectedCount * litersPerCylinder;
  const litersConsumed = fillableCount * litersPerCylinder;

  return {
    selectedCount,
    fillableCount,
    litersPerCylinder,
    litersRequired,
    litersAvailable,
    litersConsumed,
    projectedBalance: litersAvailable - litersConsumed,
    isPartial: selectedCount > 0 && fillableCount < selectedCount,
  };
}

export function pickFillableSerialIds(serialIds: string[], fillableCount: number): string[] {
  return serialIds.slice(0, Math.max(0, fillableCount));
}
