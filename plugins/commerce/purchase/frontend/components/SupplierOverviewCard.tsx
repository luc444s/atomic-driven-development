import type { Supplier } from "../types";

type Props = {
  supplier: Supplier;
};

export function SupplierOverviewCard({ supplier }: Props) {
  const doc = supplier.document_number
    ? `${supplier.document_type_code ?? ""} ${supplier.document_number}`.trim()
    : "-";
  return (
    <div className="space-y-3 rounded-2xl bg-muted/35 px-4 py-4 sm:px-5">
      <div className="flex flex-wrap items-center gap-3">
        <p className="text-lg font-semibold tracking-tight text-foreground">
          {supplier.commercial_name ?? supplier.name}
        </p>
        <span className={`rounded-full border px-2.5 py-1 text-xs font-medium ${supplier.is_active
          ? "border-success/30 bg-success/10 text-success"
          : "border-destructive/30 bg-destructive/10 text-destructive"}`}>
          {supplier.is_active ? "Activo" : "Inactivo"}
        </span>
      </div>
      <p className="text-sm text-muted-foreground">
        {supplier.commercial_name ? `Fiscal: ${supplier.name}` : "Sin nombre comercial"}
      </p>
      <div className="grid gap-x-6 gap-y-3 text-sm sm:grid-cols-2 xl:grid-cols-4">
        <div className="min-w-0">
          <p className="text-[11px] uppercase tracking-wide text-muted-foreground">Documento</p>
          <p className="font-medium text-foreground">{doc}</p>
        </div>
        <div className="min-w-0">
          <p className="text-[11px] uppercase tracking-wide text-muted-foreground">Email</p>
          <p className="font-medium text-foreground">{supplier.email ?? "-"}</p>
        </div>
        <div className="min-w-0">
          <p className="text-[11px] uppercase tracking-wide text-muted-foreground">Teléfono</p>
          <p className="font-medium text-foreground">{supplier.phone ?? "-"}</p>
        </div>
        <div className="min-w-0">
          <p className="text-[11px] uppercase tracking-wide text-muted-foreground">Forma de pago</p>
          <p className="font-medium text-foreground">{supplier.payment_term_code ?? "-"}</p>
        </div>
      </div>
    </div>
  );
}
