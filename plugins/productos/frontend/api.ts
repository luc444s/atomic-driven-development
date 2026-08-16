import { apiRequest } from "@systutor/shell/api/client";

import type {
  NamedCatalog,
  Product,
  ProductAdr,
  ProductAdrPayload,
  ProductBarcode,
  ProductBarcodePayload,
  ProductCondition,
  ProductCost,
  ProductCostPayload,
  ProductGroup,
  ProductLine,
  ProductMedia,
  ProductPage,
  ProductPayload,
  ProductPrice,
  ProductPricePayload,
  ProductPromotion,
  ProductPromotionPayload,
  ProductListItem,
  ProductSearchItem,
  ProductStatus,
  ProductSubline,
  ProductTaxConfig,
  ProductTaxConfigPayload,
  ProductUnit,
} from "./types";

const PRODUCTOS_BASE = "/api/v1/plugins/productos";

export const productosKeys = {
  all: ["productos"] as const,
  catalogs: {
    categories: ["productos", "catalog", "categories"] as const,
    lines: ["productos", "catalog", "lines"] as const,
    subline: ["productos", "catalog", "subline"] as const,
    brands: ["productos", "catalog", "brands"] as const,
    insumoTypes: ["productos", "catalog", "insumo-types"] as const,
    units: ["productos", "catalog", "units"] as const,
    conditions: ["productos", "catalog", "conditions"] as const,
    status: ["productos", "catalog", "status"] as const,
    subcategories: ["productos", "catalog", "subcategories"] as const,
    groups: ["productos", "catalog", "groups"] as const,
  },
  products: {
    all: ["productos", "products"] as const,
    list: (params: Record<string, unknown>) => ["productos", "products", params] as const,
    detail: (productId: string) => ["productos", "products", productId] as const,
    search: (query: string) => ["productos", "products", "search", query] as const,
    barcodes: (productId: string) => ["productos", "products", productId, "barcodes"] as const,
    prices: (productId: string) => ["productos", "products", productId, "prices"] as const,
    costs: (productId: string) => ["productos", "products", productId, "costs"] as const,
    tax: (productId: string) => ["productos", "products", productId, "tax"] as const,
    adr: (productId: string) => ["productos", "products", productId, "adr"] as const,
    media: (productId: string) => ["productos", "products", productId, "media"] as const,
    promotions: (productId: string) => ["productos", "products", productId, "promotions"] as const,
  },
};

function buildQuery(params: Record<string, unknown>) {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null || value === "") {
      continue;
    }
    query.set(key, String(value));
  }
  const stringified = query.toString();
  return stringified ? `?${stringified}` : "";
}

export async function listCategories(): Promise<NamedCatalog[]> {
  return apiRequest(`${PRODUCTOS_BASE}/catalog/categories`);
}

export async function createCategory(payload: { code: string; name: string; description: string | null }): Promise<NamedCatalog> {
  return apiRequest(`${PRODUCTOS_BASE}/catalog/categories`, { method: "POST", body: JSON.stringify(payload) });
}

export async function updateCategory(categoryId: string, payload: Partial<{ code: string; name: string; description: string | null; is_active: boolean }>): Promise<NamedCatalog> {
  return apiRequest(`${PRODUCTOS_BASE}/catalog/categories/${categoryId}`, { method: "PUT", body: JSON.stringify(payload) });
}

export async function listLines(): Promise<ProductLine[]> {
  return apiRequest(`${PRODUCTOS_BASE}/catalog/lines`);
}

export async function createLine(payload: { code: string; name: string; category_id: string | null; description: string | null }): Promise<ProductLine> {
  return apiRequest(`${PRODUCTOS_BASE}/catalog/lines`, { method: "POST", body: JSON.stringify(payload) });
}

export async function updateLine(lineId: string, payload: Partial<{ code: string; name: string; category_id: string | null; description: string | null; is_active: boolean }>): Promise<ProductLine> {
  return apiRequest(`${PRODUCTOS_BASE}/catalog/lines/${lineId}`, { method: "PUT", body: JSON.stringify(payload) });
}

export async function listSubline(): Promise<ProductSubline[]> {
  return apiRequest(`${PRODUCTOS_BASE}/catalog/subline`);
}

