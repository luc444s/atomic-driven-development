# SPEC 0013 — CRM Plugin (Clientes)

## Estado

En implementacion

## Contexto

SYSTUTOR OSS dispone de:

- kernel completo: auth JWT, multi-tenant, RBAC, auditoria, event bus, outbox, tareas asincronas;
- plugin runtime: mounting de routers, lifecycle hooks, sync de permisos, SDK de eventos;
- frontend shell: sidebar tenant-aware, PermissionBoundary, componentes compartidos
  (DataTable, Dialog, Card, Badge, Button, Input, Alert);
- plugin logistics completamente funcional: 20+ modelos, maquina de 18 estados de cilindro,
  33 transiciones, pedidos, rutas, movimientos, agenda, escaneo movil, 200+ endpoints.

El proyecto no tiene modulo de clientes. Las tablas de logistics referencian al cliente como
texto libre (`customer_name`) en 6 tablas, sin integridad referencial. Esto hace imposible
rastrear propiedad de cilindros por cliente, validar datos fiscales, o construir modulos
de facturacion y finanzas sobre una base solida.

El analisis legacy (`docs/docs-systutor-legacy/modulo_clientes.md`) documenta que
`Persona_Nuevo` es la entidad mas referenciada del sistema: ~30 formularios, 15+ tablas,
~30 reportes Crystal. En el nuevo sistema no existe equivalente.

Esta spec describe la construccion del modulo CRM como plugin completo y listo para
produccion, no como piloto. Incluye la refactorizacion obligatoria de las 6 tablas de
logistics que hoy dependen de texto libre.

## Objetivo

Construir el plugin `crm` que gestione clientes (personas naturales y juridicas) con:

- datos generales del cliente (nombre, nombre comercial, codigo externo);
- identificacion fiscal multi-pais con validacion de formato (Peru, Costa Rica, Espana);
- direccion fiscal con geolocalizacion (Google Maps / OSM);
- direcciones adicionales de entrega;
- multiples contactos (telefonos, correos electronicos);
- catalogos: tipos de documento de identidad, formas de pago;
- geografia departamental jerarquica (pais, departamento, provincia, distrito, localidad);
- busqueda avanzada multi-criterio;
- frontend completo con formulario multi-pestana y modal de busqueda reusable.

Y refactorizar el plugin `logistics` para:

- migrar `customer_id` huerfano a FK real y limitar `customer_name` a snapshot historico solo donde aplique;
- actualizar servicios para recibir `customer_id` obligatorio;
- reemplazar inputs de texto por CustomerSearchDialog en el frontend;
- completar `lg_delivery_points` como equivalente operativo de `Vehiculo_cliente_nuevo`.

## No objetivos

- proveedores (se postengan a modulo `purchasing`);
- empleados / RRHH (el kernel `users` ya los cubre para autenticacion);
- repartidores / agentes (son `users` con roles);
- lineas de credito / creditos;
- datos bancarios de clientes;
- contratos de alquiler de cilindros;
- validacion contra SUNAT o Hacienda en tiempo real (API externa);
- importacion de datos legacy (se hara separadamente via migrador CSV);
- facturacion electronica;
- dashboard de clientes (reportes);
- historial de movimientos del cliente (se lee desde logistics, no se duplica).

## Alcance

Toca:

- `plugins/crm/` — plugin completo (backend + frontend + migraciones + permisos + eventos);
- `plugins/logistics/backend/models.py` — modificar 6 tablas (customer_id a FK real);
- `plugins/logistics/backend/services/` — actualizar servicios (orders, movements,
  resources, envase, extras, agenda, scan) para usar customer_id real;
- `plugins/logistics/backend/schemas.py` — actualizar schemas (customer_id obligatorio,
  eliminar customer_name como campo de entrada);
- `plugins/logistics/backend/router.py` — verificar endpoints;
- `plugins/logistics/frontend/` — reemplazar inputs de customer_name por
  CustomerSearchDialog en 5+ paginas;
- `plugins/logistics/plugin.json` — agregar `"requires": ["crm"]`;
- `plugins/logistics/migrations/` — nueva migracion 006 para FKs;
- `packages/sdk/frontend/` — exportar tipos del CustomerSearchDialog si es necesario;
- `docs/specs/core/`;
- `docs/contracts/crm-api.md`;
- `apps/api/tests/` — nuevos tests para crm + tests actualizados de logistics.

No debe romper:

- kernel existente (auth, multi-tenant, RBAC, auditoria, event bus, outbox);
- plugin runtime;
- frontend shell;
- funcionalidad existente de logistics que no dependa de customer_name.

No toca el core arquitectonico:

- no modifica modelos base del kernel (`users`, `roles`, `permissions`, `tenants`, `branches`);
- no cambia auth, tenancy, RBAC, outbox, auditoria ni runtime de plugins;
- solo reutiliza infraestructura estable del core y agrega dominio nuevo en `plugins/crm/`.

---

## Arquitectura del plugin

```
plugins/crm/
├── plugin.json
├── backend/
│   ├── __init__.py
│   ├── plugin.py                  # register(): monta router, registra permisos y eventos
│   ├── router.py                  # FastAPI router con todos los endpoints
│   ├── schemas.py                 # Pydantic request/response
│   ├── models.py                  # SQLAlchemy ORM
│   └── services/
│       ├── __init__.py
│       ├── customers.py           # CRUD + busqueda avanzada
│       ├── addresses.py           # CRUD de direcciones con geolocalizacion
│       ├── fiscal_validator.py    # Validacion de documentos por pais
│       ├── geography.py           # Geografia departamental jerarquica
│       ├── search.py              # Busqueda multi-criterio optimizada
│       └── catalog.py             # Catalogos (document_types, payment_terms)
├── frontend/
│   ├── register.ts                # Plugin frontend entrypoint
│   ├── api.ts                     # API client + query keys + tipos TypeScript
│   ├── pages/
│   │   ├── CustomersListPage.tsx  # Listado con tabla, filtros y paginacion
│   │   ├── CustomerFormPage.tsx   # Crear/editar con pestanas
│   │   └── CustomerDetailPage.tsx # Detalle del cliente
│   ├── components/
│   │   ├── CustomerSearchDialog.tsx   # Modal de busqueda reusable
│   │   ├── CustomerInfoCard.tsx       # Resumen visual del cliente
│   │   ├── AddressSection.tsx         # Formulario de direccion con mapa
│   │   ├── FiscalInfoSection.tsx      # Seccion de datos fiscales
│   │   ├── ContactSection.tsx         # Telefonos y correos
│   │   └── DeliveryPointsSection.tsx  # Vista embebida de delivery points desde logistics
│   └── types.ts                  # Interfaces compartidas
├── migrations/
│   ├── 001_initial_crm.py
│   ├── 002_geography_seed.py
│   └── 003_refactor_logistics.py
├── permissions/
│   └── __init__.py
├── events/
│   └── __init__.py
└── README.md
```

