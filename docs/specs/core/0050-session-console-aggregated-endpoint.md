---
id: "0050"
title: "Session Console Aggregated Endpoint"
domain: logistics
module: vehicle-sessions
status: propuesta
extends:
  - docs/specs/core/0049-route-context-aggregated-endpoint.md
  - docs/specs/core/0024-1-3-4-operational-summary-de-jornada.md
---

# SPEC 0050 — Session Console Aggregated Endpoint

## Estado

Propuesta — v1

## Frase guía

**Un solo request para toda la consola de la jornada.**

## Contexto

La página de detalle de jornada (`VehicleSessionDetailPage`) abre **7 queries en paralelo**:

| # | Query | Endpoint backend |
|---|-------|------------------|
| 1 | `sessionQuery` | `getVehicleSession(sessionId)` |
| 2 | `loadPlanQuery` | `getLoadPlan(sessionId)` |
| 3 | `reconciliationQuery` | `getSessionReconciliation(sessionId)` |
| 4 | `operationalSummaryQuery` | `getSessionOperationalSummary(sessionId)` |
| 5 | `originBalancesQuery` | `listBalances(origin)` |
| 6 | `mobileBalancesQuery` | `listBalances(mobile)` |
| 7 | `originSerializedQuery` | `listSerializedCylinderSummary(origin)` |

SPEC 0049 ya agregó el contexto de ruta. Esta spec agrega la **consola completa** de la jornada con el mismo patrón.

## Alcance

### Incluye

- Backend: `GET /vehicle-sessions/{id}/console-context`
- Backend: service `build_session_console_context()` que agrega las 7 fuentes
- Backend: DTO `SessionConsoleContextRead`
- Frontend: `getSessionConsoleContext()` + key `consoleContext`
- Frontend: `VehicleSessionDetailPage` usa 1 query en vez de 7

### Queda fuera

- Eliminación de endpoints viejos (se mantienen)
- Cambios en `VehicleSessionsPage` (lista)
- Cambios en `RouteModal` (ya cubierto por route-context)

## Decisión de dominio

1. El endpoint agregado es de solo lectura, adicional a los existentes.
2. El load plan mantiene enriquecimiento de seriales (`requires_serials`, `serials_complete`) — la lógica `_to_read_with_serial_status` se mueve del router a un servicio para reutilizarla.
3. Los balances mantienen `ensure_catalog=True`: el LoadModal espera ver productos con balance 0 materializados (paridad con stock UI).
4. Si una sub-fuente falla en estados no aplicables, la sección degrada a `null` en vez de romper todo el contexto (paridad con 7 requests independientes).

## Modelo de datos

```python
class SessionConsoleContextRead(BaseModel):
    session: VehicleSessionDetailRead
    load_plan: LoadPlanRead
    reconciliation: SessionReconciliationRead
    operational_summary: SessionOperationalSummaryRead | None = None
    origin_balances: StockBalancePageRead
    mobile_balances: StockBalancePageRead
    origin_serialized: list[WarehouseSerializedCylinderSummaryItem]
```

## Backend esperado

### Service

`plugins/logistics/backend/services/session_console.py`:

- `build_session_console_context(db, *, tenant_id, session_id) -> SessionConsoleContextRead`
- resuelve session (404 si no existe), luego agrega:
  - `build_session_snapshot`
  - load plan + items + serial status (reusando builder movido a servicio)
  - `get_reconciliation_view`
  - `build_operational_summary` (degradación a `None` si falla por estado)
  - `get_warehouse_balances` origin + mobile (`ensure_catalog=True`)
  - `summarize_serialized_cylinders_by_warehouse` origin

### Router

`plugins/logistics/backend/routers/session_console.py`:

- `GET /{session_id}/console-context`, permiso `logistics.session.read`
- registrado en `plugin.py`

## Frontend esperado

### API

`plugins/logistics/frontend/api/session-console.ts`:

- tipo `SessionConsoleContext`
- `getSessionConsoleContext(sessionId)`

### Key

`logisticsKeys.vehicleSessions.consoleContext(id)`

### Detail page

`VehicleSessionDetailPage.tsx`:

- 7 queries → 1 `consoleContextQuery`
- `useEffect` de loadPlanItems y counts leen del contexto
- invalidaciones post-mutación apuntan a `consoleContext` (1 key)

## Riesgos

| Riesgo | Impacto | Mitigación |
|--------|---------|------------|
| Sub-fuente falla y rompe todo | alto | degradación por sección a `null` |
| Load plan pierde serial status | alto | mover builder a servicio, tests |
| Balances sin zero-materialization | medio | `ensure_catalog=True` |
| Invalidación incompleta | medio | invalidar `consoleContext` + `routeContext` + `detail` en mutaciones |

## Criterios de aceptación

1. Abrir detalle genera 1 request en vez de 7.
2. Endpoints individuales siguen funcionando.
3. Load plan mantiene `requires_serials`/`serials_complete`.
4. Balances muestran productos con 0 igual que stock UI.
5. Tests de integración del endpoint + tests frontend del mapeo.

## Plan de implementación por commits

### added: console-context dto + spec

- `docs/specs/core/0050-session-console-aggregated-endpoint.md`
- `plugins/logistics/backend/dto/session_console.py`

### added: console-context service

- `plugins/logistics/backend/services/session_console.py`
- mover `_to_read_with_serial_status` a `services/load_plans.py`
- `routers/load_plans.py` importa el builder del servicio

### added: console-context router

- `plugins/logistics/backend/routers/session_console.py`
- `plugins/logistics/backend/plugin.py` (registro)

### added: console-context test

- `apps/api/tests/test_logistics_session_console.py`
- 200 completo, 404, degradación de summary, paridad load plan serials

### modified: frontend console-context api

- `api/session-console.ts` + export en `index.ts`
- key `consoleContext` en `keys.ts`

### modified: detail page usa console-context

- `VehicleSessionDetailPage.tsx`: 7 queries → 1

### test: frontend console-context

- test vitest del mapeo de contexto a estado local (loadPlanItems/counts)

## Orden obligatorio

```text
added: console-context dto + spec
-> added: console-context service
-> added: console-context router
-> added: console-context test
-> modified: frontend console-context api
-> modified: detail page usa console-context
-> test: frontend console-context
```

## Impacto esperado

| Métrica | Antes | Después |
|---------|-------|---------|
| Requests al abrir detalle | 7 | **1** |
| Invalidaciones post-mutación | 8 keys | 1-3 keys |
