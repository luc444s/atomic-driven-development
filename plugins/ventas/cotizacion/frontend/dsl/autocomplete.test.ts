import { describe, it, expect, vi } from "vitest";
import type { CompletionContext, CompletionItem } from "../../../../../apps/web/src/shared/ui/console-editor";
import { createCotizacionCompletionProvider } from "./autocomplete";

const requestPaths: string[] = [];

vi.mock("../../../../../apps/web/src/shared/api/client", () => ({
  apiRequest: vi.fn((path: string) => {
    requestPaths.push(path);
    return Promise.resolve([]);
  }),
}));

function ctx(text: string): CompletionContext {
  return { textBeforeCursor: text, fullText: text };
}

function unwrap(result: CompletionItem[] | { items: CompletionItem[] }): CompletionItem[] {
  return Array.isArray(result) ? result : result.items;
}

describe("cotizacion completion provider", () => {
  const provider = createCotizacionCompletionProvider();

  it("suggests top-level commands when empty", () => {
    const result = unwrap(provider.provideItems(ctx("")));
    expect(result.some((i) => i.label === "cotizar")).toBe(true);
    expect(result.some((i) => i.label === "cotizar --help")).toBe(true);
  });

  it("suggests cliente keyword after cotizar", () => {
    const result = unwrap(provider.provideItems(ctx("cotizar ")));
    expect(result.some((i) => i.label === "cliente")).toBe(true);
  });

  it("returns incomplete when customer search starts", () => {
    const result = provider.provideItems(ctx("cotizar cliente Bo"));
    expect(Array.isArray(result)).toBe(false);
    if (!Array.isArray(result)) {
      expect(result.items.length).toBe(0);
      expect(result.incomplete).toBe(true);
    }
  });

  it("fires customer search on partial >= 1 char", async () => {
    requestPaths.length = 0;
    provider.provideItems(ctx("cotizar cliente B"));
    await new Promise((r) => setTimeout(r, 250));
    expect(requestPaths.some((p) => p.includes("crm/customers/search"))).toBe(true);
  });

  it("strips quotes from customer search query", async () => {
    requestPaths.length = 0;
    provider.provideItems(ctx('cotizar cliente "Boh'));
    await new Promise((r) => setTimeout(r, 250));
    const customerRequest = requestPaths.find((p) => p.includes("crm/customers/search"));
    expect(customerRequest).toBeDefined();
    expect(customerRequest).not.toContain('"');
    expect(customerRequest).toContain("query=Boh");
  });

  it("moves to quantity suggestion after customer name", () => {
    const result = unwrap(provider.provideItems(ctx("cotizar cliente Bohdan ")));
    expect(result.some((i) => i.label === "Cantidad")).toBe(true);
  });

  it("returns incomplete when product search starts", () => {
    const result = provider.provideItems(ctx("cotizar cliente Bohdan 400 Bo"));
    expect(Array.isArray(result)).toBe(false);
    if (!Array.isArray(result)) {
      expect(result.items.length).toBe(0);
      expect(result.incomplete).toBe(true);
    }
  });

  it("suggests dates after product", () => {
    const result = unwrap(provider.provideItems(ctx("cotizar cliente Bohdan 400 Bombona1 ")));
    expect(result.some((i) => i.label === "hoy")).toBe(true);
  });

  it("suggests time after date", () => {
    const result = unwrap(provider.provideItems(ctx("cotizar cliente Bohdan 400 Bombona1 hoy ")));
    expect(result.some((i) => i.label === "14:00")).toBe(true);
  });

  it("suggests vehicle/condition after time", () => {
    const result = unwrap(provider.provideItems(ctx("cotizar cliente Bohdan 400 Bombona1 hoy 14:00 ")));
    expect(result.some((i) => i.label === "vehiculo")).toBe(true);
    expect(result.some((i) => i.label === "condicion")).toBe(true);
  });

  it("does not leak date/condition keywords into product search", async () => {
    requestPaths.length = 0;
    provider.provideItems(ctx("cotizar cliente Bohdan 400 bombona1"));
    await new Promise((r) => setTimeout(r, 250));
    const productRequest = requestPaths.find((p) => p.includes("productos/products/search"));
    expect(productRequest).toBeDefined();
    expect(productRequest).toContain("q=bombona1");
    expect(productRequest).not.toContain("miercoles");
    expect(productRequest).not.toContain("condicion");
  });
});
