import { Input } from "../../../../apps/web/src/shared/ui/input";

type FiscalInfoSectionProps = {
  documentType: string;
  documentNumber: string;
  countryCode: string;
  onChange: (field: "document_type_code" | "document_number" | "country_code", value: string) => void;
};

export function FiscalInfoSection({ documentType, documentNumber, countryCode, onChange }: FiscalInfoSectionProps) {
  return (
    <div className="grid gap-4 md:grid-cols-3">
      <label className="block space-y-2 text-sm text-foreground">
        <span>País</span>
        <Input value={countryCode} onChange={(event) => onChange("country_code", event.target.value.toUpperCase())} />
      </label>
      <label className="block space-y-2 text-sm text-foreground">
        <span>Tipo documento</span>
        <Input value={documentType} onChange={(event) => onChange("document_type_code", event.target.value.toUpperCase())} />
      </label>
      <label className="block space-y-2 text-sm text-foreground">
        <span>Número documento</span>
        <Input value={documentNumber} onChange={(event) => onChange("document_number", event.target.value.toUpperCase())} />
      </label>
    </div>
  );
}
