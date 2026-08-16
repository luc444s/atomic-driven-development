// Auto-generado por split-tsx.py
import { Dialog } from "@systutor/shell/ui/dialog";
import { Button } from "@systutor/shell/ui/button";
import { Input, Textarea } from "@systutor/shell/ui/input";
import { Select } from "@systutor/shell/ui/select";
import { Field } from "../utils/formatters";

interface PrintLabelDialogProps {
  isPrintLabelOpen: boolean;
  setIsPrintLabelOpen: (open: boolean) => void;
  printLabelForm: any;
  setPrintLabelForm: (form: any) => void;
  handlePrintLabel: (event: any) => void;
  printLabelMutation: { isPending: boolean };
}

export function PrintLabelDialog({
    isPrintLabelOpen,
    setIsPrintLabelOpen,
    printLabelForm,
    setPrintLabelForm,
    handlePrintLabel,
    printLabelMutation,
}: PrintLabelDialogProps) {
  return (
<Dialog open={isPrintLabelOpen} title="Imprimir etiqueta" description="Registra la impresión operativa de la etiqueta del envase." onClose={() => setIsPrintLabelOpen(false)}>
  <form className="space-y-4" onSubmit={handlePrintLabel}>
    <div className="grid gap-3 md:grid-cols-3">
      <Field label="Origen">
        <Select value={printLabelForm.origin} onChange={(value) => setPrintLabelForm((current) => ({ ...current, origin: value }))}
          options={[
            { value: "ALTA", label: "ALTA" },
            { value: "REIMPRESION", label: "REIMPRESION" },
            { value: "PLUS", label: "PLUS" },
          ]} />
      </Field>
      <Field label="Impresora"><Input value={printLabelForm.printer_name} onChange={(event) => setPrintLabelForm((current) => ({ ...current, printer_name: event.target.value }))} /></Field>
      <Field label="Copias"><Input type="number" value={printLabelForm.copies} onChange={(event) => setPrintLabelForm((current) => ({ ...current, copies: event.target.value }))} /></Field>
    </div>
    <Field label="Motivo"><Textarea rows={3} value={printLabelForm.reason} onChange={(event) => setPrintLabelForm((current) => ({ ...current, reason: event.target.value }))} /></Field>
    <div className="flex justify-end gap-2">
      <Button type="button" variant="secondary" onClick={() => setIsPrintLabelOpen(false)}>Cancelar</Button>
      <Button type="submit" disabled={printLabelMutation.isPending}>Registrar impresión</Button>
    </div>
  </form>
</Dialog>
  );
}
