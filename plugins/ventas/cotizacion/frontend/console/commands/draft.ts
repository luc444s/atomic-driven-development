import { listCotizaciones, getCotizacion } from "../../shared/api";
import type { QuoteDraftListItem, QuoteDraftDTO } from "../../shared/types";

type DraftHandlerResult = string | { action: "open"; id: string; draft: QuoteDraftDTO };

export async function handleDraftCommand(args: string[]): Promise<DraftHandlerResult | string> {
  const sub = args[0]?.toLowerCase();

  if (!sub || sub === "list") {
    const limitFlag = args.indexOf("-n");
    const allFlag = args.includes("--all");
    const limit = allFlag ? Infinity : limitFlag !== -1 ? parseInt(args[limitFlag + 1], 10) || 10 : 10;
    const drafts = await listCotizaciones();
    if (drafts.length === 0) return "Sin cotizaciones aún.";
    const items = allFlag ? drafts : drafts.slice(0, limit);
    const output = items
      .map((d, i) => `${i + 1}. ${d.customer_name ?? "—"} — ${d.delivery_date} [${d.status}]`)
      .join("\n");
    const remaining = drafts.length - items.length;
    return remaining > 0 ? `${output}\n\n... y ${remaining} más. Usá draft list --all para ver todas.` : output;
  }

  if (sub === "open" || sub === "show") {
    const id = args[1];
    if (!id) return "Usá: draft open <id> (ej: draft open 42)";
    const fullId = id.length < 36 ? undefined : id;
    if (fullId) {
      const draft = await getCotizacion(fullId);
      return { action: "open", id: fullId, draft };
    }
    const drafts = await listCotizaciones();
    const match = drafts.find((d) => d.id.startsWith(id) || d.id.endsWith(id));
    if (!match) return `Draft #CTZ-${id} no encontrado.`;
    const draft = await getCotizacion(match.id);
    return { action: "open", id: match.id, draft };
  }

  if (sub === "refresh") {
    return "Lista recargada.";
  }

  return `Comando desconocido: draft ${sub}. Usá: draft list, draft open <id>, draft refresh.`;
}
