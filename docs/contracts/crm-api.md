# CRM API Contract

## Estado

Vigente para implementacion de `SPEC 0013` y refactor de integracion con `logistics`.

## Base path

`/api/v1/plugins/crm`

## Permisos usados

- `crm.customer.read`
- `crm.customer.create`
- `crm.customer.update`
- `crm.catalog.read`
- `crm.geography.read`
- `crm.geography.manage`

## Eventos emitidos

- `crm.customer.created`
- `crm.customer.updated`
- `crm.customer.status_changed`
- `crm.customer.address_added`
- `crm.customer.address_removed`

## Reglas transversales

- todos los endpoints son tenant-aware;
- todo `customer_id` debe pertenecer al tenant activo;
- `customer_name` no es campo de entrada en CRM ni en los flujos refactorizados de logistics;
- `document_type_code + document_number` debe ser unico por tenant;
- `fiscal_address_id` debe apuntar a una direccion del mismo cliente;
- `crm_geography` es catalogo global, no por tenant.

## Errores comunes

| Codigo | Cuando aplica |
|--------|---------------|
| 400 | payload invalido, documento mal formado, direccion fiscal inconsistente |
| 401 | token ausente o invalido |
| 403 | permiso insuficiente |
| 404 | cliente, direccion o catalogo no encontrado |
| 409 | documento duplicado por tenant |
| 422 | validacion de schema Pydantic |

Formato de error esperado:

```json
{
  "detail": "Customer not found"
}
```

o para validacion fiscal:

```json
{
  "detail": {
    "code": "INVALID_DOCUMENT",
    "message": "RUC invalido para Peru"
  }
}
```

## Catalogos

### GET `/catalog/document-types`

Permiso: `crm.catalog.read`

Query params opcionales:

- `country_code`
- `active`

Response:

```json
[
  {
    "code": "RUC",
    "name": "RUC",
    "country_code": "PER",
    "description": "Registro Unico de Contribuyentes",
    "is_person": false,
    "is_company": true,
    "validation_pattern": "\\d{11}",
    "is_active": true
  }
]
```

### GET `/catalog/payment-terms`

Permiso: `crm.catalog.read`

Response:

```json
[
  {
    "code": "CONTADO",
    "name": "Contado",
    "description": null,
    "days": 0,
    "operation_type": "CONTADO",
    "is_active": true
  }
]
```

## Geografia

### GET `/geography/countries`

Permiso: `crm.geography.read`

Response:

```json
[
  {
    "id": "uuid",
    "parent_id": null,
    "code": "PER",
    "name": "Peru",
    "level": 1,
    "country_code": "PER",
    "ubigeo_code": null,
    "is_active": true
  }
]
```

### GET `/geography/departments`

Permiso: `crm.geography.read`

Query params obligatorios:

- `country_code`

### GET `/geography/provinces`

Permiso: `crm.geography.read`

Query params obligatorios:

- `department_id`

### GET `/geography/districts`

Permiso: `crm.geography.read`

Query params obligatorios:

- `province_id`

### POST `/geography/seed`

Permiso: `crm.geography.manage`

Request:

```json
{
  "country_code": "PER"
}
```

Response:

```json
{
  "country_code": "PER",
  "inserted": 2067
}
```

## Clientes

### GET `/customers`

Permiso: `crm.customer.read`

Query params opcionales:

- `search`
- `document_type_code`
- `country_code`
- `is_active`
- `payment_term_code`
- `limit`
- `offset`

Response:

