# SYSTUTOR Database Reference

> Generado desde PostgreSQL. **115 tablas**, **1420 columnas**, **302 foreign keys**, **709 indexes**.

## Tablas centrales (mas referenciadas)

| Tabla | Referenciada por (FKs) |
|-------|------------------------|
| `tenants` | 69 |
| `users` | 61 |
| `prod_products` | 19 |
| `lg_warehouses` | 17 |
| `lg_cylinders` | 13 |
| `lg_vehicle_sessions` | 13 |
| `branches` | 12 |
| `crm_customers` | 10 |
| `lg_routes` | 8 |
| `lg_vehicles` | 8 |
| `lg_movements` | 8 |
| `lg_route_stops` | 7 |
| `lg_orders` | 4 |
| `lg_cylinder_states` | 3 |
| `crm_customer_addresses` | 3 |
| `prod_lines` | 3 |
| `prod_subline` | 3 |
| `prod_units` | 3 |
| `lg_route_operations` | 3 |
| `roles` | 2 |

---

## Nucleo (tenants, usuarios, roles, auditoria)

### `alembic_version`
Columnas: 1 | FKs: 0 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `version_num` | character varying | NO |  | PK  |

---

### `branches`
Columnas: 7 | FKs: 1 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `updated_at` | timestamp with time zone | NO |  |   |
| `created_at` | timestamp with time zone | NO |  |   |
| `is_active` | boolean | NO | true |   |
| `code` | character varying | NO |  |   |
| `name` | character varying | NO |  |   |
| `tenant_id` | character varying | NO |  |  → tenants.id |
| `id` | character varying | NO |  | PK  |

**Foreign Keys:**
- `tenant_id` → `tenants.id`

**Indexes (4):**
- `branches_pkey` (btree) on `id`
- `uq_branch_tenant_code` (btree) on `code`
- `uq_branch_tenant_code` (btree) on `tenant_id`
- `ix_branches_tenant_id` (btree) on `tenant_id`

---

### `permissions`
Columnas: 4 | FKs: 0 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `created_at` | timestamp with time zone | NO |  |   |
| `description` | text | YES |  |   |
| `name` | character varying | NO |  |   |
| `id` | character varying | NO |  | PK  |

---

### `plugin_registry`
Columnas: 20 | FKs: 0 | Filas: 5

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `updated_at` | timestamp with time zone | NO |  |   |
| `created_at` | timestamp with time zone | NO |  |   |
| `events_json` | json | NO |  |   |
| `permissions_json` | json | NO |  |   |
| `requires_json` | json | NO |  |   |
| `is_enabled` | boolean | NO | false |   |
| `disabled_at` | timestamp with time zone | YES |  |   |
| `enabled_at` | timestamp with time zone | YES |  |   |
| `installed_at` | timestamp with time zone | YES |  |   |
| `migration_version` | character varying | YES |  |   |
| `state` | character varying | NO |  |   |
| `description` | character varying | YES |  |   |
| `frontend_entrypoint` | character varying | YES |  |   |
| `backend_entrypoint` | character varying | YES |  |   |
| `api_version` | character varying | NO |  |   |
| `version` | character varying | NO |  |   |
| `name` | character varying | NO |  |   |
| `plugin_id` | character varying | NO |  |   |
| `id` | character varying | NO |  | PK  |
| `last_error` | character varying | YES |  |   |

---

### `role_permissions`
Columnas: 4 | FKs: 2 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `created_at` | timestamp with time zone | NO |  |   |
| `permission_id` | character varying | NO |  |  → permissions.id |
| `role_id` | character varying | NO |  |  → roles.id |
| `id` | character varying | NO |  | PK  |

**Foreign Keys:**
- `permission_id` → `permissions.id`
- `role_id` → `roles.id`

**Indexes (5):**
- `uq_role_permission` (btree) on `permission_id`
- `uq_role_permission` (btree) on `role_id`
- `role_permissions_pkey` (btree) on `id`
- `ix_role_permissions_permission_id` (btree) on `permission_id`
- `ix_role_permissions_role_id` (btree) on `role_id`

---

### `roles`
Columnas: 7 | FKs: 1 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `updated_at` | timestamp with time zone | NO |  |   |
| `created_at` | timestamp with time zone | NO |  |   |
| `is_active` | boolean | NO | true |   |
| `description` | text | YES |  |   |
| `name` | character varying | NO |  |   |
| `tenant_id` | character varying | NO |  |  → tenants.id |
| `id` | character varying | NO |  | PK  |

**Foreign Keys:**
- `tenant_id` → `tenants.id`

**Indexes (4):**
- `ix_roles_tenant_id` (btree) on `tenant_id`
- `uq_role_tenant_name` (btree) on `name`
- `roles_pkey` (btree) on `id`
- `uq_role_tenant_name` (btree) on `tenant_id`

---

### `tenants`
Columnas: 6 | FKs: 0 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `updated_at` | timestamp with time zone | NO |  |   |
| `created_at` | timestamp with time zone | NO |  |   |
| `is_active` | boolean | NO | true |   |
| `slug` | character varying | NO |  |   |
| `name` | character varying | NO |  |   |
| `id` | character varying | NO |  | PK  |

---

### `users`
Columnas: 11 | FKs: 2 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `updated_at` | timestamp with time zone | NO |  |   |
| `created_at` | timestamp with time zone | NO |  |   |
| `last_login_at` | timestamp with time zone | YES |  |   |
| `is_superadmin` | boolean | NO | false |   |
| `is_active` | boolean | NO | true |   |
| `password_hash` | character varying | NO |  |   |
| `full_name` | character varying | NO |  |   |
| `email` | character varying | NO |  |   |
| `branch_id` | character varying | YES |  |  → branches.id |
| `tenant_id` | character varying | NO |  |  → tenants.id |
| `id` | character varying | NO |  | PK  |

**Foreign Keys:**
- `branch_id` → `branches.id`
- `tenant_id` → `tenants.id`

**Indexes (4):**
- `users_email_key` (btree) on `email`
- `ix_users_branch_id` (btree) on `branch_id`
- `users_pkey` (btree) on `id`
- `ix_users_tenant_id` (btree) on `tenant_id`

---

## CRM (clientes, contactos, direcciones)

### `crm_customer_addresses`
Columnas: 33 | FKs: 3 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `is_operational_site` | boolean | NO |  |   |
| `updated_at` | timestamp with time zone | NO |  |   |
| `created_at` | timestamp with time zone | NO |  |   |
| `captured_at` | timestamp with time zone | YES |  |   |
| `is_active` | boolean | NO |  |   |
| `precision_meters` | integer | YES |  |   |
| `longitude` | double precision | YES |  |   |
| `latitude` | double precision | YES |  |   |
| `geography_id` | character varying | YES |  |   |
| `label` | character varying | YES |  |   |
| `address_type` | character varying | NO |  |   |
| `customer_id` | character varying | NO |  |  → crm_customers.id |
| `tenant_id` | character varying | NO |  |  → tenants.id |
| `id` | character varying | NO |  | PK  |
| `ubigeo_code` | character varying | YES |  |   |
| `captured_by` | character varying | YES |  |  → users.id |
| `notes` | character varying | YES |  |   |
| `contact_email` | character varying | YES |  |   |
| `contact_phone` | character varying | YES |  |   |
| `contact_name` | character varying | YES |  |   |
| `gps_link` | character varying | YES |  |   |
| `geocode_source` | character varying | YES |  |   |
| `street_number` | character varying | YES |  |   |
| `street_name` | character varying | YES |  |   |
| `formatted_address` | character varying | YES |  |   |
| `place_id` | character varying | YES |  |   |
| `country_code` | character varying | NO |  |   |
| `postal_code` | character varying | YES |  |   |
| `district` | character varying | YES |  |   |
| `state` | character varying | YES |  |   |
| `city` | character varying | YES |  |   |
| `line2` | character varying | YES |  |   |
| `line1` | character varying | NO |  |   |

**Foreign Keys:**
- `tenant_id` → `tenants.id`
- `customer_id` → `crm_customers.id`
- `captured_by` → `users.id`

**Indexes (7):**
- `ix_crm_addr_tenant_customer_cr` (btree) on `customer_id`
- `crm_customer_addresses_pkey` (btree) on `id`
- `ix_crm_addr_tenant_customer_cr` (btree) on `created_at`
- `ix_crm_customer_addresses_tenant_id` (btree) on `tenant_id`
- `ix_crm_addr_tenant_customer_cr` (btree) on `tenant_id`

---

### `crm_customer_bank_accounts`
Columnas: 12 | FKs: 2 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `updated_at` | timestamp with time zone | NO |  |   |
| `created_at` | timestamp with time zone | NO |  |   |
| `is_active` | boolean | NO |  |   |
| `is_primary` | boolean | NO |  |   |
| `notes` | character varying | YES |  |   |
| `bic_swift` | character varying | YES |  |   |
| `iban` | character varying | NO |  |   |
| `account_holder` | character varying | NO |  |   |
| `bank_name` | character varying | NO |  |   |
| `customer_id` | character varying | NO |  |  → crm_customers.id |
| `tenant_id` | character varying | NO |  |  → tenants.id |
| `id` | character varying | NO |  | PK  |

**Foreign Keys:**
- `tenant_id` → `tenants.id`
- `customer_id` → `crm_customers.id`

**Indexes (6):**
- `ix_crm_customer_bank_accounts_customer_id` (btree) on `customer_id`
- `ix_crm_bank_tenant_customer_cr` (btree) on `tenant_id`
- `ix_crm_bank_tenant_customer_cr` (btree) on `customer_id`
- `ix_crm_bank_tenant_customer_cr` (btree) on `created_at`
- `ix_crm_customer_bank_accounts_tenant_id` (btree) on `tenant_id`

---

### `crm_customer_commercial_assignments`
Columnas: 11 | FKs: 4 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `updated_at` | timestamp with time zone | NO |  |   |
| `created_at` | timestamp with time zone | NO |  |   |
| `is_active` | boolean | NO | true |   |
| `is_primary` | boolean | NO | false |   |
| `notes` | character varying | YES |  |   |
| `assignment_role` | character varying | NO |  |   |
| `user_id` | character varying | NO |  |  → users.id |
| `address_id` | character varying | YES |  |  → crm_customer_addresses.id |
| `customer_id` | character varying | NO |  |  → crm_customers.id |
| `tenant_id` | character varying | NO |  |  → tenants.id |
| `id` | character varying | NO |  | PK  |

**Foreign Keys:**
- `address_id` → `crm_customer_addresses.id`
- `customer_id` → `crm_customers.id`
- `tenant_id` → `tenants.id`
- `user_id` → `users.id`

**Indexes (11):**
- `ix_crm_comm_tenant_cust_role` (btree) on `customer_id`
- `ix_crm_comm_tenant_cust_role` (btree) on `is_primary`
- `ix_crm_customer_commercial_assignments_address_id` (btree) on `address_id`
- `ix_crm_comm_tenant_cust_role` (btree) on `tenant_id`
- `ix_crm_customer_commercial_assignments_user_id` (btree) on `user_id`

---

### `crm_customer_contacts`
Columnas: 16 | FKs: 3 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `updated_at` | timestamp with time zone | NO |  |   |
| `created_at` | timestamp with time zone | NO |  |   |
| `is_active` | boolean | NO |  |   |
| `is_primary` | boolean | NO |  |   |
| `id` | character varying | NO |  | PK  |
| `notes` | character varying | YES |  |   |
| `contact_purpose` | character varying | NO |  |   |
| `address_id` | character varying | YES |  |  → crm_customer_addresses.id |
| `email` | character varying | YES |  |   |
| `phone` | character varying | YES |  |   |
| `role` | character varying | YES |  |   |
| `full_name` | character varying | YES |  |   |
| `label` | character varying | YES |  |   |
| `contact_type` | character varying | NO |  |   |
| `customer_id` | character varying | NO |  |  → crm_customers.id |
| `tenant_id` | character varying | NO |  |  → tenants.id |

**Foreign Keys:**
- `tenant_id` → `tenants.id`
- `customer_id` → `crm_customers.id`
- `address_id` → `crm_customer_addresses.id`

**Indexes (10):**
- `ix_crm_contacts_tenant_cust_act` (btree) on `tenant_id`
- `ix_crm_contacts_tenant_cust_act` (btree) on `is_primary`
- `ix_crm_contacts_tenant_cust_act` (btree) on `created_at`
- `ix_crm_contacts_tenant_cust_act` (btree) on `customer_id`
- `ix_crm_contacts_tenant_cust_act` (btree) on `is_active`

---

### `crm_customer_pricing_terms`
Columnas: 17 | FKs: 3 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `updated_at` | timestamp with time zone | NO |  |   |
| `created_at` | timestamp with time zone | NO |  |   |
| `is_active` | boolean | NO |  |   |
| `valid_to` | timestamp with time zone | YES |  |   |
| `valid_from` | timestamp with time zone | NO |  |   |
| `discount_percent` | numeric | YES |  |   |
| `fixed_amount` | numeric | YES |  |   |
| `notes` | character varying | YES |  |   |
| `approved_by` | character varying | YES |  |  → users.id |
| `source_quote_ref` | character varying | YES |  |   |
| `currency` | character varying | YES |  |   |
| `pricing_mode` | character varying | NO |  |   |
| `scope_type` | character varying | NO |  |   |
| `product_id` | character varying | YES |  |   |
| `customer_id` | character varying | NO |  |  → crm_customers.id |
| `tenant_id` | character varying | NO |  |  → tenants.id |
| `id` | character varying | NO |  | PK  |

**Foreign Keys:**
- `tenant_id` → `tenants.id`
- `customer_id` → `crm_customers.id`
- `approved_by` → `users.id`

**Indexes (11):**
- `ix_crm_customer_pricing_terms_tenant_id` (btree) on `tenant_id`
- `uq_crm_customer_pricing_tenant_customer_product_scope` (btree) on `product_id`
- `ix_crm_customer_pricing_terms_customer_id` (btree) on `customer_id`
- `ix_crm_pricing_tenant_customer_cr` (btree) on `tenant_id`
- `ix_crm_pricing_tenant_customer_cr` (btree) on `customer_id`

---

### `crm_customers`
Columnas: 35 | FKs: 5 | Filas: 3

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `birth_date` | date | YES |  |   |
| `is_exempt` | boolean | NO |  |   |
| `activity_validation_date` | timestamp with time zone | YES |  |   |
| `activity_validated` | boolean | NO |  |   |
| `cash_criterion_applicable` | boolean | NO | false |   |
| `equivalence_surcharge_applicable` | boolean | NO | false |   |
| `is_intracommunity` | boolean | NO | false |   |
| `updated_at` | timestamp with time zone | NO |  |   |
| `created_at` | timestamp with time zone | NO |  |   |
| `is_active` | boolean | NO |  |   |
| `last_name` | character varying | YES |  |   |
| `first_name` | character varying | YES |  |   |
| `billing_type` | character varying | YES |  |   |
| `payment_term_code` | character varying | YES |  |  → crm_payment_terms.code |
| `activity_validation_source` | character varying | YES |  |   |
| `economic_activity_description` | character varying | YES |  |   |
| `economic_activity_code` | character varying | YES |  |   |
| `fiscal_address_id` | character varying | YES |  |  → crm_customer_addresses.id |
| `mobile` | character varying | YES |  |   |
| `phone` | character varying | YES |  |   |
| `email` | character varying | YES |  |   |
| `country_code` | character varying | NO |  |   |
| `document_number` | character varying | NO |  |   |
| `document_type_code` | character varying | NO |  |  → crm_document_types.code |
| `commercial_name` | character varying | YES |  |   |
| `legal_name` | character varying | NO |  |   |
| `external_code` | character varying | YES |  |   |
| `tenant_id` | character varying | NO |  |  → tenants.id |
| `id` | character varying | NO |  | PK  |
| `tax_regime_code` | character varying | YES |  |   |
| `fiscal_operation_key` | character varying | YES |  |   |
| `accounting_code` | character varying | YES |  |   |
| `created_by` | character varying | NO |  |  → users.id |
| `notes` | text | YES |  |   |
| `gender` | character varying | YES |  |   |

**Foreign Keys:**
- `tenant_id` → `tenants.id`
- `document_type_code` → `crm_document_types.code`
- `payment_term_code` → `crm_payment_terms.code`
- `created_by` → `users.id`
- `fiscal_address_id` → `crm_customer_addresses.id`

**Indexes (19):**
- `uq_crm_customer_tenant_document` (btree) on `tenant_id`
- `ix_crm_customers_tenant_active_leg` (btree) on `is_active`
- `ix_crm_customers_tenant_active_leg` (btree) on `legal_name`
- `ix_crm_customers_phone` (btree) on `phone`
- `ix_crm_customers_email` (btree) on `email`

