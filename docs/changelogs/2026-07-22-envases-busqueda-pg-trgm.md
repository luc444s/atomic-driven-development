# Changelog 2026-07-22 - Busqueda de Envases con pg_trgm

## Que se implemento

Se habilito `pg_trgm` para acelerar la busqueda textual de `Envases`.

## Alcance

- extension PostgreSQL `pg_trgm`
- indices GIN trigram sobre:
  - `lg_cylinders.serial`
  - `lg_cylinders.description`
  - `lg_cylinders.barcode1`
  - `lg_cylinders.barcode2`
  - `lg_cylinders.location`

## Por que

- la pantalla de `Envases` busca con `ILIKE '%texto%'`;
- con miles de registros, los indices btree normales no ayudan bien en ese patron;
- `pg_trgm` prepara el camino para escalar mejor la busqueda parcial por serial, barcode, descripcion y ubicacion.

## Archivos

- `plugins/logistics/migrations/031_cylinder_search_trgm_v1.py`

## Nota

- Esto complementa la paginacion real agregada al listado de `Envases`; no la reemplaza.
