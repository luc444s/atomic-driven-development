import { Combobox } from "../../../../apps/web/src/shared/ui/combobox";
import type { CustomerAddressPayload } from "../types";
import { Input } from "../../../../apps/web/src/shared/ui/input";

type AddressSectionProps = {
  value: CustomerAddressPayload;
  onChange: (value: CustomerAddressPayload) => void;
};

export function AddressSection({ value, onChange }: AddressSectionProps) {
  return (
    <div className="grid gap-4 md:grid-cols-2">
      <label className="block space-y-2 text-sm text-foreground md:col-span-2">
        <span>Tipo de dirección</span>
        <Combobox
          value={value.address_type}
          onChange={(addressType) => onChange({ ...value, address_type: addressType })}
          options={[
            { value: "FISCAL", label: "Fiscal" },
            { value: "COMERCIAL", label: "Comercial" },
            { value: "ENTREGA", label: "Entrega" },
            { value: "OTRA", label: "Otra" },
          ]}
          placeholder="Seleccionar tipo"
          searchPlaceholder="Buscar tipo"
        />
      </label>
      <label className="block space-y-2 text-sm text-foreground">
        <span>Dirección</span>
        <Input value={value.line1} onChange={(event) => onChange({ ...value, line1: event.target.value })} />
      </label>
      <label className="block space-y-2 text-sm text-foreground">
        <span>Distrito / Ciudad</span>
        <Input value={value.district ?? value.city ?? ""} onChange={(event) => onChange({ ...value, district: event.target.value, city: event.target.value })} />
      </label>
      <label className="block space-y-2 text-sm text-foreground">
        <span>Contacto</span>
        <Input value={value.contact_name ?? ""} onChange={(event) => onChange({ ...value, contact_name: event.target.value })} />
      </label>
      <label className="block space-y-2 text-sm text-foreground">
        <span>Teléfono</span>
        <Input value={value.contact_phone ?? ""} onChange={(event) => onChange({ ...value, contact_phone: event.target.value })} />
      </label>
      <label className="flex items-center gap-2 text-sm text-foreground md:col-span-2">
        <input
          type="checkbox"
          checked={value.is_operational_site}
          onChange={(event) => onChange({ ...value, is_operational_site: event.target.checked })}
        />
        <span>Marcar como sede / establecimiento operativo</span>
      </label>
    </div>
  );
}
