import type { QuoteDraftDTO } from "../shared/types";
import { formatDraftId } from "../dsl/parser";

interface QuotePreviewProps {
  draft: QuoteDraftDTO;
}

export function QuotePreview({ draft }: QuotePreviewProps) {
  const isPreview = draft.id === "preview";

  return (
    <div className="space-y-1 py-1 font-mono text-xs leading-relaxed text-[#C9D1D9]">
      <div className="flex gap-3">
        <span className="shrink-0 text-green-400">&check;</span>
        <span className="text-muted-foreground">Cliente</span>
        <span className="text-foreground">{draft.customer.name}</span>
      </div>

      {draft.items.map((item, i) => (
        <div key={i} className="flex gap-3">
          <span className="shrink-0 text-green-400">&check;</span>
          <span className="text-muted-foreground">Producto</span>
          <span className="text-foreground">
            {item.product_name ?? item.product_id}
            <span className="ml-2 text-muted-foreground">x{item.quantity}</span>
          </span>
        </div>
      ))}

      <div className="flex gap-3">
        <span className="shrink-0 text-green-400">&check;</span>
        <span className="text-muted-foreground">Entrega</span>
        <span className="text-foreground">
          {draft.delivery_date}
          {draft.delivery_time ? ` ${draft.delivery_time}` : ""}
        </span>
      </div>

      {draft.vehicle && (
        <div className="flex gap-3">
          <span className="shrink-0 text-green-400">&check;</span>
          <span className="text-muted-foreground">Vehículo</span>
          <span className="text-foreground">{draft.vehicle.plate}</span>
        </div>
      )}

      {draft.conditions && (
        <div className="flex gap-3">
          <span className="shrink-0 text-muted-foreground">&mdash;</span>
          <span className="text-muted-foreground">Cond</span>
          <span className="italic text-muted-foreground">{draft.conditions}</span>
        </div>
      )}

      <div className="pt-1">
        <span className="text-primary/80">
          {isPreview ? "\u2192 preview \u2014 no guardado" : `\u2192 draft ${formatDraftId(draft.id)} creado`}
        </span>
      </div>
    </div>
  );
}