---

### `crm_document_types`
Columnas: 9 | FKs: 0 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `created_at` | timestamp with time zone | NO |  |   |
| `is_active` | boolean | NO |  |   |
| `is_company` | boolean | NO |  |   |
| `is_person` | boolean | NO |  |   |
| `validation_pattern` | character varying | YES |  |   |
| `description` | character varying | YES |  |   |
| `country_code` | character varying | NO |  |   |
| `name` | character varying | NO |  |   |
| `code` | character varying | NO |  | PK  |

---

### `crm_geography`
Columnas: 9 | FKs: 1 | Filas: 15

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `created_at` | timestamp with time zone | NO |  |   |
| `is_active` | boolean | NO |  |   |
| `level` | integer | NO |  |   |
| `ubigeo_code` | character varying | YES |  |   |
| `country_code` | character varying | NO |  |   |
| `name` | character varying | NO |  |   |
| `code` | character varying | YES |  |   |
| `parent_id` | character varying | YES |  |  → crm_geography.id |
| `id` | character varying | NO |  | PK  |

**Foreign Keys:**
- `parent_id` → `crm_geography.id`

**Indexes (6):**
- `uq_crm_geography_country_level_code` (btree) on `country_code`
- `ix_crm_geography_country_code` (btree) on `country_code`
- `crm_geography_pkey` (btree) on `id`
- `ix_crm_geography_parent_id` (btree) on `parent_id`
- `uq_crm_geography_country_level_code` (btree) on `code`

---

### `crm_payment_terms`
Columnas: 8 | FKs: 0 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `created_at` | timestamp with time zone | NO |  |   |
| `is_active` | boolean | NO |  |   |
| `days` | integer | NO |  |   |
| `payment_mode` | character varying | NO | 'CONTADO'::character varying |   |
| `operation_type` | character varying | NO |  |   |
| `description` | character varying | YES |  |   |
| `name` | character varying | NO |  |   |
| `code` | character varying | NO |  | PK  |

---

## Productos (catalogo, ADR, precios)

### `prod_adr`
Columnas: 19 | FKs: 4 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `created_at` | timestamp with time zone | NO |  |   |
| `valid_to` | date | YES |  |   |
| `valid_from` | date | NO |  |   |
| `points` | integer | YES |  |   |
| `factor` | integer | YES |  |   |
| `net_volume_m3` | numeric | YES |  |   |
| `net_weight_kg` | numeric | YES |  |   |
| `tenant_id` | character varying | NO |  |  → tenants.id |
| `id` | character varying | NO |  | PK  |
| `created_by` | character varying | NO |  |  → users.id |
| `unit_measure` | character varying | YES |  |   |
| `subline_id` | character varying | YES |  |  → prod_subline.id |
| `tunnel_restriction` | character varying | YES |  |   |
| `label` | character varying | YES |  |   |
| `cargo_description` | text | YES |  |   |
| `un_number` | character varying | YES |  |   |
| `packaging_type` | character varying | YES |  |   |
| `category` | character varying | YES |  |   |
| `product_id` | character varying | NO |  |  → prod_products.id |

**Foreign Keys:**
- `tenant_id` → `tenants.id`
- `product_id` → `prod_products.id`
- `subline_id` → `prod_subline.id`
- `created_by` → `users.id`

**Indexes (7):**
- `ix_prod_adr_prod_valid` (btree) on `product_id`
- `ix_prod_adr_product_id` (btree) on `product_id`
- `ix_prod_adr_tenant_id` (btree) on `tenant_id`
- `ix_prod_adr_subline_id` (btree) on `subline_id`
- `prod_adr_pkey` (btree) on `id`

---

### `prod_barcodes`
Columnas: 9 | FKs: 2 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `updated_at` | timestamp with time zone | NO |  |   |
| `created_at` | timestamp with time zone | NO |  |   |
| `is_active` | boolean | NO |  |   |
| `is_primary` | boolean | NO |  |   |
| `barcode` | character varying | NO |  |   |
| `barcode_type` | character varying | NO |  |   |
| `product_id` | character varying | NO |  |  → prod_products.id |
| `tenant_id` | character varying | NO |  |  → tenants.id |
| `id` | character varying | NO |  | PK  |

**Foreign Keys:**
- `tenant_id` → `tenants.id`
- `product_id` → `prod_products.id`

**Indexes (10):**
- `prod_barcodes_pkey` (btree) on `id`
- `uq_prod_barcode_tenant_type_value` (btree) on `barcode`
- `ix_prod_barcodes_tenant_id` (btree) on `tenant_id`
- `ix_prod_barcodes_product_id` (btree) on `product_id`
- `ix_prod_barcodes_prod_primary_cr` (btree) on `created_at`

---

### `prod_brands`
Columnas: 8 | FKs: 1 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `updated_at` | timestamp with time zone | NO |  |   |
| `created_at` | timestamp with time zone | NO |  |   |
| `is_active` | boolean | NO |  |   |
| `description` | character varying | YES |  |   |
| `name` | character varying | NO |  |   |
| `code` | character varying | NO |  |   |
| `tenant_id` | character varying | NO |  |  → tenants.id |
| `id` | character varying | NO |  | PK  |

**Foreign Keys:**
- `tenant_id` → `tenants.id`

**Indexes (4):**
- `uq_prod_brand_tenant_code` (btree) on `code`
- `uq_prod_brand_tenant_code` (btree) on `tenant_id`
- `ix_prod_brands_tenant_id` (btree) on `tenant_id`
- `prod_brands_pkey` (btree) on `id`

---

### `prod_categories`
Columnas: 8 | FKs: 1 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `updated_at` | timestamp with time zone | NO |  |   |
| `created_at` | timestamp with time zone | NO |  |   |
| `is_active` | boolean | NO |  |   |
| `description` | character varying | YES |  |   |
| `name` | character varying | NO |  |   |
| `code` | character varying | NO |  |   |
| `tenant_id` | character varying | NO |  |  → tenants.id |
| `id` | character varying | NO |  | PK  |

**Foreign Keys:**
- `tenant_id` → `tenants.id`

**Indexes (4):**
- `prod_categories_pkey` (btree) on `id`
- `ix_prod_categories_tenant_id` (btree) on `tenant_id`
- `uq_prod_category_tenant_code` (btree) on `code`
- `uq_prod_category_tenant_code` (btree) on `tenant_id`

---

### `prod_conditions`
Columnas: 4 | FKs: 0 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `is_active` | boolean | NO |  |   |
| `description` | character varying | YES |  |   |
| `name` | character varying | NO |  |   |
| `code` | character varying | NO |  | PK  |

---

### `prod_costs`
Columnas: 10 | FKs: 3 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `created_at` | timestamp with time zone | NO |  |   |
| `valid_to` | date | YES |  |   |
| `valid_from` | date | NO |  |   |
| `amount` | numeric | NO |  |   |
| `created_by` | character varying | NO |  |  → users.id |
| `currency` | character varying | NO |  |   |
| `cost_type` | character varying | NO |  |   |
| `product_id` | character varying | NO |  |  → prod_products.id |
| `tenant_id` | character varying | NO |  |  → tenants.id |
| `id` | character varying | NO |  | PK  |

**Foreign Keys:**
- `tenant_id` → `tenants.id`
- `product_id` → `prod_products.id`
- `created_by` → `users.id`

**Indexes (8):**
- `ix_prod_costs_prod_type_valid` (btree) on `product_id`
- `ix_prod_costs_prod_type_valid` (btree) on `cost_type`
- `ix_prod_costs_cost_type` (btree) on `cost_type`
- `ix_prod_costs_product_id` (btree) on `product_id`
- `ix_prod_costs_created_by` (btree) on `created_by`

---

### `prod_groups`
Columnas: 11 | FKs: 5 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `updated_at` | timestamp with time zone | NO |  |   |
| `created_at` | timestamp with time zone | NO |  |   |
| `is_active` | boolean | NO |  |   |
| `unit_id` | character varying | YES |  |  → prod_units.id |
| `subline_id` | character varying | YES |  |  → prod_subline.id |
| `line_id` | character varying | YES |  |  → prod_lines.id |
| `gas_product_id` | character varying | YES |  |  → prod_products.id |
| `name` | character varying | NO |  |   |
| `code` | character varying | NO |  |   |
| `tenant_id` | character varying | NO |  |  → tenants.id |
| `id` | character varying | NO |  | PK  |

**Foreign Keys:**
- `tenant_id` → `tenants.id`
- `line_id` → `prod_lines.id`
- `subline_id` → `prod_subline.id`
- `unit_id` → `prod_units.id`
- `gas_product_id` → `prod_products.id`

**Indexes (8):**
- `ix_prod_groups_subline_id` (btree) on `subline_id`
- `uq_prod_group_tenant_code` (btree) on `tenant_id`
- `uq_prod_group_tenant_code` (btree) on `code`
- `ix_prod_groups_tenant_id` (btree) on `tenant_id`
- `ix_prod_groups_line_id` (btree) on `line_id`

---

### `prod_insumo_types`
Columnas: 8 | FKs: 1 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `updated_at` | timestamp with time zone | NO |  |   |
| `created_at` | timestamp with time zone | NO |  |   |
| `is_active` | boolean | NO |  |   |
| `description` | character varying | YES |  |   |
| `name` | character varying | NO |  |   |
| `code` | character varying | NO |  |   |
| `tenant_id` | character varying | NO |  |  → tenants.id |
| `id` | character varying | NO |  | PK  |

**Foreign Keys:**
- `tenant_id` → `tenants.id`

**Indexes (4):**
- `prod_insumo_types_pkey` (btree) on `id`
- `uq_prod_insumo_type_tenant_code` (btree) on `code`
- `ix_prod_insumo_types_tenant_id` (btree) on `tenant_id`
- `uq_prod_insumo_type_tenant_code` (btree) on `tenant_id`

---

### `prod_lines`
Columnas: 9 | FKs: 2 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `updated_at` | timestamp with time zone | NO |  |   |
| `created_at` | timestamp with time zone | NO |  |   |
| `is_active` | boolean | NO |  |   |
| `description` | character varying | YES |  |   |
| `category_id` | character varying | YES |  |  → prod_categories.id |
| `name` | character varying | NO |  |   |
| `code` | character varying | NO |  |   |
| `tenant_id` | character varying | NO |  |  → tenants.id |
| `id` | character varying | NO |  | PK  |

**Foreign Keys:**
- `tenant_id` → `tenants.id`
- `category_id` → `prod_categories.id`

**Indexes (5):**
- `prod_lines_pkey` (btree) on `id`
- `uq_prod_line_tenant_code` (btree) on `tenant_id`
- `ix_prod_lines_category_id` (btree) on `category_id`
- `ix_prod_lines_tenant_id` (btree) on `tenant_id`
- `uq_prod_line_tenant_code` (btree) on `code`

---

### `prod_media`
Columnas: 7 | FKs: 2 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `created_at` | timestamp with time zone | NO |  |   |
| `is_primary` | boolean | NO |  |   |
| `url` | character varying | NO |  |   |
| `media_type` | character varying | NO |  |   |
| `product_id` | character varying | NO |  |  → prod_products.id |
| `tenant_id` | character varying | NO |  |  → tenants.id |
| `id` | character varying | NO |  | PK  |

**Foreign Keys:**
- `tenant_id` → `tenants.id`
- `product_id` → `prod_products.id`

**Indexes (6):**
- `ix_prod_media_prod_primary_cr` (btree) on `created_at`
- `ix_prod_media_prod_primary_cr` (btree) on `product_id`
- `prod_media_pkey` (btree) on `id`
- `ix_prod_media_product_id` (btree) on `product_id`
- `ix_prod_media_tenant_id` (btree) on `tenant_id`

---

### `prod_prices`
Columnas: 10 | FKs: 3 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `created_at` | timestamp with time zone | NO |  |   |
| `valid_to` | date | YES |  |   |
| `valid_from` | date | NO |  |   |
| `amount` | numeric | NO |  |   |
| `created_by` | character varying | NO |  |  → users.id |
| `currency` | character varying | NO |  |   |
| `price_list` | character varying | NO |  |   |
| `product_id` | character varying | NO |  |  → prod_products.id |
| `tenant_id` | character varying | NO |  |  → tenants.id |
| `id` | character varying | NO |  | PK  |

**Foreign Keys:**
- `tenant_id` → `tenants.id`
- `product_id` → `prod_products.id`
- `created_by` → `users.id`

**Indexes (8):**
- `ix_prod_prices_tenant_id` (btree) on `tenant_id`
- `ix_prod_prices_prod_list_valid` (btree) on `price_list`
- `ix_prod_prices_prod_list_valid` (btree) on `valid_from`
- `ix_prod_prices_created_by` (btree) on `created_by`
- `ix_prod_prices_product_id` (btree) on `product_id`

---

### `prod_products`
Columnas: 27 | FKs: 12 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `updated_at` | timestamp with time zone | NO |  |   |
| `created_at` | timestamp with time zone | NO |  |   |
| `is_active` | boolean | NO |  |   |
| `is_service` | boolean | NO |  |   |
| `content_m3` | numeric | YES |  |   |
| `weight_kg` | numeric | YES |  |   |
| `qty_per_box` | numeric | YES |  |   |
| `legacy_id` | integer | YES |  |   |
| `default_weight_kg` | numeric | YES |  |   |
| `created_by` | character varying | NO |  |  → users.id |
| `country_code` | character varying | YES |  |   |
| `condition_code` | character varying | NO |  |  → prod_conditions.code |
| `status_code` | character varying | NO |  |  → prod_status.code |
| `group_id` | character varying | YES |  |  → prod_groups.id |
| `subcategory_id` | character varying | YES |  |  → prod_subcategories.id |
| `box_unit_id` | character varying | YES |  |  → prod_units.id |
| `unit_id` | character varying | NO |  |  → prod_units.id |
| `insumo_type_id` | character varying | YES |  |  → prod_insumo_types.id |
| `brand_id` | character varying | YES |  |  → prod_brands.id |
| `subline_id` | character varying | YES |  |  → prod_subline.id |
| `line_id` | character varying | NO |  |  → prod_lines.id |
| `short_description` | character varying | YES |  |   |
| `description` | text | YES |  |   |
| `name` | character varying | NO |  |   |
| `sku` | character varying | NO |  |   |
| `tenant_id` | character varying | NO |  |  → tenants.id |
| `id` | character varying | NO |  | PK  |

**Foreign Keys:**
- `tenant_id` → `tenants.id`
- `line_id` → `prod_lines.id`
- `subline_id` → `prod_subline.id`
- `brand_id` → `prod_brands.id`
- `insumo_type_id` → `prod_insumo_types.id`
- `unit_id` → `prod_units.id`
- `box_unit_id` → `prod_units.id`
- `subcategory_id` → `prod_subcategories.id`
- `group_id` → `prod_groups.id`
- `status_code` → `prod_status.code`
- `condition_code` → `prod_conditions.code`
- `created_by` → `users.id`

**Indexes (23):**
- `ix_prod_products_sku_trgm` (gin) on `sku`
- `ix_prod_products_subcategory_id` (btree) on `subcategory_id`
- `ix_prod_products_created_by` (btree) on `created_by`
- `ix_prod_products_name` (btree) on `name`
- `ix_prod_products_tenant_active_name` (btree) on `tenant_id`

---

### `prod_promotions`
Columnas: 15 | FKs: 3 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `updated_at` | timestamp with time zone | NO |  |   |
| `created_at` | timestamp with time zone | NO |  |   |
| `is_active` | boolean | NO |  |   |
| `valid_to` | date | YES |  |   |
| `valid_from` | date | NO |  |   |
| `box_price` | numeric | YES |  |   |
| `unit_price` | numeric | YES |  |   |
| `discount_percent` | numeric | YES |  |   |
| `qty_required` | integer | YES |  |   |
| `created_by` | character varying | NO |  |  → users.id |
| `condition` | character varying | NO |  |   |
| `name` | character varying | YES |  |   |
| `product_id` | character varying | NO |  |  → prod_products.id |
| `tenant_id` | character varying | NO |  |  → tenants.id |
| `id` | character varying | NO |  | PK  |

**Foreign Keys:**
- `tenant_id` → `tenants.id`
- `product_id` → `prod_products.id`
- `created_by` → `users.id`

**Indexes (7):**
- `ix_prod_promotions_tenant_id` (btree) on `tenant_id`
- `ix_prod_promotions_product_id` (btree) on `product_id`
- `ix_prod_promotions_prod_valid_cr` (btree) on `valid_from`
- `ix_prod_promotions_created_by` (btree) on `created_by`
- `ix_prod_promotions_prod_valid_cr` (btree) on `product_id`

---

