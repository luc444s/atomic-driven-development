import { describe, expect, it } from "vitest";

import { DEFAULT_MAP_CENTER } from "../../../../plugins/logistics/frontend/components/route-builder/map-defaults";

describe("DEFAULT_MAP_CENTER", () => {
  it("apunta a Trujillo, Perú", () => {
    expect(DEFAULT_MAP_CENTER).toEqual({ lat: -8.115994, lng: -79.029858 });
  });
});