Reglas:

- backend importa desde `packages/sdk` y, cuando el SDK aun no expone una dependencia
  necesaria, puede importar de `apps/api/app/` solo infraestructura estable del core
  (auth, tenant, db, modelos core) sin modificarla;
- frontend se registra via `plugins/crm/frontend/register.ts` y consume tipos publicos
  de `@systutor/sdk/frontend`;
- CustomerSearchDialog debe poder ser importado desde otros plugins (logistics, billing)
  sin duplicar el componente;
- toda accion importante (crear cliente, actualizar, cambiar direccion fiscal) es
  auditable y emite evento;
- todas las tablas usan el prefijo `crm_`.

---

## Migracion 1: 001_initial_crm.py

Schema: tablas en schema publico del core, prefijo `crm_`.
IDs: `String(36)` UUID v4 para compatibilidad con kernel existente.
Timestamps: `created_at`, `updated_at` con UTC.
Tenant: toda tabla tenant-aware tiene `tenant_id` FK a `tenants.id` e indice.

### crm_document_types

Catalogo de tipos de documento de identidad. Se siembra con datos iniciales.

```sql
CREATE TABLE crm_document_types (
    code VARCHAR(20) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    country_code VARCHAR(5) NOT NULL,
    description VARCHAR(200),
    is_person BOOLEAN NOT NULL DEFAULT true,
    is_company BOOLEAN NOT NULL DEFAULT false,
    validation_pattern VARCHAR(100),
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

Seed:

| code | name | country_code | is_person | is_company | validation_pattern |
|------|------|-------------|-----------|------------|-------------------|
| RUC | RUC | PER | false | true | \\d{11} |
| DNI | DNI | PER | true | false | \\d{8} |
| CEDULA_FISICA | Cedula Fisica | CRI | true | false | \\d-\\d{4}-\\d{4} |
| CEDULA_JURIDICA | Cedula Juridica | CRI | false | true | \\d-\\d{3}-\\d{6} |
| NIF | NIF | ESP | false | true | \\d{8}[A-Z] |
| NIE | NIE | ESP | true | false | [XYZ]\\d{7}[A-Z] |
| DIMEX | DIMEX | CRI | true | false | \\d{9} |
| NITE | NITE | CRI | false | true | \\d{10} |
| PASAPORTE | Pasaporte | -- | true | false | |
| OTRO | Otro | -- | true | true | |

### crm_payment_terms

Catalogo de formas de pago.

```sql
CREATE TABLE crm_payment_terms (
    code VARCHAR(20) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(200),
    days INTEGER NOT NULL DEFAULT 0,
    operation_type VARCHAR(20) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

Seed:

| code | name | days | operation_type |
|------|------|------|---------------|
| CONTADO | Contado | 0 | CONTADO |
| CREDITO_15 | Credito 15 dias | 15 | CREDITO |
| CREDITO_30 | Credito 30 dias | 30 | CREDITO |
| CREDITO_60 | Credito 60 dias | 60 | CREDITO |
| TARJETA | Tarjeta | 0 | TARJETA |
| TRANSFERENCIA | Transferencia | 0 | TRANSFERENCIA |
| CHEQUE | Cheque | 0 | CHEQUE |

### crm_customers

Tabla principal de clientes. Reemplaza a `Persona_Nuevo` exclusivamente para tipo=1 (cliente).

```sql
CREATE TABLE crm_customers (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id),

    -- Identificacion
    external_code VARCHAR(50),
    legal_name VARCHAR(200) NOT NULL,
    commercial_name VARCHAR(100),
    document_type_code VARCHAR(20) NOT NULL REFERENCES crm_document_types(code),
    document_number VARCHAR(30) NOT NULL,
    country_code VARCHAR(5) NOT NULL DEFAULT 'PER',

    -- Informacion de contacto principal
    email VARCHAR(100),
    phone VARCHAR(50),
    mobile VARCHAR(50),

    -- Direccion fiscal (fuente de verdad en crm_customer_addresses)
    fiscal_address_id VARCHAR(36),

    -- Actividad economica
    economic_activity_code VARCHAR(20),
    economic_activity_description VARCHAR(300),
    activity_validated BOOLEAN NOT NULL DEFAULT false,
    activity_validation_source VARCHAR(50),
    activity_validation_date TIMESTAMPTZ,

    -- Configuracion comercial
    payment_term_code VARCHAR(20) REFERENCES crm_payment_terms(code),
    billing_type VARCHAR(20),          -- mensual, por_operacion
    is_exempt BOOLEAN NOT NULL DEFAULT false,

    -- Datos de persona natural (opcional)
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    birth_date DATE,
    gender VARCHAR(10),

    -- Auditoria
    notes TEXT,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_by VARCHAR(36) NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (tenant_id, document_type_code, document_number),
    UNIQUE (tenant_id, external_code)
);

CREATE INDEX idx_crm_customers_tenant ON crm_customers(tenant_id);
CREATE INDEX idx_crm_customers_document ON crm_customers(document_number);
CREATE INDEX idx_crm_customers_legal_name ON crm_customers(legal_name);
CREATE INDEX idx_crm_customers_email ON crm_customers(email);
CREATE INDEX idx_crm_customers_phone ON crm_customers(phone);
```

Notas de diseno:
- `legal_name` es el nombre fiscal (razon social o nombre completo).
- `first_name`/`last_name` solo para persona natural, se posterga validacion estricta.
- `document_type_code` + `document_number` son unicos por tenant.
- `country_code` determina que algoritmo de validacion fiscal se aplica.
- `fiscal_address_id` debe apuntar a una direccion del mismo cliente; esto se valida en servicio.
- `billing_type` puede ser "mensual" (factura agrupada mensual) o "por_operacion"
  (cada movimiento genera factura). NULL = sin facturacion automatica.
- `is_exempt` indica si el cliente esta exento de impuestos (retenciones, etc.).

Nota tecnica de migracion:
- `crm_customers` se crea primero SIN FK a `crm_customer_addresses` para evitar
  dependencia circular en la migracion Alembic;
- luego de crear `crm_customer_addresses`, se ejecuta:

```sql
ALTER TABLE crm_customers
    ADD CONSTRAINT fk_crm_customer_fiscal_address
    FOREIGN KEY (fiscal_address_id) REFERENCES crm_customer_addresses(id);
```

### crm_customer_addresses

Direcciones del cliente. Esta tabla es la fuente de verdad de TODAS las direcciones,
incluida la fiscal. `crm_customers.fiscal_address_id` apunta a una fila de esta tabla.

```sql
CREATE TABLE crm_customer_addresses (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id),
    customer_id VARCHAR(36) NOT NULL REFERENCES crm_customers(id),
    address_type VARCHAR(30) NOT NULL DEFAULT 'DELIVERY',  -- DELIVERY, BILLING, OTHER
    label VARCHAR(100),                                     -- "Casa", "Oficina", "Sucursal Norte"
    geography_id VARCHAR(36) REFERENCES crm_geography(id),

    -- Direccion textual
    line1 VARCHAR(200) NOT NULL,
    line2 VARCHAR(200),
    city VARCHAR(100),
    state VARCHAR(100),
    district VARCHAR(100),
    postal_code VARCHAR(12),
    country_code VARCHAR(5) NOT NULL DEFAULT 'PER',

    -- Geolocalizacion
    latitude NUMERIC(10, 7),
    longitude NUMERIC(10, 7),
    place_id VARCHAR(64),
    formatted_address VARCHAR(255),
    street_name VARCHAR(160),
    street_number VARCHAR(20),
    geocode_source VARCHAR(20),
    precision_meters INTEGER,
    gps_link VARCHAR(500),

    -- Contacto en esta direccion
    contact_name VARCHAR(100),
    contact_phone VARCHAR(50),
    contact_email VARCHAR(100),

    -- Auditoria
    notes VARCHAR(250),
    is_active BOOLEAN NOT NULL DEFAULT true,
    captured_by VARCHAR(36) REFERENCES users(id),
    captured_at TIMESTAMPTZ,

    -- Ubigeo Peru
    ubigeo_code VARCHAR(6),

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_customer_address_customer FOREIGN KEY (customer_id)
        REFERENCES crm_customers(id) ON DELETE CASCADE
);

CREATE INDEX idx_crm_customer_addresses_customer ON crm_customer_addresses(customer_id);
CREATE INDEX idx_crm_customer_addresses_tenant ON crm_customer_addresses(tenant_id);
CREATE INDEX idx_crm_customer_addresses_geography ON crm_customer_addresses(geography_id);
```

Reglas:
- `address_type` soporta al menos `FISCAL`, `DELIVERY`, `BILLING`, `OTHER`.
- solo una direccion del cliente puede ser la referenciada por `fiscal_address_id`.
- `geography_id` es opcional pero, si existe, debe pertenecer al mismo `country_code`.

### crm_customer_contacts

Contactos adicionales (telefonos, correos) por cliente.

Nota de evolucion documental:

- este bloque describe el modelo generico inicial de `contact_type` + `value` + `label`;
- para el cierre mas fuerte del customer core, `SPEC 0023D` lo supersede parcialmente y enriquece `crm_customer_contacts` con persona, cargo, telefono, email y vinculo opcional a direccion base.

```sql
CREATE TABLE crm_customer_contacts (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id),
    customer_id VARCHAR(36) NOT NULL REFERENCES crm_customers(id),
    contact_type VARCHAR(20) NOT NULL CHECK (contact_type IN ('PHONE', 'EMAIL', 'OTHER')),
    value VARCHAR(200) NOT NULL,
    label VARCHAR(100),
    is_primary BOOLEAN NOT NULL DEFAULT false,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_contact_customer FOREIGN KEY (customer_id)
        REFERENCES crm_customers(id) ON DELETE CASCADE
);

CREATE INDEX idx_crm_customer_contacts_customer ON crm_customer_contacts(customer_id);
```

### Nota sobre Cliente_Sucursal legacy

El legacy tiene `Cliente_Sucursal` como relacion cliente ↔ almacen. En esta iteracion
NO se crea una tabla `crm_customer_branches` porque:

- el maestro de almacenes vive hoy en `logistics` (`lg_warehouses`), no en kernel;
- crear una FK desde CRM hacia logistics introduciria una dependencia circular;
- la necesidad operativa inmediata del legacy se cubre a nivel de punto de entrega,
  agregando `warehouse_id` en `lg_delivery_points`.

Si en una iteracion futura `warehouses` se extrae a kernel o a un modulo compartido,
se podra agregar `crm_customer_warehouses` como reemplazo formal de `Cliente_Sucursal`.

---

## Migracion 2: 002_geography_seed.py

Geografia jerarquica auto-referenciada (pais → departamento → provincia → distrito → localidad).

```sql
CREATE TABLE crm_geography (
    id VARCHAR(36) PRIMARY KEY,
    parent_id VARCHAR(36) REFERENCES crm_geography(id),
    code VARCHAR(20),
    name VARCHAR(200) NOT NULL,
    level INTEGER NOT NULL CHECK (level BETWEEN 1 AND 5),  -- 1=Pais, 2=Depto, 3=Prov, 4=Dist, 5=Local
    country_code VARCHAR(5) NOT NULL,
    ubigeo_code VARCHAR(6),
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_crm_geography_parent ON crm_geography(parent_id);
CREATE INDEX idx_crm_geography_level ON crm_geography(level, country_code);
```

`crm_geography` es un catalogo global compartido, no tenant-aware.

Seed inicial: solo paises (Peru, Costa Rica, Espana). La carga de departamentos,
provincias y distritos se hace por pais en un seed global controlado. No se siembran
1874 distritos peruanos en la migracion base.

```python
# Seed de paises
countries = [
    {"code": "PER", "name": "Peru", "level": 1, "country_code": "PER"},
    {"code": "CRI", "name": "Costa Rica", "level": 1, "country_code": "CRI"},
    {"code": "ESP", "name": "Espana", "level": 1, "country_code": "ESP"},
]
```

---

## Migracion 3: 003_refactor_logistics.py

Refactoriza las 6 tablas de logistics que hoy tienen `customer_id` huerfano y
`customer_name` texto libre.

Politica final:

- `lg_delivery_points` es dato maestro operativo y NO conserva `customer_name`;
- tablas transaccionales (`lg_orders`, `lg_movements`, `lg_agenda_tasks`,
  `lg_cylinder_ownership`, `lg_cylinder_warranties`) SI conservan `customer_name`
  como snapshot historico de solo lectura.

### lg_delivery_points

```sql
-- 1. Agregar FK constraint a customer_id
ALTER TABLE lg_delivery_points
    ADD CONSTRAINT fk_lg_delivery_point_customer
    FOREIGN KEY (customer_id) REFERENCES crm_customers(id);

-- 2. Convertir customer_id a NOT NULL
-- NOTA: requiere que todos los registros tengan customer_id seteado antes
-- (se ejecuta como paso separado con validacion previa)
ALTER TABLE lg_delivery_points
    ALTER COLUMN customer_id SET NOT NULL;

-- 3. Agregar address_id opcional
ALTER TABLE lg_delivery_points
    ADD COLUMN contact_name VARCHAR(100),
    ADD COLUMN contact_phone VARCHAR(50),
    ADD COLUMN contact_email VARCHAR(100),
    ADD COLUMN warehouse_id VARCHAR(36) REFERENCES lg_warehouses(id),
    ADD COLUMN visit_day VARCHAR(50),
    ADD COLUMN time_window VARCHAR(50),
    ADD COLUMN instructions VARCHAR(200),
    ADD COLUMN service_time_min INTEGER,
    ADD COLUMN demand_units INTEGER,
    ADD COLUMN demand_weight_kg NUMERIC(19, 4),
    ADD COLUMN agent_user_id VARCHAR(36) REFERENCES users(id),
    ADD COLUMN fiscal_operation_document VARCHAR(50),
    ADD COLUMN fiscal_operation_type VARCHAR(30);

ALTER TABLE lg_delivery_points
    ADD COLUMN address_id VARCHAR(36) REFERENCES crm_customer_addresses(id);

-- 4. Eliminar customer_name (en delivery points NO se conserva snapshot)
ALTER TABLE lg_delivery_points DROP COLUMN customer_name;
```

Cobertura legacy de `Vehiculo_cliente_nuevo`:

| Legacy | Nuevo |
|--------|-------|
| Id_ClientePersona | customer_id |
| Direccion / Id_Direccion | address_id + direccion derivada |
| Contacto | contact_name |
| Telefono | contact_phone |
| Correoresp | contact_email |
| Id_Zona | zone_id |
| Dreparto | delivery_day |
| Dvisita | visit_day |
| Id_Agente_Asignado | agent_user_id |
| Id_Sucursal | warehouse_id |
| Id_RutaAsignada | no se persiste como FK estable; se resuelve en planificacion diaria |
| VentanaHorario | time_window |
| Indicaciones | instructions |
| TiempoServicioMin | service_time_min |
| DemandaUnidades | demand_units |
| DemandaPesoKg | demand_weight_kg |
| Documento_Fiscal_Operacion | fiscal_operation_document |
| TipoOperacionFiscal | fiscal_operation_type |

### lg_orders

```sql
ALTER TABLE lg_orders
    ADD CONSTRAINT fk_lg_order_customer
    FOREIGN KEY (customer_id) REFERENCES crm_customers(id);

-- customer_id debe volverse NOT NULL en orders
ALTER TABLE lg_orders
    ALTER COLUMN customer_id SET NOT NULL;

-- customer_name se deja como denormalizado (copia del legal_name al momento de crear la orden)
-- para mantener consistencia en documentos historicos
-- NO se elimina, pero se convierte en READ ONLY desde la API
```

### lg_movements

```sql
ALTER TABLE lg_movements
    ADD CONSTRAINT fk_lg_movement_customer
    FOREIGN KEY (customer_id) REFERENCES crm_customers(id);

-- customer_name se conserva como denormalizado (documento fiscal necesita el nombre en ese momento)
```

### lg_agenda_tasks

```sql
ALTER TABLE lg_agenda_tasks
    ADD CONSTRAINT fk_lg_agenda_task_customer
    FOREIGN KEY (customer_id) REFERENCES crm_customers(id);

ALTER TABLE lg_agenda_tasks
    ALTER COLUMN customer_id SET NOT NULL;
```

### lg_cylinder_ownership

```sql
ALTER TABLE lg_cylinder_ownership
    ADD CONSTRAINT fk_lg_ownership_customer
    FOREIGN KEY (customer_id) REFERENCES crm_customers(id);
```

### lg_cylinder_warranties

```sql
ALTER TABLE lg_cylinder_warranties
    ADD CONSTRAINT fk_lg_warranty_customer
    FOREIGN KEY (customer_id) REFERENCES crm_customers(id);

ALTER TABLE lg_cylinder_warranties
    ALTER COLUMN customer_id SET NOT NULL;
```

### Politica de denormalizacion de customer_name

`customer_name` NO se elimina de las tablas de logistics. Se conserva como campo
denormalizado que se copia del `legal_name` del cliente al momento de crear el
registro. Esto es necesario porque:

- un documento fiscal (movimiento, orden) debe conservar el nombre que tenia el
  cliente en el momento de la transaccion, aunque el cliente cambie de nombre despues;
- el campo se vuelve READ ONLY desde la API de logistics — solo se escribe desde
  el servicio al crear/confirmar, nunca se edita directamente.

En schemas y servicios, `customer_name` deja de ser un campo de entrada y pasa a ser
SOLO de respuesta (response_only).

---

## Backend — Logica de servicios

### services/customers.py

Servicio principal de CRUD de clientes.

**Metodos:**

`create_customer(db, tenant_id, actor_user_id, payload) -> Customer`
- Valida que `document_type_code` + `document_number` sean unicos por tenant
- Valida formato del documento segun pais via `fiscal_validator.validate()`
- Si `document_type_code` es RUC o CEDULA_JURIDICA, `first_name`/`last_name` se ignoran
- Crea el cliente
- Emite evento `crm.customer.created`
- Registra auditoria

`update_customer(db, customer_id, tenant_id, payload) -> Customer`
- Valida unicidad de documento (excluyendo el mismo cliente)
- Si cambio `document_number`, re-valida formato
- Emite evento `crm.customer.updated`

`get_customer(db, customer_id, tenant_id) -> Customer`
- Retorna cliente con direcciones, contactos y `fiscal_address_id`

`list_customers(db, tenant_id, filters) -> Page[Customer]`
- Filtros: search, document_type_code, country_code, is_active, payment_term_code
- `search` busca por ILIKE en legal_name, document_number, email, phone
- Paginacion con limit/offset
- Orden por legal_name ASC

`search_customers(db, tenant_id, query, limit=20) -> list[CustomerBrief]`
- Busqueda rapida para autocomplete/CustomerSearchDialog
- Retorna solo id, legal_name, document_number, document_type_code, email, phone
- Busca por coincidencia en legal_name, document_number, phone
- Limite fijo de 20 resultados
- Solo clientes activos

`toggle_active(db, customer_id, tenant_id) -> Customer`
- Cambia is_active de true a false o viceversa
- Valida que el cliente no tenga operaciones abiertas si se desactiva
- Emite evento `crm.customer.status_changed`

### services/addresses.py

CRUD de direcciones de clientes.

`create_address(db, tenant_id, customer_id, payload) -> CustomerAddress`
- Valida que el cliente exista y pertenezca al tenant
- Si no se especifica `geocode_source` o es MANUAL, lat/lng pueden ser null
- Si `geocode_source` es GOOGLE, valida que place_id no este vacio

`set_fiscal_address(db, customer_id, address_id, tenant_id)`
- Valida que la direccion pertenezca al cliente
- Actualiza `crm_customers.fiscal_address_id`

`update_address(db, address_id, tenant_id, payload) -> CustomerAddress`

`delete_address(db, address_id, tenant_id)`
- Eliminacion fisica (CASCADE desde customer)

`list_addresses(db, customer_id, tenant_id) -> list[CustomerAddress]`

### services/fiscal_validator.py

Validacion de formato de documentos de identidad por pais.

Interfaz:

```python
class FiscalValidationResult:
    is_valid: bool
    formatted: str | None       # version normalizada del documento
    error_message: str | None

def validate(document_type: str, document_number: str, country_code: str) -> FiscalValidationResult
```

**Implementacion por pais:**

Peru:
- RUC: 11 digitos exactos, modulo 11 con pesaje por posicion
  (factor 5-4-3-2-7-6-5-4-3-2, digito verificador en posicion 11)
- DNI: 8 digitos exactos, solo numeros

Costa Rica:
- Cedula Fisica: formato N-NNNN-NNNN (1 digito + guion + 4 + guion + 4)
- Cedula Juridica: formato N-NNN-NNNNNN (1 digito + guion + 3 + guion + 6)

Espana:
- NIF: 8 digitos + 1 letra de control (modulo 23 sobre el numero)
  Letras: TRWAGMYFPDXBNJZSQVHLCKE
- NIE: X/Y/Z + 7 digitos + 1 letra (mismo modulo 23, X=0, Y=1, Z=2)

### services/search.py

Busqueda multi-criterio optimizada.

Construye una consulta dinamica con los siguientes filtros opcionales:

- `search` (str): busqueda global por ILIKE en legal_name, document_number,
  email, phone, external_code
- `document_type` (str): filtrar por tipo de documento
- `country_code` (str): filtrar por pais
- `is_active` (bool): filtrar por estado
- `payment_term_code` (str): filtrar por forma de pago
- `created_after` / `created_before` (datetime): rango de fecha de creacion

Retorna pagina con los resultados mas el total count para paginacion.

### services/geography.py

Gestion de geografia jerarquica.

`list_countries() -> list[Geography]`
`list_departments(country_code) -> list[Geography]`
`list_provinces(department_id) -> list[Geography]`
`list_districts(province_id) -> list[Geography]`
`seed_geography(country_code) -> int`
- Siembra toda la geografia de un pais en el catalogo global (departamentos, provincias, distritos)
- Los datos vienen de un JSON embebido en codigo (no de API externa)
- Retorna cantidad de registros insertados

### services/catalog.py

Catalogos de solo lectura.

`list_document_types(country_code=None) -> list[DocumentType]`
`list_payment_terms() -> list[PaymentTerm]`

---

## Backend — Endpoints (router.py)

Base path: `/api/v1/plugins/crm`

### Clientes

| Metodo | Path | Permiso | Descripcion |
|--------|------|---------|-------------|
| GET | /customers | crm.customer.read | Listar clientes con filtros |
| GET | /customers/search | crm.customer.read | Busqueda rapida (autocomplete) |
| GET | /customers/{id} | crm.customer.read | Detalle del cliente |
| POST | /customers | crm.customer.create | Crear cliente |
| PUT | /customers/{id} | crm.customer.update | Actualizar cliente |
| PATCH | /customers/{id}/toggle-active | crm.customer.update | Activar/desactivar cliente |

### Direcciones

| Metodo | Path | Permiso | Descripcion |
|--------|------|---------|-------------|
| GET | /customers/{id}/addresses | crm.customer.read | Listar direcciones del cliente |
| POST | /customers/{id}/addresses | crm.customer.update | Crear direccion |
| PUT | /addresses/{id} | crm.customer.update | Actualizar direccion |
| PUT | /customers/{id}/fiscal-address/{address_id} | crm.customer.update | Marcar direccion fiscal |
| DELETE | /addresses/{id} | crm.customer.update | Eliminar direccion |

### Contactos

| Metodo | Path | Permiso | Descripcion |
|--------|------|---------|-------------|
| GET | /customers/{id}/contacts | crm.customer.read | Listar contactos |
| POST | /customers/{id}/contacts | crm.customer.update | Crear contacto |
| DELETE | /contacts/{id} | crm.customer.update | Eliminar contacto |

### Catalogos

| Metodo | Path | Permiso | Descripcion |
|--------|------|---------|-------------|
| GET | /catalog/document-types | crm.catalog.read | Tipos de documento (filtrable por pais) |
| GET | /catalog/payment-terms | crm.catalog.read | Formas de pago |

### Geografia

| Metodo | Path | Permiso | Descripcion |
|--------|------|---------|-------------|
| GET | /geography/countries | crm.geography.read | Paises |
| GET | /geography/departments | crm.geography.read | Departamentos de un pais |
| GET | /geography/provinces | crm.geography.read | Provincias de un departamento |
| GET | /geography/districts | crm.geography.read | Distritos de una provincia |
| POST | /geography/seed | crm.geography.manage | Sembrar geografia global por pais |

---

## Permisos

Registrados en `plugin.json` y sincronizados via runtime:

| Permiso | Descripcion |
|---------|-------------|
| crm.customer.read | Ver clientes, direcciones, contactos |
| crm.customer.create | Crear clientes |
| crm.customer.update | Actualizar clientes, activar/desactivar |
| crm.catalog.read | Leer catalogos (tipos doc, formas pago) |
| crm.geography.read | Leer geografia |
| crm.geography.manage | Sembrar/administrar geografia |

---

## Eventos

| Evento | Payload | Cuando se emite |
|--------|---------|-----------------|
| crm.customer.created | {customer_id, legal_name, document_number, country_code} | Al crear cliente |
| crm.customer.updated | {customer_id, changed_fields} | Al actualizar datos |
| crm.customer.status_changed | {customer_id, is_active, previous_status} | Al activar/desactivar |
| crm.customer.address_added | {customer_id, address_id} | Al agregar direccion |
| crm.customer.address_removed | {customer_id, address_id} | Al eliminar direccion |

---

## Frontend — Plugins

### register.ts

Registra:

- Ruta `/customers` → `CustomersListPage`
- Ruta `/customers/new` → `CustomerFormPage` (modo crear)
- Ruta `/customers/:id` → `CustomerFormPage` (modo editar)
- Ruta `/customers/:id/detail` → `CustomerDetailPage`
- Item en sidebar: "Clientes" con icono, permisos `crm.customer.read`
- Exporta `CustomerSearchDialog` para uso externo

### CustomersListPage

- Tabla con columnas: legal_name, document_number (con tipo), email, phone, country, is_active
- Filtros: busqueda global (input), tipo documento (select), pais (select), activo (switch)
- Paginacion (20 por pagina)
- Botones: Nuevo, Editar (navega a form), Ver detalle (navega a detail)
- Tooltip con resumen rapido al hover

### CustomerFormPage

Formulario multi-pestana:

**Pestana 1: Datos generales**
- Tipo de persona: Natural / Juridica (radio)
- Tipo documento (select desde catalogo, filtrado por pais)
- Numero documento (input con validacion en frontend)
- Nombre / Razon social (input)
- Nombre comercial (input)
- Codigo externo (input)
- Pais (select: PER, CRI, ESP)
- Email, Telefono, Celular (inputs)
- Forma de pago (select desde catalogo)
- Tipo facturacion (select: mensual, por_operacion)
- Activo (switch)

**Pestana 2: Direccion fiscal**
- Direccion (linea 1, linea 2)
- Pais, Departamento, Provincia, Distrito (selects en cascada desde geografia)
- Codigo postal
- GPS: latitud, longitud
- Boton "Abrir Google Maps" para capturar coordenadas
- Place ID / Formatted Address (si se capturo desde Google Maps)

**Pestana 3: Direcciones adicionales**
- Lista de direcciones adicionales (tabla)
- Boton "Agregar direccion" → modal con AddressSection
- Cada direccion: tipo (DELIVERY/BILLING/OTHER), etiqueta, direccion, contacto, GPS

**Pestana 4: Contactos**
- Lista de telefonos y correos adicionales
- Boton "Agregar contacto" → modal con tipo (PHONE/EMAIL), valor, etiqueta

Nota:
- esta UX corresponde al corte inicial de `0013`;
- `0023D` eleva este bloque a contactos base enriquecidos y deja el modelo generico como antecedente historico, no como limite final del customer core.

**Pestana 5: Puntos de entrega**
- Vista embebida de los `delivery_points` del cliente consumiendo endpoints de logistics
- Boton "Nuevo punto de entrega" navega o abre modal del flujo de logistics
- Muestra: zona, almacen, ruta, dia reparto, ventana, contacto, activo

**Pestana 6: Observaciones**
- Textarea de notas

### CustomerDetailPage

Pagina de solo lectura con:

- Cabecera con nombre, documento, pais, estado (activo/inactivo)
- Secciones colapsables: direccion fiscal, direcciones adicionales, contactos, puntos de entrega
- Boton "Editar" que navega al formulario en modo edicion
- Boton "Ver movimientos" que navega a MovementsPage de logistics filtrado por este cliente

### CustomerSearchDialog

Componente React reusable (modal/dialog) que otros plugins importan para seleccionar
un cliente.

Props:

```typescript
interface CustomerSearchDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    onSelect: (customer: CustomerBrief) => void;
    title?: string;
    tenantId?: string;       // opcional, default del contexto
}
```

Comportamiento:

- Modal con input de busqueda que hace debounced fetch a `/customers/search`
- Resultados en tabla: nombre, documento, email, telefono
- Al hacer clic en una fila, se llama `onSelect` y se cierra el modal
- Tecla Escape cierra sin seleccionar
- Click fuera del modal cierra sin seleccionar
- Estados: loading, empty, error
- Si solo hay un resultado exacto por documento, selecciona automaticamente (opcional)

Uso desde logistics:

```tsx
const [searchOpen, setSearchOpen] = useState(false);
const [selectedCustomer, setSelectedCustomer] = useState<CustomerBrief | null>(null);

return (
    <>
        <Button onClick={() => setSearchOpen(true)}>
            {selectedCustomer
                ? `${selectedCustomer.legal_name} (${selectedCustomer.document_number})`
                : "Seleccionar cliente"}
        </Button>
        <CustomerSearchDialog
            open={searchOpen}
            onOpenChange={setSearchOpen}
            onSelect={(c) => {
                setSelectedCustomer(c);
                setFormState(prev => ({ ...prev, customer_id: c.id, customer_name: c.legal_name }));
            }}
        />
    </>
);
```

### types.ts

```typescript
export interface CustomerBrief {
    id: string;
    legal_name: string;
    document_number: string;
    document_type_code: string;
    email: string | null;
    phone: string | null;
    country_code: string;
}

export interface Customer extends CustomerBrief {
    commercial_name: string | null;
    external_code: string | null;
    first_name: string | null;
    last_name: string | null;
    birth_date: string | null;
    fiscal_address_id: string | null;
    payment_term_code: string | null;
    billing_type: string | null;
    is_exempt: boolean;
    is_active: boolean;
    notes: string | null;
    addresses: CustomerAddress[];
    contacts: CustomerContact[];
    created_at: string;
    updated_at: string;
}

export interface CustomerAddress {
    id: string;
    address_type: string;
    label: string | null;
    geography_id: string | null;
    line1: string;
    line2: string | null;
    city: string | null;
    state: string | null;
    district: string | null;
    country_code: string;
    latitude: number | null;
    longitude: number | null;
    contact_name: string | null;
    contact_phone: string | null;
    is_active: boolean;
}

export interface CustomerContact {
    // Modelo inicial de 0013. Ver 0023D para el contrato enriquecido posterior.
    id: string;
    contact_type: 'PHONE' | 'EMAIL' | 'OTHER';
    value: string;
    label: string | null;
    is_primary: boolean;
}

export interface DocumentType {
    code: string;
    name: string;
    country_code: string;
    is_person: boolean;
    is_company: boolean;
}

export interface PaymentTerm {
    code: string;
    name: string;
    days: number;
    operation_type: string;
}

export interface GeographyItem {
    id: string;
    name: string;
    code: string | null;
    level: number;
    parent_id: string | null;
}
```

---

## Refactor de logistics

### plugin.json

```json
{
    "id": "logistics",
    "requires": ["crm"],
    ...
}
```

### Servicios afectados

Cada servicio debe cambiar de:

```python
# ANTES: recibe customer_name como texto
customer_name: str = payload.customer_name.strip()
```

a:

```python
# DESPUES: recibe customer_id, obtiene nombre del cliente real
from plugins.crm.backend.services.customers import get_customer

customer = get_customer(db, payload.customer_id, tenant_id)
if not customer:
    raise HTTPException(status_code=404, detail="Customer not found")
customer_name = customer.legal_name
```

**Archivos a modificar:**

| Archivo | Cambio |
|---------|--------|
| services/orders.py | `create_order`: validar customer_id, obtener legal_name |
| services/orders.py | `update_order`: customer_name READ ONLY |
| services/movements.py | `create_movement`: validar customer_id |
| services/movements.py | `list_movements`: filtro por customer_id (no customer_name ILIKE) |
| services/resources.py | `create_delivery_point`: customer_id obligatorio, address_id opcional |
| services/resources.py | `update_delivery_point`: customer_name READ ONLY |
| services/envase.py | `register_ownership`: customer_id obligatorio |
| services/extras.py | `create_warranty`: customer_id obligatorio |
| services/agenda.py | `create_task`: customer_id obligatorio |
| services/scan.py | Referencias a movement.customer_id ya existen, solo validar FK |

### Schemas afectados

- `customer_name` se marca como `Field(read_only=True)` en response schemas
- `customer_id` pasa de `str | None` a `str` (obligatorio) en request schemas
- Se agrega validacion de que customer_id existe (via `@field_validator`)

### Frontend afectado

| Pagina | Cambio |
|--------|--------|
| OrdersPage.tsx | Reemplazar `<Input customer_name>` por CustomerSearchDialog |
| MovementsPage.tsx | Reemplazar `<Input customer_name>` por CustomerSearchDialog |
| DeliveryPointsPage.tsx | Reemplazar `<Input customer_name>` por CustomerSearchDialog |
| AgendaPage.tsx | Reemplazar `<Input customer_name>` por CustomerSearchDialog |
| LogisticsPage.tsx | Reemplazar warranty customer input por CustomerSearchDialog |
| RoutesPage.tsx | Mostrar customer_name desde delivery_point (lectura) |

Tabla de politica final por entidad:

| Tabla logistics | customer_id | customer_name |
|-----------------|-------------|---------------|
| lg_delivery_points | FK real obligatoria | se elimina |
| lg_orders | FK real obligatoria | snapshot historico de solo lectura |
| lg_movements | FK real opcional segun tipo de movimiento | snapshot historico de solo lectura |
| lg_agenda_tasks | FK real obligatoria | snapshot historico de solo lectura |
| lg_cylinder_ownership | FK real opcional | snapshot historico de solo lectura |
| lg_cylinder_warranties | FK real obligatoria | snapshot historico de solo lectura |

### Plugin contract en logistics

Se debe agregar importacion permitida desde `plugins/crm/`:

```python
# En plugins/logistics/backend/plugin.py o servicios que lo necesiten
# Se permite importar desde plugins.crm.backend.services.customers
# porque CRM es una dependencia declarada (requires: ["crm"])
```

---

## plugin.json del CRM

```json
{
    "id": "crm",
    "name": "CRM",
    "version": "1.0.0",
    "api_version": "1",
    "requires": [],
    "backend_entrypoint": "backend.plugin:register",
    "frontend_entrypoint": "frontend/register.ts",
    "permissions": [
        "crm.customer.read",
        "crm.customer.create",
        "crm.customer.update",
        "crm.catalog.read",
        "crm.geography.read",
        "crm.geography.manage"
    ],
    "events": [
        "crm.customer.created",
        "crm.customer.updated",
        "crm.customer.status_changed",
        "crm.customer.address_added",
        "crm.customer.address_removed"
    ],
    "description": "Modulo de clientes con datos fiscales, direcciones, contactos, catalogos y geografia"
}
```

---

## Contracto API

El contrato detallado de los endpoints (request/response bodies, codigos de error,
ejemplos) vive en `docs/contracts/crm-api.md`.

---

## Pruebas

### Backend (pytest)

| Test | Que cubre |
|------|-----------|
| test_create_customer | Creacion exitosa, validacion de unicidad, validacion fiscal |
| test_create_customer_invalid_document | RUC mal formado, DNI corto, NIF con letra incorrecta |
| test_create_customer_duplicate | Mismo documento + tenant da 409 |
| test_create_customer_cross_tenant | Mismo documento en otro tenant es valido |
| test_update_customer | Cambio de datos, re-validacion fiscal si cambio documento |
| test_toggle_active | Activar/desactivar cliente |
| test_search_customers | Busqueda por nombre, documento, email, telefono |
| test_search_customers_pagination | Paginacion y ordenamiento |
| test_customer_addresses | CRUD de direcciones, CASCADE al eliminar cliente |
| test_customer_contacts | CRUD de contactos |
| test_set_fiscal_address | Asignacion de fiscal_address_id a una direccion del mismo cliente |
| test_geography_seed | Siembra de geografia para tenant |
| test_geography_list | Listado jerarquico |
| test_catalog_document_types | Listado filtrable por pais |
| test_catalog_payment_terms | Listado de formas de pago |
| test_fiscal_validator_peru_ruc | RUC valido e invalido con modulo 11 |
| test_fiscal_validator_peru_dni | DNI 8 digitos |
| test_fiscal_validator_cr_cedula | Cedula fisica y juridica |
| test_fiscal_validator_esp_nif | NIF con letra modulo 23 |
| test_fiscal_validator_esp_nie | NIE con letra modulo 23 |
| test_permissions_endpoints | Acceso sin permiso da 403 |
| test_tenant_isolation | Clientes de tenant A no visibles en tenant B |

### Integracion con logistics

| Test | Que cubre |
|------|-----------|
| test_create_order_with_customer | Order creada con customer_id valido |
| test_create_order_invalid_customer | Order con customer_id inexistente da 404 |
| test_delivery_point_customer_fk | Delivery point creado con customer valido |
| test_delivery_point_full_legacy_fields | zone, warehouse, route, visit_day, window, demand, agent |
| test_movement_customer_fk | Movement creado con customer valido |
| test_agenda_task_customer_fk | Agenda task creada con customer valido |
| test_cylinder_ownership_customer_fk | Ownership creado con customer valido |
| test_customer_name_denormalized | customer_name se copia del legal_name al crear |

---

## Riesgos y pendientes

| # | Riesgo | Mitigacion |
|---|--------|------------|
| R1 | Refactor de logistics requiere que `customer_id` exista en todos los registros actuales. Si hay registros con customer_id=NULL, la migracion falla. | Antes de la migracion 003, ejecutar script que identifica registros huerfanos y los asigna a un cliente "SIN ASIGNAR" por tenant, creado automaticamente. |
| R2 | La validacion fiscal modulo 11 de RUC peruano puede tener casos borde no documentados. | Implementar con tabla de factores y probar contra casos reales. Marcar como [VALIDAR] si hay dudas. |
| R3 | La geografia de Peru tiene 196 provincias y 1874 distritos. El JSON embebido pesa ~2MB. | Cargar por pais en un catalogo global, no por tenant y no en migracion base. |
| R4 | CustomerSearchDialog debe ser importable desde otros plugins. Si no se expone via SDK, cada plugin duplica el componente. | Exportar desde `plugins/crm/frontend/register.ts` y documentar en SDK. Los plugins que dependan de CRM pueden importarlo directamente. |
| R5 | logistics ya tiene customer_name como obligatorio en varias tablas. Si se elimina el input de texto y solo se acepta customer_id, los tests existentes pueden fallar. | Actualizar tests de logistics para usar customer_id real. Los fixtures de tests deben crear un customer primero. |
| R6 | El contrato `requires: ["crm"]` en logistics significa que logistics no puede habilitarse si CRM no lo esta. Para desarrollo local, hay que instalar ambos. | Documentar en README de logistics que CRM es prerequisito. El seed demo debe instalar ambos. |
| R7 | `Cliente_Sucursal` no se modela 1:1 en CRM porque almacenes viven hoy en logistics. | Cubrir la necesidad operativa en `lg_delivery_points.warehouse_id` y reevaluar si `warehouses` se extrae a un modulo compartido. |
| R8 | Hay registros legacy o actuales de logistics con `customer_name` pero sin `customer_id`. | Migracion previa: agrupar por `tenant_id + normalize(customer_name)`, crear clientes placeholder autogenerados y relinkear antes de imponer NOT NULL/FK. |

---

## Orden de implementacion

1. Migracion 001 — tablas CRM (customers, addresses, contacts, document_types, payment_terms)
2. Catalogos seed (document_types, payment_terms)
3. Servicio `fiscal_validator.py` con tests
4. Servicio `customers.py` (CRUD basico)
5. Servicio `addresses.py`
6. Servicio `search.py` (busqueda multi-criterio)
7. Router con endpoints de clientes
8. Frontend: CustomersListPage + CustomerFormPage
9. Frontend: CustomerSearchDialog
10. Migracion 002 — geography seed global + endpoints
11. Servicio geography.py
12. Frontend: CustomerDetailPage
13. Migracion 003 — refactor FKs de logistics
14. Refactor servicios de logistics (orders, movements, resources, envase, extras, agenda, scan)
15. Refactor schemas de logistics
16. Refactor frontend de logistics (5 paginas)
17. Actualizar plugin.json de logistics (requires: ["crm"])
18. Migracion de datos actual: agrupar `customer_name` legacy/actual, crear placeholders y relinkear
19. Tests de integracion CRM + logistics
20. Contracto API `docs/contracts/crm-api.md`
