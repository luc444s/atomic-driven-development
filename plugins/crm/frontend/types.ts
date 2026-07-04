export type DocumentType = {
  code: string;
  name: string;
  country_code: string;
  description: string | null;
  is_person: boolean;
  is_company: boolean;
  validation_pattern: string | null;
  is_active: boolean;
};

export type PaymentTerm = {
  code: string;
  name: string;
  description: string | null;
  days: number;
  operation_type: string;
  payment_mode: string;
  is_active: boolean;
};

export type GeographyItem = {
  id: string;
  parent_id: string | null;
  code: string | null;
  name: string;
  level: number;
  country_code: string;
  ubigeo_code: string | null;
  is_active: boolean;
};

export type CustomerContact = {
  id: string;
  full_name: string | null;
  label: string | null;
  role: string | null;
  phone: string | null;
  email: string | null;
  address_id: string | null;
  contact_purpose: string;
  contact_type: string;
  notes: string | null;
  is_primary: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type CommercialUserOption = {
  id: string;
  full_name: string;
  email: string;
  is_active: boolean;
};

export type CustomerCommercialAssignment = {
  id: string;
  customer_id: string;
  address_id: string | null;
  user_id: string;
  user_display_name: string;
  user_email: string;
  assignment_role: string;
  notes: string | null;
  is_primary: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type CustomerAddress = {
  id: string;
  customer_id: string;
  address_type: string;
  label: string | null;
  geography_id: string | null;
  line1: string;
  line2: string | null;
  city: string | null;
  state: string | null;
  district: string | null;
  postal_code: string | null;
  country_code: string;
  latitude: number | null;
  longitude: number | null;
  place_id: string | null;
  formatted_address: string | null;
  street_name: string | null;
  street_number: string | null;
  geocode_source: string | null;
  precision_meters: number | null;
  gps_link: string | null;
  contact_name: string | null;
  contact_phone: string | null;
  contact_email: string | null;
  is_operational_site: boolean;
  notes: string | null;
  is_active: boolean;
  captured_by: string | null;
  captured_at: string | null;
  ubigeo_code: string | null;
  created_at: string;
  updated_at: string;
};

export type CustomerBrief = {
  id: string;
  legal_name: string;
  commercial_name: string | null;
  display_name: string;
  document_type_code: string;
  document_number: string;
  external_code: string | null;
  email: string | null;
  phone: string | null;
  country_code: string;
  fiscal_address_summary: string | null;
  locality_summary: string | null;
};

export type CustomerListItem = {
  id: string;
  legal_name: string;
  commercial_name: string | null;
  external_code: string | null;
  document_type_code: string;
  document_number: string;
  country_code: string;
  email: string | null;
  phone: string | null;
  mobile: string | null;
  payment_term_code: string | null;
  billing_type: string | null;
  is_exempt: boolean;
  accounting_code: string | null;
  is_intracommunity: boolean;
  fiscal_operation_key: string | null;
  tax_regime_code: string | null;
  equivalence_surcharge_applicable: boolean;
  cash_criterion_applicable: boolean;
  is_active: boolean;
  fiscal_address_id: string | null;
  created_at: string;
  updated_at: string;
};

export type Customer = CustomerListItem & {
  economic_activity_code: string | null;
  economic_activity_description: string | null;
  activity_validated: boolean;
  activity_validation_source: string | null;
  activity_validation_date: string | null;
  first_name: string | null;
  last_name: string | null;
  birth_date: string | null;
  gender: string | null;
  notes: string | null;
  addresses: CustomerAddress[];
  contacts: CustomerContact[];
};

export type CustomerPage = {
  items: CustomerListItem[];
  total: number;
  limit: number;
  offset: number;
};

export type CustomerPayload = {
  external_code: string | null;
  legal_name: string;
  commercial_name: string | null;
  document_type_code: string;
  document_number: string;
  country_code: string;
  email: string | null;
  phone: string | null;
  mobile: string | null;
  economic_activity_code: string | null;
  economic_activity_description: string | null;
  payment_term_code: string | null;
  billing_type: string | null;
  is_exempt: boolean;
  accounting_code: string | null;
  is_intracommunity: boolean;
  fiscal_operation_key: string | null;
  tax_regime_code: string | null;
  equivalence_surcharge_applicable: boolean;
  cash_criterion_applicable: boolean;
  first_name: string | null;
  last_name: string | null;
  birth_date: string | null;
  gender: string | null;
  notes: string | null;
};

export type CustomerAddressPayload = {
  address_type: string;
  label: string | null;
  geography_id: string | null;
  line1: string;
  line2: string | null;
  city: string | null;
  state: string | null;
  district: string | null;
  postal_code: string | null;
  country_code: string;
  latitude: number | null;
  longitude: number | null;
  place_id: string | null;
  formatted_address: string | null;
  street_name: string | null;
  street_number: string | null;
  geocode_source: string | null;
  precision_meters: number | null;
  gps_link: string | null;
  contact_name: string | null;
  contact_phone: string | null;
  contact_email: string | null;
  is_operational_site: boolean;
  notes: string | null;
  ubigeo_code: string | null;
};

export type CustomerContactPayload = {
  full_name: string | null;
  label: string | null;
  role: string | null;
  phone: string | null;
  email: string | null;
  address_id: string | null;
  contact_purpose: string;
  contact_type: string;
  notes: string | null;
  is_primary: boolean;
};

export type CustomerCommercialAssignmentPayload = {
  address_id: string | null;
  user_id: string;
  assignment_role: string;
  notes: string | null;
  is_primary: boolean;
  is_active?: boolean;
};

export type CustomerBankAccount = {
  id: string;
  customer_id: string;
  bank_name: string;
  account_holder: string;
  iban: string;
  bic_swift: string | null;
  is_primary: boolean;
  is_active: boolean;
  notes: string | null;
  created_at: string;
  updated_at: string;
};

export type CustomerBankAccountPayload = {
  bank_name: string;
  account_holder: string;
  iban: string;
  bic_swift: string | null;
  is_primary: boolean;
  notes: string | null;
};

export type CustomerPricingTerm = {
  id: string;
  customer_id: string;
  product_id: string | null;
  scope_type: "GLOBAL" | "PRODUCT";
  pricing_mode: "FIXED_PRICE" | "PERCENT_DISCOUNT";
  fixed_amount: string | null;
  discount_percent: string | null;
  currency: string | null;
  valid_from: string;
  valid_to: string | null;
  source_quote_ref: string | null;
  approved_by: string | null;
  is_active: boolean;
  notes: string | null;
  created_at: string;
  updated_at: string;
};

export type CustomerPricingTermPayload = {
  product_id: string | null;
  scope_type: "GLOBAL" | "PRODUCT";
  pricing_mode: "FIXED_PRICE" | "PERCENT_DISCOUNT";
  fixed_amount: string | null;
  discount_percent: string | null;
  currency: string | null;
  valid_from: string;
  valid_to: string | null;
  source_quote_ref: string | null;
  notes: string | null;
};
