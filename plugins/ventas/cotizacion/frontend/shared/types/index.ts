export interface QuoteDraftDTO {
  id: string;
  status: string;
  customer: { id: string; name: string };
  items: Array<{
    id: string;
    product_id: string;
    product_name: string | null;
    quantity: number;
    unit_weight_kg: number | null;
  }>;
  delivery_date: string;
  delivery_time: string | null;
  vehicle: { id: string; plate: string } | null;
  conditions: string | null;
  created_at: string;
}

export interface QuoteDraftListItem {
  id: string;
  status: string;
  customer_name: string | null;
  delivery_date: string;
  created_at: string;
}
