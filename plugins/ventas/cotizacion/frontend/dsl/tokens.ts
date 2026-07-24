import type { TokenProvider } from "../../../../../apps/web/src/shared/ui/console-editor";

const KEYWORDS = [
  "cotizar", "preview", "cliente", "vehiculo", "condicion",
  "hoy", "mañana", "tarde", "noche",
  "lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo",
  "history", "clear", "cancelar",
];

export const COTIZACION_TOKENS: TokenProvider = {
  language: "cotizacion",
  keywords: KEYWORDS,
  ignoreCase: true,
  tokens: [
    { pattern: /\b(\d{4}-\d{2}-\d{2})\b/, token: "value.date" },
    { pattern: /\b(\d{1,2}[:h]\d{2})\b/i, token: "value.time" },
    { pattern: /\b\d+\s*(hrs?|h)?\b/, token: "value.quantity" },
    { pattern: /"[^"]*"/, token: "string" },
    { pattern: /[A-Z]{2,}\d+[A-Z\d]*/, token: "entity.vehicle" },
    { pattern: /#.*$/, token: "comment" },
    { pattern: /[,:;]/, token: "operator" },
  ],
};
