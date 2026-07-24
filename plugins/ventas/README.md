# Ventas

Plugin de ventas con entrada via consola DSL (Monaco Editor).

## Sub-módulos

- `cotizacion/` — Cotización vía DSL, draft-first (SPEC 0026)
- `pricing/` — Futuro
- `pedidos/` — Futuro
- `condiciones/` — Futuro

## Dependencias

- `crm` — resolución de clientes
- `productos` — catálogo de productos
- `logistics` (opcional) — vehículos

## Arquitectura

Cada sub-módulo es autocontenido con su propio `backend/`, `frontend/` y `migrations/`. Componentes compartidos entre sub-módulos viven en `_shared/`.
