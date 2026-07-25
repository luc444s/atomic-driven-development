import type { CompletionProvider, CompletionItem, CompletionContext, SuggestionResult } from "../../../../../apps/web/src/shared/ui/console-editor";
import { apiRequest } from "../../../../../apps/web/src/shared/api/client";

const TOP_LEVEL_COMMANDS: CompletionItem[] = [
  { label: "cotizar", kind: "keyword", detail: "Crear nueva cotización", insertText: "cotizar cliente " },
  { label: "cotizar --help", kind: "keyword", detail: "Ver ayuda del comando", insertText: "cotizar --help" },
  { label: "preview cotizar", kind: "keyword", detail: "Previsualizar sin guardar", insertText: "preview cotizar cliente " },
  { label: "neofetch", kind: "keyword", detail: "Mostrar información del sistema" },
  { label: "fastfetch", kind: "keyword", detail: "Mostrar información del sistema" },
  { label: "sysinfo", kind: "keyword", detail: "Mostrar información del sistema" },
  { label: "draft list", kind: "keyword", detail: "Listar cotizaciones recientes" },
  { label: "draft open", kind: "keyword", detail: "Abrir detalle de cotización (draft open <id>)" },
  { label: "draft refresh", kind: "keyword", detail: "Recargar lista de cotizaciones" },
  { label: "sysinfo", kind: "keyword", detail: "Mostrar información del sistema" },
  { label: "history", kind: "keyword", detail: "Ver historial de comandos" },
  { label: "clear", kind: "keyword", detail: "Limpiar terminal" },
];

const DATE_SUGGESTIONS: CompletionItem[] = [
  { label: "hoy", kind: "value", detail: "Fecha actual" },
  { label: "mañana", kind: "value", detail: "Mañana" },
  { label: "manana", kind: "value", detail: "Mañana (sin acento)" },
  { label: "pasado mañana", kind: "value", detail: "Pasado mañana" },
];

const WEEKDAY_SUGGESTIONS: CompletionItem[] = [
  { label: "lunes", kind: "value" }, { label: "martes", kind: "value" },
  { label: "miercoles", kind: "value" }, { label: "jueves", kind: "value" },
  { label: "viernes", kind: "value" }, { label: "sabado", kind: "value" },
  { label: "domingo", kind: "value" },
];

const TIME_SUGGESTIONS: CompletionItem[] = [
  { label: "mañana (06:00)", kind: "value", insertText: "mañana " },
  { label: "tarde (14:00)", kind: "value", insertText: "tarde " },
  { label: "noche (20:00)", kind: "value", insertText: "noche " },
  { label: "08:00", kind: "value" }, { label: "10:00", kind: "value" },
  { label: "12:00", kind: "value" }, { label: "14:00", kind: "value" },
  { label: "16:00", kind: "value" }, { label: "18:00", kind: "value" },
];

const FECHA_KW = new Set([
  "hoy", "mañana", "manana", "lunes", "martes", "miercoles", "jueves",
  "viernes", "sabado", "domingo", "tarde", "noche",
]);

function normalizeQuery(query: string): string {
  return query.replace(/^"+|"+$/g, "").trim();
}

class EntitySearch {
  private cache = new Map<string, CompletionItem[]>();
  private debounceTimer: ReturnType<typeof setTimeout> | null = null;
  private controller: AbortController | null = null;
  private lastQuery = "";

  constructor(
    private fetcher: (query: string, signal: AbortSignal) => Promise<CompletionItem[]>,
    private debounceMs = 0,
  ) {}

  getItems(query: string): CompletionItem[] | null {
    const normalized = normalizeQuery(query);
    const exact = this.cache.get(normalized);
    if (exact) return exact;

    // Filtramos desde cualquier cache previo, incluso si tenía 5 resultados.
    for (const [cachedQuery, items] of this.cache.entries()) {
      if (normalized.toLowerCase().startsWith(cachedQuery.toLowerCase()) && items.length > 0) {
        const filtered = items.filter((item) =>
          item.label.toLowerCase().includes(normalized.toLowerCase()),
        );
        if (filtered.length > 0) return filtered;
      }
    }

    return null;
  }

  search(query: string) {
    const normalized = normalizeQuery(query);
    if (normalized === this.lastQuery || normalized.length < 1) return;
    this.lastQuery = normalized;

    if (this.debounceTimer) {
      clearTimeout(this.debounceTimer);
    }

    if (this.controller) {
      this.controller.abort();
      this.controller = null;
    }

    this.debounceTimer = setTimeout(() => {
      this.execute(normalized);
    }, this.debounceMs);
  }

