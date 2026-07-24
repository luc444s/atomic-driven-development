import { type FormEvent, useEffect, useState } from "react";
import { Dialog } from "../../../../../apps/web/src/shared/ui/dialog";
import { Button } from "../../../../../apps/web/src/shared/ui/button";
import type { DriverOption, LogisticsRoute, LogisticsVehicle, LogisticsWarehouse, PlanningReservation, PlanningReservationPayload } from "../../api";
import { PlanningReservationForm, type PlanningReservationFormValues } from "./planning-reservation-form";
import { fromDateTimeLocalValue, toDateTimeLocalValue } from "../utils/planning-calendar-formatters";
import {
  buildPlanningProductLinesFromSummary,
  createEmptyPlanningProductLine,
  summarizePlanningProductLines,
} from "./planning-load-summary";
import type { PlanningProductCatalogItem } from "./planning-product-lines-editor";

type Props = {
  open: boolean;
  onClose: () => void;
  onSubmit: (payload: Partial<PlanningReservationPayload>) => Promise<void>;
  isPending: boolean;
  reservation: PlanningReservation | null;
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
};

function buildForm(reservation: PlanningReservation | null): PlanningReservationFormValues {
  return {
    vehicle_id: reservation?.vehicle_id ?? "",
    origin_warehouse_id: reservation?.origin_warehouse_id ?? "",
    planned_start_at: toDateTimeLocalValue(reservation?.planned_start_at),
    planned_end_at: toDateTimeLocalValue(reservation?.planned_end_at),
    driver_id: reservation?.driver_id ?? "",
    route_id: reservation?.route_id ?? "",
    items: buildPlanningProductLinesFromSummary(reservation?.expected_load_summary),
    notes: reservation?.notes ?? "",
    permit_override: reservation?.permit_override ?? false,
    override_reason: reservation?.override_reason ?? "",
  };
}

export function EditPlanningReservationDialog(props: Props) {
  const [form, setForm] = useState<PlanningReservationFormValues>(() => buildForm(props.reservation));

  useEffect(() => {
    if (props.open) {
      setForm(buildForm(props.reservation));
    }
  }, [props.open, props.reservation]);

  if (!props.open || !props.reservation) {
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
      title="Editar planificación"
      description="Ajusta la reserva antes de materializarla en jornada."
      actions={<Button type="submit" form="edit-planning-reservation-form">{props.isPending ? "Guardando..." : "Guardar cambios"}</Button>}
      maxWidthClassName="max-w-4xl"
    >
      <form id="edit-planning-reservation-form" onSubmit={handleSubmit}>
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
