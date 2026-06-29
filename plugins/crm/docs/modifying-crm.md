# Modifying CRM

## Propósito

Esta guía existe para modificar el plugin `crm` sin tener que reconstruir mentalmente
todo el módulo cada vez.

## Qué vive en CRM

El plugin `crm` es dueño de:

- `crm_customers`
- `crm_customer_addresses`
- `crm_customer_contacts`
- `crm_document_types`
- `crm_payment_terms`
- `crm_geography`

También es dueño de la validación fiscal multi-país y del componente frontend
`CustomerSearchDialog`.

## Qué NO vive en CRM

No vive aquí:

- auth
- roles/permisos del kernel
- runtime de plugins
- almacenes (`lg_warehouses`)
- rutas operativas (`lg_routes`)
- puntos de entrega como operación diaria

`logistics` sigue siendo dueño de `lg_delivery_points`, pero depende de `crm_customers`.

## Regla de ownership con logistics

### CRM controla

- identidad del cliente
- documento fiscal
- estado activo/inactivo
- direcciones
- contactos
- catálogos de documento y pago

### Logistics controla

- `delivery_day`
- `visit_day`
- `zone_id`
- `warehouse_id`
- `time_window`
- `instructions`
- `service_time_min`
- `demand_units`
- `demand_weight_kg`
- `agent_user_id`

Si necesitas tocar esos campos, probablemente el cambio va en `plugins/logistics/`, no en CRM.

## Estructura backend

### `backend/models.py`

Toca este archivo cuando cambies estructura de datos.

Regla:
- todo cambio estructural relevante debe venir acompañado de una nueva migración en
  `plugins/crm/migrations/`.

### `backend/router.py`

Toca este archivo cuando cambies el contrato HTTP.

Regla:
- si agregas/modificas endpoints, actualiza también `docs/contracts/crm-api.md`.

### `backend/services/customers.py`

Es el núcleo del dominio.

Tócalo para:
- reglas de unicidad
- lógica de activación/desactivación
- validaciones de negocio del cliente
- búsquedas

### `backend/services/addresses.py`

Tócalo para:
- reglas de dirección fiscal
- validaciones de geografía
- altas/bajas de contactos y direcciones

### `backend/services/fiscal_validator.py`

Es la única fuente de verdad para validación por país.

Si agregas un país nuevo:
1. agrega tipos de documento en `catalog.py`
2. agrega validación aquí
3. agrega tests en `apps/api/tests/test_crm_plugin.py`
4. actualiza `docs/contracts/crm-api.md`

## Estructura frontend

### `frontend/api.ts`

Cambios de payload o response del backend deben reflejarse aquí primero.

### `frontend/components/CustomerSearchDialog.tsx`

Este componente es reusable por otros plugins.

No lo dupliques en `logistics` ni en otro módulo.
Si falta una variante, extiéndelo con props.

### `frontend/pages/CustomerFormPage.tsx`

Este archivo concentra el flujo de crear/editar cliente.

Si agregas campos nuevos al cliente:
1. agrégalos en `types.ts`
2. agrégalos en `api.ts`
3. agrégalos en el form state
4. agrégalos al submit

### `frontend/pages/CustomerDetailPage.tsx`

Úsalo para vistas de lectura y enlaces hacia otros plugins.

No metas lógica de mutación compleja aquí.

## Migraciones

### Convención

- `001_*` crea núcleo CRM
- `002_*` geografía
- `003_*` integración/refactor con logistics
- siguientes revisiones continúan `0004`, `0005`, etc.

### Regla práctica

Si cambias columnas en `crm_*`:
- actualiza `models.py`
- agrega migración nueva, no edites revisiones anteriores

Si cambias integración con `lg_*`:
- revisa si el cambio pertenece a CRM o a logistics
- evita meter lógica operativa de logistics dentro de CRM

## Tests que debes tocar según el cambio

### Si cambias validación fiscal

Toca:
- `apps/api/tests/test_crm_plugin.py`

### Si cambias customer search

Toca:
- `apps/api/tests/test_crm_plugin.py`
- `frontend/components/CustomerSearchDialog.tsx`

### Si cambias customer_id/customer_name en logistics

Toca:
- `apps/api/tests/test_logistics_plugin.py`
- páginas de `plugins/logistics/frontend/`

## Reglas de evolución

### Para agregar proveedores

No metas proveedores en `crm_customers`.

Haz una decisión explícita:
- o crear `crm_suppliers`
- o crear plugin nuevo (`purchasing`, `suppliers`)

### Para agregar créditos o bancos

Esos datos estaban en el legacy, pero hoy quedaron fuera del corte.

Si se agregan:
- documentar primero si siguen perteneciendo a CRM o a finanzas
- no mezclarlos con customer core sin una spec nueva

### Para agregar geografía completa por país

Mantener `crm_geography` global.
No duplicar por tenant salvo requerimiento explícito.

## Checklist rápido antes de merge

1. ¿Cambié modelos? entonces hice migración nueva
2. ¿Cambié endpoints? entonces actualicé `docs/contracts/crm-api.md`
3. ¿Cambié reglas fiscales? entonces actualicé tests
4. ¿Toqué integración con logistics? entonces corrí tests CRM + logistics
5. ¿Toqué frontend compartido? entonces verifiqué `CustomerSearchDialog`

## Archivos de referencia

- `docs/adr/0012-crm-plugin-clientes.md`
- `docs/specs/core/0013-crm-plugin.md`
- `docs/contracts/crm-api.md`
- `docs/docs-systutor-legacy/modulo_clientes.md`