  private async execute(query: string) {
    this.controller = new AbortController();
    try {
      const items = await this.fetcher(query, this.controller.signal);
      this.cache.set(query, items);
    } catch (err) {
      if ((err as Error).name !== "AbortError") {
        this.cache.set(query, []);
      }
    } finally {
      this.controller = null;
    }
  }
}

const customerSearch = new EntitySearch(async (query, signal) => {
  const data = await apiRequest<any[]>(
    `/api/v1/plugins/crm/customers/search?query=${encodeURIComponent(query)}&limit=5`,
    { signal },
  );
  return (data ?? []).map((c: any) => ({
        label: c.display_name,
        kind: "entity" as const,
        detail: `${c.document_type_code}: ${c.document_number}`,
        insertText: `"${c.display_name}" `,
  }));
});

const productSearch = new EntitySearch(async (query, signal) => {
  const data = await apiRequest<any[]>(
    `/api/v1/plugins/productos/products/search?q=${encodeURIComponent(query)}&limit=5`,
    { signal },
  );
  return (data ?? []).map((p: any) => ({
        label: p.name,
        kind: "entity" as const,
        detail: [p.sku, p.brand_name].filter(Boolean).join(" · "),
        insertText: `"${p.name}" `,
  }));
});

const vehicleSearch = new EntitySearch(async (query, signal) => {
  const data = await apiRequest<any[]>("/api/v1/plugins/logistics/vehicles", { signal });
  return (data ?? [])
    .filter((v: any) => v.plate.toLowerCase().includes(query.toLowerCase()))
    .slice(0, 5)
    .map((v: any) => ({
          label: v.plate,
          kind: "entity" as const,
          detail: "Vehículo",
          insertText: `"${v.plate}" `,
    }));
});

type SuggestionContext =
  | { type: "command"; partial: string }
  | { type: "cliente_keyword" }
  | { type: "cliente"; partial: string }
  | { type: "cantidad" }
  | { type: "producto"; partial: string }
  | { type: "fecha"; partial: string }
  | { type: "hora"; partial: string }
  | { type: "vehiculo"; partial: string }
  | { type: "condicion"; partial: string }
  | { type: "ready" };

function getContext(textBeforeCursor: string): SuggestionContext {
  const trimmed = textBeforeCursor.trim();
  const tokens = trimmed.split(/\s+/);
  const first = tokens[0]?.toLowerCase() ?? "";

  if (first !== "cotizar" && !(first === "preview" && tokens[1]?.toLowerCase() === "cotizar")) {
    return { type: "command", partial: trimmed.toLowerCase() };
  }

  if (!tokens.some((t) => t.toLowerCase() === "cliente")) {
    return { type: "cliente_keyword" };
  }

  const isNewToken = textBeforeCursor.endsWith(" ");
  const clienteIndex = findLastIndex(tokens, (t) => t.toLowerCase() === "cliente");
  const afterCliente = tokens.slice(clienteIndex + 1);

  if (afterCliente.length === 0) {
    return { type: "cliente", partial: "" };
  }

  const hasQty = afterCliente.some((t) => /^\d+$/.test(t));
  const hasFecha = afterCliente.some(
    (t) => FECHA_KW.has(t.toLowerCase()) || /^\d{4}-\d{2}-\d{2}$/.test(t),
  );
  const hasHora = afterCliente.some(
    (t) => /^\d{1,2}[:h]/i.test(t) || ["tarde", "noche"].includes(t.toLowerCase()),
  );

  const last = afterCliente[afterCliente.length - 1];
  const lastLower = last.toLowerCase();

  if (!isNewToken) {
    if (lastLower === "vehiculo") return { type: "vehiculo", partial: "" };
    if (lastLower === "condicion") return { type: "condicion", partial: "" };
    if (FECHA_KW.has(lastLower) || /^\d{4}-\d{2}-\d{2}$/.test(last)) {
      return { type: "hora", partial: "" };
    }
    if (/^\d{1,2}[:h]/i.test(last) || ["tarde", "noche"].includes(lastLower)) {
      return { type: "ready" };
    }
    if (/^\d+$/.test(last)) {
      return { type: "cantidad" };
    }
    if (hasQty) {
      const lastQtyIndex = findLastIndex(afterCliente, (t) => /^\d+$/.test(t));
      const afterQty = extractProductTokens(afterCliente, lastQtyIndex);
      return { type: "producto", partial: afterQty.join(" ").trim() };
    }
    const partial = textBeforeCursor.replace(/^.*\bcliente\s+/i, "").trim();
    return { type: "cliente", partial };
  }

  if (hasHora) return { type: "ready" };
  if (hasFecha) return { type: "hora", partial: "" };
  if (hasQty) {
    const lastQtyIndex = findLastIndex(afterCliente, (t) => /^\d+$/.test(t));
    const productoPartial = extractProductTokens(afterCliente, lastQtyIndex).join(" ").trim();
    if (productoPartial) {
      return { type: "fecha", partial: "" };
    }
    return { type: "producto", partial: "" };
  }

  return { type: "cantidad" };
}

