import { describe, expect, it } from "vitest";

import {
  buildSessionWaybillHistoryLabel,
  formatSessionWaybillDocumentKind,
} from "../../../../../plugins/logistics/frontend/components/vehicle-sessions/session-waybill-view";

describe("official waybill helpers", () => {
  it("formats document kinds with operational labels", () => {
    expect(formatSessionWaybillDocumentKind("PREVIEW")).toBe("Preview viva");
    expect(formatSessionWaybillDocumentKind("OFFICIAL")).toBe("Documento oficial");
  });

  it("builds history labels from kind and version", () => {
    expect(buildSessionWaybillHistoryLabel({ document_kind: "PREVIEW", version: 3 })).toBe(
      "Preview viva v3"
    );
    expect(buildSessionWaybillHistoryLabel({ document_kind: "OFFICIAL", version: 4 })).toBe(
      "Documento oficial v4"
    );
  });
});