### `prod_status`
Columnas: 3 | FKs: 0 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `is_active` | boolean | NO |  |   |
| `code` | character varying | NO |  | PK  |
| `name` | character varying | NO |  |   |

---

### `prod_subcategories`
Columnas: 8 | FKs: 1 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `updated_at` | timestamp with time zone | NO |  |   |
| `created_at` | timestamp with time zone | NO |  |   |
| `is_active` | boolean | NO |  |   |
| `description` | character varying | YES |  |   |
| `name` | character varying | NO |  |   |
| `code` | character varying | NO |  |   |
| `tenant_id` | character varying | NO |  |  → tenants.id |
| `id` | character varying | NO |  | PK  |

**Foreign Keys:**
- `tenant_id` → `tenants.id`

**Indexes (4):**
- `ix_prod_subcategories_tenant_id` (btree) on `tenant_id`
- `uq_prod_subcategory_tenant_code` (btree) on `tenant_id`
- `uq_prod_subcategory_tenant_code` (btree) on `code`
- `prod_subcategories_pkey` (btree) on `id`

---

### `prod_subline`
Columnas: 8 | FKs: 2 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `updated_at` | timestamp with time zone | NO |  |   |
| `created_at` | timestamp with time zone | NO |  |   |
| `is_active` | boolean | NO |  |   |
| `line_id` | character varying | NO |  |  → prod_lines.id |
| `name` | character varying | NO |  |   |
| `code` | character varying | NO |  |   |
| `tenant_id` | character varying | NO |  |  → tenants.id |
| `id` | character varying | NO |  | PK  |

**Foreign Keys:**
- `tenant_id` → `tenants.id`
- `line_id` → `prod_lines.id`

**Indexes (6):**
- `ix_prod_subline_line_id` (btree) on `line_id`
- `uq_prod_subline_tenant_code_line` (btree) on `line_id`
- `uq_prod_subline_tenant_code_line` (btree) on `tenant_id`
- `prod_subline_pkey` (btree) on `id`
- `ix_prod_subline_tenant_id` (btree) on `tenant_id`

---

### `prod_tax_config`
Columnas: 9 | FKs: 2 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `created_at` | timestamp with time zone | NO |  |   |
| `valid_to` | date | YES |  |   |
| `valid_from` | date | NO |  |   |
| `is_exempt` | boolean | NO |  |   |
| `value` | numeric | YES |  |   |
| `tax_type` | character varying | NO |  |   |
| `product_id` | character varying | NO |  |  → prod_products.id |
| `tenant_id` | character varying | NO |  |  → tenants.id |
| `id` | character varying | NO |  | PK  |

**Foreign Keys:**
- `tenant_id` → `tenants.id`
- `product_id` → `prod_products.id`

**Indexes (7):**
- `ix_prod_tax_config_product_id` (btree) on `product_id`
- `ix_prod_tax_prod_type_valid` (btree) on `product_id`
- `ix_prod_tax_config_tenant_id` (btree) on `tenant_id`
- `ix_prod_tax_config_tax_type` (btree) on `tax_type`
- `ix_prod_tax_prod_type_valid` (btree) on `tax_type`

---

### `prod_units`
Columnas: 11 | FKs: 1 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `updated_at` | timestamp with time zone | NO |  |   |
| `created_at` | timestamp with time zone | NO |  |   |
| `is_active` | boolean | NO |  |   |
| `kg_factor` | double precision | YES |  |   |
| `liter_factor` | double precision | YES |  |   |
| `m3_factor` | double precision | YES |  |   |
| `equivalencia` | integer | YES |  |   |
| `name` | character varying | NO |  |   |
| `code` | character varying | NO |  |   |
| `tenant_id` | character varying | NO |  |  → tenants.id |
| `id` | character varying | NO |  | PK  |

**Foreign Keys:**
- `tenant_id` → `tenants.id`

**Indexes (4):**
- `ix_prod_units_tenant_id` (btree) on `tenant_id`
- `uq_prod_unit_tenant_code` (btree) on `code`
- `prod_units_pkey` (btree) on `id`
- `uq_prod_unit_tenant_code` (btree) on `tenant_id`

---

## Stock (inventario, ledger)

### `stk_allocation`
Columnas: 16 | FKs: 5 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `released_at` | timestamp with time zone | YES |  |   |
| `expires_at` | timestamp with time zone | YES |  |   |
| `created_at` | timestamp with time zone | NO | now() |   |
| `remaining_quantity` | numeric | NO |  |   |
| `quantity` | numeric | NO |  |   |
| `release_reason` | text | YES |  |   |
| `released_by` | character varying | YES |  |  → users.id |
| `created_by` | character varying | NO |  |  → users.id |
| `status` | character varying | NO | 'active'::character varying |   |
| `reference_id` | character varying | NO |  |   |
| `reference_type` | character varying | NO |  |   |
| `warehouse_id` | character varying | NO |  |  → lg_warehouses.id |
| `product_id` | character varying | NO |  |  → prod_products.id |
| `allocation_group_id` | character varying | YES |  |   |
| `tenant_id` | character varying | NO |  |  → tenants.id |
| `id` | character varying | NO |  | PK  |

**Foreign Keys:**
- `tenant_id` → `tenants.id`
- `product_id` → `prod_products.id`
- `warehouse_id` → `lg_warehouses.id`
- `created_by` → `users.id`
- `released_by` → `users.id`

**Indexes (12):**
- `ix_stk_allocation_tenant_group` (btree) on `tenant_id`
- `ix_stk_allocation_tenant_status` (btree) on `tenant_id`
- `ix_stk_allocation_tenant_status` (btree) on `status`
- `ix_stk_allocation_tenant_expires` (btree) on `expires_at`
- `uq_stk_allocation_ref` (btree) on `product_id`

---

### `stk_balance`
Columnas: 10 | FKs: 4 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `reserved_quantity` | numeric | NO | 0 |   |
| `allow_negative_stock` | boolean | NO | false |   |
| `total_cost` | numeric | NO | 0 |   |
| `updated_at` | timestamp with time zone | NO |  |   |
| `quantity` | numeric | NO |  |   |
| `updated_by` | character varying | NO |  |  → users.id |
| `warehouse_id` | character varying | NO |  |  → lg_warehouses.id |
| `product_id` | character varying | NO |  |  → prod_products.id |
| `tenant_id` | character varying | NO |  |  → tenants.id |
| `id` | character varying | NO |  | PK  |

**Foreign Keys:**
- `tenant_id` → `tenants.id`
- `product_id` → `prod_products.id`
- `warehouse_id` → `lg_warehouses.id`
- `updated_by` → `users.id`

**Indexes (11):**
- `ix_stk_balance_updated_by` (btree) on `updated_by`
- `ix_stk_balance_tenant_wh_prod` (btree) on `product_id`
- `uq_stk_balance_tenant_product_warehouse` (btree) on `product_id`
- `ix_stk_balance_tenant_wh_prod` (btree) on `warehouse_id`
- `stk_balance_pkey` (btree) on `id`

---

### `stk_config`
Columnas: 10 | FKs: 4 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `updated_at` | timestamp with time zone | NO |  |   |
| `is_active` | boolean | NO |  |   |
| `max_quantity` | numeric | YES |  |   |
| `min_quantity` | numeric | NO |  |   |
| `allow_negative_stock` | boolean | NO | false |   |
| `updated_by` | character varying | NO |  |  → users.id |
| `warehouse_id` | character varying | NO |  |  → lg_warehouses.id |
| `product_id` | character varying | NO |  |  → prod_products.id |
| `tenant_id` | character varying | NO |  |  → tenants.id |
| `id` | character varying | NO |  | PK  |

**Foreign Keys:**
- `tenant_id` → `tenants.id`
- `product_id` → `prod_products.id`
- `warehouse_id` → `lg_warehouses.id`
- `updated_by` → `users.id`

**Indexes (8):**
- `ix_stk_config_updated_by` (btree) on `updated_by`
- `ix_stk_config_product_id` (btree) on `product_id`
- `stk_config_pkey` (btree) on `id`
- `ix_stk_config_tenant_id` (btree) on `tenant_id`
- `uq_stk_config_tenant_product_warehouse` (btree) on `product_id`

---

### `stk_ledger`
Columnas: 22 | FKs: 4 | Filas: 4

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `cost_after` | numeric | YES |  |   |
| `total_cost` | numeric | YES |  |   |
| `unit_cost` | numeric | YES |  |   |
| `created_at` | timestamp with time zone | NO |  |   |
| `balance_after` | numeric | NO |  |   |
| `quantity` | numeric | NO |  |   |
| `warehouse_id` | character varying | NO |  |  → lg_warehouses.id |
| `product_id` | character varying | NO |  |  → prod_products.id |
| `tenant_id` | character varying | NO |  |  → tenants.id |
| `id` | character varying | NO |  | PK  |
| `source` | character varying | YES |  |   |
| `related_party_id` | character varying | YES |  |   |
| `related_party_type` | character varying | YES |  |   |
| `document_id` | character varying | YES |  |   |
| `document_type` | character varying | YES |  |   |
| `operation_type` | character varying | YES |  |   |
| `movement_type` | character varying | YES |  |   |
| `created_by` | character varying | NO |  |  → users.id |
| `notes` | text | YES |  |   |
| `reference_id` | character varying | YES |  |   |
| `reference_type` | character varying | YES |  |   |
| `operation` | character varying | NO |  |   |

**Foreign Keys:**
- `tenant_id` → `tenants.id`
- `product_id` → `prod_products.id`
- `warehouse_id` → `lg_warehouses.id`
- `created_by` → `users.id`

**Indexes (24):**
- `ix_stk_ledger_tenant_prod_wh_cr` (btree) on `warehouse_id`
- `ix_stk_ledger_reference_id` (btree) on `reference_id`
- `ix_stk_ledger_warehouse_id` (btree) on `warehouse_id`
- `ix_stk_ledger_reference_type` (btree) on `reference_type`
- `uq_stk_ledger_idempotency` (btree) on `operation`

---

## Ventas (cotizaciones)

### `ventas_quote_drafts`
Columnas: 15 | FKs: 5 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `updated_at` | timestamp with time zone | NO | now() |   |
| `created_at` | timestamp with time zone | NO | now() |   |
| `delivery_time` | time without time zone | YES |  |   |
| `delivery_date` | date | NO |  |   |
| `updated_by` | character varying | YES |  |  → users.id |
| `created_by` | character varying | NO |  |  → users.id |
| `notes` | text | YES |  |   |
| `conditions` | text | YES |  |   |
| `vehicle_plate` | character varying | YES |  |   |
| `vehicle_id` | character varying | YES |  |  → lg_vehicles.id |
| `status` | character varying | NO | 'DRAFT'::character varying |   |
| `customer_name` | character varying | YES |  |   |
| `customer_id` | character varying | NO |  |  → crm_customers.id |
| `tenant_id` | character varying | NO |  |  → tenants.id |
| `id` | character varying | NO |  | PK  |

**Foreign Keys:**
- `tenant_id` → `tenants.id`
- `customer_id` → `crm_customers.id`
- `vehicle_id` → `lg_vehicles.id`
- `created_by` → `users.id`
- `updated_by` → `users.id`

**Indexes (6):**
- `ix_ventas_quote_drafts_created_by` (btree) on `created_by`
- `ix_ventas_quote_drafts_customer_id` (btree) on `customer_id`
- `ix_ventas_quote_drafts_vehicle_id` (btree) on `vehicle_id`
- `ventas_quote_drafts_pkey` (btree) on `id`
- `ix_ventas_quote_drafts_status` (btree) on `status`

---

### `ventas_quote_items`
Columnas: 7 | FKs: 2 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `created_at` | timestamp with time zone | NO | now() |   |
| `unit_weight_kg` | numeric | YES |  |   |
| `quantity` | integer | NO |  |   |
| `product_name` | character varying | YES |  |   |
| `product_id` | character varying | NO |  |  → prod_products.id |
| `quote_draft_id` | character varying | NO |  |  → ventas_quote_drafts.id |
| `id` | character varying | NO |  | PK  |

**Foreign Keys:**
- `quote_draft_id` → `ventas_quote_drafts.id`
- `product_id` → `prod_products.id`

**Indexes (5):**
- `ventas_quote_items_pkey` (btree) on `id`
- `ix_ventas_quote_items_quote_draft_id` (btree) on `quote_draft_id`
- `uq_quote_item_draft_product` (btree) on `product_id`
- `ix_ventas_quote_items_product_id` (btree) on `product_id`
- `uq_quote_item_draft_product` (btree) on `quote_draft_id`

---

## Logistics - Almacenes y vehiculos

### `lg_vehicle_delivery_points`
Columnas: 5 | FKs: 0 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `created_at` | timestamp without time zone | YES |  |   |
| `delivery_point_id` | character varying | NO |  |   |
| `vehicle_id` | character varying | NO |  |   |
| `tenant_id` | character varying | NO |  |   |
| `id` | character varying | NO |  | PK  |

**Indexes (4):**
- `uq_lg_vehicle_delivery_point` (btree) on `delivery_point_id`
- `uq_lg_vehicle_delivery_point` (btree) on `vehicle_id`
- `uq_lg_vehicle_delivery_point` (btree) on `tenant_id`
- `lg_vehicle_delivery_points_pkey` (btree) on `id`

---

### `lg_vehicle_route_restrictions`
Columnas: 6 | FKs: 0 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `created_at` | timestamp without time zone | YES |  |   |
| `restriction_type` | character varying | NO | 'ALLOW'::character varying |   |
| `route_id` | character varying | NO |  |   |
| `vehicle_id` | character varying | NO |  |   |
| `tenant_id` | character varying | NO |  |   |
| `id` | character varying | NO |  | PK  |

**Indexes (4):**
- `uq_lg_vehicle_route_restriction` (btree) on `vehicle_id`
- `lg_vehicle_route_restrictions_pkey` (btree) on `id`
- `uq_lg_vehicle_route_restriction` (btree) on `route_id`
- `uq_lg_vehicle_route_restriction` (btree) on `tenant_id`

---

### `lg_vehicles`
Columnas: 16 | FKs: 3 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `updated_at` | timestamp with time zone | NO |  |   |
| `created_at` | timestamp with time zone | NO |  |   |
| `is_active` | boolean | NO |  |   |
| `useful_load` | numeric | YES |  |   |
| `capacity_volume` | numeric | YES |  |   |
| `capacity_weight` | numeric | YES |  |   |
| `mobile_warehouse_id` | character varying | YES |  |  → lg_warehouses.id |
| `warehouse_id` | character varying | YES |  |  → lg_warehouses.id |
| `status` | character varying | NO |  |   |
| `adr_class` | character varying | YES |  |   |
| `model` | character varying | YES |  |   |
| `brand` | character varying | YES |  |   |
| `vehicle_type` | character varying | YES |  |   |
| `plate` | character varying | NO |  |   |
| `tenant_id` | character varying | NO |  |  → tenants.id |
| `id` | character varying | NO |  | PK  |

**Foreign Keys:**
- `tenant_id` → `tenants.id`
- `warehouse_id` → `lg_warehouses.id`
- `mobile_warehouse_id` → `lg_warehouses.id`

**Indexes (5):**
- `ix_lg_vehicles_tenant_id` (btree) on `tenant_id`
- `uq_lg_vehicle_tenant_plate` (btree) on `tenant_id`
- `uq_lg_vehicle_tenant_plate` (btree) on `plate`
- `lg_vehicles_pkey` (btree) on `id`
- `ix_lg_vehicles_warehouse_id` (btree) on `warehouse_id`

---

### `lg_warehouses`
Columnas: 11 | FKs: 1 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `updated_at` | timestamp with time zone | NO |  |   |
| `created_at` | timestamp with time zone | NO |  |   |
| `is_active` | boolean | NO |  |   |
| `warehouse_type` | character varying | NO | 'FIXED'::character varying |   |
| `branch_id` | character varying | YES |  |   |
| `phone` | character varying | YES |  |   |
| `address` | character varying | YES |  |   |
| `code` | character varying | NO |  |   |
| `name` | character varying | NO |  |   |
| `tenant_id` | character varying | NO |  |  → tenants.id |
| `id` | character varying | NO |  | PK  |

**Foreign Keys:**
- `tenant_id` → `tenants.id`

**Indexes (4):**
- `uq_lg_warehouse_tenant_code` (btree) on `tenant_id`
- `lg_warehouses_pkey` (btree) on `id`
- `uq_lg_warehouse_tenant_code` (btree) on `code`
- `ix_lg_warehouses_tenant_id` (btree) on `tenant_id`

---

### `lg_zones`
Columnas: 6 | FKs: 1 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `created_at` | timestamp with time zone | NO |  |   |
| `is_active` | boolean | NO |  |   |
| `code` | character varying | NO |  |   |
| `name` | character varying | NO |  |   |
| `tenant_id` | character varying | NO |  |  → tenants.id |
| `id` | character varying | NO |  | PK  |

