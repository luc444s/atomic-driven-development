import { type FormEvent, useEffect, useState } from "react";
import { Dialog } from "../../../../../apps/web/src/shared/ui/dialog";
import { Button } from "../../../../../apps/web/src/shared/ui/button";
import type { DriverOption, LogisticsRoute, LogisticsVehicle, LogisticsWarehouse, PlanningReservationPayload } from "../../api";
import { PlanningReservationForm, type PlanningReservationFormValues } from "./planning-reservation-form";
import { fromDateTimeLocalValue, toDateTimeLocalValue } from "../utils/planning-calendar-formatters";
import {
  createEmptyPlanningProductLine,
  summarizePlanningProductLines,
  type PlanningReservationProductLine,
} from "./planning-load-summary";
import type { PlanningProductCatalogItem } from "./planning-product-lines-editor";

type Props = {
  open: boolean;
  onClose: () => void;
  onSubmit: (payload: PlanningReservationPayload) => Promise<void>;
  isPending: boolean;
  vehicles: LogisticsVehicle[];
  warehouses: LogisticsWarehouse[];
  routes: LogisticsRoute[];
  drivers: DriverOption[];
  initialDraft: { vehicleId: string; plannedStartAt: string; plannedEndAt: string } | null;
  products: PlanningProductCatalogItem[];
  resolveProduct: (productId: string) => Promise<{
    product_id: string;
    product_name: string;
    sku: string;
    adr_required: boolean;
    unit_weight_kg: number | null;
  }>;
  quotePrefill?: {
    items: Array<{ product_id: string; product_name: string | null; quantity: number; unit_weight_kg: number | null }>;
    vehicle_id?: string;
    notes?: string;
    planned_start_at?: string;
    planned_end_at?: string;
  } | null;
};

function buildInitialForm(
  initialDraft: Props["initialDraft"],
  quotePrefill?: Props["quotePrefill"],
): PlanningReservationFormValues {
  const quoteItems: PlanningReservationProductLine[] =
    quotePrefill?.items.map((item) => ({
      product_id: item.product_id,
      product_name: item.product_name ?? "",
      sku: "",
      quantity: String(item.quantity),
      unit_weight_kg: item.unit_weight_kg,
    })) ?? [];

  return {
    vehicle_id: quotePrefill?.vehicle_id ?? initialDraft?.vehicleId ?? "",
    origin_warehouse_id: "",
    planned_start_at:
      quotePrefill?.planned_start_at
        ? toDateTimeLocalValue(quotePrefill.planned_start_at)
        : toDateTimeLocalValue(initialDraft?.plannedStartAt),
    planned_end_at:
      quotePrefill?.planned_end_at
        ? toDateTimeLocalValue(quotePrefill.planned_end_at)
        : toDateTimeLocalValue(initialDraft?.plannedEndAt),
    driver_id: "",
    route_id: "",
    items: quoteItems.length > 0 ? quoteItems : [createEmptyPlanningProductLine()],
    notes: quotePrefill?.notes ?? "",
    permit_override: false,
    override_reason: "",
  };
}

export function CreatePlanningReservationDialog(props: Props) {
  const [form, setForm] = useState<PlanningReservationFormValues>(() =>
    buildInitialForm(props.initialDraft, props.quotePrefill),
  );

  useEffect(() => {
    if (props.open) {
      setForm(buildInitialForm(props.initialDraft));
    }
  }, [props.initialDraft, props.open]);

  if (!props.open) {
    return null;
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const expected_load_summary = summarizePlanningProductLines(form.items);
    await props.onSubmit({
      vehicle_id: form.vehicle_id,
      origin_warehouse_id: form.origin_warehouse_id,
      planned_start_at: fromDateTimeLocalValue(form.planned_start_at),
      planned_end_at: fromDateTimeLocalValue(form.planned_end_at),
      driver_id: form.driver_id || null,
      route_id: form.route_id || null,
      expected_load_summary,
      expected_weight_total: expected_load_summary.total_weight_kg,
      notes: form.notes || null,
      adr_required: expected_load_summary.items.some((item) => item.adr_required),
      permit_override: form.permit_override,
      override_reason: form.override_reason || null,
    });
  }

  return (
    <Dialog
      open={props.open}
      onClose={props.onClose}
      title="Nueva planificación"
      description="Reserva capacidad futura del vehículo desde el calendario."
      actions={<Button type="submit" form="create-planning-reservation-form">{props.isPending ? "Guardando..." : "Guardar"}</Button>}
      maxWidthClassName="max-w-4xl"
    >
      <form id="create-planning-reservation-form" onSubmit={handleSubmit}>
        <PlanningReservationForm
          form={form}
          setForm={setForm}
          vehicles={props.vehicles}
          warehouses={props.warehouses}
          routes={props.routes}
          drivers={props.drivers}
          products={props.products}
          resolveProduct={props.resolveProduct}
          onAddLine={() => setForm((current) => ({ ...current, items: [...current.items, createEmptyPlanningProductLine()] }))}
        />
      </form>
    </Dialog>
  );
}
