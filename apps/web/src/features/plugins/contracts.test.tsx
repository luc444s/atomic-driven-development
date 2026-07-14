import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";

import {
  buildCreatePayload,
  buildTerminatePayload,
} from "../../../../../plugins/logistics/frontend/contracts/forms/contract-payload";
import {
  EMPTY_CONTRACT_FORM,
  EMPTY_TERMINATE_FORM,
} from "../../../../../plugins/logistics/frontend/contracts/forms/contract-form-state";
import { ContractStatusBadge } from "../../../../../plugins/logistics/frontend/contracts/components/contract-status-badge";

describe("contracts form builders", () => {
  it("builds create payload from valid form", () => {
    const form = {
      ...EMPTY_CONTRACT_FORM,
      contract_type: "ANNUAL",
      customer_id: "cust-1",
      warehouse_id: "wh-1",
      start_date: "2026-07-01",
      end_date: "2027-07-01",
      renewal_type: "AUTO",
      quantity: "5",
      unit_price: "150.50",
      contract_file_path: "D:/CONTRATOS/ct.pdf",
      notes: "Contrato de prueba",
      observations: "Observacion de prueba",
    };

    const payload = buildCreatePayload(form);

    expect(payload.contract_type).toBe("ANNUAL");
    expect(payload.customer_id).toBe("cust-1");
    expect(payload.warehouse_id).toBe("wh-1");
    expect(payload.start_date).toBe("2026-07-01");
    expect(payload.end_date).toBe("2027-07-01");
    expect(payload.renewal_type).toBe("AUTO");
    expect(payload.quantity).toBe(5);
    expect(payload.unit_price).toBe(150.50);
    expect(payload.contract_file_path).toBe("D:/CONTRATOS/ct.pdf");
    expect(payload.notes).toBe("Contrato de prueba");
    expect(payload.observations).toBe("Observacion de prueba");
  });

  it("converts empty optional fields to null", () => {
    const payload = buildCreatePayload(EMPTY_CONTRACT_FORM);

    expect(payload.end_date).toBeNull();
    expect(payload.renewal_type).toBeNull();
    expect(payload.cylinder_type_id).toBeNull();
    expect(payload.cylinder_condition).toBeNull();
    expect(payload.contract_file_path).toBeNull();
    expect(payload.notes).toBeNull();
    expect(payload.observations).toBeNull();
    expect(payload.quantity).toBe(1);
  });

  it("builds terminate payload with reason", () => {
    const form = { reason: "Devolucion completa de cilindros" };

    const payload = buildTerminatePayload(form);

    expect(payload.reason).toBe("Devolucion completa de cilindros");
  });
});

describe("contracts UI components", () => {
  it("renders status badge for each state", () => {
    expect(renderToStaticMarkup(<ContractStatusBadge status="DRAFT" />)).toContain("Borrador");
    expect(renderToStaticMarkup(<ContractStatusBadge status="PENDING_SIGNATURE" />)).toContain("Por firmar");
    expect(renderToStaticMarkup(<ContractStatusBadge status="ACTIVE" />)).toContain("Vigente");
    expect(renderToStaticMarkup(<ContractStatusBadge status="EXPIRED" />)).toContain("Vencido");
    expect(renderToStaticMarkup(<ContractStatusBadge status="CANCELLED" />)).toContain("Anulado");
  });

  it("renders unknown status as raw string", () => {
    const markup = renderToStaticMarkup(<ContractStatusBadge status="UNKNOWN" />);
    expect(markup).toContain("UNKNOWN");
  });
});