export async function createSubline(payload: { code: string; name: string; line_id: string }): Promise<ProductSubline> {
  return apiRequest(`${PRODUCTOS_BASE}/catalog/subline`, { method: "POST", body: JSON.stringify(payload) });
}

export async function updateSubline(sublineId: string, payload: Partial<{ code: string; name: string; line_id: string; is_active: boolean }>): Promise<ProductSubline> {
  return apiRequest(`${PRODUCTOS_BASE}/catalog/subline/${sublineId}`, { method: "PUT", body: JSON.stringify(payload) });
}

export async function listBrands(): Promise<NamedCatalog[]> {
  return apiRequest(`${PRODUCTOS_BASE}/catalog/brands`);
}

export async function createBrand(payload: { code: string; name: string; description: string | null }): Promise<NamedCatalog> {
  return apiRequest(`${PRODUCTOS_BASE}/catalog/brands`, { method: "POST", body: JSON.stringify(payload) });
}

export async function updateBrand(brandId: string, payload: Partial<{ code: string; name: string; description: string | null; is_active: boolean }>): Promise<NamedCatalog> {
  return apiRequest(`${PRODUCTOS_BASE}/catalog/brands/${brandId}`, { method: "PUT", body: JSON.stringify(payload) });
}

export async function listInsumoTypes(): Promise<NamedCatalog[]> {
  return apiRequest(`${PRODUCTOS_BASE}/catalog/insumo-types`);
}

export async function createInsumoType(payload: { code: string; name: string; description: string | null }): Promise<NamedCatalog> {
  return apiRequest(`${PRODUCTOS_BASE}/catalog/insumo-types`, { method: "POST", body: JSON.stringify(payload) });
}

export async function updateInsumoType(insumoTypeId: string, payload: Partial<{ code: string; name: string; description: string | null; is_active: boolean }>): Promise<NamedCatalog> {
  return apiRequest(`${PRODUCTOS_BASE}/catalog/insumo-types/${insumoTypeId}`, { method: "PUT", body: JSON.stringify(payload) });
}

export async function listUnits(): Promise<ProductUnit[]> {
  return apiRequest(`${PRODUCTOS_BASE}/catalog/units`);
}

export async function createUnit(payload: { code: string; name: string; equivalencia: number | null; m3_factor: number | null; liter_factor: number | null; kg_factor: number | null }): Promise<ProductUnit> {
  return apiRequest(`${PRODUCTOS_BASE}/catalog/units`, { method: "POST", body: JSON.stringify(payload) });
}

export async function updateUnit(unitId: string, payload: Partial<{ code: string; name: string; equivalencia: number | null; m3_factor: number | null; liter_factor: number | null; kg_factor: number | null; is_active: boolean }>): Promise<ProductUnit> {
  return apiRequest(`${PRODUCTOS_BASE}/catalog/units/${unitId}`, { method: "PUT", body: JSON.stringify(payload) });
}

export async function listConditions(): Promise<ProductCondition[]> {
  return apiRequest(`${PRODUCTOS_BASE}/catalog/conditions`);
}

export async function listStatus(): Promise<ProductStatus[]> {
  return apiRequest(`${PRODUCTOS_BASE}/catalog/status`);
}

export async function listSubcategories(): Promise<NamedCatalog[]> {
  return apiRequest(`${PRODUCTOS_BASE}/catalog/subcategories`);
}

export async function createSubcategory(payload: { code: string; name: string; description: string | null }): Promise<NamedCatalog> {
  return apiRequest(`${PRODUCTOS_BASE}/catalog/subcategories`, { method: "POST", body: JSON.stringify(payload) });
}

export async function updateSubcategory(subcategoryId: string, payload: Partial<{ code: string; name: string; description: string | null; is_active: boolean }>): Promise<NamedCatalog> {
  return apiRequest(`${PRODUCTOS_BASE}/catalog/subcategories/${subcategoryId}`, { method: "PUT", body: JSON.stringify(payload) });
}

export async function listGroups(): Promise<ProductGroup[]> {
  return apiRequest(`${PRODUCTOS_BASE}/catalog/groups`);
}

export async function createGroup(payload: { code: string; name: string; gas_product_id: string | null; line_id: string | null; subline_id: string | null; unit_id: string | null }): Promise<ProductGroup> {
  return apiRequest(`${PRODUCTOS_BASE}/catalog/groups`, { method: "POST", body: JSON.stringify(payload) });
}

