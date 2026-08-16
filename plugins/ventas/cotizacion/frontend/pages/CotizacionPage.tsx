import { useCallback, useState } from "react";
import { ConsoleShell } from "@systutor/shell/ui/console-shell";
import { COTIZACION_TOKENS } from "../dsl/tokens";
import { createCotizacionCompletionProvider } from "../dsl/autocomplete";
import { executeCotizacion } from "../shared/api";
import { buildCommandFromText, prepareQuote, isCompleteQuote } from "../shared/application/prepareQuote";
import { createQuote } from "../shared/application/createQuote";
import { handleDraftCommand } from "../console/commands";
import { QuotePreview } from "../components/QuotePreview";
import { DraftExplorer } from "../components/DraftExplorer";
import { CotizacionForm } from "../ui";
import { useDraftList } from "../shared/hooks/useDraftList";
import { COTIZACION_HELP, isHelpCommand } from "../dsl/help";
import type { ConfirmAction } from "@systutor/shell/confirm";
import type { QuoteCommand } from "../shared/types/commands";

const MODE_STORAGE_KEY = "cotizacion-mode";

function getInitialMode(): "console" | "form" {
  try {
    const saved = sessionStorage.getItem(MODE_STORAGE_KEY);
    if (saved === "console" || saved === "form") return saved;
  } catch {
    // sessionStorage not available
  }
  return "form";
}

const completionProvider = createCotizacionCompletionProvider();

export function CotizacionPage() {
  const [mode, setMode] = useState<"console" | "form">(getInitialMode);
  const { invalidate } = useDraftList();

  const handleModeChange = useCallback((newMode: "console" | "form") => {
    setMode(newMode);
    try {
      sessionStorage.setItem(MODE_STORAGE_KEY, newMode);
    } catch {
      // sessionStorage not available
    }
  }, []);

  const handleExecute = useCallback(
    async (command: string): Promise<unknown> => {
      const trimmed = command.trim();
      if (!trimmed) return;

      if (isHelpCommand(trimmed)) return COTIZACION_HELP;

      if (trimmed.toLowerCase().startsWith("draft ")) {
        const args = trimmed.slice(6).trim().split(/\s+/);
        const result = await handleDraftCommand(args);
        if (typeof result === "object" && "action" in result && result.action === "open") {
          return result.draft;
        }
        return result;
      }

      if (trimmed.toLowerCase().startsWith("preview cotizar")) {
        return executeCotizacion(trimmed);
      }

      if (trimmed.toLowerCase().startsWith("cotizar")) {
        const cmd: QuoteCommand = buildCommandFromText(trimmed);
        if (!isCompleteQuote(cmd)) {
          return executeCotizacion(trimmed);
        }
        const prepared = await prepareQuote(cmd);
        const confirmAction: ConfirmAction = {
          _confirm: true,
          previewResult: prepared.preview,
          confirmMessage: `Crear cotización para ${cmd.cliente} (${cmd.items.length} item(s))`,
          execute: async () => {
            const result = await createQuote(cmd);
            invalidate();
            return result;
          },
          cancelMessage: "Cotización cancelada",
        };
        return confirmAction;
      }

      return executeCotizacion(trimmed);
    },
    [invalidate],
  );

  const handleFormDraftCreated = useCallback(() => {
    invalidate();
  }, [invalidate]);

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-white/10">
        <h2 className="text-sm font-semibold text-foreground">Cotización</h2>
        <div className="flex gap-1">
          <button
            onClick={() => handleModeChange("console")}
            className={`px-2 py-1 text-xs rounded ${
              mode === "console"
                ? "bg-primary/20 text-primary"
                : "text-muted-foreground/60 hover:text-foreground"
            }`}
          >
            ⌨ Consola
          </button>
          <button
            onClick={() => handleModeChange("form")}
            className={`px-2 py-1 text-xs rounded ${
              mode === "form"
                ? "bg-primary/20 text-primary"
                : "text-muted-foreground/60 hover:text-foreground"
            }`}
          >
            📋 Formulario
          </button>
        </div>
      </div>

      {/* Content */}
      {mode === "console" ? (
        <div className="flex-1 flex flex-col min-h-0">
          <div className="flex-1 min-h-0">
            <ConsoleShell
              completionProvider={completionProvider}
              tokenProvider={COTIZACION_TOKENS}
              onExecute={handleExecute}
              renderResult={(data) =>
                typeof data === "string" ? (
                  <pre className="whitespace-pre-wrap text-xs leading-relaxed">{data}</pre>
                ) : (
                  <QuotePreview draft={data as any} />
                )
              }
              placeholder='cotizar cliente "nombre" ...'
            />
          </div>
          <div className="border-t border-white/10 px-4 py-2">
            <DraftExplorer />
          </div>
        </div>
      ) : (
        <div className="flex-1 flex flex-col min-h-0">
          <div className="flex-1 min-h-0 overflow-y-auto">
            <CotizacionForm onDraftCreated={handleFormDraftCreated} />
          </div>
          <div className="border-t border-white/10 px-4 py-2">
            <DraftExplorer />
          </div>
        </div>
      )}
    </div>
  );
}
