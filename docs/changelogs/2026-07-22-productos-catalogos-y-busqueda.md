# Changelog 2026-07-22 - Catálogos y búsqueda de Productos

## Qué se implementó

Se reforzó el frente de `Productos` en dos niveles:

1. paginación visible en tablas de catálogos del frontend;
2. soporte `pg_trgm` para búsqueda por `sku`, `name` y `barcode`.

## Catálogos

- las tablas de `Categorías`, `Líneas`, `Sublíneas`, `Marcas`, `Tipos de insumo`, `Unidades`, `Subcategorías` y `Grupos` ahora muestran paginación visible local de 10 elementos por página;
- esto evita renderizar listas completas largas en una sola vista.

## Búsqueda de productos

- la búsqueda actual usa `ILIKE '%texto%'` sobre `prod_products.sku`, `prod_products.name` y `prod_barcodes.barcode`;
- se agregaron índices trigram para preparar ese patrón a volúmenes mayores.

## Archivos

- `apps/web/src/shared/ui/paginated-data-table.tsx`
- `plugins/productos/frontend/pages/CatalogManagerPage.tsx`
- `plugins/productos/frontend/components/ModalCatalogo.tsx`
- `plugins/productos/migrations/005_product_search_trgm_v1.py`

## Nota

- La tabla paginada se subio al core compartido para que otros modulos puedan reutilizarla sin duplicacion.
- En el volumen actual el `EXPLAIN` puede seguir elegirendo planes simples; el beneficio de `pg_trgm` se vuelve más claro cuando crece la tabla y la búsqueda parcial deja de ser trivial.