export async function updateGroup(groupId: string, payload: Partial<{ code: string; name: string; gas_product_id: string | null; line_id: string | null; subline_id: string | null; unit_id: string | null; is_active: boolean }>): Promise<ProductGroup> {
  return apiRequest(`${PRODUCTOS_BASE}/catalog/groups/${groupId}`, { method: "PUT", body: JSON.stringify(payload) });
}

export async function listProducts(params: Record<string, unknown>): Promise<ProductPage> {
  return apiRequest(`${PRODUCTOS_BASE}/products${buildQuery(params)}`);
}

export async function listAllProducts(params: Record<string, unknown> = {}): Promise<ProductListItem[]> {
  return apiRequest(`${PRODUCTOS_BASE}/products/flat${buildQuery(params)}`);
}

export async function searchProducts(query: string, limit = 10): Promise<ProductSearchItem[]> {
  if (!query.trim()) return [];
  return apiRequest(`${PRODUCTOS_BASE}/products/search${buildQuery({ q: query, limit })}`);
}

export async function getProduct(productId: string): Promise<Product> {
  return apiRequest(`${PRODUCTOS_BASE}/products/${productId}`);
}

export async function createProduct(payload: ProductPayload): Promise<Product> {
  return apiRequest(`${PRODUCTOS_BASE}/products`, { method: "POST", body: JSON.stringify(payload) });
}

export async function updateProduct(productId: string, payload: Partial<ProductPayload>): Promise<Product> {
  return apiRequest(`${PRODUCTOS_BASE}/products/${productId}`, { method: "PUT", body: JSON.stringify(payload) });
}

export async function toggleProduct(productId: string, isActive: boolean, reason?: string | null): Promise<Product> {
  return apiRequest(`${PRODUCTOS_BASE}/products/${productId}/status`, {
    method: "PATCH",
    body: JSON.stringify({ is_active: isActive, reason: reason ?? null }),
  });
}

export async function listProductBarcodes(productId: string): Promise<ProductBarcode[]> {
  return apiRequest(`${PRODUCTOS_BASE}/products/${productId}/barcodes`);
}

export async function createProductBarcode(productId: string, payload: ProductBarcodePayload): Promise<ProductBarcode> {
  return apiRequest(`${PRODUCTOS_BASE}/products/${productId}/barcodes`, { method: "POST", body: JSON.stringify(payload) });
}

export async function updateProductBarcode(productId: string, barcodeId: string, payload: Partial<ProductBarcodePayload>): Promise<ProductBarcode> {
  return apiRequest(`${PRODUCTOS_BASE}/products/${productId}/barcodes/${barcodeId}`, { method: "PUT", body: JSON.stringify(payload) });
}

export async function deleteProductBarcode(productId: string, barcodeId: string): Promise<void> {
  await apiRequest(`${PRODUCTOS_BASE}/products/${productId}/barcodes/${barcodeId}`, { method: "DELETE" });
}

export async function setPrimaryProductBarcode(productId: string, barcodeId: string): Promise<ProductBarcode> {
  return apiRequest(`${PRODUCTOS_BASE}/products/${productId}/barcodes/${barcodeId}/set-primary`, { method: "POST" });
}

export async function listProductPrices(productId: string): Promise<ProductPrice[]> {
  return apiRequest(`${PRODUCTOS_BASE}/products/${productId}/prices`);
}

export async function createProductPrice(productId: string, payload: ProductPricePayload): Promise<ProductPrice> {
  return apiRequest(`${PRODUCTOS_BASE}/products/${productId}/prices`, { method: "POST", body: JSON.stringify(payload) });
}

export async function supersedeProductPrice(productId: string, priceId: string, payload: { amount: number; currency: string; valid_from: string }): Promise<ProductPrice> {
  return apiRequest(`${PRODUCTOS_BASE}/products/${productId}/prices/${priceId}/supersede`, { method: "POST", body: JSON.stringify(payload) });
}

export async function updateAllProductPrices(productId: string, payload: { items: ProductPricePayload[] }): Promise<ProductPrice[]> {
  return apiRequest(`${PRODUCTOS_BASE}/products/${productId}/prices/update-all`, { method: "POST", body: JSON.stringify(payload) });
}

