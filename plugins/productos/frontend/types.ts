export type NamedCatalog = {
  id: string;
  tenant_id: string;
  code: string;
  name: string;
  description: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type ProductLine = NamedCatalog & {
  category_id: string | null;
};

export type ProductSubline = {
  id: string;
  tenant_id: string;
  code: string;
  name: string;
  line_id: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type ProductUnit = {
  id: string;
  tenant_id: string;
  code: string;
  name: string;
  equivalencia: number | null;
  m3_factor: number | null;
  liter_factor: number | null;
  kg_factor: number | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type ProductGroup = {
  id: string;
  tenant_id: string;
  code: string;
  name: string;
  gas_product_id: string | null;
  line_id: string | null;
  subline_id: string | null;
  unit_id: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type ProductCondition = {
  code: string;
  name: string;
  description: string | null;
  is_active: boolean;
};

export type ProductStatus = {
  code: string;
  name: string;
  is_active: boolean;
};

export type ProductBarcode = {
  id: string;
  product_id: string;
  barcode_type: string;
  barcode: string;
  is_primary: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type ProductPrice = {
  id: string;
  product_id: string;
  price_list: string;
  amount: number;
  currency: string;
  valid_from: string;
  valid_to: string | null;
  created_by: string;
  created_at: string;
};

export type ProductCost = {
  id: string;
  product_id: string;
  cost_type: string;
  amount: number;
  currency: string;
  valid_from: string;
  valid_to: string | null;
  created_by: string;
  created_at: string;
};

export type ProductTaxConfig = {
  id: string;
  product_id: string;
  tax_type: string;
  value: number | null;
  is_exempt: boolean;
  valid_from: string;
  valid_to: string | null;
  created_at: string;
};

export type ProductAdr = {
  id: string;
  product_id: string;
  source_product_id: string | null;
  source_product_id_2: string | null;
  source_product_id_3: string | null;
  source_quantity_liters: number | null;
  category: string | null;
  packaging_type: string | null;
  net_weight_kg: number | null;
  net_volume_m3: number | null;
  un_number: string | null;
  cargo_description: string | null;
  label: string | null;
  tunnel_restriction: string | null;
  subline_id: string | null;
  factor: number | null;
  points: number | null;
  unit_measure: string | null;
  valid_from: string;
  valid_to: string | null;
  created_by: string;
  created_at: string;
};

export type ProductMedia = {
  id: string;
  product_id: string;
  media_type: string;
  url: string;
  is_primary: boolean;
  created_at: string;
};

export type ProductPromotion = {
  id: string;
  product_id: string;
  name: string | null;
  condition: string;
  qty_required: number | null;
  discount_percent: number | null;
  unit_price: number | null;
  box_price: number | null;
  valid_from: string;
  valid_to: string | null;
  is_active: boolean;
  created_by: string;
  created_at: string;
  updated_at: string;
};

export type ProductListItem = {
  id: string;
  sku: string;
  name: string;
  line_id: string;
  line_name: string | null;
  brand_id: string | null;
  brand_name: string | null;
  unit_id: string;
  unit_name: string | null;
  subcategory_id: string | null;
  subcategory_name: string | null;
  status_code: string;
  status_name: string | null;
  condition_code: string;
  condition_name: string | null;
  is_service: boolean;
  is_active: boolean;
  default_weight_kg: number | null;
  created_at: string;
  updated_at: string;
};

export type ProductSearchItem = {
  id: string;
  sku: string;
  name: string;
  brand_name: string | null;
  condition_code: string;
  is_active: boolean;
};

export type ProductPage = {
  items: ProductListItem[];
  total: number;
  limit: number;
  offset: number;
};

export type Product = {
  id: string;
  tenant_id: string;
  legacy_id: number | null;
  sku: string;
  name: string;
  description: string | null;
  short_description: string | null;
  line_id: string;
  subline_id: string | null;
  brand_id: string | null;
  insumo_type_id: string | null;
  unit_id: string;
  box_unit_id: string | null;
  qty_per_box: number | null;
  subcategory_id: string | null;
  group_id: string | null;
  status_code: string;
  condition_code: string;
  weight_kg: number | null;
  content_m3: number | null;
  country_code: string | null;
  is_service: boolean;
  is_active: boolean;
  created_by: string;
  created_at: string;
  updated_at: string;
  line_name: string | null;
  subline_name: string | null;
  brand_name: string | null;
  unit_name: string | null;
  insumo_type_name: string | null;
  subcategory_name: string | null;
  group_name: string | null;
  condition_name: string | null;
  status_name: string | null;
  barcodes: ProductBarcode[];
  prices: ProductPrice[];
  costs: ProductCost[];
  taxes: ProductTaxConfig[];
  adr_configs: ProductAdr[];
  media_items: ProductMedia[];
  promotions: ProductPromotion[];
};

export type ProductPayload = {
  legacy_id: number | null;
  sku: string;
  name: string;
  description: string | null;
  short_description: string | null;
  line_id: string;
  subline_id: string | null;
  brand_id: string | null;
  insumo_type_id: string | null;
  unit_id: string;
  box_unit_id: string | null;
  qty_per_box: number | null;
  subcategory_id: string | null;
  group_id: string | null;
  status_code: string;
  condition_code: string;
  weight_kg: number | null;
  content_m3: number | null;
  country_code: string | null;
  is_service: boolean;
  is_active: boolean;
};

export type ProductBarcodePayload = {
  barcode_type: string;
  barcode: string;
  is_primary: boolean;
  is_active: boolean;
};

export type ProductPricePayload = {
  price_list: string;
  amount: number;
  currency: string;
  valid_from: string;
};

export type ProductCostPayload = {
  cost_type: string;
  amount: number;
  currency: string;
  valid_from: string;
};

export type ProductTaxConfigPayload = {
  tax_type: string;
  value: number | null;
  is_exempt: boolean;
  valid_from: string;
};

export type ProductAdrPayload = {
  category: string | null;
  packaging_type: string | null;
  net_weight_kg: number | null;
  net_volume_m3: number | null;
  un_number: string | null;
  cargo_description: string | null;
  label: string | null;
  tunnel_restriction: string | null;
  subline_id: string | null;
  factor: number | null;
  points: number | null;
  unit_measure: string | null;
  valid_from: string;
};

export type ProductPromotionPayload = {
  name: string | null;
  condition: string;
  qty_required: number | null;
  discount_percent: number | null;
  unit_price: number | null;
  box_price: number | null;
  valid_from: string;
  valid_to: string | null;
  is_active: boolean;
};
