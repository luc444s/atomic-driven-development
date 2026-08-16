// Auto-generado por split-tsx.py
import { Dialog } from "@systutor/shell/ui/dialog";
import { Button } from "@systutor/shell/ui/button";
import { Input, Textarea } from "@systutor/shell/ui/input";
import { Field } from "../utils/formatters";

interface HydrotestDialogProps {
  isHydrotestOpen: boolean;
  setIsHydrotestOpen: (open: boolean) => void;
  hydrotestForm: any;
  setHydrotestForm: (form: any) => void;
  handleHydrotest: (event: any) => void;
  hydrotestMutation: { isPending: boolean };
}

export function HydrotestDialog({
    isHydrotestOpen,
    setIsHydrotestOpen,
    hydrotestForm,
    setHydrotestForm,
    handleHydrotest,
    hydrotestMutation,
}: HydrotestDialogProps) {
  return (
<Dialog open={isHydrotestOpen} title="Registrar PH" description="Actualiza la prueba hidrostática vigente del envase." onClose={() => setIsHydrotestOpen(false)}>
  <form className="space-y-4" onSubmit={handleHydrotest}>
    <div className="grid gap-3 md:grid-cols-2">
      <Field label="Fecha de PH"><Input type="date" value={hydrotestForm.test_date} onChange={(event) => setHydrotestForm((current) => ({ ...current, test_date: event.target.value }))} /></Field>
      <Field label="Estado"><Input value={hydrotestForm.status} onChange={(event) => setHydrotestForm((current) => ({ ...current, status: event.target.value }))} /></Field>
    </div>
    <Field label="Notas"><Textarea rows={4} value={hydrotestForm.notes} onChange={(event) => setHydrotestForm((current) => ({ ...current, notes: event.target.value }))} /></Field>
    <div className="flex justify-end gap-2">
      <Button type="button" variant="secondary" onClick={() => setIsHydrotestOpen(false)}>Cancelar</Button>
      <Button type="submit" disabled={hydrotestMutation.isPending}>Registrar PH</Button>
    </div>
  </form>
</Dialog>
  );
}