```json
{
  "items": [
    {
      "id": "uuid",
      "legal_name": "GLP Norte SAC",
      "commercial_name": "GLP Norte",
      "external_code": "CLI-0001",
      "document_type_code": "RUC",
      "document_number": "20123456789",
      "country_code": "PER",
      "email": "ventas@glpnorte.pe",
      "phone": "014445555",
      "mobile": null,
      "payment_term_code": "CONTADO",
      "billing_type": "por_operacion",
      "is_exempt": false,
      "is_active": true,
      "fiscal_address_id": "uuid|null",
      "created_at": "2026-06-27T00:00:00Z",
      "updated_at": "2026-06-27T00:00:00Z"
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

`search` filtra por:

- `legal_name`
- `commercial_name`
- `document_number`
- `phone`
- `email`
- `external_code`
- localidad (`district`, `city`, `state`)
- texto de direccion base

### GET `/customers/search`

Permiso: `crm.customer.read`

Query params:

- `query` obligatorio
- `limit` opcional, default `20`, max `50`

Uso principal: `CustomerSearchDialog` y selects remotos de otros plugins.

Response:

```json
[
  {
    "id": "uuid",
    "legal_name": "GLP Norte SAC",
    "commercial_name": "GLP Norte",
    "display_name": "GLP Norte",
    "document_type_code": "RUC",
    "document_number": "20123456789",
    "external_code": "CLI-0001",
    "email": "ventas@glpnorte.pe",
    "phone": "014445555",
    "country_code": "PER",
    "fiscal_address_summary": "Av. Peru 123, Lima",
    "locality_summary": "Lima"
  }
]
```

### GET `/customers/{id}`

Permiso: `crm.customer.read`

Response:

```json
{
  "id": "uuid",
  "legal_name": "GLP Norte SAC",
  "commercial_name": "GLP Norte",
  "external_code": "CLI-0001",
  "document_type_code": "RUC",
  "document_number": "20123456789",
  "country_code": "PER",
  "email": "ventas@glpnorte.pe",
  "phone": "014445555",
  "mobile": null,
  "economic_activity_code": "4671",
  "economic_activity_description": "Comercio de combustibles",
  "activity_validated": false,
  "activity_validation_source": null,
  "activity_validation_date": null,
  "payment_term_code": "CONTADO",
  "billing_type": "por_operacion",
  "is_exempt": false,
  "first_name": null,
  "last_name": null,
  "birth_date": null,
  "gender": null,
  "notes": null,
  "is_active": true,
  "fiscal_address_id": "uuid",
  "addresses": [],
  "contacts": [],
  "created_at": "2026-06-27T00:00:00Z",
  "updated_at": "2026-06-27T00:00:00Z"
}
```

### POST `/customers`

Permiso: `crm.customer.create`

Request:

```json
{
  "external_code": "CLI-0001",
  "legal_name": "GLP Norte SAC",
  "commercial_name": "GLP Norte",
  "document_type_code": "RUC",
  "document_number": "20123456789",
  "country_code": "PER",
  "email": "ventas@glpnorte.pe",
  "phone": "014445555",
  "mobile": null,
  "economic_activity_code": "4671",
  "economic_activity_description": "Comercio de combustibles",
  "payment_term_code": "CONTADO",
  "billing_type": "por_operacion",
  "is_exempt": false,
  "first_name": null,
  "last_name": null,
  "birth_date": null,
  "gender": null,
  "notes": "Cliente mayorista"
}
```

Reglas:

- si `document_type_code` es `RUC`, `NIF`, `CEDULA_JURIDICA`, se asume persona juridica;
- si `document_type_code` es `DNI`, `NIE`, `CEDULA_FISICA`, se permite persona natural;
- `fiscal_address_id` no se acepta en alta inicial si la direccion aun no existe;
- la direccion fiscal normalmente se crea despues via `/customers/{id}/addresses` y luego se marca.

Response: `201 Created` con el cliente creado.

### PUT `/customers/{id}`

Permiso: `crm.customer.update`

Request: mismo shape que `POST /customers`, todos los campos editables.

Reglas:

- si cambia `document_number`, se revalida el documento;
- `customer_name` no existe como alias editable;
- no se puede cambiar el `tenant_id`.

Response: `200 OK` con cliente actualizado.

### PATCH `/customers/{id}/toggle-active`

Permiso: `crm.customer.update`

Request:

```json
{
  "is_active": false,
  "reason": "Cliente inactivo por cierre comercial"
}
```

Reglas:

- si el cliente tiene operaciones abiertas que no permiten desactivacion, responde `409`.

## Direcciones

### GET `/customers/{id}/addresses`

Permiso: `crm.customer.read`

Response:

```json
[
  {
    "id": "uuid",
    "customer_id": "uuid",
    "address_type": "FISCAL",
    "label": "Fiscal",
    "geography_id": "uuid|null",
    "line1": "Av. Peru 123",
    "line2": null,
    "city": "Lima",
    "state": "Lima",
    "district": "Lima",
    "postal_code": null,
    "country_code": "PER",
    "latitude": -12.0464,
    "longitude": -77.0428,
    "place_id": null,
    "formatted_address": "Av. Peru 123, Lima",
    "street_name": "Av. Peru",
    "street_number": "123",
    "geocode_source": "MANUAL",
    "precision_meters": null,
    "gps_link": null,
    "contact_name": null,
    "contact_phone": null,
    "contact_email": null,
    "notes": null,
    "is_active": true,
    "captured_by": null,
    "captured_at": null,
    "ubigeo_code": null,
    "created_at": "2026-06-27T00:00:00Z",
    "updated_at": "2026-06-27T00:00:00Z"
  }
]
```

### POST `/customers/{id}/addresses`

Permiso: `crm.customer.update`

Request:

```json
{
  "address_type": "DELIVERY",
  "label": "Sucursal Norte",
  "geography_id": null,
  "line1": "Jr. Comercio 450",
  "line2": null,
  "city": "Lima",
  "state": "Lima",
  "district": "San Martin de Porres",
  "postal_code": null,
  "country_code": "PER",
  "latitude": null,
  "longitude": null,
  "place_id": null,
  "formatted_address": null,
  "street_name": null,
  "street_number": null,
  "geocode_source": "MANUAL",
  "precision_meters": null,
  "gps_link": null,
  "contact_name": "Juan Perez",
  "contact_phone": "999888777",
  "contact_email": "recepcion@glpnorte.pe",
  "notes": null,
  "ubigeo_code": null
}
```

### PUT `/addresses/{id}`

Permiso: `crm.customer.update`

Request: mismo shape que `POST /customers/{id}/addresses`.

### PUT `/customers/{id}/fiscal-address/{address_id}`

Permiso: `crm.customer.update`

Reglas:

- la direccion debe pertenecer al cliente;
- si no pertenece, responde `400`;
- si la direccion esta inactiva, responde `409`.

Response:

```json
{
  "customer_id": "uuid",
  "fiscal_address_id": "uuid"
}
```

### DELETE `/addresses/{id}`

Permiso: `crm.customer.update`

Reglas:

- no se puede eliminar una direccion si es la `fiscal_address_id` activa del cliente;
- en ese caso responde `409` y se debe reasignar otra direccion fiscal primero.

## Contactos

### GET `/customers/{id}/contacts`

Permiso: `crm.customer.read`

### POST `/customers/{id}/contacts`

Permiso: `crm.customer.update`

Request:

```json
{
  "contact_type": "EMAIL",
  "value": "cobranzas@glpnorte.pe",
  "label": "Cobranza",
  "is_primary": false
}
```

### DELETE `/contacts/{id}`

Permiso: `crm.customer.update`

## Integracion con logistics

### Reglas de request para logistics

Despues del refactor, estos endpoints de logistics cambian su contrato funcional:

- `POST /api/v1/plugins/logistics/orders`
- `PUT /api/v1/plugins/logistics/orders/{id}`
- `POST /api/v1/plugins/logistics/movements`
- `POST /api/v1/plugins/logistics/agenda`
- `POST /api/v1/plugins/logistics/delivery-points`
- `POST /api/v1/plugins/logistics/warranties`
- `POST /api/v1/plugins/logistics/ownership`

Nuevo criterio:

- `customer_id` se envia siempre como referencia primaria;
- `customer_name` no se acepta en request;
- el backend de logistics resuelve `customer_name = customer.legal_name` y lo guarda
  solo como snapshot historico donde aplique.

### Politica final por tabla

| Tabla | customer_id | customer_name |
|-------|-------------|---------------|
| `lg_delivery_points` | obligatorio, FK real | eliminado |
| `lg_orders` | obligatorio, FK real | snapshot historico |
| `lg_movements` | opcional segun tipo | snapshot historico |
| `lg_agenda_tasks` | obligatorio, FK real | snapshot historico |
| `lg_cylinder_ownership` | opcional | snapshot historico |
| `lg_cylinder_warranties` | obligatorio, FK real | snapshot historico |

### Ejemplo de request nuevo en logistics: orden

```json
{
  "customer_id": "uuid",
  "movement_type": "SC",
  "warehouse_id": "uuid",
  "notes": "Entrega urgente",
  "items": [
    {
      "product_name": "GLP 10kg",
      "quantity_requested": 10
    }
  ]
}
```

### Ejemplo de response de logistics: orden

```json
{
  "id": "uuid",
  "customer_id": "uuid",
  "customer_name": "GLP Norte SAC",
  "movement_type": "SC",
  "status": "PENDIENTE"
}
```

## Casos especiales

### Clientes placeholder para migracion

Durante la migracion de registros existentes de logistics con `customer_name` pero sin
`customer_id`, se permite crear clientes autogenerados con estas reglas:

- `external_code = AUTO-{hash}`
- `legal_name = customer_name original`
- `document_type_code = OTRO`
- `document_number = AUTO-{hash}`
- `notes` incluye `autogenerado_por_migracion_logistics`

Estos clientes son validos tecnicamente pero deben quedar claramente identificados para
depuracion posterior.

### Desactivacion de clientes

Desactivar un cliente NO elimina ni modifica sus registros transaccionales historicos en logistics.

Efecto esperado:

- ya no aparece por defecto en `GET /customers/search`;
- puede seguir siendo visible en `GET /customers/{id}`;
- orders, movements, warranties y ownership historicos conservan `customer_name` snapshot.
