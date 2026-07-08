# Faltantes — Contracts (0023AD) y specs relacionadas

## Core Internal API: patrón de comunicación inter-plugin

### Regla

Ningún plugin importa modelos de otro plugin directamente. Toda comunicación entre plugins va por `core/internal_api/` que usa httpx real sobre los endpoints REST públicos.

### Módulos futuros que deben usar este patrón

| Módulo | ¿Existe? | Dependencias esperadas |
|--------|----------|----------------------|
| Caja (pos) | ❌ No creado | Productos (catálogos, precios), Clientes, Logistics (envases) |
| Ventas | ❌ No creado | Productos, Clientes, Precios, Logistics |
| Compras | ❌ No creado | Productos, Proveedores, Logistics |
| Facturación | ❌ No creado | Ventas, Clientes, Productos, CRM (fiscal) |

### Implementación pendiente

| Item | Prioridad |
|------|-----------|
| `core/internal_api/client.py` — httpx singleton con config, timeout, retry | Alta (bloqueante) |
| `core/internal_api/catalog.py` — resolve_brand, resolve_gas_product, resolve_condition | Alta |
| `core/internal_api/errors.py` — InternalApiError, NotFound, Timeout | Alta |
| `SYSTUTOR_INTERNAL_API_URL` + `SYSTUTOR_INTERNAL_API_KEY` en settings | Alta |
| Endpoints individuales en productos: `GET /brands/{id}`, `GET /conditions/{code}`, `GET /products/{id}/basic` | Media |
| Migrar `product_bridge.py` de logistics a `core/internal_api/` | Media |
| Documentar patrón en `docs/adr/0021-core-internal-api.md` | Baja |

## 0023AD — Contratos de envases (implementado ~70%)

### Backend

| Item | Estado | Notas |
|------|--------|-------|
| Modelos `lg_cylinder_contracts` + `lg_cylinder_contract_items` | ✅ | Existen |
| `GET /cylinders/contracts` (list con filtros) | ✅ | |
| `GET /cylinders/contracts/{id}` (detail con items) | ✅ | Se arregló `_contract_to_read` para consultar items explícitamente (faltaba relationship) |
| `POST /cylinders/contracts` (crear) | ✅ | |
| `PATCH /cylinders/contracts/{id}` (actualizar) | ✅ | |
| `POST /cylinders/contracts/{id}/activate` | ✅ | |
| `POST /cylinders/contracts/{id}/terminate` | ✅ | |
| `POST /cylinders/contracts/{id}/cancel` | ✅ | |
| `GET /cylinders/contracts/{id}/items` | ✅ | |
| `POST /cylinders/contracts/{id}/items` (agregar item) | ✅ | |
| `PATCH /cylinders/contracts/{id}/items/{item_id}/deliver` | ✅ | |
| `PATCH /cylinders/contracts/{id}/items/{item_id}/return` | ✅ | |
| `POST /cylinders/contracts/{id}/renew` (renovar) | ✅ | Implementado en v1. Mantiene `contract_number` y actualiza vigencia |
| `GET /customers/{customer_id}/contracts` | ❌ | No existe como endpoint separado (se puede filtrar por `customer_id` en el list) |
| Contrato modelado como documento numerado `CT...` | ✅ | V1 reintroduce `contract_number`, `series` y correlativo contractual como construcción OSS alineada al patrón documental legacy |
| `customer_snapshot` al activar | ⚠️ | Se mantiene como compatibilidad transicional; no es el centro del modelo contractual |
| Firma (`signed_at`, `signed_by`, `signature_type`) | ❌ | Modelo tiene campos pero no hay UI ni lógica de firma |
| Liberar cilindros al terminar contrato (regla 6 anterior) | ✅ | Ya no corresponde como gap de 0023AD: la spec corregida elimina esa regla porque legacy no libera automáticamente |
| Historial contractual | ✅ | V1 agrega `lg_cylinder_contract_history` y endpoint de lectura |
| Relación `contract_items` en modelo SQLAlchemy | ❌ | Sigue sin `relationship()`. La lectura continúa resolviéndose por query explícita |
| Eventos de auditoría | ⚠️ | La v1 emite auditoría/eventos en create/update/issue/renew/cancel/item flows; falta cobertura más amplia |
| Tests | ⚠️ | Hay prueba unitaria backend del formato contractual y test frontend del form/badges; faltan pruebas integrales |

