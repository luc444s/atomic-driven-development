# SPEC 0023XB - Frontend de condiciones comerciales, fiscalidad y cobro del cliente

## Estado

Cerrada — 2026-07-04

> Nota de cierre: El selector de productos quedó implementado completamente vía `GET /products/flat` de `productos` + Combobox, superando el alcance original que lo dejaba como placeholder.

## Contexto

`0023XA` dejo implementado el backend completo de la capa comercial, fiscal y financiera del cliente: 6 campos fiscales nuevos en `crm_customers`, `payment_mode` en `crm_payment_terms`, tabla `crm_customer_bank_accounts`, tabla `crm_customer_pricing_terms`, endpoints REST, permisos y eventos.

El frontend del plugin CRM (`plugins/crm/frontend/`) **no fue actualizado**. Los campos, endpoints y tablas nuevas existen en la API pero no son visibles ni editables desde la UI. Esta spec cubre ese gap.

## Dependencia

- `0023XA` backend implementado (completado)
- `plugins/crm/frontend/` existente con patrón establecido de componentes, tipos y API

## Objetivo

Exponer en la UI del CRM todos los datos maestros, endpoints y reglas que `0023XA` implemento en el backend:

1. campos fiscales espanoles en formulario de alta/edicion de cliente
2. visualizacion de flags fiscales en ficha de detalle
3. modo de pago en selectores de payment terms
4. gestion completa de cuentas bancarias del cliente
5. gestion completa de precios especiales del cliente
6. respetar permisos `crm.financial.*` y `crm.pricing.*`

## No objetivos

- no tocar `CustomerSearchDialog` (ya expone `CustomerBrief`, no requiere campos fiscales)
- no tocar `CustomersListPage` (ya usa `CustomerListItem` que la API ya devuelve con campos fiscales; la tabla los omite pero eso es aceptable en modo lista)
- no implementar frontend de remesas, cobros ni deuda (son de `cobros`, modulo futuro)
- ~~no implementar selector de productos para pricing terms con alcance `PRODUCT`~~ → Implementado vía `GET /products/flat` de `productos` + Combobox en `PricingTermsSection.tsx`
- no modificar `AddressSection`, `ContactSection`, `CrmSection`, `DeliveryPointsSection` — estas secciones no se tocan

## Archivos afectados

| Archivo | Tipo de cambio |
|---|---|
| `plugins/crm/frontend/types.ts` | Ampliar con nuevos tipos y extender existentes |
| `plugins/crm/frontend/api.ts` | Agregar funciones API y query keys nuevos |
| `plugins/crm/frontend/components/FiscalInfoSection.tsx` | Extender con flags fiscales espanoles |
| `plugins/crm/frontend/components/CustomerInfoCard.tsx` | Mostrar resumen fiscal y payment mode |
| `plugins/crm/frontend/components/ModalNuevoCliente.tsx` | Agregar seccion fiscal, payment mode, campos nuevos |
| `plugins/crm/frontend/components/ModalDetalleCliente.tsx` | Agregar dialogs de bank accounts y pricing terms |
| `plugins/crm/frontend/components/BankAccountsSection.tsx` | **NUEVO** — tabla + form CRUD |
| `plugins/crm/frontend/components/PricingTermsSection.tsx` | **NUEVO** — tabla + form CRUD |

## Cambios detallados

### 1. `types.ts` — Extension de tipos

#### 1.1 Nuevo tipo `CustomerBankAccount`

```ts
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
```

#### 1.2 Nuevo tipo `CustomerBankAccountPayload`

```ts
export type CustomerBankAccountPayload = {
  bank_name: string;
  account_holder: string;
  iban: string;
  bic_swift: string | null;
  is_primary: boolean;
  notes: string | null;
};
```

#### 1.3 Nuevo tipo `CustomerPricingTerm`

```ts
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
```

#### 1.4 Nuevo tipo `CustomerPricingTermPayload`

```ts
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
```

#### 1.5 Campos nuevos en `CustomerListItem`

Agregar a la interfaz existente:

