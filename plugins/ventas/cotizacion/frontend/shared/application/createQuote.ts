import type { QuoteCommand } from "../types/commands";
import { executeCotizacion } from "../api";
import type { QuoteDraftDTO } from "../types";

export async function createQuote(command: QuoteCommand): Promise<QuoteDraftDTO> {
  const parts = [
    command.dryRun ? "preview" : "",
    "cotizar",
    "cliente",
    command.cliente ? `"${command.cliente}"` : "",
    ...command.items.flatMap((i) => [`${i.cantidad}`, `"${i.producto}"`]),
    command.fecha ?? "",
    command.hora ?? "",
    command.vehiculo ? `vehiculo "${command.vehiculo}"` : "",
    command.condiciones ? `condicion ${command.condiciones}` : "",
  ];
  const text = parts.filter(Boolean).join(" ");
  return executeCotizacion(text);
}
