# SPEC 0023AN — Pesos promedio: integración con catálogos y visibilidad en envases

## Estado

Obsoleta / reemplazada — 2026-07-07

> Nota: el enfoque de `pesos promedio` en `logistics` fue descartado.
> Se reemplazó por `prod_products.default_weight_kg` como fuente de peso por defecto.

## Problema

La implementación inicial de `0023B` (pesos promedio) tenía dos carencias:

1. **Catálogos no integrados** — los campos `brand_id` y `gas_group_id` en el CRUD de pesos promedio eran IDs libres, cuando debían usar los catálogos existentes via `SearchDialog`.

2. **Sin visibilidad en el envase** — el detalle del cilindro mostraba `(peso promedio)` pero no decía cuál registro de peso promedio se aplicaba ni por qué combinación matcheó.

## Solución implementada

### 1. Consolidación de catálogos: productos como fuente única de verdad

Se eliminaron las tablas duplicadas `lg_brands`, `lg_gas_products` y `lg_cylinder_conditions` de logistics. Ahora:

| Catálogo | Fuente única | Endpoint |
|----------|-------------|----------|
| Marcas | `prod_brands` (productos) | `GET /api/v1/plugins/productos/catalog/brands` |
| Productos gas | `prod_products` (productos, cond=GAS) | `GET /api/v1/plugins/productos/catalog/gas-products` |
| Condiciones | `prod_conditions` (productos) | `GET /api/v1/plugins/productos/catalog/conditions` |

**Frontend**: los `SearchDialog` ahora llaman directamente a los endpoints de productos en lugar de logistics. Sin cache, sin staleTime — siempre datos frescos.

**Backend**: se creó `product_bridge.py` como único punto de acceso desde logistics a productos. Las funciones de resolución de nombres (brand, gas, condition) están aisladas para migrar a REST puro en el futuro.

**FKs**: las columnas `brand_id`, `gas_group_id`, `condition` en `lg_cylinders`, `lg_cylinder_average_weights` y `lg_cylinder_contracts` ahora apuntan directamente a `prod_brands`, `prod_products` y `prod_conditions`.

### 2. Nuevo endpoint en productos

Se agregó `GET /api/v1/plugins/productos/catalog/gas-products` que devuelve:

```json
[
  {
    "id": "uuid",
    "name": "GLP 10kg",
    "code": "GLP-10",
    "content_kg": 10.0,
    "is_active": true,
    "created_at": "...",
    "updated_at": "..."
  }
]
```

### 3. Resultado final adoptado

El CRUD de pesos promedio fue eliminado. El fallback vigente en envases quedó así:

`weight_current -> weight_origin -> product.default_weight_kg -> 0`

## Migración BD

Se agregó migración `0014` que:
1. Elimina constraints FK viejas a tablas `lg_*`
2. Migra datos: mapea UUIDs de `lg_brands` → `prod_brands` por `code`, y `lg_gas_products` → `prod_products` por `sku`
3. Dropea tablas `lg_brands`, `lg_gas_products`, `lg_cylinder_conditions`

Solo se ejecuta en PostgreSQL (se salta en SQLite/tests).

## Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `plugins/productos/backend/schemas.py` | Nuevo schema `GasProductRead` |
| `plugins/productos/backend/services/catalog.py` | Nueva función `list_gas_products()` |
| `plugins/productos/backend/router.py` | Nuevo endpoint `GET /catalog/gas-products` |
| `plugins/logistics/backend/services/product_bridge.py` | Nuevo — bridge para acceso a catálogos |
| `plugins/logistics/backend/models/catalog.py` | Eliminados `LogisticsBrand`, `LogisticsGasProduct` |
| `plugins/logistics/backend/models/cylinder.py` | Eliminado `LogisticsCylinderCondition`, FKs → `prod_*` |
| `plugins/logistics/backend/models/average_weight.py` | Eliminado posteriormente |
| `plugins/logistics/backend/models/contracts.py` | FKs → `prod_*` |
| `plugins/logistics/backend/models/__init__.py` | Eliminados imports de modelos borrados |
| `plugins/logistics/backend/schemas.py` | Eliminados `GasProductRead`, `BrandRead`, `CylinderConditionRead` |
| `plugins/logistics/backend/services/catalog.py` | Eliminadas funciones de catálogo duplicadas |
| `plugins/logistics/backend/services/envase.py` | Usa `product_bridge` en vez de queries directas |
| `plugins/logistics/backend/services/cylinders.py` | Eliminada dependencia de `LogisticsGasProduct` |
| `plugins/logistics/backend/router.py` | Eliminados endpoints `/catalog/brands`, `/catalog/gas-products`, `/catalog/conditions` |
| `plugins/logistics/frontend/api/cylinders.ts` | API calls apuntan a `productos` |
| `plugins/logistics/migrations/014_consolidate_catalogs.py` | Migración de datos + drop de tablas |
| `plugins/logistics/migrations/004_envase_completo.py` | Legacy tables con `Table` inline |
| `plugins/logistics/migrations/005_cylinder_conditions.py` | Legacy seeds con raw SQL |
| `plugins/logistics/migrations/010_cylinder_product_reference.py` | Queries raw SQL en vez de modelos |
| `apps/api/tests/test_logistics_plugin.py` | Test actualizado a endpoint de productos |

## Tests

- 12 tests de logistics: ✅ pasan
- 4 tests de core management: ✅ pasan
- 1 test de productos: ✅ pasa
