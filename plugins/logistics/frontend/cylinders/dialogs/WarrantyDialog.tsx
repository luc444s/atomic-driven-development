// Auto-generado por split-tsx.py
import { Dialog } from "@systutor/shell/ui/dialog";
import { Button } from "@systutor/shell/ui/button";
import { Input, Textarea } from "@systutor/shell/ui/input";
import { Field } from "../utils/formatters";

interface WarrantyDialogProps {
  isWarrantyOpen: boolean;
  setIsWarrantyOpen: (open: boolean) => void;
  warrantyForm: any;
  setWarrantyForm: (form: any) => void;
  handleWarranty: (event: any) => void;
  warrantyMutation: { isPending: boolean };
  setIsWarrantyCustomerSearchOpen: (open: boolean) => void;
}

export function WarrantyDialog({
    isWarrantyOpen,
    setIsWarrantyOpen,
    warrantyForm,
    setWarrantyForm,
    handleWarranty,
    warrantyMutation,
    setIsWarrantyCustomerSearchOpen,
}: WarrantyDialogProps) {
  return (
<Dialog open={isWarrantyOpen} title="Registrar garantía" description="Asocia la garantía comercial del envase." onClose={() => setIsWarrantyOpen(false)}>
  <form className="space-y-4" onSubmit={handleWarranty}>
    <div className="grid gap-3 md:grid-cols-2">
      <Field label="Cliente">
        <Button type="button" variant="secondary" onClick={() => setIsWarrantyCustomerSearchOpen(true)}>
          {warrantyForm.customer_name ? `${warrantyForm.customer_name} (${warrantyForm.customer_id})` : "Seleccionar cliente"}
        </Button>
      </Field>
      <Field label="Tipo"><Input value={warrantyForm.warranty_type} onChange={(event) => setWarrantyForm((current) => ({ ...current, warranty_type: event.target.value }))} /></Field>
    </div>
    <Field label="Detalle"><Textarea rows={4} value={warrantyForm.description} onChange={(event) => setWarrantyForm((current) => ({ ...current, description: event.target.value }))} /></Field>
    <div className="flex justify-end gap-2">
      <Button type="button" variant="secondary" onClick={() => setIsWarrantyOpen(false)}>Cancelar</Button>
      <Button type="submit" disabled={warrantyMutation.isPending}>Registrar garantía</Button>
    </div>
  </form>
</Dialog>
  );
}
