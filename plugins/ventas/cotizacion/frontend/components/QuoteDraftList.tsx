import { useState, Fragment } from "react";
import { useQuery } from "@tanstack/react-query";
import { listCotizaciones, cotizacionKeys, getCotizacion } from "../api";
import { formatDraftId } from "../dsl/parser";
import type { QuoteDraftDTO } from "../api";

export function QuoteDraftList() {
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const { data: drafts } = useQuery({
    queryKey: cotizacionKeys.list(),
    queryFn: listCotizaciones,
    refetchInterval: 30_000,
  });

  const { data: detail } = useQuery({
    queryKey: cotizacionKeys.detail(selectedId ?? ""),
    queryFn: () => getCotizacion(selectedId!),
    enabled: !!selectedId,
  });

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
            <Fragment key={d.id}>
              <tr
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
                <tr>
                  <td colSpan={6} className="px-2 pb-2">
                    <QuoteDraftDetail draft={detail} />
                  </td>
                </tr>
              )}
            </Fragment>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function QuoteDraftDetail({ draft }: { draft: QuoteDraftDTO }) {
  return (
    <div className="bg-white/5 rounded p-2 space-y-1 text-xs leading-relaxed">
      <div className="flex gap-3">
        <span className="text-green-400">✓</span>
        <span className="text-muted-foreground">Cliente</span>
        <span>{draft.customer.name}</span>
      </div>
      {draft.items.map((item, i) => (
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