const FIELD_BREAK_TOKENS = new Set([
  "hoy", "mañana", "manana", "lunes", "martes", "miercoles", "jueves",
  "viernes", "sabado", "domingo", "tarde", "noche", "vehiculo", "condicion",
]);

function extractProductTokens(tokens: string[], lastQtyIndex: number): string[] {
  const productTokens: string[] = [];
  for (let i = lastQtyIndex + 1; i < tokens.length; i++) {
    const t = tokens[i];
    const lower = t.toLowerCase();
    if (FIELD_BREAK_TOKENS.has(lower)) break;
    if (/^\d{4}-\d{2}-\d{2}$/.test(t)) break;
    if (/^\d{1,2}[:h]/i.test(t)) break;
    if (/^\d+$/.test(t)) break;
    productTokens.push(t);
  }
  return productTokens;
}

function findLastIndex<T>(arr: T[], predicate: (item: T) => boolean): number {
  for (let i = arr.length - 1; i >= 0; i--) {
    if (predicate(arr[i])) return i;
  }
  return -1;
}

function filterCommands(partial: string): CompletionItem[] {
  if (!partial) return TOP_LEVEL_COMMANDS;
  return TOP_LEVEL_COMMANDS.filter((c) => c.label.toLowerCase().includes(partial));
}

function filterStatic(items: CompletionItem[], partial: string): CompletionItem[] {
  if (!partial) return items;
  const lower = partial.toLowerCase();
  return items.filter((s) => s.label.toLowerCase().includes(lower));
}

function resolveSuggestions(ctx: CompletionContext): CompletionItem[] | SuggestionResult {
  const { textBeforeCursor } = ctx;
  const context = getContext(textBeforeCursor);

  switch (context.type) {
    case "command":
      return filterCommands(context.partial);

    case "cliente_keyword":
      return [{ label: "cliente", kind: "keyword", detail: "Nombre del cliente", insertText: "cliente " }];

    case "cliente": {
      const partial = context.partial;
      if (partial && partial.length >= 1) {
        const cached = customerSearch.getItems(partial);
        if (cached) return cached;
        customerSearch.search(partial);
        return { items: [], incomplete: true };
      }
      return [];
    }

    case "cantidad":
      return [{ label: "Cantidad", kind: "value", detail: "Ej: 400" }];

    case "producto": {
      const partial = context.partial;
      if (partial && partial.length >= 1) {
        const cached = productSearch.getItems(partial);
        if (cached) return cached;
        productSearch.search(partial);
        return { items: [], incomplete: true };
      }
      return [];
    }

    case "fecha": {
      const partial = context.partial;
      return filterStatic([...DATE_SUGGESTIONS, ...WEEKDAY_SUGGESTIONS], partial);
    }

    case "hora": {
      const partial = context.partial;
      return filterStatic(TIME_SUGGESTIONS, partial);
    }

    case "vehiculo": {
      const partial = context.partial;
      if (!partial) {
        return [
          { label: "vehiculo", kind: "keyword", detail: "Asignar vehículo (opcional)", insertText: "vehiculo " },
          { label: "condicion", kind: "keyword", detail: "Condiciones de entrega", insertText: "condicion " },
        ];
      }
      if (partial.length >= 1) {
        const cached = vehicleSearch.getItems(partial);
        if (cached) return cached;
        vehicleSearch.search(partial);
        return { items: [], incomplete: true };
      }
      return [];
    }

    case "condicion":
      return [{ label: "condicion", kind: "keyword", detail: "Condiciones de entrega", insertText: "condicion " }];

    case "ready":
      return [
        { label: "vehiculo", kind: "keyword", detail: "Asignar vehículo (opcional)", insertText: "vehiculo " },
        { label: "condicion", kind: "keyword", detail: "Condiciones de entrega", insertText: "condicion " },
      ];

    default:
      return [];
  }
}

export function createCotizacionCompletionProvider(): CompletionProvider {
  customerSearch.search("a");
  productSearch.search("a");
  return {
    language: "cotizacion",
    provideItems(ctx: CompletionContext): CompletionItem[] | SuggestionResult {
      return resolveSuggestions(ctx);
    },
  };
}
