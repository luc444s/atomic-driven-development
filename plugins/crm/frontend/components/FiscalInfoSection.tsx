import { Combobox, type ComboboxOption } from "../../../../apps/web/src/shared/ui/combobox";
import { Input } from "../../../../apps/web/src/shared/ui/input";

type FiscalInfoSectionProps = {
  documentType: string;
  documentNumber: string;
  countryCode: string;
  countryOptions: ComboboxOption[];
  documentTypeOptions: ComboboxOption[];
  accountingCode: string | null;
  isIntracommunity: boolean;
  fiscalOperationKey: string | null;
  taxRegimeCode: string | null;
  equivalenceSurchargeApplicable: boolean;
  cashCriterionApplicable: boolean;
  onChange: (field: string, value: string | boolean) => void;
};

export function FiscalInfoSection({
  documentType,
  documentNumber,
  countryCode,
  countryOptions,
  documentTypeOptions,
  accountingCode,
  isIntracommunity,
  fiscalOperationKey,
  taxRegimeCode,
  equivalenceSurchargeApplicable,
  cashCriterionApplicable,
  onChange,
}: FiscalInfoSectionProps) {
  return (
    <div className="space-y-4">
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

      <div className="rounded-md border border-border p-4">
        <p className="mb-3 text-sm font-medium text-foreground">Datos fiscales</p>
        <div className="grid gap-4 md:grid-cols-3">
          <label className="block space-y-2 text-sm text-foreground">
            <span>Código contable</span>
            <Input
              value={accountingCode ?? ""}
              onChange={(event) => onChange("accounting_code", event.target.value || null)}
              placeholder="Ej. 43000001"
            />
          </label>
          <label className="block space-y-2 text-sm text-foreground">
            <span>Clave operación fiscal</span>
            <Input
              value={fiscalOperationKey ?? ""}
              onChange={(event) => onChange("fiscal_operation_key", event.target.value || null)}
              placeholder="Ej. S1"
            />
          </label>
          <label className="block space-y-2 text-sm text-foreground">
            <span>Régimen fiscal</span>
            <Input
              value={taxRegimeCode ?? ""}
              onChange={(event) => onChange("tax_regime_code", event.target.value || null)}
              placeholder="Ej. 612"
            />
          </label>
        </div>
        <div className="mt-4 grid gap-3 md:grid-cols-3">
          <label className="flex items-center gap-2 text-sm text-foreground">
            <input
              type="checkbox"
              checked={isIntracommunity}
              onChange={(event) => onChange("is_intracommunity", event.target.checked)}
            />
            <span>Intracomunitario</span>
          </label>
          <label className="flex items-center gap-2 text-sm text-foreground">
            <input
              type="checkbox"
              checked={equivalenceSurchargeApplicable}
              onChange={(event) => onChange("equivalence_surcharge_applicable", event.target.checked)}
            />
            <span>Recargo de equivalencia</span>
          </label>
          <label className="flex items-center gap-2 text-sm text-foreground">
            <input
              type="checkbox"
              checked={cashCriterionApplicable}
              onChange={(event) => onChange("cash_criterion_applicable", event.target.checked)}
            />
            <span>Criterio de caja</span>
          </label>
        </div>
      </div>
    </div>
  );
}