export async function listProductCosts(productId: string): Promise<ProductCost[]> {
  return apiRequest(`${PRODUCTOS_BASE}/products/${productId}/costs`);
}

export async function createProductCost(productId: string, payload: ProductCostPayload): Promise<ProductCost> {
  return apiRequest(`${PRODUCTOS_BASE}/products/${productId}/costs`, { method: "POST", body: JSON.stringify(payload) });
}

export async function supersedeProductCost(productId: string, costId: string, payload: { amount: number; currency: string; valid_from: string }): Promise<ProductCost> {
  return apiRequest(`${PRODUCTOS_BASE}/products/${productId}/costs/${costId}/supersede`, { method: "POST", body: JSON.stringify(payload) });
}

export async function listProductTax(productId: string): Promise<ProductTaxConfig[]> {
  return apiRequest(`${PRODUCTOS_BASE}/products/${productId}/tax`);
}

export async function replaceProductTax(productId: string, payload: { configs: ProductTaxConfigPayload[] }): Promise<ProductTaxConfig[]> {
  return apiRequest(`${PRODUCTOS_BASE}/products/${productId}/tax`, { method: "PUT", body: JSON.stringify(payload) });
}

export async function listProductAdr(productId: string): Promise<ProductAdr[]> {
  return apiRequest(`${PRODUCTOS_BASE}/products/${productId}/adr`);
}

export async function createProductAdr(productId: string, payload: ProductAdrPayload): Promise<ProductAdr> {
  return apiRequest(`${PRODUCTOS_BASE}/products/${productId}/adr`, { method: "POST", body: JSON.stringify(payload) });
}

export async function updateProductAdr(productId: string, adrId: string, payload: Partial<ProductAdrPayload & { valid_to: string | null }>): Promise<ProductAdr> {
  return apiRequest(`${PRODUCTOS_BASE}/products/${productId}/adr/${adrId}`, { method: "PUT", body: JSON.stringify(payload) });
}

export async function expireProductAdr(productId: string, adrId: string): Promise<ProductAdr> {
  return apiRequest(`${PRODUCTOS_BASE}/products/${productId}/adr/${adrId}/expire`, { method: "POST" });
}

export async function listProductMedia(productId: string): Promise<ProductMedia[]> {
  return apiRequest(`${PRODUCTOS_BASE}/products/${productId}/media`);
}

export async function uploadProductMedia(productId: string, payload: { media_type: string; is_primary: boolean; file: File }): Promise<ProductMedia> {
  const form = new FormData();
  form.append("file", payload.file);
  return apiRequest(`${PRODUCTOS_BASE}/products/${productId}/media${buildQuery({ media_type: payload.media_type, is_primary: payload.is_primary })}`, {
    method: "POST",
    body: form,
  });
}

export async function deleteProductMedia(productId: string, mediaId: string): Promise<void> {
  await apiRequest(`${PRODUCTOS_BASE}/products/${productId}/media/${mediaId}`, { method: "DELETE" });
}

export async function setPrimaryProductMedia(productId: string, mediaId: string): Promise<ProductMedia> {
  return apiRequest(`${PRODUCTOS_BASE}/products/${productId}/media/${mediaId}/set-primary`, { method: "POST" });
}

export async function listProductPromotions(productId: string): Promise<ProductPromotion[]> {
  return apiRequest(`${PRODUCTOS_BASE}/products/${productId}/promotions`);
}

export async function createProductPromotion(productId: string, payload: ProductPromotionPayload): Promise<ProductPromotion> {
  return apiRequest(`${PRODUCTOS_BASE}/products/${productId}/promotions`, { method: "POST", body: JSON.stringify(payload) });
}

export async function updatePromotion(promotionId: string, payload: Partial<ProductPromotionPayload>): Promise<ProductPromotion> {
  return apiRequest(`${PRODUCTOS_BASE}/promotions/${promotionId}`, { method: "PUT", body: JSON.stringify(payload) });
}

export async function deletePromotion(promotionId: string): Promise<void> {
  await apiRequest(`${PRODUCTOS_BASE}/promotions/${promotionId}`, { method: "DELETE" });
}
