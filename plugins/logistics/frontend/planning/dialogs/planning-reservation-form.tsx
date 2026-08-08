import { Dispatch, SetStateAction, useEffect, useMemo, useState } from "react";
import { useQuery } from "../../../../../apps/web/src/lib/react-query";
import { Input, Textarea } from "../../../../../apps/web/src/shared/ui/input";
import { Select } from "../../../../../apps/web/src/shared/ui/select";
import { Button } from "../../../../../apps/web/src/shared/ui/button";
import { LocationMap } from "../../../../../apps/web/src/shared/ui/location-map";
import type { ComboboxOption } from "../../../../../apps/web/src/shared/ui/combobox";
import { CustomerSearchDialog } from "../../../../crm/frontend/components/CustomerSearchDialog";
import { listCustomerAddressesByCustomers } from "../../api/delivery-points";
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
import { formatRouteLabel } from "../../lib/route-labels";

export type PlanningReservationFormValues = {
  vehicle_id: string;
  origin_warehouse_id: string;
  planned_start_at: string;
  planned_end_at: string;
  driver_id: string;
  route_id: string;
  customer_ids: string[];
  address_ids: string[];
  customer_names: Record<string, string>;
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
  showRouteSelect?: boolean;
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
  showRouteSelect = false,
}: Props) {
  const [isCustomerSearchOpen, setIsCustomerSearchOpen] = useState(false);
  const [addressesQuery, setAddressesQuery] = useState<
    { id: string; customer_id: string; line1: string; latitude: number | null; longitude: number | null }[]
  >([]);

  const addressesByCustomers = useQuery({
    queryKey: ["logistics", "planning-addresses", form.customer_ids],
    queryFn: () => listCustomerAddressesByCustomers(form.customer_ids.join(",")),
    enabled: form.customer_ids.length > 0,
  });

  useEffect(() => {
    setAddressesQuery(addressesByCustomers.data ?? []);
  }, [addressesByCustomers.data]);

  function toggleCustomer(customer: { id: string; display_name: string }) {
    if (form.customer_ids.includes(customer.id)) {
      setForm((current) => ({
        ...current,
        customer_ids: current.customer_ids.filter((id) => id !== customer.id),
      }));
    } else {
      setForm((current) => ({
        ...current,
        customer_ids: [...current.customer_ids, customer.id],
        customer_names: { ...current.customer_names, [customer.id]: customer.display_name },
      }));
    }
  }

  function toggleAddress(addressId: string) {
    setForm((current) => ({
      ...current,
      address_ids: current.address_ids.includes(addressId)
        ? current.address_ids.filter((id) => id !== addressId)
        : [...current.address_ids, addressId],
    }));
  }

  const gpsMarkers = addressesQuery
    .filter((address) => address.latitude != null && address.longitude != null)
    .map((address) => ({
      id: address.id,
      position: { lat: address.latitude!, lng: address.longitude! },
      label: `${form.customer_names[address.customer_id] ?? ""} — ${address.line1}`,
    }));

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

      <div className="space-y-2 md:col-span-2">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-foreground">Clientes de la planificación</span>
          <Button type="button" variant="secondary" onClick={() => setIsCustomerSearchOpen(true)}>
            Agregar cliente
          </Button>
        </div>
        {form.customer_ids.length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {form.customer_ids.map((customerId) => (
              <span
                key={customerId}
                className="inline-flex items-center gap-2 rounded-full border border-border bg-surface px-3 py-1 text-xs text-foreground"
              >
                {form.customer_names[customerId] ?? customerId}
                <button
                  type="button"
                  onClick={() => setForm((current) => ({ ...current, customer_ids: current.customer_ids.filter((id) => id !== customerId) }))}
                  className="text-muted-foreground hover:text-foreground"
                >
                  ×
                </button>
              </span>
            ))}
          </div>
        ) : (
          <p className="text-xs text-muted-foreground">
            Agrega los clientes a visitar. Sus puntos de entrega aparecerán en el mapa.
          </p>
        )}
        <CustomerSearchDialog
          open={isCustomerSearchOpen}
          onOpenChange={setIsCustomerSearchOpen}
          onSelect={toggleCustomer}
        />
      </div>

      {addressesQuery.length > 0 ? (
        <div className="space-y-2 md:col-span-2">
          <span className="block text-sm font-medium text-foreground">Direcciones del cliente (clic para incluir)</span>
          <LocationMap
            center={gpsMarkers[0]?.position ?? { lat: 37.18, lng: -4.75 }}
            height={200}
            autoFit
            markers={gpsMarkers.map((marker) => {
              const assigned = form.address_ids.includes(marker.id);
              return {
                ...marker,
                label: assigned ? "Punto asignado" : `${marker.label}${assigned ? " ✓" : ""}`,
                labelVisible: assigned,
                color: (assigned ? "assigned" : "default") as const,
              };
            })}
            onMarkerClick={(id) => toggleAddress(id)}
          />
          <div className="grid gap-1">
            {addressesQuery.map((address) => {
              const selected = form.address_ids.includes(address.id);
              return (
                <button
                  key={address.id}
                  type="button"
                  onClick={() => toggleAddress(address.id)}
                  className={`flex items-center justify-between gap-2 rounded-md border px-3 py-2 text-left text-xs transition ${
                    selected ? "border-primary bg-primary/10 text-foreground" : "border-border bg-surface text-foreground"
                  }`}
                >
                  <span className="truncate">
                    {form.customer_names[address.customer_id] ?? ""} — {address.line1}
                  </span>
                  <span className="text-muted-foreground">
                    {address.latitude != null && address.longitude != null ? "📍" : "sin GPS"}
                  </span>
                </button>
              );
            })}
          </div>
        </div>
      ) : null}

      {form.address_ids.length > 0 ? (
        <div className="rounded-lg border border-dashed border-border p-4 text-center md:col-span-2">
          {form.driver_id ? (
            <p className="text-sm text-foreground">
              La ruta se creará automáticamente con las {form.address_ids.length} dirección(es) seleccionada(s).
            </p>
          ) : (
            <div>
              <p className="text-sm text-amber-600">
                Selecciona un conductor para auto-crear la ruta desde las direcciones.
              </p>
              <p className="mt-1 text-xs text-muted-foreground">
                Sin conductor, deberás seleccionar una ruta manualmente.
              </p>
            </div>
          )}
        </div>
      ) : null}

      {form.address_ids.length > 0 && !form.driver_id ? (
        <div className="space-y-2">
          <label className="text-sm font-medium">Ruta (requerida sin conductor)</label>
          <Select value={form.route_id} onChange={(value) => setForm((current) => ({ ...current, route_id: value }))} options={[{ value: "", label: "Seleccionar ruta" }, ...routes.map((route) => ({ value: route.id, label: formatRouteLabel(route) }))]} />
        </div>
      ) : null}

      {showRouteSelect && form.customer_ids.length === 0 && form.address_ids.length === 0 ? (
        <div className="space-y-2">
          <label className="text-sm font-medium">Ruta</label>
          <Select value={form.route_id} onChange={(value) => setForm((current) => ({ ...current, route_id: value }))} options={[{ value: "", label: "Sin ruta" }, ...routes.map((route) => ({ value: route.id, label: formatRouteLabel(route) }))]} />
        </div>
      ) : null}
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