**Foreign Keys:**
- `tenant_id` → `tenants.id`

**Indexes (4):**
- `lg_zones_pkey` (btree) on `id`
- `uq_lg_zone_tenant_code` (btree) on `tenant_id`
- `uq_lg_zone_tenant_code` (btree) on `code`
- `ix_lg_zones_tenant_id` (btree) on `tenant_id`

---

## Logistics - Sesiones de vehiculo

### `lg_session_reconciliations`
Columnas: 11 | FKs: 4 | Filas: 2

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `updated_at` | timestamp with time zone | NO |  |   |
| `created_at` | timestamp with time zone | NO |  |   |
| `closed_at` | timestamp with time zone | YES |  |   |
| `counted_at` | timestamp with time zone | YES |  |   |
| `notes` | text | YES |  |   |
| `closed_by` | character varying | YES |  |  → users.id |
| `counted_by` | character varying | YES |  |  → users.id |
| `status` | character varying | NO | 'MATCHED'::character varying |   |
| `session_id` | character varying | NO |  |  → lg_vehicle_sessions.id |
| `tenant_id` | character varying | NO |  |  → tenants.id |
| `id` | character varying | NO |  | PK  |

**Foreign Keys:**
- `tenant_id` → `tenants.id`
- `session_id` → `lg_vehicle_sessions.id`
- `counted_by` → `users.id`
- `closed_by` → `users.id`

---

### `lg_session_waybill_versions`
Columnas: 18 | FKs: 4 | Filas: 2

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `updated_at` | timestamp with time zone | NO |  |   |
| `created_at` | timestamp with time zone | NO |  |   |
| `snapshot_schema_version` | integer | NO | 1 |   |
| `generated_at` | timestamp with time zone | NO |  |   |
| `version` | integer | NO |  |   |
| `idempotency_key` | character varying | YES |  |   |
| `change_reason` | text | NO |  |   |
| `change_event` | character varying | NO |  |   |
| `snapshot_json` | text | NO |  |   |
| `movement_ids_json` | text | NO | '[]'::text |   |
| `operational_hash` | character varying | NO |  |   |
| `generated_by` | character varying | YES |  |  → users.id |
| `regulatory_context` | character varying | NO | 'ES_HACIENDA'::character va... |   |
| `status` | character varying | NO | 'ACTIVE'::character varying |   |
| `previous_version_id` | character varying | YES |  |  → lg_session_waybill_versions.id |
| `session_id` | character varying | NO |  |  → lg_vehicle_sessions.id |
| `tenant_id` | character varying | NO |  |  → tenants.id |
| `id` | character varying | NO |  | PK  |

**Foreign Keys:**
- `tenant_id` → `tenants.id`
- `session_id` → `lg_vehicle_sessions.id`
- `previous_version_id` → `lg_session_waybill_versions.id`
- `generated_by` → `users.id`

**Indexes (9):**
- `ix_lg_session_waybill_versions_previous` (btree) on `previous_version_id`
- `ix_lg_waybill_active_sess_ver` (btree) on `version`
- `ix_lg_session_waybill_versions_status` (btree) on `status`
- `lg_session_waybill_versions_pkey` (btree) on `id`
- `ix_lg_session_waybill_versions_idempotency` (btree) on `idempotency_key`

---

### `lg_vehicle_location_events`
Columnas: 16 | FKs: 6 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `recorded_at` | timestamp with time zone | NO |  |   |
| `accuracy_meters` | numeric | YES |  |   |
| `heading` | numeric | YES |  |   |
| `speed` | numeric | YES |  |   |
| `lng` | numeric | NO |  |   |
| `lat` | numeric | NO |  |   |
| `created_at` | timestamp with time zone | NO |  |   |
| `received_at` | timestamp with time zone | NO |  |   |
| `source` | character varying | NO |  |   |
| `driver_id` | character varying | NO |  |  → users.id |
| `vehicle_id` | character varying | NO |  |  → lg_vehicles.id |
| `route_id` | character varying | YES |  |  → lg_routes.id |
| `session_id` | character varying | NO |  |  → lg_vehicle_sessions.id |
| `branch_id` | character varying | YES |  |  → branches.id |
| `tenant_id` | character varying | NO |  |  → tenants.id |
| `id` | character varying | NO |  | PK  |

**Foreign Keys:**
- `tenant_id` → `tenants.id`
- `branch_id` → `branches.id`
- `session_id` → `lg_vehicle_sessions.id`
- `route_id` → `lg_routes.id`
- `vehicle_id` → `lg_vehicles.id`
- `driver_id` → `users.id`

**Indexes (10):**
- `ix_lg_vehicle_location_events_vehicle_recorded_at` (btree) on `vehicle_id`
- `ix_lg_vehicle_location_events_route_recorded_at` (btree) on `route_id`
- `ix_lg_vehicle_location_events_route_recorded_at` (btree) on `tenant_id`
- `ix_lg_vehicle_location_events_session_recorded_at` (btree) on `tenant_id`
- `ix_lg_vehicle_location_events_session_recorded_at` (btree) on `recorded_at`

---

### `lg_vehicle_sessions`
Columnas: 21 | FKs: 9 | Filas: 2

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `updated_at` | timestamp with time zone | NO |  |   |
| `created_at` | timestamp with time zone | NO |  |   |
| `loaded_weight_kg` | numeric | YES |  |   |
| `planned_weight_kg` | numeric | YES |  |   |
| `closed_at` | timestamp with time zone | YES |  |   |
| `returned_at` | timestamp with time zone | YES |  |   |
| `departed_at` | timestamp with time zone | YES |  |   |
| `ready_at` | timestamp with time zone | YES |  |   |
| `opened_at` | timestamp with time zone | NO |  |   |
| `updated_by` | character varying | NO |  |  → users.id |
| `created_by` | character varying | NO |  |  → users.id |
| `closing_notes` | text | YES |  |   |
| `status` | character varying | NO | 'DRAFT'::character varying |   |
| `route_id` | character varying | YES |  |  → lg_routes.id |
| `mobile_warehouse_id` | character varying | NO |  |  → lg_warehouses.id |
| `origin_warehouse_id` | character varying | NO |  |  → lg_warehouses.id |
| `driver_id` | character varying | NO |  |  → users.id |
| `vehicle_id` | character varying | NO |  |  → lg_vehicles.id |
| `branch_id` | character varying | YES |  |  → branches.id |
| `tenant_id` | character varying | NO |  |  → tenants.id |
| `id` | character varying | NO |  | PK  |

**Foreign Keys:**
- `tenant_id` → `tenants.id`
- `branch_id` → `branches.id`
- `vehicle_id` → `lg_vehicles.id`
- `driver_id` → `users.id`
- `origin_warehouse_id` → `lg_warehouses.id`
- `mobile_warehouse_id` → `lg_warehouses.id`
- `route_id` → `lg_routes.id`
- `created_by` → `users.id`
- `updated_by` → `users.id`

**Indexes (9):**
- `lg_vehicle_sessions_pkey` (btree) on `id`
- `ix_lg_vs_tenant_vehicle_active` (btree) on `vehicle_id`
- `ix_lg_vehicle_sessions_status` (btree) on `status`
- `ix_lg_vehicle_sessions_tenant` (btree) on `tenant_id`
- `ix_lg_vehicle_sessions_vehicle` (btree) on `vehicle_id`

---

## Logistics - Envases / Cilindros

### `lg_cylinder_average_weights`
Columnas: 12 | FKs: 2 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `updated_at` | timestamp without time zone | NO | now() |   |
| `created_at` | timestamp without time zone | NO | now() |   |
| `is_active` | boolean | NO | true |   |
| `weight_kg` | numeric | NO |  |   |
| `capacity_kg` | numeric | YES |  |   |
| `created_by` | character varying | NO |  |  → users.id |
| `material` | character varying | YES |  |   |
| `condition` | character varying | YES |  |   |
| `gas_group_id` | character varying | YES |  |   |
| `brand_id` | character varying | YES |  |   |
| `tenant_id` | character varying | NO |  |  → tenants.id |
| `id` | character varying | NO |  | PK  |

**Foreign Keys:**
- `tenant_id` → `tenants.id`
- `created_by` → `users.id`

---

### `lg_cylinder_contract_history`
Columnas: 7 | FKs: 2 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `occurred_at` | timestamp without time zone | NO | now() |   |
| `created_by` | character varying | YES |  |   |
| `description` | character varying | YES |  |   |
| `event_type` | character varying | NO |  |   |
| `contract_id` | character varying | NO |  |  → lg_cylinder_contracts.id |
| `tenant_id` | character varying | NO |  |  → tenants.id |
| `id` | character varying | NO |  | PK  |

**Foreign Keys:**
- `tenant_id` → `tenants.id`
- `contract_id` → `lg_cylinder_contracts.id`

---

### `lg_cylinder_contracts`
Columnas: 34 | FKs: 4 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `cancelled_at` | timestamp without time zone | YES |  |   |
| `signed_flag` | boolean | NO | false |   |
| `number` | integer | YES |  |   |
| `document_type_code` | integer | NO | 4 |   |
| `terminated_at` | timestamp without time zone | YES |  |   |
| `updated_at` | timestamp without time zone | NO | now() |   |
| `created_at` | timestamp without time zone | NO | now() |   |
| `is_active` | boolean | NO | true |   |
| `signed_at` | timestamp without time zone | YES |  |   |
| `unit_price` | numeric | NO |  |   |
| `quantity` | integer | NO |  |   |
| `end_date` | date | YES |  |   |
| `start_date` | date | NO |  |   |
| `customer_snapshot` | json | YES |  |   |
| `observations` | text | YES |  |   |
| `contract_file_path` | character varying | YES |  |   |
| `series` | character varying | YES |  |   |
| `document_prefix` | character varying | NO | 'CT'::character varying |   |
| `warehouse_id` | character varying | YES |  |   |
| `termination_reason` | text | YES |  |   |
| `created_by` | character varying | NO |  |  → users.id |
| `notes` | text | YES |  |   |
| `signature_type` | character varying | YES |  |   |
| `signed_by` | character varying | YES |  |   |
| `cylinder_condition` | character varying | YES |  |   |
| `cylinder_type_id` | character varying | YES |  |   |
| `renewal_type` | character varying | YES |  |   |
| `customer_id` | character varying | NO |  |  → crm_customers.id |
| `status` | character varying | NO | 'DRAFT'::character varying |   |
| `contract_type` | character varying | NO |  |   |
| `contract_number` | character varying | YES |  |   |
| `branch_id` | character varying | YES |  |  → branches.id |
| `tenant_id` | character varying | NO |  |  → tenants.id |
| `id` | character varying | NO |  | PK  |

**Foreign Keys:**
- `tenant_id` → `tenants.id`
- `branch_id` → `branches.id`
- `customer_id` → `crm_customers.id`
- `created_by` → `users.id`

**Indexes (9):**
- `uq_lg_cylinder_contracts_series_number` (btree) on `series`
- `ix_lg_cylinder_contracts_tenant_id` (btree) on `tenant_id`
- `ix_lg_cylinder_contracts_customer_id` (btree) on `customer_id`
- `lg_cylinder_contracts_pkey` (btree) on `id`
- `uq_lg_cylinder_contracts_series_number` (btree) on `tenant_id`

---

### `lg_cylinder_events`
Columnas: 14 | FKs: 6 | Filas: 3057

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `created_at` | timestamp with time zone | NO | now() |   |
| `occurred_at` | timestamp with time zone | NO |  |   |
| `created_by` | character varying | NO |  |  → users.id |
| `source_id` | character varying | YES |  |   |
| `source_type` | character varying | NO |  |   |
| `customer_id` | character varying | YES |  |  → crm_customers.id |
| `session_id` | character varying | YES |  |  → lg_vehicle_sessions.id |
| `warehouse_id` | character varying | YES |  |  → lg_warehouses.id |
| `location_id` | character varying | NO |  |   |
| `location_type` | character varying | NO |  |   |
| `event_type` | character varying | NO |  |   |
| `cylinder_id` | character varying | NO |  |  → lg_cylinders.id |
| `tenant_id` | character varying | NO |  |  → tenants.id |
| `id` | character varying | NO |  | PK  |

**Foreign Keys:**
- `tenant_id` → `tenants.id`
- `cylinder_id` → `lg_cylinders.id`
- `warehouse_id` → `lg_warehouses.id`
- `session_id` → `lg_vehicle_sessions.id`
- `customer_id` → `crm_customers.id`
- `created_by` → `users.id`

**Indexes (10):**
- `ix_lg_cylinder_events_session` (btree) on `session_id`
- `ix_lg_cylinder_events_session` (btree) on `occurred_at`
- `ix_lg_cylinder_events_warehouse` (btree) on `occurred_at`
- `ix_lg_cylinder_events_cylinder_time` (btree) on `created_at`
- `ix_lg_cylinder_events_warehouse` (btree) on `warehouse_id`

---

### `lg_cylinder_label_history`
Columnas: 9 | FKs: 2 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `created_at` | timestamp with time zone | NO |  |   |
| `printed_at` | timestamp with time zone | NO |  |   |
| `copies` | integer | NO |  |   |
| `printed_by` | character varying | NO |  |  → users.id |
| `printer_name` | character varying | YES |  |   |
| `reason` | character varying | YES |  |   |
| `origin` | character varying | NO |  |   |
| `cylinder_id` | character varying | NO |  |  → lg_cylinders.id |
| `id` | character varying | NO |  | PK  |

**Foreign Keys:**
- `cylinder_id` → `lg_cylinders.id`
- `printed_by` → `users.id`

---

### `lg_cylinder_ownership`
Columnas: 10 | FKs: 3 | Filas: 1

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `created_at` | timestamp with time zone | NO |  |   |
| `change_date` | timestamp with time zone | NO |  |   |
| `created_by` | character varying | NO |  |  → users.id |
| `notes` | text | YES |  |   |
| `condition` | character varying | YES |  |   |
| `movement_id` | character varying | YES |  |  → lg_movements.id |
| `customer_name` | character varying | YES |  |   |
| `customer_id` | character varying | YES |  |   |
| `cylinder_id` | character varying | NO |  |  → lg_cylinders.id |
| `id` | character varying | NO |  | PK  |

**Foreign Keys:**
- `cylinder_id` → `lg_cylinders.id`
- `movement_id` → `lg_movements.id`
- `created_by` → `users.id`

**Indexes (5):**
- `ix_lg_cylinder_ownership_created_by` (btree) on `created_by`
- `ix_lg_cylinder_ownership_customer_id` (btree) on `customer_id`
- `lg_cylinder_ownership_pkey` (btree) on `id`
- `ix_lg_cylinder_ownership_movement_id` (btree) on `movement_id`
- `ix_lg_cylinder_ownership_cylinder_id` (btree) on `cylinder_id`

---

### `lg_cylinder_retimbrados`
Columnas: 25 | FKs: 3 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `test_pressure` | numeric | YES |  |   |
| `service_pressure` | numeric | YES |  |   |
| `weight_current` | numeric | YES |  |   |
| `weight_origin` | numeric | YES |  |   |
| `manufacture_year` | integer | YES |  |   |
| `retimbrado_date` | date | NO |  |   |
| `updated_at` | timestamp with time zone | NO |  |   |
| `created_at` | timestamp with time zone | NO |  |   |
| `transport_code` | integer | YES |  |   |
| `danger_class` | character varying | YES |  |   |
| `approval_number` | character varying | YES |  |   |
| `serial_number` | character varying | YES |  |   |
| `manufacture_code` | character varying | YES |  |   |
| `cylinder_id` | character varying | NO |  |  → lg_cylinders.id |
| `id` | character varying | NO |  | PK  |
| `created_by` | character varying | NO |  |  → users.id |
| `notes` | text | YES |  |   |
| `movement_id` | character varying | YES |  |  → lg_movements.id |
| `food_registry` | character varying | YES |  |   |
| `un_number` | character varying | YES |  |   |
| `adr_tunnel` | character varying | YES |  |   |
| `adr_label` | character varying | YES |  |   |
| `package_format` | character varying | YES |  |   |
| `marking2` | character varying | YES |  |   |
| `marking1` | character varying | YES |  |   |

**Foreign Keys:**
- `cylinder_id` → `lg_cylinders.id`
- `movement_id` → `lg_movements.id`
- `created_by` → `users.id`

**Indexes (4):**
- `ix_lg_cylinder_retimbrados_created_by` (btree) on `created_by`
- `lg_cylinder_retimbrados_pkey` (btree) on `id`
- `ix_lg_cylinder_retimbrados_movement_id` (btree) on `movement_id`
- `ix_lg_cylinder_retimbrados_cylinder_id` (btree) on `cylinder_id`