```ts
  accounting_code: string | null;
  is_intracommunity: boolean;
  fiscal_operation_key: string | null;
  tax_regime_code: string | null;
  equivalence_surcharge_applicable: boolean;
  cash_criterion_applicable: boolean;
```

#### 1.6 Campos nuevos en `Customer` (hereda de `CustomerListItem`, ya los recibe)

No requiere cambios porque `Customer extends CustomerListItem`. Los 6 campos fiscales se heredan automaticamente.

#### 1.7 Campos nuevos en `CustomerPayload`

Agregar:

```ts
  accounting_code: string | null;
  is_intracommunity: boolean;
  fiscal_operation_key: string | null;
  tax_regime_code: string | null;
  equivalence_surcharge_applicable: boolean;
  cash_criterion_applicable: boolean;
```

#### 1.8 Campo nuevo en `PaymentTerm`

Agregar `payment_mode: string;` a la interfaz existente.

### 2. `api.ts` — Nuevas funciones y query keys

#### 2.1 Query keys nuevas

Agregar en `crmKeys.customers`:

```ts
bankAccounts: (customerId: string) => ["crm", "customers", customerId, "bank-accounts"] as const,
pricingTerms: (customerId: string) => ["crm", "customers", customerId, "pricing-terms"] as const,
```

#### 2.2 Funciones de bank accounts

```ts
export async function listCustomerBankAccounts(customerId: string): Promise<CustomerBankAccount[]>
export async function createCustomerBankAccount(customerId: string, payload: CustomerBankAccountPayload): Promise<CustomerBankAccount>
export async function updateCustomerBankAccount(bankAccountId: string, payload: Partial<CustomerBankAccountPayload> & { is_active?: boolean }): Promise<CustomerBankAccount>
export async function deleteCustomerBankAccount(bankAccountId: string): Promise<void>
```

Rutas:
- `GET /customers/{customerId}/bank-accounts`
- `POST /customers/{customerId}/bank-accounts`
- `PUT /bank-accounts/{id}`
- `DELETE /bank-accounts/{id}`

#### 2.3 Funciones de pricing terms

```ts
export async function listCustomerPricingTerms(customerId: string): Promise<CustomerPricingTerm[]>
export async function createCustomerPricingTerm(customerId: string, payload: CustomerPricingTermPayload): Promise<CustomerPricingTerm>
export async function updateCustomerPricingTerm(pricingTermId: string, payload: Partial<CustomerPricingTermPayload> & { is_active?: boolean }): Promise<CustomerPricingTerm>
export async function deleteCustomerPricingTerm(pricingTermId: string): Promise<void>
```

Rutas:
- `GET /customers/{customerId}/pricing-terms`
- `POST /customers/{customerId}/pricing-terms`
- `PUT /pricing-terms/{id}`
- `DELETE /pricing-terms/{id}`

### 3. `FiscalInfoSection.tsx` — Extension con flags fiscales

El componente actual solo maneja pais, tipo documento y numero documento. Extenderlo para que reciba y renderice los 6 campos fiscales nuevos.

#### Props nuevas

```ts
type FiscalInfoSectionProps = {
  // ... existentes ...
  documentType: string;
  documentNumber: string;
  countryCode: string;
  countryOptions: ComboboxOption[];
  documentTypeOptions: ComboboxOption[];
  // nuevos:
  accountingCode: string | null;
  isIntracommunity: boolean;
  fiscalOperationKey: string | null;
  taxRegimeCode: string | null;
  equivalenceSurchargeApplicable: boolean;
  cashCriterionApplicable: boolean;
  // onChange ampliado:
  onChange: (field: string, value: string | boolean) => void;
};
```

#### Layout

Despues de la fila de 3 columnas existente (pais, tipo doc, numero), agregar una segunda fila con:

- `md:grid-cols-3`: `accounting_code` (Input), `fiscal_operation_key` (Input), `tax_regime_code` (Input)
- Una fila de checkboxes con `md:grid-cols-3`: `is_intracommunity`, `equivalence_surcharge_applicable`, `cash_criterion_applicable`
- Los checkboxes usan `<input type="checkbox">` con el mismo patrón del checkbox `is_primary` de `ModalDetalleCliente`

