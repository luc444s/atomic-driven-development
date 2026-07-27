# Ventas

Plugin de ventas con entrada via consola DSL (Monaco Editor) y formulario visual.

## Sub-módulo

- `cotizacion/` — Cotización draft-first, consola + formulario (SPEC 0026, SPEC 0027)

## Flujo

`QuoteDraft (DRAFT) → CONFIRMED → PlanningEntry → VehicleSession`

No existe entidad "pedido" separada. La cotización confirmada se integra directo en planificación y jornadas.

## Dependencias

- `crm` — resolución de clientes
- `productos` — catálogo de productos
- `logistics` (opcional) — vehículos

## Arquitectura

Cada sub-módulo es autocontenido con su propio `backend/`, `frontend/` y `migrations/`. Componentes compartidos entre sub-módulos viven en `_shared/`.