---

### `lg_cylinder_services`
Columnas: 21 | FKs: 6 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `start_date` | timestamp with time zone | YES |  |   |
| `updated_at` | timestamp with time zone | NO |  |   |
| `created_at` | timestamp with time zone | NO |  |   |
| `total_amount` | numeric | YES |  |   |
| `discount_amount` | numeric | YES |  |   |
| `discount_pct` | numeric | YES |  |   |
| `stock_out` | numeric | YES |  |   |
| `stock_in` | numeric | YES |  |   |
| `sale_price` | numeric | YES |  |   |
| `purchase_price` | numeric | YES |  |   |
| `end_date` | timestamp with time zone | YES |  |   |
| `status` | character varying | NO |  |   |
| `service_type_id` | character varying | NO |  |  → lg_service_types.id |
| `movement_id` | character varying | YES |  |  → lg_movements.id |
| `order_item_id` | character varying | YES |  |  → lg_order_items.id |
| `order_id` | character varying | YES |  |  → lg_orders.id |
| `cylinder_id` | character varying | NO |  |  → lg_cylinders.id |
| `id` | character varying | NO |  | PK  |
| `created_by` | character varying | NO |  |  → users.id |
| `group_code` | character varying | YES |  |   |
| `notes` | text | YES |  |   |

**Foreign Keys:**
- `cylinder_id` → `lg_cylinders.id`
- `order_id` → `lg_orders.id`
- `order_item_id` → `lg_order_items.id`
- `movement_id` → `lg_movements.id`
- `service_type_id` → `lg_service_types.id`
- `created_by` → `users.id`

**Indexes (7):**
- `ix_lg_cylinder_services_order_id` (btree) on `order_id`
- `lg_cylinder_services_pkey` (btree) on `id`
- `ix_lg_cylinder_services_created_by` (btree) on `created_by`
- `ix_lg_cylinder_services_movement_id` (btree) on `movement_id`
- `ix_lg_cylinder_services_service_type_id` (btree) on `service_type_id`

---

### `lg_cylinder_state_log`
Columnas: 12 | FKs: 3 | Filas: 80

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `created_at` | timestamp with time zone | NO |  |   |
| `metadata_json` | json | NO |  |   |
| `id` | serial | NO |  | PK  |
| `notes` | text | YES |  |   |
| `reason_code` | character varying | YES |  |   |
| `origin` | character varying | YES |  |   |
| `movement_id` | character varying | YES |  |   |
| `changed_by` | character varying | NO |  |  → users.id |
| `to_state` | character varying | NO |  |   |
| `from_state` | character varying | YES |  |   |
| `cylinder_id` | character varying | NO |  |  → lg_cylinders.id |
| `tenant_id` | character varying | NO |  |  → tenants.id |

**Foreign Keys:**
- `tenant_id` → `tenants.id`
- `cylinder_id` → `lg_cylinders.id`
- `changed_by` → `users.id`

**Indexes (7):**
- `ix_lg_cylinder_state_log_changed_by` (btree) on `changed_by`
- `ix_lg_cyl_log_cyl_created` (btree) on `created_at`
- `ix_lg_cylinder_state_log_tenant_id` (btree) on `tenant_id`
- `ix_lg_cylinder_state_log_cylinder_id` (btree) on `cylinder_id`
- `ix_lg_cylinder_state_log_created_at` (btree) on `created_at`

---

### `lg_cylinder_states`
Columnas: 3 | FKs: 0 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `is_final` | boolean | NO |  |   |
| `description` | text | YES |  |   |
| `code` | character varying | NO |  | PK  |

---

### `lg_cylinder_warranties`
Columnas: 12 | FKs: 3 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `updated_at` | timestamp with time zone | NO |  |   |
| `created_at` | timestamp with time zone | NO |  |   |
| `return_date` | timestamp with time zone | YES |  |   |
| `created_by` | character varying | NO |  |  → users.id |
| `description` | text | YES |  |   |
| `status` | character varying | NO |  |   |
| `warranty_type` | character varying | NO |  |   |
| `customer_name` | character varying | NO |  |   |
| `customer_id` | character varying | YES |  |   |
| `cylinder_id` | character varying | NO |  |  → lg_cylinders.id |
| `tenant_id` | character varying | NO |  |  → tenants.id |
| `id` | character varying | NO |  | PK  |

**Foreign Keys:**
- `tenant_id` → `tenants.id`
- `cylinder_id` → `lg_cylinders.id`
- `created_by` → `users.id`

**Indexes (5):**
- `ix_lg_cylinder_warranties_customer_id` (btree) on `customer_id`
- `ix_lg_cylinder_warranties_created_by` (btree) on `created_by`
- `lg_cylinder_warranties_pkey` (btree) on `id`
- `ix_lg_cylinder_warranties_cylinder_id` (btree) on `cylinder_id`
- `ix_lg_cylinder_warranties_tenant_id` (btree) on `tenant_id`

---

### `lg_cylinders`
Columnas: 44 | FKs: 5 | Filas: 3050

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `adr_factor` | numeric | YES |  |   |
| `adr_weight_kg` | numeric | YES |  |   |
| `is_service` | boolean | NO |  |   |
| `price` | numeric | YES |  |   |
| `cost` | numeric | YES |  |   |
| `volume_m3` | numeric | YES |  |   |
| `content_kg` | numeric | YES |  |   |
| `updated_at` | timestamp with time zone | NO |  |   |
| `created_at` | timestamp with time zone | NO |  |   |
| `is_active` | boolean | NO |  |   |
| `next_hydrotest_date` | date | YES |  |   |
| `last_hydrotest_date` | date | YES |  |   |
| `weight_current` | numeric | YES |  |   |
| `weight_origin` | numeric | YES |  |   |
| `manufacture_year` | integer | YES |  |   |
| `manufacturer_date` | date | YES |  |   |
| `is_medical` | boolean | NO | false |   |
| `adr_points` | integer | YES |  |   |
| `adr_subline` | character varying | YES |  |   |
| `adr_tunnel` | character varying | YES |  |   |
| `adr_merchandise` | character varying | YES |  |   |
| `adr_package_type` | character varying | YES |  |   |
| `box_number` | character varying | YES |  |   |
| `country_code` | character varying | YES |  |   |
| `brand_id` | character varying | YES |  |   |
| `gas_group_id` | character varying | YES |  |   |
| `barcode2` | character varying | YES |  |   |
| `barcode1` | character varying | YES |  |   |
| `description` | character varying | YES |  |   |
| `location` | character varying | YES |  |   |
| `adr_label` | character varying | YES |  |   |
| `adr_un_number` | character varying | YES |  |   |
| `adr_category` | character varying | YES |  |   |
| `manufacturer_code` | character varying | YES |  |   |
| `current_state` | character varying | NO |  |  → lg_cylinder_states.code |
| `serial` | character varying | NO |  |   |
| `branch_id` | character varying | YES |  |  → branches.id |
| `tenant_id` | character varying | NO |  |  → tenants.id |
| `id` | character varying | NO |  | PK  |
| `session_id` | character varying | YES |  |  → lg_vehicle_sessions.id |
| `medical_notes` | text | YES |  |   |
| `product_id` | character varying | YES |  |  → prod_products.id |
| `condition` | character varying | YES |  |   |
| `adr_unit_measure` | character varying | YES |  |   |

**Foreign Keys:**
- `tenant_id` → `tenants.id`
- `branch_id` → `branches.id`
- `current_state` → `lg_cylinder_states.code`
- `product_id` → `prod_products.id`
- `session_id` → `lg_vehicle_sessions.id`

**Indexes (27):**
- `lg_cylinders_pkey` (btree) on `id`
- `ix_lg_cyl_barcode2_trgm` (gin) on `barcode2`
- `uq_lg_cylinder_tenant_barcode1_idx` (btree) on `barcode1`
- `ix_lg_cyl_active_prod_state_ser` (btree) on `serial`
- `ix_lg_cylinders_condition` (btree) on `condition`

---

### `lg_equipment`
Columnas: 7 | FKs: 0 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `updated_at` | timestamp without time zone | YES |  |   |
| `created_at` | timestamp without time zone | YES |  |   |
| `is_active` | boolean | NO | true |   |
| `equipment_type` | character varying | YES |  |   |
| `name` | character varying | NO |  |   |
| `tenant_id` | character varying | NO |  |   |
| `id` | character varying | NO |  | PK  |

---

### `lg_scan_log`
Columnas: 15 | FKs: 4 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `created_at` | timestamp with time zone | NO |  |   |
| `scanned_at` | timestamp with time zone | NO |  |   |
| `hydrotest_validated` | boolean | NO |  |   |
| `adr_validated` | boolean | NO |  |   |
| `gps_lng` | numeric | YES |  |   |
| `gps_lat` | numeric | YES |  |   |
| `error_reason` | text | YES |  |   |
| `result` | character varying | NO |  |   |
| `user_id` | character varying | NO |  |  → users.id |
| `service_type` | character varying | NO |  |   |
| `barcode_scanned` | character varying | NO |  |   |
| `cylinder_id` | character varying | YES |  |  → lg_cylinders.id |
| `movement_id` | character varying | YES |  |  → lg_movements.id |
| `tenant_id` | character varying | NO |  |  → tenants.id |
| `id` | character varying | NO |  | PK  |

**Foreign Keys:**
- `tenant_id` → `tenants.id`
- `movement_id` → `lg_movements.id`
- `cylinder_id` → `lg_cylinders.id`
- `user_id` → `users.id`

**Indexes (6):**
- `ix_lg_scan_log_tenant_id` (btree) on `tenant_id`
- `ix_lg_scan_log_service_type` (btree) on `service_type`
- `ix_lg_scan_log_cylinder_id` (btree) on `cylinder_id`
- `ix_lg_scan_log_user_id` (btree) on `user_id`
- `lg_scan_log_pkey` (btree) on `id`

---

### `lg_service_types`
Columnas: 7 | FKs: 1 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `updated_at` | timestamp with time zone | NO |  |   |
| `created_at` | timestamp with time zone | NO |  |   |
| `is_active` | boolean | NO |  |   |
| `name` | character varying | NO |  |   |
| `code` | character varying | NO |  |   |
| `tenant_id` | character varying | NO |  |  → tenants.id |
| `id` | character varying | NO |  | PK  |

**Foreign Keys:**
- `tenant_id` → `tenants.id`

**Indexes (4):**
- `uq_lg_service_type_tenant_code` (btree) on `code`
- `ix_lg_service_types_tenant_id` (btree) on `tenant_id`
- `lg_service_types_pkey` (btree) on `id`
- `uq_lg_service_type_tenant_code` (btree) on `tenant_id`

---

### `lg_state_transitions`
Columnas: 6 | FKs: 2 | Filas: 35

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `requires_hydrotest` | boolean | NO |  |   |
| `requires_adr` | boolean | NO |  |   |
| `description` | text | YES |  |   |
| `to_state` | character varying | NO |  |  → lg_cylinder_states.code |
| `from_state` | character varying | NO |  |  → lg_cylinder_states.code |
| `id` | character varying | NO |  | PK  |

**Foreign Keys:**
- `from_state` → `lg_cylinder_states.code`
- `to_state` → `lg_cylinder_states.code`

**Indexes (5):**
- `lg_state_transitions_pkey` (btree) on `id`
- `uq_lg_state_transition_from_to` (btree) on `from_state`
- `ix_lg_state_transitions_from_state` (btree) on `from_state`
- `uq_lg_state_transition_from_to` (btree) on `to_state`
- `ix_lg_state_transitions_to_state` (btree) on `to_state`

---

## Logistics - Movimientos

### `lg_movement_equipment`
Columnas: 7 | FKs: 0 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `returned_at` | timestamp without time zone | YES |  |   |
| `assigned_at` | timestamp without time zone | YES |  |   |
| `notes` | text | YES |  |   |
| `equipment_id` | character varying | NO |  |   |
| `movement_id` | character varying | NO |  |   |
| `tenant_id` | character varying | NO |  |   |
| `id` | character varying | NO |  | PK  |

---

### `lg_movement_items`
Columnas: 17 | FKs: 2 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `created_at` | timestamp with time zone | NO |  |   |
| `discount` | numeric | NO |  |   |
| `total_item` | numeric | YES |  |   |
| `unit_price` | numeric | YES |  |   |
| `quantity_planned` | numeric | NO |  |   |
| `quantity` | integer | NO |  |   |
| `quantity_out` | numeric | NO |  |   |
| `quantity_in` | numeric | NO |  |   |
| `product_name` | character varying | YES |  |   |
| `product_id` | character varying | YES |  |   |
| `notes` | text | YES |  |   |
| `state_after` | character varying | YES |  |   |
| `state_before` | character varying | YES |  |   |
| `item_status` | character varying | NO |  |   |
| `cylinder_id` | character varying | YES |  |  → lg_cylinders.id |
| `movement_id` | character varying | NO |  |  → lg_movements.id |
| `id` | character varying | NO |  | PK  |

**Foreign Keys:**
- `movement_id` → `lg_movements.id`
- `cylinder_id` → `lg_cylinders.id`

---

### `lg_movement_status_history`
Columnas: 8 | FKs: 2 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `created_at` | timestamp with time zone | NO |  |   |
| `notes` | text | YES |  |   |
| `changed_by` | character varying | NO |  |  → users.id |
| `to_value` | character varying | NO |  |   |
| `from_value` | character varying | YES |  |   |
| `field_name` | character varying | NO |  |   |
| `movement_id` | character varying | NO |  |  → lg_movements.id |
| `id` | character varying | NO |  | PK  |

**Foreign Keys:**
- `movement_id` → `lg_movements.id`
- `changed_by` → `users.id`

---

### `lg_movement_types`
Columnas: 6 | FKs: 0 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `moves_cylinders` | boolean | NO |  |   |
| `target_state` | character varying | YES |  |   |
| `origin_state` | character varying | YES |  |   |
| `category` | character varying | NO |  |   |
| `name` | character varying | NO |  |   |
| `code` | character varying | NO |  | PK  |

---

### `lg_movements`
Columnas: 33 | FKs: 10 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `dispatched_at` | timestamp without time zone | YES |  |   |
| `updated_at` | timestamp with time zone | NO |  |   |
| `created_at` | timestamp with time zone | NO |  |   |
| `exchange_rate` | numeric | NO |  |   |
| `discount` | numeric | YES |  |   |
| `tax` | numeric | YES |  |   |
| `total` | numeric | YES |  |   |
| `last_stock_sync_error` | text | YES |  |   |
| `origin_movement_id` | character varying | YES |  |   |
| `created_by` | character varying | NO |  |  → users.id |
| `parent_movement_id` | character varying | YES |  |  → lg_movements.id |
| `notes` | text | YES |  |   |
| `destination_address` | character varying | YES |  |   |
| `destination_place` | character varying | YES |  |   |
| `plate` | character varying | YES |  |   |
| `carrier` | character varying | YES |  |   |
| `payment_status` | character varying | YES |  |   |
| `status` | character varying | NO |  |   |
| `currency` | character varying | NO |  |   |
| `vehicle_id` | character varying | YES |  |  → lg_vehicles.id |
| `driver_id` | character varying | YES |  |  → users.id |
| `warehouse_id` | character varying | YES |  |  → lg_warehouses.id |
| `customer_name` | character varying | YES |  |   |
| `customer_id` | character varying | YES |  |   |
| `route_id` | character varying | YES |  |  → lg_routes.id |
| `order_id` | character varying | YES |  |  → lg_orders.id |
| `full_document` | character varying | YES |  |   |
| `document_number` | character varying | YES |  |   |
| `document_series` | character varying | YES |  |   |
| `movement_type` | character varying | NO |  |  → lg_movement_types.code |
| `branch_id` | character varying | YES |  |  → branches.id |
| `tenant_id` | character varying | NO |  |  → tenants.id |
| `id` | character varying | NO |  | PK  |

**Foreign Keys:**
- `tenant_id` → `tenants.id`
- `branch_id` → `branches.id`
- `movement_type` → `lg_movement_types.code`
- `order_id` → `lg_orders.id`
- `route_id` → `lg_routes.id`
- `warehouse_id` → `lg_warehouses.id`
- `driver_id` → `users.id`
- `vehicle_id` → `lg_vehicles.id`
- `parent_movement_id` → `lg_movements.id`
- `created_by` → `users.id`

**Indexes (23):**
- `ix_lg_mov_tenant_wh_status_upd` (btree) on `warehouse_id`
- `ix_lg_mov_tenant_wh_status_upd` (btree) on `updated_at`
- `ix_lg_movements_movement_type` (btree) on `movement_type`
- `ix_mov_assigned` (btree) on `customer_id`
- `lg_movements_pkey` (btree) on `id`

---

