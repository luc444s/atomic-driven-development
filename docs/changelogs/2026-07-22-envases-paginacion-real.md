# Changelog 2026-07-22 - Paginacion real en Envases

## Que se implemento

Se agrego paginacion real de punta a punta para el listado principal de `Envases`.

## Problema

- el frontend cargaba todos los envases en una sola consulta;
- con miles de registros, la vista tardaba bastante en responder y renderizar.

## Solucion

1. backend ahora expone `GET /cylinders/page` con `page` y `per_page`;
2. frontend de `Envases` consulta esa ruta paginada;
3. la tabla muestra solo la pagina actual y usa el componente compartido `Pagination`.
4. la pagina actual de `Envases` trabaja con 10 resultados por pagina.

## Alcance

- `plugins/logistics/backend/services/cylinders.py`
- `plugins/logistics/backend/router.py`
- `plugins/logistics/backend/schemas.py`
- `plugins/logistics/frontend/api/cylinder-list.ts`
- `plugins/logistics/frontend/cylinders/hooks/use-cylinder-data.ts`
- `plugins/logistics/frontend/LogisticsPage.tsx`
- `apps/api/tests/test_logistics_plugin.py`

## Nota

- El endpoint viejo `GET /cylinders` se mantiene para no romper otros consumidores existentes.
- La siguiente optimizacion natural, si sigue haciendo falta, es una segunda pasada sobre busquedas `ILIKE` con trigram/GIN.
