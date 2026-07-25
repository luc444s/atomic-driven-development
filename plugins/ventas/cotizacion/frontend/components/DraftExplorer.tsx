import { useState, useMemo, useCallback } from "react";
import { useDraftList, useDraftDetail } from "../shared/hooks/useDraftList";
import { formatDraftId } from "../dsl/parser";

const PAGE_SIZE = 25;

export function DraftExplorer() {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [limit, setLimit] = useState(PAGE_SIZE);
  const { drafts } = useDraftList();

  const filtered = useMemo(() => {
    if (!drafts) return [];
    if (!query) return drafts;
    const q = query.toLowerCase();
    return drafts.filter(
      (d) =>
        d.customer_name?.toLowerCase().includes(q) ||
        d.id.toLowerCase().includes(q) ||
        d.delivery_date.includes(q),
    );
  }, [drafts, query]);

  const visible = useMemo(() => filtered.slice(0, limit), [filtered, limit]);
  const hasMore = filtered.length > limit;

  const handleLoadMore = useCallback(() => {
    setLimit((prev) => prev + PAGE_SIZE);
  }, []);

  const { data: detail } = useDraftDetail(selectedId);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const handleToggle = useCallback((id: string) => {
    setExpandedId((prev) => (prev === id ? null : id));
    setSelectedId(id);
  }, []);

  if (!drafts || drafts.length === 0) {
    return (
      <div className="text-xs text-muted-foreground/50 py-2 text-center">
        Sin cotizaciones aún
      </div>
    );
  }

  return (
    <div className="text-xs font-mono">
      <div className="flex gap-2 pb-2">
        <input
          type="text"
          placeholder="Buscar por cliente, ID o fecha..."
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setLimit(PAGE_SIZE);
          }}
          className="flex-1 bg-white/5 border border-white/10 rounded px-2 py-1 text-xs text-foreground placeholder:text-muted-foreground/40 outline-none focus:border-primary/50"
        />
        <span className="text-muted-foreground/40 py-1 text-[10px]">
          {filtered.length} resultado(s)
        </span>
      </div>

      {visible.length === 0 ? (
        <div className="text-xs text-muted-foreground/50 py-2 text-center">
          Sin resultados para "{query}"
        </div>
      ) : (
        <table className="w-full border-collapse">
          <thead>
            <tr className="text-muted-foreground/60 border-b border-white/5">
              <th className="text-left py-1 px-2 font-normal">#</th>
              <th className="text-left py-1 px-2 font-normal">Cliente</th>
              <th className="text-left py-1 px-2 font-normal">Entrega</th>
              <th className="text-left py-1 px-2 font-normal">Estado</th>
              <th className="w-4" />
            </tr>
          </thead>
          <tbody>
            {visible.map((d) => (
              <>
                <tr
                  key={d.id}
                  className="border-b border-white/5 hover:bg-white/5 cursor-pointer"
                  onClick={() => handleToggle(d.id)}
                >
                  <td className="py-1.5 px-2 text-primary/70">{formatDraftId(d.id)}</td>
                  <td className="py-1.5 px-2">{d.customer_name ?? "—"}</td>
                  <td className="py-1.5 px-2 text-muted-foreground">{d.delivery_date}</td>
                  <td className="py-1.5 px-2">
                    <span className="text-yellow-400/80">{d.status}</span>
                  </td>
                  <td className="py-1.5 px-2 text-muted-foreground/40">
                    {expandedId === d.id ? "▲" : "▼"}
                  </td>
                </tr>
                {expandedId === d.id && detail && (
                  <tr key={`${d.id}-detail`}>
                    <td colSpan={5} className="px-2 pb-2">
                      <QuotePreviewText draft={detail} />
                    </td>
                  </tr>
                )}
              </>
            ))}
          </tbody>
        </table>
      )}

      {hasMore && (
        <button
          onClick={handleLoadMore}
          className="w-full text-center text-primary/70 hover:text-primary py-2 text-xs"
        >
          Cargar más ({filtered.length - limit} restantes)
        </button>
      )}
    </div>
  );
}

function QuotePreviewText({ draft }: { draft: any }) {
  return (
    <div className="bg-white/5 rounded p-2 space-y-1 text-xs leading-relaxed">
      <div className="flex gap-3">
        <span className="text-green-400">✓</span>
        <span className="text-muted-foreground">Cliente</span>
        <span>{draft.customer.name}</span>
      </div>
      {draft.items.map((item: any, i: number) => (
        <div key={i} className="flex gap-3">
          <span className="text-green-400">✓</span>
          <span className="text-muted-foreground">Producto</span>
          <span>
            {item.product_name ?? item.product_id}
            <span className="ml-2 text-muted-foreground">x{item.quantity}</span>
          </span>
        </div>
      ))}
      <div className="flex gap-3">
        <span className="text-green-400">✓</span>
        <span className="text-muted-foreground">Entrega</span>
        <span>
          {draft.delivery_date}
          {draft.delivery_time ? ` ${draft.delivery_time}` : ""}
        </span>
      </div>
      {draft.vehicle && (
        <div className="flex gap-3">
          <span className="text-green-400">✓</span>
          <span className="text-muted-foreground">Vehículo</span>
          <span>{draft.vehicle.plate}</span>
        </div>
      )}
      {draft.conditions && (
        <div className="flex gap-3">
          <span className="text-muted-foreground">—</span>
          <span className="text-muted-foreground">Cond</span>
          <span className="italic text-muted-foreground">{draft.conditions}</span>
        </div>
      )}
      <div className="pt-1 text-muted-foreground/60 text-[10px]">
        Creado {new Date(draft.created_at).toLocaleString()}
      </div>
    </div>
  );
}
