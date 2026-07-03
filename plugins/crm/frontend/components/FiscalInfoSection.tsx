import { Combobox, type ComboboxOption } from "../../../../apps/web/src/shared/ui/combobox";
import { Input } from "../../../../apps/web/src/shared/ui/input";

type FiscalInfoSectionProps = {
  documentType: string;
  documentNumber: string;
  countryCode: string;
  countryOptions: ComboboxOption[];
  documentTypeOptions: ComboboxOption[];
  onChange: (field: "document_type_code" | "document_number" | "country_code", value: string) => void;
};

export function FiscalInfoSection({ documentType, documentNumber, countryCode, countryOptions, documentTypeOptions, onChange }: FiscalInfoSectionProps) {
  return (
    <div className="grid gap-4 md:grid-cols-3">
      <label className="block space-y-2 text-sm text-foreground">
        <span>País</span>
        <Combobox
          value={countryCode}
          onChange={(value) => onChange("country_code", value)}
          options={countryOptions}
          placeholder="Seleccionar país"
          searchPlaceholder="Buscar país"
        />
      </label>
      <label className="block space-y-2 text-sm text-foreground">
        <span>Tipo documento</span>
        <Combobox
          value={documentType}
          onChange={(value) => onChange("document_type_code", value)}
          options={documentTypeOptions}
          placeholder="Seleccionar tipo"
          searchPlaceholder="Buscar tipo"
        />
      </label>
      <label className="block space-y-2 text-sm text-foreground">
        <span>Número documento</span>
        <Input value={documentNumber} onChange={(event) => onChange("document_number", event.target.value.toUpperCase())} />
      </label>
    </div>
  );
}
