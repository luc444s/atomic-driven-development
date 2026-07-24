import { useCallback, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { ConsoleShell } from "../../../../../apps/web/src/shared/ui/console-shell";
import { COTIZACION_TOKENS } from "../dsl/tokens";
import { createCotizacionCompletionProvider } from "../dsl/autocomplete";
import { executeCotizacion, cotizacionKeys } from "../api";
import { CotizacionResult } from "../components/CotizacionResult";
import { QuoteDraftList } from "../components/QuoteDraftList";
import { COTIZACION_HELP, isHelpCommand } from "../dsl/help";
import { parseCommand } from "../dsl/parser";
import type { ConfirmAction } from "../../../../../apps/web/src/shared/confirm";

const completionProvider = createCotizacionCompletionProvider();

export function CotizacionPage() {
  const [mode, setMode] = useState<"tui" | "ui">("tui");
  const queryClient = useQueryClient();

  const invalidate = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: cotizacionKeys.list() });
  }, [queryClient]);

  const handleExecute = useCallback(
    async (command: string): Promise<unknown> => {
      const trimmed = command.trim();
      if (!trimmed) return;

      if (isHelpCommand(trimmed)) return COTIZACION_HELP;

      if (trimmed.toLowerCase().startsWith("preview cotizar")) {
        return executeCotizacion(trimmed);
      }

      if (trimmed.toLowerCase().startsWith("cotizar")) {
        const parsed = parseCommand(trimmed);
        if (!parsed.cliente || parsed.items.length === 0 || !parsed.fecha) {
          return executeCotizacion(trimmed);
        }
        const previewResult = await executeCotizacion(`preview ${trimmed}`);
        const confirmAction: ConfirmAction = {
          _confirm: true,
          previewResult,
          confirmMessage: `Crear cotización para ${parsed.cliente.raw} (${parsed.items.length} item(s))`,
          execute: async () => {
            const result = await executeCotizacion(trimmed);
            invalidate();
            return result;
          },
          cancelMessage: "Cotización cancelada",
        };
        return confirmAction;
      }

      if (trimmed.toLowerCase() === "lista") {
        const drafts = await (await import("../api")).listCotizaciones();
        if (drafts.length === 0) return "Sin cotizaciones aún.";
        return drafts
          .map(
            (d, i) =>
              `${i + 1}. ${d.customer_name ?? "—"} — ${d.delivery_date} [${d.status}]`,
          )
          .join("\n");
      }

      return executeCotizacion(trimmed);
    },
    [invalidate],
  );

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-white/10">
        <h2 className="text-sm font-semibold text-foreground">Cotización</h2>
        <div className="flex gap-1">
          <button
            onClick={() => setMode("tui")}
            className={`px-2 py-1 text-xs rounded ${
              mode === "tui"
                ? "bg-primary/20 text-primary"
                : "text-muted-foreground/60 hover:text-foreground"
            }`}
          >
            ⌨ Terminal
          </button>
          <button
            onClick={() => setMode("ui")}
            className={`px-2 py-1 text-xs rounded ${
              mode === "ui"
                ? "bg-primary/20 text-primary"
                : "text-muted-foreground/60 hover:text-foreground"
            }`}
          >
            📋 Formulario
          </button>
        </div>
      </div>

      {/* Content */}
      {mode === "tui" ? (
        <div className="flex-1 flex flex-col min-h-0">
          <div className="flex-1 min-h-0">
            <ConsoleShell
              completionProvider={completionProvider}
              tokenProvider={COTIZACION_TOKENS}
              onExecute={handleExecute}
              renderResult={(data) =>
                typeof data === "string" ? (
                  <pre className="whitespace-pre-wrap text-xs leading-relaxed">
                    {data}
                  </pre>
                ) : (
                  <CotizacionResult draft={data as any} />
                )
              }
              placeholder='cotizar cliente "nombre" ...'
            />
          </div>
          <div className="border-t border-white/10 px-4 py-2">
            <QuoteDraftList />
          </div>
        </div>
      ) : (
        <div className="flex-1 p-4 overflow-y-auto">
          <p className="text-sm text-muted-foreground">
            Formulario visual — próximamente
          </p>
        </div>
      )}
    </div>
  );
}
