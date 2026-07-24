import { Dispatch, SetStateAction, useMemo } from "react";
import { useQuery } from "../../../../../apps/web/src/lib/react-query";
import { Input, Textarea } from "../../../../../apps/web/src/shared/ui/input";
import { Select } from "../../../../../apps/web/src/shared/ui/select";
import type { ComboboxOption } from "../../../../../apps/web/src/shared/ui/combobox";
import {
  listPlanningStockBalances,
  planningKeys,
  type DriverOption,
  type LogisticsRoute,
  type LogisticsVehicle,
  type LogisticsWarehouse,
} from "../../api";
import {
  type PlanningReservationProductLine,
  summarizePlanningProductLines,
} from "./planning-load-summary";
import {
  PlanningProductLinesEditor,
  type PlanningProductCatalogItem,
} from "./planning-product-lines-editor";

export type PlanningReservationFormValues = {
  vehicle_id: string;
  origin_warehouse_id: string;
  planned_start_at: string;
  planned_end_at: string;
  driver_id: string;
  route_id: string;
  items: PlanningReservationProductLine[];
  notes: string;
  permit_override: boolean;
  override_reason: string;
};

type Props = {
  form: PlanningReservationFormValues;
  setForm: Dispatch<SetStateAction<PlanningReservationFormValues>>;
  vehicles: LogisticsVehicle[];
  warehouses: LogisticsWarehouse[];
  routes: LogisticsRoute[];
  drivers: DriverOption[];
  products: PlanningProductCatalogItem[];
  resolveProduct: (productId: string) => Promise<{
    product_id: string;
    product_name: string;
    sku: string;
    adr_required: boolean;
    unit_weight_kg: number | null;
  }>;
  onAddLine: () => void;
};

