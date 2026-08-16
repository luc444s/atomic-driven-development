// Auto-generado por split-tsx.py
import { Dialog } from "@systutor/shell/ui/dialog";
import { Button } from "@systutor/shell/ui/button";
import { Input, Textarea } from "@systutor/shell/ui/input";
import { Field } from "../utils/formatters";

interface RetimbradoDialogProps {
  isRetimbradoOpen: boolean;
  setIsRetimbradoOpen: (open: boolean) => void;
  retimbradoForm: any;
  setRetimbradoForm: (form: any) => void;
  handleRetimbrado: (event: any) => void;
  retimbradoMutation: { isPending: boolean };
}

export function RetimbradoDialog({
    isRetimbradoOpen,
    setIsRetimbradoOpen,
    retimbradoForm,
    setRetimbradoForm,
    handleRetimbrado,
    retimbradoMutation,
}: RetimbradoDialogProps) {
  return (
<Dialog open={isRetimbradoOpen} title="Registrar retimbrado" description="Carga la ficha técnica del retimbrado del envase." onClose={() => setIsRetimbradoOpen(false)}>
  <form className="space-y-4" onSubmit={handleRetimbrado}>
    <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
      <Field label="Fecha"><Input type="date" value={retimbradoForm.retimbrado_date} onChange={(event) => setRetimbradoForm((current) => ({ ...current, retimbrado_date: event.target.value }))} /></Field>
      <Field label="Código fabricación"><Input value={retimbradoForm.manufacture_code} onChange={(event) => setRetimbradoForm((current) => ({ ...current, manufacture_code: event.target.value }))} /></Field>
      <Field label="Año"><Input type="number" value={retimbradoForm.manufacture_year} onChange={(event) => setRetimbradoForm((current) => ({ ...current, manufacture_year: event.target.value }))} /></Field>
      <Field label="Nro bombona"><Input value={retimbradoForm.serial_number} onChange={(event) => setRetimbradoForm((current) => ({ ...current, serial_number: event.target.value }))} /></Field>
      <Field label="Peso origen"><Input type="number" value={retimbradoForm.weight_origin} onChange={(event) => setRetimbradoForm((current) => ({ ...current, weight_origin: event.target.value }))} /></Field>
      <Field label="Peso actual"><Input type="number" value={retimbradoForm.weight_current} onChange={(event) => setRetimbradoForm((current) => ({ ...current, weight_current: event.target.value }))} /></Field>
      <Field label="Presión servicio"><Input type="number" value={retimbradoForm.service_pressure} onChange={(event) => setRetimbradoForm((current) => ({ ...current, service_pressure: event.target.value }))} /></Field>
      <Field label="Presión prueba"><Input type="number" value={retimbradoForm.test_pressure} onChange={(event) => setRetimbradoForm((current) => ({ ...current, test_pressure: event.target.value }))} /></Field>
      <Field label="Nro aprobación"><Input value={retimbradoForm.approval_number} onChange={(event) => setRetimbradoForm((current) => ({ ...current, approval_number: event.target.value }))} /></Field>
      <Field label="Clase peligro"><Input value={retimbradoForm.danger_class} onChange={(event) => setRetimbradoForm((current) => ({ ...current, danger_class: event.target.value }))} /></Field>
      <Field label="Marcado 1"><Input value={retimbradoForm.marking1} onChange={(event) => setRetimbradoForm((current) => ({ ...current, marking1: event.target.value }))} /></Field>
      <Field label="Marcado 2"><Input value={retimbradoForm.marking2} onChange={(event) => setRetimbradoForm((current) => ({ ...current, marking2: event.target.value }))} /></Field>
      <Field label="Formato bulto"><Input value={retimbradoForm.package_format} onChange={(event) => setRetimbradoForm((current) => ({ ...current, package_format: event.target.value }))} /></Field>
      <Field label="Transporte"><Input type="number" value={retimbradoForm.transport_code} onChange={(event) => setRetimbradoForm((current) => ({ ...current, transport_code: event.target.value }))} /></Field>
      <Field label="Etiqueta ADR"><Input value={retimbradoForm.adr_label} onChange={(event) => setRetimbradoForm((current) => ({ ...current, adr_label: event.target.value }))} /></Field>
      <Field label="Túnel ADR"><Input value={retimbradoForm.adr_tunnel} onChange={(event) => setRetimbradoForm((current) => ({ ...current, adr_tunnel: event.target.value }))} /></Field>
      <Field label="Nro ONU"><Input value={retimbradoForm.un_number} onChange={(event) => setRetimbradoForm((current) => ({ ...current, un_number: event.target.value }))} /></Field>
      <Field label="Registro alimentario"><Input value={retimbradoForm.food_registry} onChange={(event) => setRetimbradoForm((current) => ({ ...current, food_registry: event.target.value }))} /></Field>
    </div>
    <Field label="Notas"><Textarea rows={4} value={retimbradoForm.notes} onChange={(event) => setRetimbradoForm((current) => ({ ...current, notes: event.target.value }))} /></Field>
    <div className="flex justify-end gap-2">
      <Button type="button" variant="secondary" onClick={() => setIsRetimbradoOpen(false)}>Cancelar</Button>
      <Button type="submit" disabled={retimbradoMutation.isPending}>Registrar retimbrado</Button>
    </div>
  </form>
</Dialog>
  );
}
