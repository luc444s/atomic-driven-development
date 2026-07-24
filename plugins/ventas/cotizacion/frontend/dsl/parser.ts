export interface ParsedCommand {
  action: "cotizar" | "preview";
  dryRun: boolean;
  cliente: {
    raw: string;
    resolvedId?: string;
  } | null;
  items: Array<{
    raw: string;
    cantidad: number;
    producto: string;
    resolvedId?: string;
  }>;
  fecha: {
    raw: string;
    iso?: string;
  } | null;
  hora: {
    raw: string;
    iso?: string;
  } | null;
  vehiculo: {
    raw: string;
    resolvedId?: string;
  } | null;
  condiciones: string | null;
}

const DATE_BREAK_TOKENS = new Set([
  "hoy", "mañana", "manana", "tarde", "noche",
  "lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo",
  "vehiculo", "condicion",
]);

function tokenize(input: string): string[] {
  const tokens: string[] = [];
  let current = "";
  let inQuotes = false;

  for (let i = 0; i < input.length; i++) {
    const ch = input[i];
    if (ch === '"') {
      if (inQuotes) {
        current += ch;
        tokens.push(current);
        current = "";
        inQuotes = false;
      } else {
        if (current.trim()) {
          tokens.push(current.trim());
        }
        current = '"';
        inQuotes = true;
      }
      continue;
    }
    if (ch === " " && !inQuotes) {
      if (current.trim()) {
        tokens.push(current.trim());
      }
      current = "";
      continue;
    }
    current += ch;
  }
  if (current.trim()) {
    tokens.push(current.trim());
  }
  return tokens;
}

function unquote(token: string): string | null {
  if (token.startsWith('"') && token.endsWith('"') && token.length >= 2) {
    return token.slice(1, -1);
  }
  return null;
}

function consumeQuotedOrWords(tokens: string[]): string | null {
  if (tokens.length === 0) return null;
  const first = tokens[0];
  const quoted = unquote(first);
  if (quoted !== null) {
    tokens.shift();
    return quoted;
  }

  const parts: string[] = [];
  while (tokens.length > 0) {
    const t = tokens[0];
    const lower = t.toLowerCase();
    if (DATE_BREAK_TOKENS.has(lower)) break;
    if (/^\d+$/.test(t) && parts.length > 0) break;
    if (/^\d{4}-\d{2}-\d{2}$/.test(t)) break;
    if (/^\d{1,2}[:h]/i.test(t)) break;
    if (unquote(t) !== null) break;
    parts.push(tokens.shift()!);
  }
  return parts.length > 0 ? parts.join(" ") : null;
}

export function parseCommand(command: string): ParsedCommand {
  const trimmed = command.trim();
  const actionMatch = trimmed.match(/^(cotizar|preview)/i);
  const action = (actionMatch?.[1]?.toLowerCase() ?? "cotizar") as "cotizar" | "preview";
  let rest = actionMatch ? trimmed.slice(actionMatch[0].length).trim() : trimmed;

  const dryRun = action === "preview";
  if (dryRun) {
    const cotMatch = rest.match(/^cotizar\s+/i);
    if (cotMatch) rest = rest.slice(cotMatch[0].length).trim();
  }

  let clienteRaw: string | null = null;
  let vehiculoRaw: string | null = null;
  let condiciones: string | null = null;
  const items: ParsedCommand["items"] = [];
  let fechaRaw: string | null = null;
  let horaRaw: string | null = null;

  const condParts = rest.split(/\bcondicion\b/i);
  if (condParts.length > 1) {
    rest = condParts[0].trim();
    condiciones = condParts[1].trim();
  }

  const vehParts = rest.split(/\bvehiculo\b/i);
  if (vehParts.length > 1) {
    rest = vehParts[0].trim();
    const vehTokens = tokenize(vehParts[1].trim());
    vehiculoRaw = vehTokens[0] ? unquote(vehTokens[0]) ?? vehTokens[0] : null;
  }

  const tokens = tokenize(rest);

  if (tokens[0]?.toLowerCase() === "cliente") {
    tokens.shift();
    clienteRaw = consumeQuotedOrWords(tokens);
  }

  while (tokens.length > 0) {
    const t = tokens[0];
    const lower = t.toLowerCase();

    if (/^\d+$/.test(t)) {
      const cantidad = parseInt(t, 10);
      tokens.shift();
      const producto = consumeQuotedOrWords(tokens);
      if (producto) {
        items.push({
          raw: `${cantidad} ${producto}`,
          cantidad,
          producto,
        });
      }
      continue;
    }

    const dateTokens = new Set(["hoy", "mañana", "manana", "lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]);
    if (dateTokens.has(lower) || /^\d{4}-\d{2}-\d{2}$/.test(t)) {
      fechaRaw = tokens.shift()!;
      if (tokens.length > 0) {
        const nt = tokens[0];
        const nl = nt.toLowerCase();
        if (/^\d{1,2}[:h]/i.test(nt) || nl === "tarde" || nl === "noche" || nl === "mañana" || nl === "manana") {
          horaRaw = tokens.shift()!;
        }
      }
      break;
    }

    if (lower === "tarde" || lower === "noche" || lower === "mañana" || lower === "manana" || /^\d{1,2}[:h]/i.test(t)) {
      if (!fechaRaw) fechaRaw = "hoy";
      horaRaw = tokens.shift()!;
      continue;
    }

    tokens.shift();
  }

  return {
    action,
    dryRun,
    cliente: clienteRaw ? { raw: clienteRaw } : null,
    items,
    fecha: fechaRaw ? { raw: fechaRaw } : null,
    hora: horaRaw ? { raw: horaRaw } : null,
    vehiculo: vehiculoRaw ? { raw: vehiculoRaw } : null,
    condiciones,
  };
}

export function formatDraftId(id: string): string {
  return `#CTZ-${id.slice(0, 4).toUpperCase()}`;
}