## Logistics - Rutas y paradas

### `lg_delivery_points`
Columnas: 28 | FKs: 2 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `gps_coordinates` | json | YES |  |   |
| `demand_weight_kg` | numeric | YES |  |   |
| `demand_units` | integer | YES |  |   |
| `service_time_min` | integer | YES |  |   |
| `updated_at` | timestamp with time zone | NO |  |   |
| `created_at` | timestamp with time zone | NO |  |   |
| `is_active` | boolean | NO |  |   |
| `is_primary` | boolean | NO |  |   |
| `contact_role` | character varying | YES |  |   |
| `fiscal_operation_type` | character varying | YES |  |   |
| `fiscal_operation_document` | character varying | YES |  |   |
| `agent_user_id` | character varying | YES |  |   |
| `instructions` | character varying | YES |  |   |
| `time_window` | character varying | YES |  |   |
| `visit_day` | character varying | YES |  |   |
| `address_id` | character varying | YES |  |   |
| `warehouse_id` | character varying | YES |  |   |
| `contact_email` | character varying | YES |  |   |
| `gps_link` | character varying | YES |  |   |
| `delivery_day` | character varying | YES |  |   |
| `zone_id` | character varying | YES |  |  → lg_zones.id |
| `phone` | character varying | YES |  |   |
| `address` | character varying | NO |  |   |
| `contact_name` | character varying | YES |  |   |
| `customer_name` | character varying | NO |  |   |
| `customer_id` | character varying | YES |  |   |
| `tenant_id` | character varying | NO |  |  → tenants.id |
| `id` | character varying | NO |  | PK  |

**Foreign Keys:**
- `tenant_id` → `tenants.id`
- `zone_id` → `lg_zones.id`

**Indexes (4):**
- `ix_lg_delivery_points_tenant_id` (btree) on `tenant_id`
- `lg_delivery_points_pkey` (btree) on `id`
- `ix_lg_delivery_points_zone_id` (btree) on `zone_id`
- `ix_lg_delivery_points_customer_id` (btree) on `customer_id`

---

### `lg_route_control_states`
Columnas: 21 | FKs: 6 | Filas: 1

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `last_recorded_at` | timestamp with time zone | YES |  |   |
| `last_heading` | numeric | YES |  |   |
| `last_speed` | numeric | YES |  |   |
| `last_lng` | numeric | YES |  |   |
| `last_lat` | numeric | YES |  |   |
| `current_stop_index` | integer | YES |  |   |
| `active_stop_started_at` | timestamp with time zone | YES |  |   |
| `updated_at` | timestamp with time zone | NO |  |   |
| `next_stop_eta_minutes` | integer | YES |  |   |
| `off_route` | boolean | NO | false |   |
| `progress_percent` | numeric | NO | 0 |   |
| `total_stops` | integer | NO | 0 |   |
| `completed_stops` | integer | NO | 0 |   |
| `geofence_state` | character varying | YES |  |   |
| `status` | character varying | NO |  |   |
| `current_stop_id` | character varying | YES |  |  → lg_route_stops.id |
| `active_stop_id` | character varying | YES |  |  → lg_route_stops.id |
| `vehicle_id` | character varying | NO |  |  → lg_vehicles.id |
| `route_id` | character varying | YES |  |  → lg_routes.id |
| `tenant_id` | character varying | NO |  |  → tenants.id |
| `session_id` | character varying | NO |  | PK → lg_vehicle_sessions.id |

**Foreign Keys:**
- `session_id` → `lg_vehicle_sessions.id`
- `tenant_id` → `tenants.id`
- `route_id` → `lg_routes.id`
- `vehicle_id` → `lg_vehicles.id`
- `active_stop_id` → `lg_route_stops.id`
- `current_stop_id` → `lg_route_stops.id`

**Indexes (4):**
- `ix_lg_route_control_states_status` (btree) on `status`
- `ix_lg_route_control_states_route_id` (btree) on `route_id`
- `ix_lg_route_control_states_vehicle_id` (btree) on `vehicle_id`
- `lg_route_control_states_pkey` (btree) on `session_id`

---

### `lg_route_incidents`
Columnas: 14 | FKs: 7 | Filas: 2

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `updated_at` | timestamp with time zone | NO |  |   |
| `closed_at` | timestamp with time zone | YES |  |   |
| `created_at` | timestamp with time zone | NO |  |   |
| `created_by` | character varying | NO |  |  → users.id |
| `notes` | text | YES |  |   |
| `status` | character varying | NO | 'OPEN'::character varying |   |
| `type` | character varying | NO |  |   |
| `related_operation_id` | character varying | YES |  |  → lg_route_operations.id |
| `route_stop_id` | character varying | YES |  |  → lg_route_stops.id |
| `session_id` | character varying | NO |  |  → lg_vehicle_sessions.id |
| `tenant_id` | character varying | NO |  |  → tenants.id |
| `id` | character varying | NO |  | PK  |
| `corrective_operation_id` | character varying | YES |  |  → lg_route_operations.id |
| `closed_by` | character varying | YES |  |  → users.id |

**Foreign Keys:**
- `tenant_id` → `tenants.id`
- `session_id` → `lg_vehicle_sessions.id`
- `route_stop_id` → `lg_route_stops.id`
- `related_operation_id` → `lg_route_operations.id`
- `created_by` → `users.id`
- `closed_by` → `users.id`
- `corrective_operation_id` → `lg_route_operations.id`

**Indexes (12):**
- `ix_lg_route_incidents_stop` (btree) on `route_stop_id`
- `lg_route_incidents_pkey` (btree) on `id`
- `ix_lg_ri_sess_created` (btree) on `session_id`
- `ix_lg_ri_sess_stop_status` (btree) on `route_stop_id`
- `ix_lg_ri_sess_updated` (btree) on `session_id`

---

### `lg_route_operation_items`
Columnas: 7 | FKs: 2 | Filas: 3

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `created_at` | timestamp with time zone | NO |  |   |
| `quantity` | numeric | NO |  |   |
| `direction` | character varying | NO |  |   |
| `product_name` | character varying | NO |  |   |
| `product_id` | character varying | NO |  |  → prod_products.id |
| `route_operation_id` | character varying | NO |  |  → lg_route_operations.id |
| `id` | character varying | NO |  | PK  |

**Foreign Keys:**
- `route_operation_id` → `lg_route_operations.id`
- `product_id` → `prod_products.id`

---

### `lg_route_operations`
Columnas: 21 | FKs: 7 | Filas: 3

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `location_lng` | numeric | YES |  |   |
| `location_lat` | numeric | YES |  |   |
| `updated_at` | timestamp with time zone | NO |  |   |
| `created_at` | timestamp with time zone | NO |  |   |
| `performed_at` | timestamp with time zone | YES |  |   |
| `location_event_id` | character varying | YES |  |  → lg_vehicle_location_events.id |
| `warehouse_name_snapshot` | character varying | YES |  |   |
| `warehouse_id` | character varying | YES |  |  → lg_warehouses.id |
| `customer_name_snapshot` | character varying | YES |  |   |
| `customer_id` | character varying | YES |  |  → crm_customers.id |
| `context_type` | character varying | YES |  |   |
| `performed_by` | character varying | YES |  |  → users.id |
| `notes` | text | YES |  |   |
| `idempotency_key` | character varying | NO |  |   |
| `movement_ids_json` | text | NO | '[]'::text |   |
| `status` | character varying | NO | 'DRAFT'::character varying |   |
| `operation_type` | character varying | NO |  |   |
| `route_stop_id` | character varying | YES |  |  → lg_route_stops.id |
| `session_id` | character varying | NO |  |  → lg_vehicle_sessions.id |
| `tenant_id` | character varying | NO |  |  → tenants.id |
| `id` | character varying | NO |  | PK  |

**Foreign Keys:**
- `tenant_id` → `tenants.id`
- `session_id` → `lg_vehicle_sessions.id`
- `route_stop_id` → `lg_route_stops.id`
- `performed_by` → `users.id`
- `customer_id` → `crm_customers.id`
- `warehouse_id` → `lg_warehouses.id`
- `location_event_id` → `lg_vehicle_location_events.id`

**Indexes (18):**
- `lg_route_operations_pkey` (btree) on `id`
- `ix_lg_ro_conf_sess_stop_perf` (btree) on `route_stop_id`
- `ix_lg_route_operations_warehouse` (btree) on `warehouse_id`
- `ix_lg_ro_conf_sess_stop_perf` (btree) on `performed_at`
- `ix_lg_route_operations_type` (btree) on `operation_type`

---

### `lg_route_stop_results`
Columnas: 12 | FKs: 5 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `completion_percent` | numeric | NO | 0 |   |
| `updated_at` | timestamp with time zone | NO | now() |   |
| `created_at` | timestamp with time zone | NO | now() |   |
| `outcome_type` | character varying | NO |  |   |
| `status` | character varying | NO |  |   |
| `route_stop_id` | character varying | NO |  |  → lg_route_stops.id |
| `session_id` | character varying | NO |  |  → lg_vehicle_sessions.id |
| `tenant_id` | character varying | NO |  |  → tenants.id |
| `id` | character varying | NO |  | PK  |
| `updated_by` | character varying | NO |  |  → users.id |
| `created_by` | character varying | NO |  |  → users.id |
| `driver_note` | text | YES |  |   |

**Foreign Keys:**
- `tenant_id` → `tenants.id`
- `session_id` → `lg_vehicle_sessions.id`
- `route_stop_id` → `lg_route_stops.id`
- `created_by` → `users.id`
- `updated_by` → `users.id`

**Indexes (6):**
- `uq_lg_route_stop_results_session_stop` (btree) on `session_id`
- `uq_lg_route_stop_results_session_stop` (btree) on `route_stop_id`
- `ix_lg_route_stop_results_route_stop_id` (btree) on `route_stop_id`
- `ix_lg_route_stop_results_session_id` (btree) on `session_id`
- `lg_route_stop_results_pkey` (btree) on `id`

---

### `lg_route_stops`
Columnas: 14 | FKs: 3 | Filas: 5

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `gps_coordinates` | json | YES |  |   |
| `updated_at` | timestamp with time zone | NO |  |   |
| `created_at` | timestamp with time zone | NO |  |   |
| `departure_time` | timestamp with time zone | YES |  |   |
| `arrival_time` | timestamp with time zone | YES |  |   |
| `scheduled_time` | time without time zone | YES |  |   |
| `stop_order` | integer | NO |  |   |
| `customer_name_snapshot` | character varying | YES |  |   |
| `customer_id` | character varying | YES |  |  → crm_customers.id |
| `notes` | text | YES |  |   |
| `status` | character varying | NO |  |   |
| `delivery_point_id` | character varying | YES |  |  → lg_delivery_points.id |
| `route_id` | character varying | NO |  |  → lg_routes.id |
| `id` | character varying | NO |  | PK  |

**Foreign Keys:**
- `route_id` → `lg_routes.id`
- `delivery_point_id` → `lg_delivery_points.id`
- `customer_id` → `crm_customers.id`

**Indexes (6):**
- `ix_lg_route_stops_delivery_point_id` (btree) on `delivery_point_id`
- `lg_route_stops_pkey` (btree) on `id`
- `uq_lg_route_stop_order` (btree) on `stop_order`
- `ix_lg_route_stops_customer` (btree) on `customer_id`
- `ix_lg_route_stops_route_id` (btree) on `route_id`

---

### `lg_route_weekdays`
Columnas: 5 | FKs: 0 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `created_at` | timestamp without time zone | YES |  |   |
| `weekday` | integer | NO |  |   |
| `route_id` | character varying | NO |  |   |
| `tenant_id` | character varying | NO |  |   |
| `id` | character varying | NO |  | PK  |

---

### `lg_routes`
Columnas: 12 | FKs: 5 | Filas: 7

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `route_date` | date | NO |  |   |
| `gps_start_coordinates` | json | YES |  |   |
| `updated_at` | timestamp with time zone | NO |  |   |
| `created_at` | timestamp with time zone | NO |  |   |
| `notes` | text | YES |  |   |
| `status` | character varying | NO |  |   |
| `vehicle_id` | character varying | YES |  |  → lg_vehicles.id |
| `driver_id` | character varying | NO |  |  → users.id |
| `branch_id` | character varying | YES |  |  → branches.id |
| `tenant_id` | character varying | NO |  |  → tenants.id |
| `id` | character varying | NO |  | PK  |
| `created_by` | character varying | NO |  |  → users.id |

**Foreign Keys:**
- `tenant_id` → `tenants.id`
- `branch_id` → `branches.id`
- `driver_id` → `users.id`
- `vehicle_id` → `lg_vehicles.id`
- `created_by` → `users.id`

**Indexes (7):**
- `ix_lg_routes_route_date` (btree) on `route_date`
- `ix_lg_routes_tenant_id` (btree) on `tenant_id`
- `ix_lg_routes_branch_id` (btree) on `branch_id`
- `ix_lg_routes_driver_id` (btree) on `driver_id`
- `ix_lg_routes_vehicle_id` (btree) on `vehicle_id`

---

## Logistics - Operaciones en ruta

### `lg_logistics_operation_items`
Columnas: 8 | FKs: 2 | Filas: 2

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `created_at` | timestamp with time zone | NO |  |   |
| `weight_kg` | numeric | YES |  |   |
| `quantity` | numeric | NO |  |   |
| `notes` | text | YES |  |   |
| `product_name` | character varying | NO |  |   |
| `product_id` | character varying | NO |  |  → prod_products.id |
| `operation_id` | character varying | NO |  |  → lg_logistics_operations.id |
| `id` | character varying | NO |  | PK  |

**Foreign Keys:**
- `operation_id` → `lg_logistics_operations.id`
- `product_id` → `prod_products.id`

---

### `lg_logistics_operations`
Columnas: 14 | FKs: 4 | Filas: 3

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `updated_at` | timestamp with time zone | NO |  |   |
| `created_at` | timestamp with time zone | NO |  |   |
| `performed_at` | timestamp with time zone | YES |  |   |
| `movement_type` | character varying | NO |  |   |
| `route_stop_id` | character varying | YES |  |  → lg_route_stops.id |
| `session_id` | character varying | NO |  |  → lg_vehicle_sessions.id |
| `tenant_id` | character varying | NO |  |  → tenants.id |
| `id` | character varying | NO |  | PK  |
| `evidence_json` | text | YES |  |   |
| `notes` | text | YES |  |   |
| `performed_by` | character varying | YES |  |  → users.id |
| `idempotency_key` | character varying | NO |  |   |
| `external_movement_id` | character varying | YES |  |   |
| `status` | character varying | NO | 'DRAFT'::character varying |   |

**Foreign Keys:**
- `tenant_id` → `tenants.id`
- `session_id` → `lg_vehicle_sessions.id`
- `route_stop_id` → `lg_route_stops.id`
- `performed_by` → `users.id`

---

### `lg_reception_incidents`
Columnas: 8 | FKs: 0 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `created_at` | timestamp without time zone | YES |  |   |
| `created_by` | character varying | NO |  |   |
| `description` | text | YES |  |   |
| `reason_code` | character varying | NO |  |   |
| `cylinder_id` | character varying | YES |  |   |
| `movement_id` | character varying | NO |  |   |
| `tenant_id` | character varying | NO |  |   |
| `id` | character varying | NO |  | PK  |

---

## Logistics - Carga y planificacion

### `lg_load_plan_items`
Columnas: 9 | FKs: 3 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `created_at` | timestamp with time zone | NO |  |   |
| `planned_weight_kg` | numeric | YES |  |   |
| `planned_quantity` | numeric | NO |  |   |
| `id` | character varying | NO |  | PK  |
| `notes` | text | YES |  |   |
| `source_warehouse_id` | character varying | NO |  |  → lg_warehouses.id |
| `product_name` | character varying | NO |  |   |
| `product_id` | character varying | NO |  |  → prod_products.id |
| `load_plan_id` | character varying | NO |  |  → lg_load_plans.id |

**Foreign Keys:**
- `load_plan_id` → `lg_load_plans.id`
- `product_id` → `prod_products.id`
- `source_warehouse_id` → `lg_warehouses.id`

**Indexes (4):**
- `ix_lg_load_plan_items_plan` (btree) on `load_plan_id`
- `lg_load_plan_items_pkey` (btree) on `id`
- `ix_lg_lpi_plan_product` (btree) on `product_id`
- `ix_lg_lpi_plan_product` (btree) on `load_plan_id`

---

### `lg_load_plans`
Columnas: 8 | FKs: 3 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `updated_at` | timestamp with time zone | NO |  |   |
| `created_at` | timestamp with time zone | NO |  |   |
| `created_by` | character varying | NO |  |  → users.id |
| `notes` | text | YES |  |   |
| `status` | character varying | NO | 'DRAFT'::character varying |   |
| `session_id` | character varying | NO |  |  → lg_vehicle_sessions.id |
| `tenant_id` | character varying | NO |  |  → tenants.id |
| `id` | character varying | NO |  | PK  |

