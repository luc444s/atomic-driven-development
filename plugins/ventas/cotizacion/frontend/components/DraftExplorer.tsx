import { useState } from "react";
import { useDraftList, useDraftDetail } from "../../shared/hooks/useDraftList";
import { formatDraftId } from "../../console/parser/parser";

export function DraftExplorer() {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const { drafts } = useDraftList();
  const { data: detail } = useDraftDetail(selectedId);

  if (!drafts || drafts.length === 0) {
    return (
      <div className="text-xs text-muted-foreground/50 py-2 text-center">
        Sin cotizaciones aún
      </div>
    );
  }

  return (
    <div className="text-xs font-mono">
      <table className="w-full border-collapse">
        <thead>
          <tr className="text-muted-foreground/60 border-b border-white/5">
            <th className="text-left py-1 px-2 font-normal">#</th>
            <th className="text-left py-1 px-2 font-normal">Cliente</th>
            <th className="text-right py-1 px-2 font-normal">Items</th>
            <th className="text-left py-1 px-2 font-normal">Entrega</th>
            <th className="text-left py-1 px-2 font-normal">Estado</th>
            <th className="w-4" />
          </tr>
        </thead>
        <tbody>
          {drafts.map((d) => (
            <>
              <tr
                key={d.id}
                className="border-b border-white/5 hover:bg-white/5 cursor-pointer"
                onClick={() => setSelectedId(selectedId === d.id ? null : d.id)}
              >
                <td className="py-1.5 px-2 text-primary/70">{formatDraftId(d.id)}</td>
                <td className="py-1.5 px-2">{d.customer_name ?? "—"}</td>
                <td className="py-1.5 px-2 text-right text-muted-foreground">—</td>
                <td className="py-1.5 px-2 text-muted-foreground">{d.delivery_date}</td>
                <td className="py-1.5 px-2">
                  <span className="text-yellow-400/80">{d.status}</span>
                </td>
                <td className="py-1.5 px-2 text-muted-foreground/40">
                  {selectedId === d.id ? "▲" : "▼"}
                </td>
              </tr>
              {selectedId === d.id && detail && (
                <tr key={`${d.id}-detail`}>
                  <td colSpan={6} className="px-2 pb-2">
                    <QuotePreview draft={detail} />
                  </td>
                </tr>
              )}
            </>
          ))}
        </tbody>
      </table>
    </div>
  );
}

import { QuotePreview } from "./QuotePreview";
