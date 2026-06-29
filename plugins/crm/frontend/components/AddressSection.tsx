import type { CustomerAddressPayload } from "../types";
import { Input } from "../../../../apps/web/src/shared/ui/input";

type AddressSectionProps = {
  value: CustomerAddressPayload;
  onChange: (value: CustomerAddressPayload) => void;
};

export function AddressSection({ value, onChange }: AddressSectionProps) {
  return (
    <div className="grid gap-4 md:grid-cols-2">
      <label className="block space-y-2 text-sm text-slate-300">
        <span>Dirección</span>
        <Input value={value.line1} onChange={(event) => onChange({ ...value, line1: event.target.value })} />
      </label>
      <label className="block space-y-2 text-sm text-slate-300">
        <span>Distrito / Ciudad</span>
        <Input value={value.district ?? value.city ?? ""} onChange={(event) => onChange({ ...value, district: event.target.value, city: event.target.value })} />
      </label>
      <label className="block space-y-2 text-sm text-slate-300">
        <span>Contacto</span>
        <Input value={value.contact_name ?? ""} onChange={(event) => onChange({ ...value, contact_name: event.target.value })} />
      </label>
      <label className="block space-y-2 text-sm text-slate-300">
        <span>Teléfono</span>
        <Input value={value.contact_phone ?? ""} onChange={(event) => onChange({ ...value, contact_phone: event.target.value })} />
      </label>
    </div>
  );
}
