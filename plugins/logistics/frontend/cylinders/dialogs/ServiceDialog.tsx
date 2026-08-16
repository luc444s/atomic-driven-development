// Auto-generado por split-tsx.py
import { Dialog } from "@systutor/shell/ui/dialog";
import { Button } from "@systutor/shell/ui/button";
import { Input, Textarea } from "@systutor/shell/ui/input";
import { Select } from "@systutor/shell/ui/select";
import { Field } from "../utils/formatters";

interface ServiceDialogProps {
  isServiceOpen: boolean;
  setIsServiceOpen: (open: boolean) => void;
  serviceForm: any;
  setServiceForm: (form: any) => void;
  handleService: (event: any) => void;
  serviceMutation: { isPending: boolean };
  serviceTypesQuery: { data: Array<{ id: string; name: string }> };
}

export function ServiceDialog({
    isServiceOpen,
    setIsServiceOpen,
    serviceForm,
    setServiceForm,
    handleService,
    serviceMutation,
    serviceTypesQuery,
}: ServiceDialogProps) {
  return (
<Dialog open={isServiceOpen} title="Registrar servicio" description="Asocia un servicio operativo sobre el envase." onClose={() => setIsServiceOpen(false)}>
  <form className="space-y-4" onSubmit={handleService}>
    <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
      <Field label="Tipo servicio">
        <Select value={serviceForm.service_type_id} onChange={(value) => setServiceForm((current) => ({ ...current, service_type_id: value }))}
          placeholder="Selecciona"
          options={(serviceTypesQuery.data ?? []).map((item) => ({ value: item.id, label: item.name }))} />
      </Field>
      <Field label="Estado"><Input value={serviceForm.status} onChange={(event) => setServiceForm((current) => ({ ...current, status: event.target.value }))} /></Field>
      <Field label="Inicio"><Input type="datetime-local" value={serviceForm.start_date} onChange={(event) => setServiceForm((current) => ({ ...current, start_date: event.target.value }))} /></Field>
      <Field label="Fin"><Input type="datetime-local" value={serviceForm.end_date} onChange={(event) => setServiceForm((current) => ({ ...current, end_date: event.target.value }))} /></Field>
      <Field label="Precio compra"><Input type="number" value={serviceForm.purchase_price} onChange={(event) => setServiceForm((current) => ({ ...current, purchase_price: event.target.value }))} /></Field>
      <Field label="Precio venta"><Input type="number" value={serviceForm.sale_price} onChange={(event) => setServiceForm((current) => ({ ...current, sale_price: event.target.value }))} /></Field>
      <Field label="Stock ingreso"><Input type="number" value={serviceForm.stock_in} onChange={(event) => setServiceForm((current) => ({ ...current, stock_in: event.target.value }))} /></Field>
      <Field label="Stock egreso"><Input type="number" value={serviceForm.stock_out} onChange={(event) => setServiceForm((current) => ({ ...current, stock_out: event.target.value }))} /></Field>
      <Field label="Grupo"><Input value={serviceForm.group_code} onChange={(event) => setServiceForm((current) => ({ ...current, group_code: event.target.value }))} /></Field>
      <Field label="Desc %"><Input type="number" value={serviceForm.discount_pct} onChange={(event) => setServiceForm((current) => ({ ...current, discount_pct: event.target.value }))} /></Field>
      <Field label="Desc monto"><Input type="number" value={serviceForm.discount_amount} onChange={(event) => setServiceForm((current) => ({ ...current, discount_amount: event.target.value }))} /></Field>
      <Field label="Total"><Input type="number" value={serviceForm.total_amount} onChange={(event) => setServiceForm((current) => ({ ...current, total_amount: event.target.value }))} /></Field>
    </div>
    <Field label="Notas"><Textarea rows={4} value={serviceForm.notes} onChange={(event) => setServiceForm((current) => ({ ...current, notes: event.target.value }))} /></Field>
    <div className="flex justify-end gap-2">
      <Button type="button" variant="secondary" onClick={() => setIsServiceOpen(false)}>Cancelar</Button>
      <Button type="submit" disabled={serviceMutation.isPending}>Registrar servicio</Button>
    </div>
  </form>
</Dialog>
  );
}