export function PlanningReservationForm({
  form,
  setForm,
  vehicles,
  warehouses,
  routes,
  drivers,
  products,
  resolveProduct,
  onAddLine,
}: Props) {
  const stockBalancesQuery = useQuery({
    queryKey: planningKeys.stock(form.origin_warehouse_id || undefined),
    queryFn: () => listPlanningStockBalances(form.origin_warehouse_id),
    enabled: Boolean(form.origin_warehouse_id),
  });
  const summary = summarizePlanningProductLines(form.items);
  const selectedProductIds = new Set(
    form.items.filter((line) => line.product_id).map((line) => line.product_id),
  );
  const availableByProductId = useMemo(() => {
    const map = new Map<string, number>();
    for (const item of stockBalancesQuery.data ?? []) {
      map.set(item.product_id, item.quantity);
    }
    return map;
  }, [stockBalancesQuery.data]);
  const productOptions: ComboboxOption[] = useMemo(
    () =>
      products
        .filter((product) => {
          const available = availableByProductId.get(product.id) ?? 0;
          return available > 0 || selectedProductIds.has(product.id);
        })
        .map((product) => {
          const available = availableByProductId.get(product.id) ?? 0;
          return {
            value: product.id,
            label: `${product.name}${product.sku ? ` · ${product.sku}` : ""} · Disp ${available}`,
            keywords: [product.name, product.sku, product.brand_name ?? ""],
          };
        }),
    [availableByProductId, products, selectedProductIds],
  );
  const warehouseStockUnits = useMemo(() => {
    if (summary.items.length > 0) {
      return summary.items.reduce(
        (sum, item) => sum + (availableByProductId.get(item.product_id) ?? 0),
        0,
      );
    }
    return (stockBalancesQuery.data ?? []).reduce((sum, item) => sum + item.quantity, 0);
  }, [availableByProductId, stockBalancesQuery.data, summary.items]);
  const inferredAdrRequired = summary.items.some((item) => item.adr_required);

  return (
    <div className="grid gap-4 md:grid-cols-2">
      <div className="space-y-2">
        <label className="text-sm font-medium">Vehículo</label>
        <Select value={form.vehicle_id} onChange={(value) => setForm((current) => ({ ...current, vehicle_id: value }))} options={vehicles.map((vehicle) => ({ value: vehicle.id, label: vehicle.plate }))} />
      </div>
      <div className="space-y-2">
        <label className="text-sm font-medium">Almacén origen</label>
        <Select value={form.origin_warehouse_id} onChange={(value) => setForm((current) => ({ ...current, origin_warehouse_id: value }))} options={warehouses.map((warehouse) => ({ value: warehouse.id, label: warehouse.name }))} />
      </div>
      <div className="space-y-2">
        <label className="text-sm font-medium">Inicio</label>
        <Input type="datetime-local" value={form.planned_start_at} onChange={(event) => setForm((current) => ({ ...current, planned_start_at: event.target.value }))} />
      </div>
      <div className="space-y-2">
        <label className="text-sm font-medium">Fin</label>
        <Input type="datetime-local" value={form.planned_end_at} onChange={(event) => setForm((current) => ({ ...current, planned_end_at: event.target.value }))} />
      </div>
      <div className="space-y-2">
        <label className="text-sm font-medium">Conductor</label>
        <Select value={form.driver_id} onChange={(value) => setForm((current) => ({ ...current, driver_id: value }))} options={[{ value: "", label: "Sin conductor" }, ...drivers.map((driver) => ({ value: driver.id, label: driver.full_name }))]} />
      </div>
      <div className="space-y-2">
        <label className="text-sm font-medium">Ruta</label>
        <Select value={form.route_id} onChange={(value) => setForm((current) => ({ ...current, route_id: value }))} options={[{ value: "", label: "Sin ruta" }, ...routes.map((route) => ({ value: route.id, label: `${route.route_date} · ${route.status}` }))]} />
      </div>
      <div className="md:col-span-2">
        <PlanningProductLinesEditor
          lines={form.items}
          setLines={(updater) => setForm((current) => ({ ...current, items: updater(current.items) }))}
          productOptions={productOptions}
          availableByProductId={availableByProductId}
          disabled={!form.origin_warehouse_id}
          resolveProduct={resolveProduct}
          onAddLine={onAddLine}
        />
        {!form.origin_warehouse_id ? (
          <p className="mt-2 text-xs text-muted-foreground">
            Selecciona primero el almacén origen para filtrar productos por stock real.
          </p>
        ) : null}
      </div>
      <div className="grid gap-3 rounded-xl border border-border/70 p-3 md:col-span-2 md:grid-cols-4">
        <div>
          <div className="text-xs text-muted-foreground">Productos</div>
          <div className="text-sm font-medium text-foreground">{summary.total_products}</div>
        </div>
        <div>
          <div className="text-xs text-muted-foreground">Unidades</div>
          <div className="text-sm font-medium text-foreground">{summary.total_units}</div>
        </div>
        <div>
          <div className="text-xs text-muted-foreground">Stock almacén</div>
          <div className="text-sm font-medium text-foreground">{warehouseStockUnits}</div>
        </div>
        <div>
          <div className="text-xs text-muted-foreground">Peso total kg</div>
          <div className="text-sm font-medium text-foreground">
            {summary.total_weight_kg != null ? summary.total_weight_kg.toFixed(2) : "Sin peso definido"}
          </div>
        </div>
      </div>
      <div className="space-y-2 md:col-span-2">
        <label className="text-sm font-medium">Notas</label>
        <Textarea value={form.notes} onChange={(event) => setForm((current) => ({ ...current, notes: event.target.value }))} rows={4} />
      </div>
      <div className="flex items-center justify-between gap-3 rounded-xl border border-border/70 p-3 text-sm md:col-span-2">
        <span>ADR inferido por productos</span>
        <span className={`font-medium ${inferredAdrRequired ? "text-amber-600" : "text-muted-foreground"}`}>
          {inferredAdrRequired ? "Sí" : "No"}
        </span>
      </div>
    </div>
  );
}
