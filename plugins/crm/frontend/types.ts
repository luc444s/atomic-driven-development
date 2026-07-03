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
  contact_type: "PHONE" | "EMAIL" | "OTHER";
  value: string;
  label: string | null;
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
  notes: string | null;
  ubigeo_code: string | null;
};

export type CustomerContactPayload = {
  contact_type: "PHONE" | "EMAIL" | "OTHER";
  value: string;
  label: string | null;
  is_primary: boolean;
};
