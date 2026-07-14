export type ContractFormState = {
  contract_type: string;
  customer_id: string;
  customer_name: string;
  warehouse_id: string;
  start_date: string;
  end_date: string;
  renewal_type: string;
  cylinder_type_id: string;
  cylinder_condition: string;
  quantity: string;
  unit_price: string;
  contract_file_path: string;
  notes: string;
  observations: string;
};

export type TerminateFormState = {
  reason: string;
};

export const EMPTY_CONTRACT_FORM: ContractFormState = {
  contract_type: "ANNUAL",
  customer_id: "",
  customer_name: "",
  warehouse_id: "",
  start_date: "",
  end_date: "",
  renewal_type: "",
  cylinder_type_id: "",
  cylinder_condition: "",
  quantity: "1",
  unit_price: "",
  contract_file_path: "",
  notes: "",
  observations: "",
};

export const EMPTY_TERMINATE_FORM: TerminateFormState = {
  reason: "",
};
