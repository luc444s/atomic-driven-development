import type { StockBalanceItem } from "../../../../stock/frontend/types";

type Props = {
  mobileRows: StockBalanceItem[];
};

export function MobileStockInline({ mobileRows }: Props) {
  const nonZeroRows = mobileRows.filter((row) => row.quantity > 0);
  const totalUnits = nonZeroRows.reduce((sum, row) => sum + row.quantity, 0);
  const stockSummary = nonZeroRows.length
    ? nonZeroRows.map((row) => `${row.product_name} ${row.quantity}`).join(" · ")
    : "Sin saldo móvil todavía.";

  return (
    <div className="flex h-full flex-col justify-between space-y-3 rounded-2xl bg-muted/35 px-4 py-4 sm:px-5">
      <div>
        <p className="text-[11px] uppercase tracking-wide text-muted-foreground">
          Stock actual del almacén móvil
        </p>
        <p className="mt-1 font-medium text-foreground">
          Stock móvil actual: {totalUnits} und / {nonZeroRows.length} productos
        </p>
      </div>
      <p className="text-sm leading-relaxed text-muted-foreground">{stockSummary}</p>
    </div>
  );
}