### 4. `CustomerInfoCard.tsx` — Resumen fiscal

Agregar nuevos campos al `CardContent` existente:

- `Código contable: {customer.accounting_code ?? "-"}`
- `Forma de pago: ...` (puede consumirse del payment_term o de un join; en este corte mostrar el `payment_term_code` directamente)
- `Intracomunitario: {customer.is_intracommunity ? "Sí" : "No"}`
- `Recargo equivalencia: {customer.equivalence_surcharge_applicable ? "Sí" : "No"}`
- `Criterio de caja: {customer.cash_criterion_applicable ? "Sí" : "No"}`
- `Clave operación fiscal: {customer.fiscal_operation_key ?? "-"}`

### 5. `ModalNuevoCliente.tsx` — Formulario ampliado

#### 5.1 `EMPTY_CUSTOMER` — valores por defecto nuevos

```ts
  accounting_code: null,
  is_intracommunity: false,
  fiscal_operation_key: null,
  tax_regime_code: null,
  equivalence_surcharge_applicable: false,
  cash_criterion_applicable: false,
```

#### 5.2 Seccion de datos comerciales/fiscales

Despues del `ContactSection` actual, agregar dentro del mismo `Card` de "Datos generales" un bloque colapsable (o directamente visible) con:

- `Combobox` para `payment_term_code` (ya existe en `ModalNuevoCliente` pero esta oculto; debe hacerse visible con las opciones del catalogo de payment terms)
- `Combobox` para `billing_type` con opciones `por_operacion`, `mensual`, `anticipada`
- Checkbox `is_exempt`

Estos campos ya estan en el `CustomerPayload` y en `EMPTY_CUSTOMER` pero **no tienen inputs en el formulario actual**. Hay que agregarlos.

#### 5.3 FiscalInfoSection ampliado

El componente `FiscalInfoSection` ya recibe las props ampliadas (segun seccion 3). `ModalNuevoCliente` debe pasarle los nuevos valores desde `formState`.

#### 5.4 Sincronizacion con `detailQuery.data`

El `useEffect` que carga datos de `getCustomer` en `formState` debe incluir los 6 campos fiscales nuevos, `payment_term_code`, `billing_type`, e `is_exempt` (estos tres ultimos ya estan, solo verificar).

### 6. `ModalDetalleCliente.tsx` — Nuevos dialogs

Agregar dos botones nuevos en el `CardContent` de "Resumen del cliente" (junto a Direcciones, Contactos, Gestion comercial, Puntos de entrega):

```
[Cuentas bancarias]   [Precios especiales]
```

Y sus respectivos `Dialog` con `DataTable` + formulario.

#### 6.1 Dialog: Cuentas bancarias

- Query: `listCustomerBankAccounts(customerId)`
- Estado: `isBankAccountsOpen`, `bankAccountForm`, `editingBankAccountId`
- Mutations: `createBankAccountMutation`, `updateBankAccountMutation`, `deleteBankAccountMutation`
- `DataTable` columnas: `bank_name`, `account_holder`, `iban`, `bic_swift` o "-", `is_primary` (Sí/No)
- `onRowClick`: carga en `bankAccountForm` y activa edicion
- Formulario: `bank_name` (Input), `account_holder` (Input), `iban` (Input), `bic_swift` (Input), `is_primary` (checkbox), `notes` (Input)
- Boton eliminar en cada fila (x)
- Patron identico al dialog de "Direcciones" existente

#### 6.2 Dialog: Precios especiales

