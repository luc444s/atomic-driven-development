export function toNullable(value: string) {
  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : null;
}

export function toNumberOrNull(value: string) {
  const trimmed = value.trim();
  if (!trimmed) {
    return null;
  }
  const parsed = Number(trimmed);
  return Number.isNaN(parsed) ? null : parsed;
}

export function toIntegerOrNull(value: string) {
  const parsed = toNumberOrNull(value);
  return parsed === null ? null : Math.trunc(parsed);
}

export function formatDate(value: string | null | undefined) {
  if (!value) {
    return "-";
  }
  return value;
}

export function formatDateTime(value: string | null | undefined) {
  if (!value) {
    return "-";
  }
  return new Date(value).toLocaleString();
}

export function InfoBlock({ label, value }: { label: string; value: string | null }) {
  return (
    <div className="space-y-1">
      <p className="text-xs uppercase tracking-[0.12em] text-muted-foreground">{label}</p>
      <p className="text-sm text-foreground">{value || "-"}</p>
    </div>
  );
}

export function DataCard({ title, description, table }: { title: string; description: string; table: any }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent>{table}</CardContent>
    </Card>
  );
}

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@systutor/shell/ui/card";

export function Field({ label, children, className }: { label: string; children: any; className?: string }) {
  return (
    <label className={["space-y-1 text-sm text-foreground", className ?? ""].join(" ")}>
      <span className="block text-xs uppercase tracking-[0.12em] text-muted-foreground">{label}</span>
      {children}
    </label>
  );
}

export function FormRow({ title, children }: { title: string; children: any }) {
  return (
    <div className="space-y-3">
      <p className="text-xs font-medium uppercase tracking-[0.18em] text-muted-foreground">{title}</p>
      {children}
    </div>
  );
}
