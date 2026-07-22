# Changelog 2026-07-22 - Batch serio de indices PostgreSQL

## Que se implemento

Se agrego un batch amplio de indices orientado a los hot paths reales del sistema en `logistics`, `productos`, `stock` y `crm`.

## Objetivo

- reducir scans completos en jornadas y rutas;
- acelerar carga operativa, seriales, incidencias y carta porte;
- mejorar listados y lecturas frecuentes en productos, stock y clientes;
- preparar mejor las tablas para crecimiento sin indexar a ciegas toda la base.

## Cobertura principal

### Logistics

- jornadas activas por vehiculo y listados por estado/fecha;
- load plans y load serial assignments activos;
- busqueda operativa de cilindros por producto/estado;
- trazabilidad de estado por cilindro;
- route operations / incidents / waybills;
- movimientos y pedidos usados por recepcion y planificacion.

### Productos

- listados por tenant/activo/nombre;
- filtros por linea y marca;
- lecturas por producto de precios, costos, impuestos, ADR, media y promociones.

### Stock

- balance por tenant/almacen/producto;
- ledger por producto y por almacen/operacion ordenado por fecha.

### CRM

- listados activos de clientes por tenant y nombre;
- lecturas por cliente de direcciones, contactos, asignaciones, pricing y cuentas bancarias.

## Archivos

- `plugins/logistics/migrations/030_query_indexes_v1.py`
- `plugins/productos/migrations/004_query_indexes.py`
- `plugins/stock/migrations/004_query_indexes.py`
- `plugins/crm/migrations/005_query_indexes.py`

## Nota

- Este batch prioriza indices btree compuestos y parciales de bajo riesgo.
- La busqueda textual profunda con `ILIKE '%term%'` todavia puede merecer una segunda pasada con trigram/GIN si el volumen lo justifica.
