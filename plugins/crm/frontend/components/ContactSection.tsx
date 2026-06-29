import { Input } from "../../../../apps/web/src/shared/ui/input";

type ContactSectionProps = {
  email: string;
  phone: string;
  mobile: string;
  onChange: (field: "email" | "phone" | "mobile", value: string) => void;
};

export function ContactSection({ email, phone, mobile, onChange }: ContactSectionProps) {
  return (
    <div className="grid gap-4 md:grid-cols-3">
      <label className="block space-y-2 text-sm text-slate-300">
        <span>Email</span>
        <Input value={email} onChange={(event) => onChange("email", event.target.value)} />
      </label>
      <label className="block space-y-2 text-sm text-slate-300">
        <span>Teléfono</span>
        <Input value={phone} onChange={(event) => onChange("phone", event.target.value)} />
      </label>
      <label className="block space-y-2 text-sm text-slate-300">
        <span>Celular</span>
        <Input value={mobile} onChange={(event) => onChange("mobile", event.target.value)} />
      </label>
    </div>
  );
}