- Query: `listCustomerPricingTerms(customerId)`
- Estado: `isPricingOpen`, `pricingForm`, `editingPricingTermId`
- Mutations: `createPricingMutation`, `updatePricingMutation`, `deletePricingMutation`
- `DataTable` columnas: `scope_type` (PRODUCT/GLOBAL), `pricing_mode` (FIXED_PRICE/PERCENT_DISCOUNT), `fixed_amount` o `discount_percent`, `currency`, `valid_from`, `valid_to` o "-", `is_active` (Sí/No)
- `onRowClick`: carga en `pricingForm` y activa edicion
- Formulario:
  - `scope_type` (Combobox: PRODUCT, GLOBAL)
  - `pricing_mode` (Combobox: FIXED_PRICE, PERCENT_DISCOUNT)
  - Dependiendo de `pricing_mode`: `fixed_amount` (Input number) o `discount_percent` (Input number)
  - `currency` (Input, default EUR)
  - `valid_from` (Input type date)
  - `valid_to` (Input type date, nullable)
  - `source_quote_ref` (Input, nullable)
  - `notes` (Input, nullable)
  - `product_id`: placeholder Input deshabilitado con texto "Requiere catálogo de productos"
- Boton eliminar en cada fila (x)

### 7. `BankAccountsSection.tsx` — Componente nuevo

Componente standalone que encapsula tabla + form de cuentas bancarias. Sigue el mismo patron que `DeliveryPointsSection`: recibe los datos por props o los fetchea internamente.

**Props:**

```ts
type BankAccountsSectionProps = {
  customerId: string;
};
```

El componente maneja internamente:
- query con `listCustomerBankAccounts`
- estado de formulario y edicion
- mutations

Esto permite reusarlo si en el futuro se necesita embebido en otro lado.

**Regla de negocio en UI:**
- Al marcar una cuenta como `is_primary`, el backend se encarga de desmarcar las demas. El frontend debe invalidar la query tras crear/actualizar para reflejar el cambio.
- No permitir eliminar si es la unica cuenta primaria (warning, no bloqueante).

### 8. `PricingTermsSection.tsx` — Componente nuevo

Mismo patron que `BankAccountsSection`.

**Props:**

```ts
type PricingTermsSectionProps = {
  customerId: string;
};
```

**Nota sobre serializacion de Decimal:**

`fixed_amount` y `discount_percent` llegan como `string` desde la API (Pydantic v2 serializa `Decimal` como string, ej. `"12.500"`). Para mostrarlos en la tabla usar `parseFloat()` para formateo. Para enviarlos en POST/PUT, el backend acepta tanto string como number porque Pydantic coerce automaticamente; se recomienda enviar como string para preservar precision.

**Nota sobre `approved_by`:**

`approved_by` aparece en `CustomerPricingTerm` (lectura) pero no en `CustomerPricingTermPayload` (escritura) porque el backend lo asigna automaticamente con el `user_id` autenticado al crear o actualizar el registro.

**Validaciones en UI:**
- Si `scope_type === "PRODUCT"`, avisar que `product_id` es obligatorio pero no hay selector disponible aun. Mostrar campo deshabilitado.
- Si `pricing_mode === "FIXED_PRICE"`, mostrar campo `fixed_amount` y ocultar `discount_percent`.
- Si `pricing_mode === "PERCENT_DISCOUNT"`, mostrar campo `discount_percent` y ocultar `fixed_amount`.
- `valid_from` obligatorio, `valid_to` opcional.

## Permisos en UI

Los nuevos botones y secciones deben respetar permisos:

| Elemento | Permiso requerido |
|---|---|
| Boton "Cuentas bancarias" | `crm.financial.read` |
| Formulario crear/editar bank account | `crm.financial.manage` |
| Boton eliminar bank account | `crm.financial.manage` |
| Boton "Precios especiales" | `crm.pricing.read` |
| Formulario crear/editar pricing term | `crm.pricing.manage` |
| Boton eliminar pricing term | `crm.pricing.manage` |

El hook de permisos debe consultarse via `useHasPermission` o equivalente del SDK. Si no existe un hook global, usar `ctx.hasPermission` del `PluginFrontendContext`. Si el contexto no esta disponible en componentes hijos, pasar `canManageFinancial` / `canManagePricing` como props desde `ModalDetalleCliente`.

## Reglas de UI

