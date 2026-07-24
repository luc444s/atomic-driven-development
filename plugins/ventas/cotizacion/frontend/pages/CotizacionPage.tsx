import { useCallback } from "react";
import { ConsoleShell } from "../../../../../apps/web/src/shared/ui/console-shell";
import { COTIZACION_TOKENS } from "../dsl/tokens";
import { createCotizacionCompletionProvider } from "../dsl/autocomplete";
import { executeCotizacion } from "../api";
import { CotizacionResult } from "../components/CotizacionResult";
import { COTIZACION_HELP, isHelpCommand } from "../dsl/help";
import { parseCommand } from "../dsl/parser";
import type { ConfirmAction } from "../../../../../apps/web/src/shared/confirm";

const completionProvider = createCotizacionCompletionProvider();

export function CotizacionPage() {
  const handleExecute = useCallback(
    async (command: string): Promise<unknown> => {
      const trimmed = command.trim();
      if (!trimmed) return;

      if (isHelpCommand(trimmed)) {
        return COTIZACION_HELP;
      }

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
          execute: () => executeCotizacion(trimmed),
          cancelMessage: "Cotización cancelada",
        };
        return confirmAction;
      }

      return executeCotizacion(trimmed);
    },
    [],
  );

  return (
    <ConsoleShell
      completionProvider={completionProvider}
      tokenProvider={COTIZACION_TOKENS}
      onExecute={handleExecute}
      renderResult={(data) =>
        typeof data === "string" ? (
          <pre className="whitespace-pre-wrap text-xs leading-relaxed">{data}</pre>
        ) : (
          <CotizacionResult draft={data as any} />
        )
      }
      placeholder="cotizar cliente ..."
    />
  );
}
