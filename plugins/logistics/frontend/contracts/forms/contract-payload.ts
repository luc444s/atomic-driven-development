import { toNullable, toNumberOrNull } from "../../cylinders/utils/formatters";
import type {
  ContractFormState,
  TerminateFormState,
} from "./contract-form-state";
import type {
  CreateContractPayload,
  TerminateContractPayload,
  UpdateContractPayload,
} from "../../api/contracts";

export function buildCreatePayload(form: ContractFormState): CreateContractPayload {
  return {
    contract_type: form.contract_type,
    customer_id: form.customer_id,
    warehouse_id: form.warehouse_id,
    start_date: form.start_date,
    end_date: toNullable(form.end_date),
    renewal_type: toNullable(form.renewal_type),
    cylinder_type_id: toNullable(form.cylinder_type_id),
    cylinder_condition: toNullable(form.cylinder_condition),
    quantity: Number(form.quantity || "0"),
    unit_price: Number(form.unit_price || "0"),
    contract_file_path: toNullable(form.contract_file_path),
    notes: toNullable(form.notes),
    observations: toNullable(form.observations),
  };
}

export function buildUpdatePayload(form: ContractFormState): UpdateContractPayload {
  return buildCreatePayload(form);
}

export function buildTerminatePayload(form: TerminateFormState): TerminateContractPayload {
  return { reason: form.reason };
}