- seguir el patron `Dialog` + `DataTable` + formulario que ya usan Direcciones, Contactos y Gestion comercial en `ModalDetalleCliente`
- usar `Combobox` para selects con valores controlados (pais, tipo doc, scope_type, pricing_mode, billing_type)
- usar `Input` para campos de texto, IBAN, codigos
- usar `input type="checkbox"` con `<label>` para flags booleanos, mismo patron que `is_primary` en contactos
- `Input` de fecha usar `type="date"` para `valid_from`, `valid_to`
- no usar `@apply` ni colores hardcodeados; usar variables CSS semanticas
- mantener imports desde `apps/web/src/shared/ui/` sin crear componentes UI duplicados
- `BankAccountsSection` y `PricingTermsSection` deben poder funcionar tanto dentro de un `Dialog` como standalone (reciben `customerId`, no dependen de estar dentro de `ModalDetalleCliente`)

## Criterios de aceptacion

1. el formulario de alta/edicion de cliente (`ModalNuevoCliente`) expone `payment_term_code`, `billing_type`, `is_exempt` y los 6 campos fiscales nuevos
2. al editar un cliente existente, los campos fiscales se cargan correctamente desde `getCustomer`
3. la ficha de detalle (`ModalDetalleCliente`) muestra los flags fiscales en `CustomerInfoCard`
4. el dialog de cuentas bancarias permite listar, crear, editar y eliminar cuentas con validacion de IBAN normalizado
5. el dialog de precios especiales permite listar, crear, editar y eliminar condiciones con validacion visual de `scope_type`/`pricing_mode`
6. ambas secciones respetan permisos `crm.financial.*` y `crm.pricing.*`
7. los componentes `BankAccountsSection` y `PricingTermsSection` son reutilizables (reciben `customerId` por props)
8. no se introducen componentes UI duplicados ni colores hardcodeados
9. `ruff check` y `pyright` no deben fallar (el cambio es solo TSX/TS, pero el check de backend debe seguir limpio)
10. los tipos en `types.ts` reflejan fielmente los schemas Pydantic del backend

## Pruebas requeridas

- **Unitarias**: renderizado de `FiscalInfoSection` con/sin valores fiscales; `BankAccountsSection` y `PricingTermsSection` con estados vacio, cargado y error; validacion de ocultamiento de campos segun `pricing_mode`.
- **Integracion**: mutaciones de bank accounts y pricing terms contra API mock; verificacion de invalidacion de queries tras create/update/delete.
- **Frontend manual**: flujo completo de alta de cliente con campos fiscales; CRUD de cuentas bancarias y precios especiales desde `ModalDetalleCliente`; verificacion de ocultamiento de botones sin permiso `crm.financial.*` / `crm.pricing.*`.

## Riesgos

| Riesgo | Impacto | Mitigacion |
|---|---|---|
| Selector de productos no disponible para pricing PRODUCT | medio | Dejar input deshabilitado con mensaje claro; no bloquear |
| Permisos no accesibles desde componentes hijos | bajo | Pasar flags como props desde `ModalDetalleCliente` si el contexto no esta disponible |
| Duplicar logica de formulario entre secciones | medio | Extraer `BankAccountsSection` y `PricingTermsSection` como componentes independientes |

## Fases

### Fase 1 — Tipos y API
- Ampliar `types.ts` con `CustomerBankAccount`, `CustomerPricingTerm`, payloads, y campos en `CustomerListItem`, `CustomerPayload`, `PaymentTerm`
- Agregar funciones API y query keys en `api.ts`

### Fase 2 — Componentes nuevos
- Crear `BankAccountsSection.tsx`
- Crear `PricingTermsSection.tsx`

### Fase 3 — Integracion en formularios existentes
- Extender `FiscalInfoSection.tsx` con flags fiscales
- Actualizar `CustomerInfoCard.tsx` con resumen fiscal
- Actualizar `ModalNuevoCliente.tsx` con payment term, billing type, exento, y campos fiscales
- Agregar dialogs de bank accounts y pricing terms en `ModalDetalleCliente.tsx`