**Foreign Keys:**
- `tenant_id` → `tenants.id`
- `session_id` → `lg_vehicle_sessions.id`
- `created_by` → `users.id`

**Indexes (4):**
- `ix_lg_lp_session_updated` (btree) on `updated_at`
- `ix_lg_lp_session_updated` (btree) on `session_id`
- `lg_load_plans_pkey` (btree) on `id`
- `ix_lg_load_plans_session` (btree) on `session_id`

---

### `lg_load_serial_assignments`
Columnas: 15 | FKs: 6 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `updated_at` | timestamp with time zone | NO |  |   |
| `released_at` | timestamp with time zone | YES |  |   |
| `confirmed_at` | timestamp with time zone | YES |  |   |
| `selected_at` | timestamp with time zone | NO |  |   |
| `session_id` | character varying | NO |  |  → lg_vehicle_sessions.id |
| `tenant_id` | character varying | NO |  |  → tenants.id |
| `id` | character varying | NO |  | PK  |
| `notes` | text | YES |  |   |
| `release_reason` | character varying | YES |  |   |
| `confirmed_by_operation_id` | character varying | YES |  |  → lg_logistics_operations.id |
| `selected_by` | character varying | NO |  |  → users.id |
| `assignment_status` | character varying | NO |  |   |
| `cylinder_serial` | character varying | NO |  |   |
| `cylinder_id` | character varying | NO |  |  → lg_cylinders.id |
| `product_id` | character varying | NO |  |  → prod_products.id |

**Foreign Keys:**
- `tenant_id` → `tenants.id`
- `session_id` → `lg_vehicle_sessions.id`
- `product_id` → `prod_products.id`
- `cylinder_id` → `lg_cylinders.id`
- `selected_by` → `users.id`
- `confirmed_by_operation_id` → `lg_logistics_operations.id`

**Indexes (12):**
- `ix_lg_lsa_sess_status_sel` (btree) on `selected_at`
- `ix_lg_load_serial_assignments_cylinder_id` (btree) on `cylinder_id`
- `ix_lg_load_serial_assignments_status` (btree) on `assignment_status`
- `ux_lg_load_serial_assignments_cylinder_active` (btree) on `cylinder_id`
- `ix_lg_lsa_active_sess_prod_sel` (btree) on `selected_at`

---

### `lg_loads`
Columnas: 10 | FKs: 3 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `updated_at` | timestamp with time zone | NO |  |   |
| `created_at` | timestamp with time zone | NO |  |   |
| `unloaded_at` | timestamp with time zone | YES |  |   |
| `loaded_at` | timestamp with time zone | YES |  |   |
| `notes` | text | YES |  |   |
| `status` | character varying | NO |  |   |
| `stop_id` | character varying | YES |  |  → lg_route_stops.id |
| `cylinder_id` | character varying | NO |  |  → lg_cylinders.id |
| `route_id` | character varying | NO |  |  → lg_routes.id |
| `id` | character varying | NO |  | PK  |

**Foreign Keys:**
- `route_id` → `lg_routes.id`
- `cylinder_id` → `lg_cylinders.id`
- `stop_id` → `lg_route_stops.id`

**Indexes (6):**
- `lg_loads_pkey` (btree) on `id`
- `ix_lg_loads_cylinder_id` (btree) on `cylinder_id`
- `ix_lg_loads_stop_id` (btree) on `stop_id`
- `ix_lg_loads_route_id` (btree) on `route_id`
- `uq_lg_load_route_cylinder` (btree) on `cylinder_id`

---

### `lg_plan_preload_items`
Columnas: 9 | FKs: 0 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `created_at` | timestamp without time zone | YES |  |   |
| `quantity_loaded` | numeric | NO | 0 |   |
| `quantity_planned` | numeric | NO | 0 |   |
| `product_name` | character varying | YES |  |   |
| `product_id` | character varying | NO |  |   |
| `order_item_id` | character varying | NO |  |   |
| `preload_id` | character varying | NO |  |   |
| `tenant_id` | character varying | NO |  |   |
| `id` | character varying | NO |  | PK  |

---

### `lg_plan_preloads`
Columnas: 10 | FKs: 0 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `updated_at` | timestamp without time zone | YES |  |   |
| `created_at` | timestamp without time zone | YES |  |   |
| `preload_date` | date | NO |  |   |
| `created_by` | character varying | NO |  |   |
| `notes` | text | YES |  |   |
| `status` | character varying | NO |  |   |
| `branch_id` | character varying | YES |  |   |
| `warehouse_id` | character varying | NO |  |   |
| `tenant_id` | character varying | NO |  |   |
| `id` | character varying | NO |  | PK  |

**Indexes (7):**
- `ix_lg_plan_preloads_status` (btree) on `warehouse_id`
- `uq_lg_plan_preloads_active` (btree) on `tenant_id`
- `uq_lg_plan_preloads_active` (btree) on `preload_date`
- `ix_lg_plan_preloads_status` (btree) on `preload_date`
- `ix_lg_plan_preloads_status` (btree) on `status`

---

### `lg_planning_reservations`
Columnas: 28 | FKs: 10 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `actual_load_summary` | json | YES |  |   |
| `actual_end_at` | timestamp with time zone | YES |  |   |
| `actual_start_at` | timestamp with time zone | YES |  |   |
| `permit_override` | boolean | NO | false |   |
| `adr_required` | boolean | NO | false |   |
| `expected_volume_total` | numeric | YES |  |   |
| `expected_weight_total` | numeric | YES |  |   |
| `expected_load_summary` | json | NO |  |   |
| `planned_end_at` | timestamp with time zone | NO |  |   |
| `planned_start_at` | timestamp with time zone | NO |  |   |
| `updated_at` | timestamp with time zone | NO |  |   |
| `created_at` | timestamp with time zone | NO |  |   |
| `created_by` | character varying | NO |  |  → users.id |
| `linked_session_id` | character varying | YES |  |  → lg_vehicle_sessions.id |
| `override_reason` | text | YES |  |   |
| `conflict_reason` | character varying | YES |  |   |
| `status` | character varying | NO | 'PLANNED'::character varying |   |
| `notes` | text | YES |  |   |
| `driver_id` | character varying | YES |  |  → users.id |
| `route_id` | character varying | YES |  |  → lg_routes.id |
| `service_type` | character varying | YES |  |   |
| `origin_warehouse_id` | character varying | NO |  |  → lg_warehouses.id |
| `vehicle_id` | character varying | NO |  |  → lg_vehicles.id |
| `branch_id` | character varying | YES |  |  → branches.id |
| `tenant_id` | character varying | NO |  |  → tenants.id |
| `id` | character varying | NO |  | PK  |
| `quote_id` | character varying | YES |  |  → ventas_quote_drafts.id |
| `updated_by` | character varying | NO |  |  → users.id |

**Foreign Keys:**
- `tenant_id` → `tenants.id`
- `branch_id` → `branches.id`
- `vehicle_id` → `lg_vehicles.id`
- `origin_warehouse_id` → `lg_warehouses.id`
- `route_id` → `lg_routes.id`
- `driver_id` → `users.id`
- `linked_session_id` → `lg_vehicle_sessions.id`
- `created_by` → `users.id`
- `updated_by` → `users.id`
- `quote_id` → `ventas_quote_drafts.id`

**Indexes (8):**
- `ex_lg_planning_vehicle_window_active` (gist) on `vehicle_id`
- `ix_lg_planning_reservations_window` (btree) on `planned_start_at`
- `ix_lg_planning_reservations_window` (btree) on `planned_end_at`
- `ix_lg_planning_reservations_status` (btree) on `status`
- `ix_lg_planning_quote` (btree) on `quote_id`

---

## Logistics - Almacen movil

### `lg_mobile_warehouse_item_events`
Columnas: 10 | FKs: 1 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `metadata` | jsonb | YES |  |   |
| `occurred_at` | timestamp without time zone | NO |  |   |
| `tenant_id` | character varying | NO |  |   |
| `id` | character varying | NO |  | PK  |
| `created_by` | character varying | YES |  |   |
| `customer_id` | character varying | YES |  |   |
| `movement_id` | character varying | YES |  |   |
| `ledger_entry_id` | character varying | YES |  |   |
| `event_type` | character varying | NO |  |   |
| `mobile_warehouse_item_id` | character varying | NO |  |  → lg_mobile_warehouse_items.id |

**Foreign Keys:**
- `mobile_warehouse_item_id` → `lg_mobile_warehouse_items.id`

---

### `lg_mobile_warehouse_items`
Columnas: 19 | FKs: 8 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `created_at` | timestamp with time zone | YES |  |   |
| `unloaded_at` | timestamp with time zone | YES |  |   |
| `loaded_at` | timestamp with time zone | YES |  |   |
| `weight_kg` | numeric | YES |  |   |
| `quantity` | numeric | NO |  |   |
| `customer_id` | character varying | YES |  |   |
| `unloaded_by` | character varying | YES |  |  → users.id |
| `loaded_by` | character varying | NO |  |  → users.id |
| `notes` | text | YES |  |   |
| `status` | character varying | NO |  |   |
| `product_name` | character varying | YES |  |   |
| `product_id` | character varying | YES |  |   |
| `cylinder_id` | character varying | YES |  |  → lg_cylinders.id |
| `movement_id` | character varying | YES |  |  → lg_movements.id |
| `destination_warehouse_id` | character varying | YES |  |  → lg_warehouses.id |
| `source_warehouse_id` | character varying | YES |  |  → lg_warehouses.id |
| `mobile_warehouse_id` | character varying | NO |  |  → lg_mobile_warehouses.id |
| `tenant_id` | character varying | NO |  |  → tenants.id |
| `id` | character varying | NO |  | PK  |

**Foreign Keys:**
- `cylinder_id` → `lg_cylinders.id`
- `destination_warehouse_id` → `lg_warehouses.id`
- `loaded_by` → `users.id`
- `mobile_warehouse_id` → `lg_mobile_warehouses.id`
- `movement_id` → `lg_movements.id`
- `source_warehouse_id` → `lg_warehouses.id`
- `tenant_id` → `tenants.id`
- `unloaded_by` → `users.id`

**Indexes (13):**
- `ix_lg_mobile_warehouse_items_destination_warehouse_id` (btree) on `destination_warehouse_id`
- `ix_lg_mobile_warehouse_items_customer` (btree) on `customer_id`
- `ix_lg_mobile_warehouse_items_product_id` (btree) on `product_id`
- `ix_lg_mobile_warehouse_items_customer` (btree) on `tenant_id`
- `ix_lg_mobile_warehouse_items_loaded_by` (btree) on `loaded_by`

---

### `lg_mobile_warehouse_snapshot_items`
Columnas: 6 | FKs: 1 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `weight_kg` | numeric | NO | 0 |   |
| `quantity` | numeric | NO |  |   |
| `condition` | character varying | YES |  |   |
| `product_id` | character varying | NO |  |   |
| `snapshot_id` | character varying | NO |  |  → lg_mobile_warehouse_snapshots.id |
| `id` | character varying | NO |  | PK  |

**Foreign Keys:**
- `snapshot_id` → `lg_mobile_warehouse_snapshots.id`

---

### `lg_mobile_warehouse_snapshots`
Columnas: 9 | FKs: 0 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `metadata` | jsonb | YES |  |   |
| `total_weight_kg` | numeric | NO | 0 |   |
| `total_units` | numeric | NO | 0 |   |
| `captured_at` | timestamp without time zone | NO |  |   |
| `snapshot_type` | character varying | NO |  |   |
| `mobile_warehouse_id` | character varying | NO |  |   |
| `tenant_id` | character varying | NO |  |   |
| `id` | character varying | NO |  | PK  |
| `captured_by` | character varying | YES |  |   |

---

### `lg_mobile_warehouses`
Columnas: 14 | FKs: 6 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `updated_at` | timestamp with time zone | YES |  |   |
| `created_at` | timestamp with time zone | YES |  |   |
| `closed_at` | timestamp with time zone | YES |  |   |
| `opened_at` | timestamp with time zone | YES |  |   |
| `stock_warehouse_id` | character varying | YES |  |   |
| `created_by` | character varying | NO |  |  → users.id |
| `notes` | text | YES |  |   |
| `status` | character varying | NO |  |   |
| `vehicle_id` | character varying | NO |  |  → lg_vehicles.id |
| `warehouse_id` | character varying | NO |  |  → lg_warehouses.id |
| `branch_id` | character varying | YES |  |  → branches.id |
| `tenant_id` | character varying | NO |  |  → tenants.id |
| `id` | character varying | NO |  | PK  |
| `driver_id` | character varying | YES |  |  → users.id |

**Foreign Keys:**
- `branch_id` → `branches.id`
- `created_by` → `users.id`
- `driver_id` → `users.id`
- `tenant_id` → `tenants.id`
- `vehicle_id` → `lg_vehicles.id`
- `warehouse_id` → `lg_warehouses.id`

**Indexes (10):**
- `ix_lg_mobile_warehouses_warehouse_id` (btree) on `warehouse_id`
- `ix_lg_mobile_warehouses_status` (btree) on `status`
- `ix_lg_mobile_warehouses_created_by` (btree) on `created_by`
- `ix_lg_mobile_warehouses_vehicle_id` (btree) on `vehicle_id`
- `ix_lg_mobile_warehouses_branch_id` (btree) on `branch_id`

---

## Logistics - Contratos

### `lg_contract_types`
Columnas: 5 | FKs: 0 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `is_active` | boolean | NO | true |   |
| `duration_value` | integer | NO |  |   |
| `duration_unit` | character varying | NO |  |   |
| `name` | character varying | NO |  |   |
| `code` | character varying | NO |  | PK  |

---

## Logistics - Agenda

### `lg_agenda_task_types`
Columnas: 2 | FKs: 0 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `description` | character varying | NO |  |   |
| `code` | character varying | NO |  | PK  |

---

### `lg_agenda_tasks`
Columnas: 25 | FKs: 6 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `updated_at` | timestamp with time zone | NO |  |   |
| `created_at` | timestamp with time zone | NO |  |   |
| `completed_at` | timestamp with time zone | YES |  |   |
| `gps_coordinates` | json | NO |  |   |
| `requires_signature` | boolean | NO |  |   |
| `customer_confirmed` | boolean | NO |  |   |
| `quantity_served` | integer | YES |  |   |
| `quantity_requested` | integer | YES |  |   |
| `priority` | integer | NO |  |   |
| `scheduled_time` | time without time zone | YES |  |   |
| `scheduled_date` | date | NO |  |   |
| `delivery_location` | character varying | YES |  |   |
| `evidence_url` | character varying | YES |  |   |
| `cylinder_serial` | character varying | YES |  |   |
| `order_id` | character varying | YES |  |  → lg_orders.id |
| `status` | character varying | NO |  |   |
| `description` | character varying | YES |  |   |
| `task_type` | character varying | NO |  |  → lg_agenda_task_types.code |
| `delivery_point_id` | character varying | YES |  |  → lg_delivery_points.id |
| `customer_name` | character varying | YES |  |   |
| `customer_id` | character varying | YES |  |   |
| `driver_id` | character varying | NO |  |  → users.id |
| `route_id` | character varying | YES |  |  → lg_routes.id |
| `tenant_id` | character varying | NO |  |  → tenants.id |
| `id` | character varying | NO |  | PK  |

**Foreign Keys:**
- `tenant_id` → `tenants.id`
- `route_id` → `lg_routes.id`
- `driver_id` → `users.id`
- `delivery_point_id` → `lg_delivery_points.id`
- `task_type` → `lg_agenda_task_types.code`
- `order_id` → `lg_orders.id`

**Indexes (8):**
- `lg_agenda_tasks_pkey` (btree) on `id`
- `ix_lg_agenda_tasks_order_id` (btree) on `order_id`
- `ix_lg_agenda_tasks_scheduled_date` (btree) on `scheduled_date`
- `ix_lg_agenda_tasks_delivery_point_id` (btree) on `delivery_point_id`
- `ix_lg_agenda_tasks_route_id` (btree) on `route_id`

---

## Logistics - Otros

### `audit_logs`
Columnas: 14 | FKs: 3 | Filas: 1400

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `occurred_at` | timestamp with time zone | NO |  |   |
| `details` | json | NO |  |   |
| `module` | character varying | NO |  |   |
| `actor_type` | character varying | NO |  |   |
| `actor_user_id` | character varying | YES |  |  → users.id |
| `branch_id` | character varying | YES |  |  → branches.id |
| `tenant_id` | character varying | YES |  |  → tenants.id |
| `id` | character varying | NO |  | PK  |
| `request_id` | character varying | YES |  |   |
| `correlation_id` | character varying | YES |  |   |
| `result` | character varying | NO |  |   |
| `entity_id` | character varying | YES |  |   |
| `entity_type` | character varying | YES |  |   |
| `action` | character varying | NO |  |   |

