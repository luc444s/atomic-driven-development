# Changelog 2026-07-22 - Paginacion UI en Productos

## Que se implemento

Se activo la navegacion paginada en la pantalla principal de `Productos` reutilizando la paginacion backend ya existente.

## Problema

- la API de productos ya devolvia `items`, `total`, `limit` y `offset`;
- pero la UI siempre consultaba `offset = 0`, asi que solo trabajaba sobre la primera pagina sin navegacion real.

## Solucion

1. la pantalla ahora mantiene estado de `page`;
2. consulta `offset` real segun la pagina actual;
3. muestra `Pagination` en frontend;
4. resetea a pagina 1 cuando cambia la busqueda.

## Alcance

- `plugins/productos/frontend/pages/ProductListPage.tsx`

## Nota

- El backend de productos ya estaba paginado; este ajuste fue principalmente de consumo y UX.
