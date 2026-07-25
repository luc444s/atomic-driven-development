import type { QuoteCommand } from "../types/commands";
import { executeCotizacion } from "../api";
import type { QuoteDraftDTO } from "../types";
import { parseCommand } from "../../dsl/parser";

export interface PreparedQuote {
  command: QuoteCommand;
  preview: QuoteDraftDTO;
}

export function buildCommandFromText(text: string): QuoteCommand {
  const parsed = parseCommand(text);
  return {
    action: parsed.dryRun ? "preview" : "cotizar",
    dryRun: parsed.dryRun,
    cliente: parsed.cliente?.raw ?? null,
    items: parsed.items.map((i) => ({ cantidad: i.cantidad, producto: i.producto })),
    fecha: parsed.fecha?.raw ?? null,
    hora: parsed.hora?.raw ?? null,
    vehiculo: parsed.vehiculo?.raw ?? null,
    condiciones: parsed.condiciones,
  };
}

export async function prepareQuote(command: QuoteCommand): Promise<PreparedQuote> {
  const previewCmd = `preview cotizar cliente "${command.cliente}" ${command.items.map((i) => `${i.cantidad} "${i.producto}"`).join(" ")} ${command.fecha ?? ""} ${command.hora ?? ""}`;
  const preview = await executeCotizacion(previewCmd);
  return { command, preview };
}

export function isCompleteQuote(cmd: QuoteCommand): boolean {
  return !!cmd.cliente && cmd.items.length > 0 && !!cmd.fecha;
}