### Frontend

| Item | Estado | Notas |
|------|--------|-------|
| ContractsSection (list + filters) | ✅ | DataTable con búsqueda, filtros por status/tipo |
| ContractFormDialog (create/edit) | ✅ | Con CustomerSearchDialog y cylinder SearchDialog |
| ContractStatusBadge | ✅ | |
| ContractDetailDialog | ⚠️ | Mejoró con historial visible, pero todavía no es un detalle completo por tabs |
| Agregar item con SearchDialog de cilindros | ✅ | |
| Marcar entregado/devuelto desde detalle | ✅ | |
| ContractItemForm como componente separado | ❌ | El form de agregar item está inline en ContractsPage, no como wrapper dominio |
| ContractCard para CRM | ❌ | La spec pide una sección "Contratos de envases activos" en la ficha de cliente |
| Navegación cilindro → contrato activo | ❌ | En detalle del cilindro debe verse el contrato activo |
| UX/UI refinements | ⚠️ | La v1 ya soporta emitir, firmar, renovar y vencer; aún faltan refinamientos visuales y de flujo |
| customer_name en item de contrato | ❌ | Sigue pendiente si se quiere UX adicional, pero no debe confundirse con `Dueño` del envase ni con numeración documental |

### Permisos

| Permiso | Estado |
|---------|--------|
| `logistics.contract.view` | ✅ |
| `logistics.contract.create` | ✅ |
| `logistics.contract.update` | ✅ |
| `logistics.contract.activate` | ✅ |
| `logistics.contract.terminate` | ✅ |
| `logistics.contract.renew` | ❌ No implementado |

## 0023B — Pesos promedio (descartado / reemplazado)

| Item | Estado | Notas |
|------|--------|-------|
| `lg_cylinder_average_weights` | ❌ | Eliminado. Se reemplaza por `prod_products.default_weight_kg` |
| Endpoints `/cylinders/average-weights` | ❌ | Eliminados |
| Matching por scoring | ❌ | Eliminado |
| Fallback actual | ✅ | `weight_current → weight_origin → product.default_weight_kg → 0` |
| UI admin de pesos promedio | ❌ | Eliminada |
| Badge en detalle | ✅ | Muestra `peso por defecto de producto` cuando aplica |

## 0023C — Trazabilidad extendida (no iniciado)

- Endpoint `GET /cylinders/{id}/traceability` no existe
- Vista unificada `CylinderTraceabilityTimeline` no existe
- Paginación y filtros no implementados
- `FullDetailInfoDialog` aún usa tablas sueltas

## Core Internal API — bridge HTTP multi-plugin (no iniciado)

Refactorizar `product_bridge.py` de logistics para que viva en `core/internal_api/` y use httpx real en vez de imports directos a modelos de productos.

| Item | Estado | Notas |
|------|--------|-------|
| `apps/api/app/core/internal_api/client.py` | ❌ | httpx client singleton con timeout, retry, config |
| `apps/api/app/core/internal_api/catalog.py` | ❌ | resolve_brand, resolve_gas_product, resolve_condition via HTTP |
| `apps/api/app/core/internal_api/errors.py` | ❌ | InternalApiError, NotFound |
| `apps/api/app/core/internal_api/__init__.py` | ❌ | exporta funciones públicas |
| `product_bridge.py` → usar `core.internal_api` | ❌ | Reemplazar imports directos por llamadas al core |
| `SYSTUTOR_INTERNAL_API_URL` en settings | ❌ | URL base + token de servicio interno |
| Endpoints individuales en productos (`GET /brands/{id}`, etc.) | ❌ | Hoy solo hay listados, no lookup por ID |

## Bugs conocidos

- `active: undefined` en `fetchFn` de `SearchDialog` no funciona como esperado porque el backend por defecto filtra `is_active=True`. No hay forma de pedir "todos" desde la API actualmente
- `_contract_to_read` usa consulta explícita a DB en vez de relationship (workaround, no fix real)
- `listGasProducts()` en `SearchDialog` no acepta filtro de búsqueda (trae todos siempre)