**Foreign Keys:**
- `actor_user_id` → `users.id`
- `branch_id` → `branches.id`
- `tenant_id` → `tenants.id`

**Indexes (7):**
- `ix_audit_logs_branch_id` (btree) on `branch_id`
- `ix_audit_logs_actor_user_id` (btree) on `actor_user_id`
- `ix_audit_logs_correlation_id` (btree) on `correlation_id`
- `ix_audit_logs_tenant_id` (btree) on `tenant_id`
- `audit_logs_pkey` (btree) on `id`

---

### `core_document_versions`
Columnas: 13 | FKs: 2 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `created_at` | timestamp with time zone | YES |  |   |
| `version_number` | integer | NO |  |   |
| `created_by` | character varying | YES |  |  → users.id |
| `sha256` | character varying | NO |  |   |
| `file_path` | character varying | NO |  |   |
| `title` | character varying | YES |  |   |
| `status` | character varying | NO |  |   |
| `template_code` | character varying | NO |  |   |
| `entity_id` | character varying | NO |  |   |
| `entity_type` | character varying | NO |  |   |
| `module` | character varying | NO |  |   |
| `tenant_id` | character varying | NO |  |  → tenants.id |
| `id` | character varying | NO |  | PK  |

**Foreign Keys:**
- `created_by` → `users.id`
- `tenant_id` → `tenants.id`

**Indexes (11):**
- `ix_core_document_versions_entity_id` (btree) on `entity_id`
- `uq_core_document_version_entity` (btree) on `version_number`
- `uq_core_document_version_entity` (btree) on `module`
- `uq_core_document_version_entity` (btree) on `entity_type`
- `core_document_versions_pkey` (btree) on `id`

---

### `core_signature_evidence`
Columnas: 6 | FKs: 2 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `created_at` | timestamp with time zone | YES |  |   |
| `payload_json` | json | NO |  |   |
| `evidence_type` | character varying | NO |  |   |
| `signature_session_id` | character varying | NO |  |  → core_signature_sessions.id |
| `tenant_id` | character varying | NO |  |  → tenants.id |
| `id` | character varying | NO |  | PK  |

**Foreign Keys:**
- `signature_session_id` → `core_signature_sessions.id`
- `tenant_id` → `tenants.id`

---

### `core_signature_sessions`
Columnas: 13 | FKs: 2 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `created_at` | timestamp with time zone | YES |  |   |
| `completed_at` | timestamp with time zone | YES |  |   |
| `verification_ref` | character varying | YES |  |   |
| `verification_channel` | character varying | NO |  |   |
| `status` | character varying | NO |  |   |
| `provider` | character varying | NO |  |   |
| `signer_role` | character varying | YES |  |   |
| `signer_phone` | character varying | YES |  |   |
| `signer_email` | character varying | YES |  |   |
| `signer_name` | character varying | YES |  |   |
| `document_version_id` | character varying | NO |  |  → core_document_versions.id |
| `tenant_id` | character varying | NO |  |  → tenants.id |
| `id` | character varying | NO |  | PK  |

**Foreign Keys:**
- `document_version_id` → `core_document_versions.id`
- `tenant_id` → `tenants.id`

**Indexes (4):**
- `ix_core_signature_sessions_document_version_id` (btree) on `document_version_id`
- `core_signature_sessions_pkey` (btree) on `id`
- `ix_core_signature_sessions_tenant_id` (btree) on `tenant_id`
- `ix_core_signature_sessions_status` (btree) on `status`

---

### `event_logs`
Columnas: 15 | FKs: 3 | Filas: 1022

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `occurred_at` | timestamp with time zone | NO |  |   |
| `metadata_json` | json | NO |  |   |
| `payload` | json | NO |  |   |
| `causation_id` | character varying | YES |  |   |
| `correlation_id` | character varying | YES |  |   |
| `entity_id` | character varying | YES |  |   |
| `entity_type` | character varying | YES |  |   |
| `actor_type` | character varying | NO |  |   |
| `actor_user_id` | character varying | YES |  |  → users.id |
| `branch_id` | character varying | YES |  |  → branches.id |
| `tenant_id` | character varying | YES |  |  → tenants.id |
| `module` | character varying | NO |  |   |
| `version` | character varying | NO |  |   |
| `event_name` | character varying | NO |  |   |
| `id` | character varying | NO |  | PK  |

**Foreign Keys:**
- `actor_user_id` → `users.id`
- `branch_id` → `branches.id`
- `tenant_id` → `tenants.id`

**Indexes (8):**
- `event_logs_pkey` (btree) on `id`
- `ix_event_logs_causation_id` (btree) on `causation_id`
- `ix_event_logs_occurred_at` (btree) on `occurred_at`
- `ix_event_logs_actor_user_id` (btree) on `actor_user_id`
- `ix_event_logs_correlation_id` (btree) on `correlation_id`

---

### `event_outbox`
Columnas: 10 | FKs: 2 | Filas: 702

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `processed_at` | timestamp with time zone | YES |  |   |
| `created_at` | timestamp with time zone | NO |  |   |
| `retry_count` | integer | NO | 0 |   |
| `error_message` | character varying | YES |  |   |
| `status` | character varying | NO |  |   |
| `correlation_id` | character varying | YES |  |   |
| `tenant_id` | character varying | YES |  |  → tenants.id |
| `event_name` | character varying | NO |  |   |
| `event_log_id` | character varying | NO |  |  → event_logs.id |
| `id` | character varying | NO |  | PK  |

**Foreign Keys:**
- `event_log_id` → `event_logs.id`
- `tenant_id` → `tenants.id`

**Indexes (7):**
- `ix_event_outbox_tenant_id` (btree) on `tenant_id`
- `ix_event_outbox_status` (btree) on `status`
- `ix_event_outbox_created_at` (btree) on `created_at`
- `ix_event_outbox_event_name` (btree) on `event_name`
- `ix_event_outbox_correlation_id` (btree) on `correlation_id`

---

### `lg_adr_incompatibilities`
Columnas: 5 | FKs: 0 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `created_at` | timestamp without time zone | YES |  |   |
| `product_id_2` | character varying | NO |  |   |
| `product_id_1` | character varying | NO |  |   |
| `tenant_id` | character varying | NO |  |   |
| `id` | character varying | NO |  | PK  |

**Indexes (4):**
- `uq_lg_adr_incompatibility_pair` (btree) on `product_id_2`
- `lg_adr_incompatibilities_pkey` (btree) on `id`
- `uq_lg_adr_incompatibility_pair` (btree) on `tenant_id`
- `uq_lg_adr_incompatibility_pair` (btree) on `product_id_1`

---

### `lg_adr_product_config`
Columnas: 11 | FKs: 0 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `updated_at` | timestamp without time zone | YES |  |   |
| `created_at` | timestamp without time zone | YES |  |   |
| `valid_to` | date | YES |  |   |
| `valid_from` | date | NO |  |   |
| `max_quantity` | numeric | YES |  |   |
| `adr_points` | numeric | YES |  |   |
| `id` | character varying | NO |  | PK  |
| `adr_tunnel` | character varying | YES |  |   |
| `adr_class` | character varying | YES |  |   |
| `product_id` | character varying | NO |  |   |
| `tenant_id` | character varying | NO |  |   |

**Indexes (4):**
- `uq_lg_adr_product_config_from` (btree) on `product_id`
- `lg_adr_product_config_pkey` (btree) on `id`
- `uq_lg_adr_product_config_from` (btree) on `tenant_id`
- `uq_lg_adr_product_config_from` (btree) on `valid_from`

---

### `lg_customer_cylinder_ledger`
Columnas: 17 | FKs: 0 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `created_at` | timestamp without time zone | NO |  |   |
| `occurred_at` | timestamp without time zone | NO |  |   |
| `quantity` | numeric | NO |  |   |
| `condition` | character varying | YES |  |   |
| `product_name` | character varying | YES |  |   |
| `product_id` | character varying | YES |  |   |
| `event_type` | character varying | NO |  |   |
| `source_id` | character varying | NO |  |   |
| `source_type` | character varying | NO |  |   |
| `contract_id` | character varying | YES |  |   |
| `customer_id` | character varying | NO |  |   |
| `tenant_id` | character varying | NO |  |   |
| `id` | character varying | NO |  | PK  |
| `notes` | text | YES |  |   |
| `created_by` | character varying | NO |  |   |
| `trace_mode` | character varying | NO | 'AGGREGATE'::character varying |   |
| `cylinder_id` | character varying | YES |  |   |

**Indexes (9):**
- `uq_lg_customer_cylinder_ledger_source_event` (btree) on `source_id`
- `lg_customer_cylinder_ledger_pkey` (btree) on `id`
- `ix_lg_customer_cylinder_ledger_customer` (btree) on `tenant_id`
- `uq_lg_customer_cylinder_ledger_source_event` (btree) on `event_type`
- `uq_lg_customer_cylinder_ledger_source_event` (btree) on `tenant_id`

---

### `lg_driver_parameters`
Columnas: 6 | FKs: 0 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `updated_at` | timestamp without time zone | YES |  |   |
| `param_value` | text | YES |  |   |
| `param_key` | character varying | NO |  |   |
| `driver_id` | character varying | NO |  |   |
| `tenant_id` | character varying | NO |  |   |
| `id` | character varying | NO |  | PK  |

**Indexes (4):**
- `uq_lg_driver_parameter_key` (btree) on `driver_id`
- `uq_lg_driver_parameter_key` (btree) on `tenant_id`
- `lg_driver_parameters_pkey` (btree) on `id`
- `uq_lg_driver_parameter_key` (btree) on `param_key`

---

### `lg_hydrostatic_tests`
Columnas: 9 | FKs: 1 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `created_at` | timestamp with time zone | NO |  |   |
| `previous_test_date` | date | YES |  |   |
| `test_date` | date | NO |  |   |
| `notes` | text | YES |  |   |
| `modified_by` | character varying | YES |  |   |
| `movement_id` | character varying | YES |  |   |
| `status` | character varying | YES |  |   |
| `cylinder_id` | character varying | NO |  |  → lg_cylinders.id |
| `id` | character varying | NO |  | PK  |

**Foreign Keys:**
- `cylinder_id` → `lg_cylinders.id`

---

### `lg_inventory_discrepancies`
Columnas: 13 | FKs: 3 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `updated_at` | timestamp with time zone | NO |  |   |
| `created_at` | timestamp with time zone | NO |  |   |
| `resolved_at` | timestamp with time zone | YES |  |   |
| `difference_quantity` | numeric | NO |  |   |
| `counted_quantity` | numeric | NO |  |   |
| `expected_quantity` | numeric | NO |  |   |
| `resolved_by` | character varying | YES |  |  → users.id |
| `resolution_notes` | text | YES |  |   |
| `status` | character varying | NO | 'OPEN'::character varying |   |
| `product_name` | character varying | NO |  |   |
| `product_id` | character varying | NO |  |  → prod_products.id |
| `reconciliation_id` | character varying | NO |  |  → lg_session_reconciliations.id |
| `id` | character varying | NO |  | PK  |

**Foreign Keys:**
- `reconciliation_id` → `lg_session_reconciliations.id`
- `product_id` → `prod_products.id`
- `resolved_by` → `users.id`

---

### `lg_order_items`
Columnas: 12 | FKs: 1 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `created_at` | timestamp with time zone | NO |  |   |
| `status` | integer | NO |  |   |
| `quantity_planned` | numeric | NO |  |   |
| `quantity_requested` | numeric | NO |  |   |
| `description` | character varying | YES |  |   |
| `location` | character varying | YES |  |   |
| `condition` | character varying | YES |  |   |
| `reason` | character varying | YES |  |   |
| `product_name` | character varying | NO |  |   |
| `product_id` | character varying | YES |  |   |
| `order_id` | character varying | NO |  |  → lg_orders.id |
| `id` | character varying | NO |  | PK  |

**Foreign Keys:**
- `order_id` → `lg_orders.id`

**Indexes (4):**
- `lg_order_items_pkey` (btree) on `id`
- `ix_lg_order_items_order_id` (btree) on `order_id`
- `ix_lg_order_items_order_prod` (btree) on `product_id`
- `ix_lg_order_items_order_prod` (btree) on `order_id`

---

### `lg_orders`
Columnas: 19 | FKs: 4 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `updated_at` | timestamp with time zone | NO |  |   |
| `created_at` | timestamp with time zone | NO |  |   |
| `time_window_end` | timestamp with time zone | YES |  |   |
| `time_window_start` | timestamp with time zone | YES |  |   |
| `commitment_date` | timestamp with time zone | YES |  |   |
| `document_number` | integer | YES |  |   |
| `order_date` | timestamp with time zone | NO |  |   |
| `created_by` | character varying | NO |  |  → users.id |
| `notes` | text | YES |  |   |
| `status` | character varying | NO |  |   |
| `carrier` | character varying | YES |  |   |
| `warehouse_id` | character varying | YES |  |  → lg_warehouses.id |
| `document_series` | character varying | YES |  |   |
| `movement_type` | character varying | NO |  |   |
| `customer_name` | character varying | NO |  |   |
| `customer_id` | character varying | YES |  |   |
| `branch_id` | character varying | YES |  |  → branches.id |
| `tenant_id` | character varying | NO |  |  → tenants.id |
| `id` | character varying | NO |  | PK  |

**Foreign Keys:**
- `tenant_id` → `tenants.id`
- `branch_id` → `branches.id`
- `warehouse_id` → `lg_warehouses.id`
- `created_by` → `users.id`

**Indexes (9):**
- `ix_lg_orders_customer_id` (btree) on `customer_id`
- `ix_lg_orders_tenant_status_cr` (btree) on `tenant_id`
- `ix_lg_orders_created_by` (btree) on `created_by`
- `lg_orders_pkey` (btree) on `id`
- `ix_lg_orders_tenant_id` (btree) on `tenant_id`

---

### `lg_stock_bridge_log`
Columnas: 11 | FKs: 1 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `created_at` | timestamp with time zone | NO | now() |   |
| `payload` | jsonb | YES |  |   |
| `unit_cost` | numeric | YES |  |   |
| `quantity` | numeric | YES |  |   |
| `error_msg` | text | YES |  |   |
| `status` | character varying | NO |  |   |
| `product_id` | character varying | YES |  |   |
| `operation` | character varying | NO |  |   |
| `movement_id` | character varying | NO |  |   |
| `tenant_id` | character varying | NO |  |  → tenants.id |
| `id` | character varying | NO |  | PK  |

**Foreign Keys:**
- `tenant_id` → `tenants.id`

**Indexes (5):**
- `ix_stock_bridge_log_movement` (btree) on `tenant_id`
- `lg_stock_bridge_log_pkey` (btree) on `id`
- `ix_stock_bridge_log_movement` (btree) on `movement_id`
- `ix_stock_bridge_log_created` (btree) on `created_at`
- `ix_stock_bridge_log_created` (btree) on `tenant_id`

---

### `user_context_claims`
Columnas: 6 | FKs: 2 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `created_at` | timestamp with time zone | NO |  |   |
| `claim_value` | character varying | NO |  |   |
| `claim_type` | character varying | NO |  |   |
| `user_id` | character varying | NO |  |  → users.id |
| `tenant_id` | character varying | NO |  |  → tenants.id |
| `id` | character varying | NO |  | PK  |

**Foreign Keys:**
- `tenant_id` → `tenants.id`
- `user_id` → `users.id`

**Indexes (8):**
- `uq_user_context_claim` (btree) on `user_id`
- `user_context_claims_pkey` (btree) on `id`
- `ix_user_context_claims_claim_value` (btree) on `claim_value`
- `ix_user_context_claims_tenant_id` (btree) on `tenant_id`
- `ix_user_context_claims_claim_type` (btree) on `claim_type`

---

### `user_roles`
Columnas: 4 | FKs: 2 | Filas: 0

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `created_at` | timestamp with time zone | NO |  |   |
| `role_id` | character varying | NO |  |  → roles.id |
| `user_id` | character varying | NO |  |  → users.id |
| `id` | character varying | NO |  | PK  |

**Foreign Keys:**
- `role_id` → `roles.id`
- `user_id` → `users.id`

**Indexes (5):**
- `uq_user_role` (btree) on `user_id`
- `uq_user_role` (btree) on `role_id`
- `ix_user_roles_user_id` (btree) on `user_id`
- `user_roles_pkey` (btree) on `id`
- `ix_user_roles_role_id` (btree) on `role_id`

---

