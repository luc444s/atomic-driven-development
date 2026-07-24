import { describe, it, expect } from "vitest";
import { parseCommand } from "./parser";

describe("parser", () => {
  it("parses a full cotizar command", () => {
    const parsed = parseCommand("cotizar cliente Bohdan 400 Bombona1 mañana 14h vehiculo IHUI-329I4G");
    expect(parsed.action).toBe("cotizar");
    expect(parsed.dryRun).toBe(false);
    expect(parsed.cliente?.raw).toBe("Bohdan");
    expect(parsed.items).toHaveLength(1);
    expect(parsed.items[0].cantidad).toBe(400);
    expect(parsed.items[0].producto).toBe("Bombona1");
    expect(parsed.fecha?.raw).toBe("mañana");
    expect(parsed.hora?.raw).toBe("14h");
    expect(parsed.vehiculo?.raw).toBe("IHUI-329I4G");
  });

  it("parses preview cotizar", () => {
    const parsed = parseCommand("preview cotizar cliente Juan 200 ProductoA hoy");
    expect(parsed.action).toBe("preview");
    expect(parsed.dryRun).toBe(true);
    expect(parsed.cliente?.raw).toBe("Juan");
    expect(parsed.items[0].cantidad).toBe(200);
  });

  it("handles customer names with spaces", () => {
    const parsed = parseCommand("cotizar cliente Gas del Norte 500 Tanque hoy");
    expect(parsed.cliente?.raw).toBe("Gas del Norte");
    expect(parsed.items[0].cantidad).toBe(500);
  });

  it("handles quoted customer names", () => {
    const parsed = parseCommand('cotizar cliente "Gas del Norte" 400 "Bombona 10kg" hoy');
    expect(parsed.cliente?.raw).toBe("Gas del Norte");
    expect(parsed.items[0].cantidad).toBe(400);
    expect(parsed.items[0].producto).toBe("Bombona 10kg");
  });

  it("handles quoted vehicle plates", () => {
    const parsed = parseCommand('cotizar cliente "Bohdan" 400 Bombona1 hoy vehiculo "IHUI-329I4G"');
    expect(parsed.vehiculo?.raw).toBe("IHUI-329I4G");
  });

  it("ignores keywords inside quoted strings", () => {
    const parsed = parseCommand('cotizar cliente "Grupo hoy" 400 "Producto tarde" hoy');
    expect(parsed.cliente?.raw).toBe("Grupo hoy");
    expect(parsed.items[0].producto).toBe("Producto tarde");
  });

  it("parses commands case-insensitively", () => {
    const parsed = parseCommand('COTIZAR CLIENTE "BOHDAN" 400 "BOMBONA1" MAÑANA 14H');
    expect(parsed.action).toBe("cotizar");
    expect(parsed.cliente?.raw).toBe("BOHDAN");
    expect(parsed.items[0].cantidad).toBe(400);
    expect(parsed.items[0].producto).toBe("BOMBONA1");
    expect(parsed.fecha?.raw).toBe("MAÑANA");
    expect(parsed.hora?.raw).toBe("14H");
  });
});
