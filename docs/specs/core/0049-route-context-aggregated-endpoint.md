---
id: "0049"
title: "Route Context Aggregated Endpoint"
domain: logistics
module: vehicle-sessions
status: propuesta
extends:
  - docs/specs/core/0024-1-3-1-route-operation-y-composicion-vigente.md
  - docs/specs/core/0024-1-3-carta-porte-operativa-en-jornada.md
---

# SPEC 0049 — Route Context Aggregated Endpoint

## Estado

Propuesta — v1

## Frase guía

**Un solo request para todo el contexto de ruta.**

## Contexto

El modal de ruta de una jornada (`RouteModal` → `SessionRouteTab` → `useSessionRouteTabController`) actualmente realiza **10+ requests en paralelo** al abrirse:

| # | Query | Endpoint backend |
|---|-------|------------------|
| 1 | `stopsQuery` | `listRouteStops(routeId)` |
| 2 | `customersQuery` | `listCustomers({ limit: 200 })` |
| 3 | `warehousesQuery` | `listWarehouses()` |
| 4 | `routeOperationsQuery` | `listRouteOperations(sessionId)` |
| 5 | `compositionQuery` | `getCurrentComposition(sessionId)` |
| 6 | `waybillQuery` | `getSessionWaybill(sessionId)` |
| 7 | `historyQuery` | `listSessionWaybillHistory(sessionId)` |
| 8 | `routeIncidentsQuery` | `listRouteIncidents(sessionId)` |
| 9 | `routeStopProgressQuery` | `getRouteStopProgress(sessionId)` |
| 10 | `routeStopResultsQuery` | `listRouteStopResults(sessionId)` |

Además, `SessionRouteTab` agrega 4 queries adicionales, 3 de las cuales son duplicadas del controller.

**Resultado:** ~14 requests al abrir ruta, ~27 requests al abrir jornada completa. Cada mutación invalida 7 queries → 7 requests más.

En entorno dev, esto genera lentitud percibida en cada paso del flujo operativo.

## Alcance

### Incluye

- Backend: nuevo endpoint `GET /vehicle-sessions/{id}/route-context`
- Backend: service function que agrega todos los datos en un solo query
- Backend: DTO `RouteContextRead` con toda la data
- Frontend: nuevo hook `useRouteContextQuery` que reemplaza las 10 queries del controller
- Frontend: eliminación de queries duplicadas en `SessionRouteTab`
- Frontend: agregado `staleTime` a queries de datos estáticos

### Queda fuera

- Eliminación de endpoints viejos (se mantienen para compatibilidad)
- Cambios en `VehicleJornadasDialog` (queries independientes)
- Optimización de mutaciones (fase futura)
- Cambios en la lista de jornadas (`VehicleSessionsPage`)

## Decisión de dominio

El contexto de ruta es una **vista materializada** de datos que ya existen en endpoints individuales. No es una nueva entidad, sino una agregación de conveniencia.

### Reglas

1. El endpoint agregado es **adicional**, no reemplazante
2. Los endpoints individuales se mantienen para usos independientes
3. El frontend puede degradarse a endpoints individuales si el agregado falla
4. Los datos estáticos (warehouses, customers) usan `staleTime` agresivo

## Modelo de datos

### `RouteContextRead`

```python
class RouteContextRead(BaseModel):
    # Session data
    session: VehicleSessionDetailRead
    
    # Route data (from route_id in session)
    route_detail: RouteDetailRead | None = None
    assigned_route: RoutingAssignedRouteRead | None = None
    stops: list[RouteStopRead] = []
    
    # Session-related data
    operations: list[RouteOperationRead] = []
    composition: CurrentCompositionRead
    waybill: SessionWaybillStateRead
    waybill_history: list[SessionWaybillHistoryVersionRead] = []
    incidents: list[RouteIncidentRead] = []
    stop_progress: list[RouteStopProgressRead] = []
    stop_results: list[RouteStopResultRead] = []
    
    # Reference data (embedded)
    customers: list[CustomerBrief] = []
    warehouses: list[WarehouseRead] = []
```

## Backend esperado

### Service function

```python
# plugins/logistics/backend/services/route_context.py

def build_route_context(
    db: Session,
    *,
    tenant_id: str,
    session_id: str,
) -> RouteContextRead:
    """
    Un solo request que retorna todo lo que el frontend necesita
    para el modal de ruta de una jornada.
    """
    session = get_vehicle_session(db, tenant_id=tenant_id, session_id=session_id)
    if session is None:
        raise LookupError("Jornada no encontrada")
    
    route_id = session.route_id
    
    # Datos de sesión
    session_snapshot = build_session_snapshot(db, session=session)
    
    # Datos de ruta (si existe)
    route_detail = None
    assigned_route = None
    stops = []
    if route_id:
        route_detail = get_route_detail(db, route_id=route_id)
        assigned_route = get_assigned_route_snapshot(db, route_id=route_id)
        stops = list_route_stops(db, route_id=route_id)
    
    # Datos operacionales de la sesión
    operations = list_route_operations(db, session_id=session_id)
    composition = build_current_composition(db, session=session)
    waybill = get_session_waybill_state(db, session=session)
    waybill_history = list_session_waybill_history(db, session=session)
    incidents = list_route_incidents(db, session_id=session_id)
    stop_progress = build_route_stop_progress(db, session=session)
    stop_results = list_route_stop_results(db, session_id=session_id)
    
    # Datos de referencia
    customers = list_customer_briefs(db, tenant_id=tenant_id, limit=200)
    warehouses = list_warehouses(db, tenant_id=tenant_id)
    
    return RouteContextRead(
        session=session_snapshot,
        route_detail=route_detail,
        assigned_route=assigned_route,
        stops=stops,
        operations=operations,
        composition=composition,
        waybill=waybill,
        waybill_history=waybill_history,
        incidents=incidents,
        stop_progress=stop_progress,
        stop_results=stop_results,
        customers=customers,
        warehouses=warehouses,
    )
```

### Router endpoint

```python
# plugins/logistics/backend/routers/route_context.py

@router.get("/{session_id}/route-context", response_model=RouteContextRead)
async def get_route_context(
    session_id: str,
    request: Request,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_SESSION_READ,
) -> RouteContextRead:
    def _load() -> RouteContextRead:
        db = _make_sync_session(request)
        try:
            return build_route_context(
                db,
                tenant_id=tenant_context.current_tenant_id,
                session_id=session_id,
            )
        finally:
            db.close()
    
    return await asyncio.to_thread(_load)
```

## Frontend esperado

### API function

```typescript
// plugins/logistics/frontend/api/sessions.ts

export type RouteContext = {
  session: VehicleSessionDetail;
  route_detail: RouteDetail | null;
  assigned_route: AssignedRoute | null;
  stops: RouteStop[];
  operations: RouteOperation[];
  composition: CurrentComposition;
  waybill: SessionWaybillState;
  waybill_history: SessionWaybillVersion[];
  incidents: RouteIncident[];
  stop_progress: RouteStopProgress[];
  stop_results: RouteStopResult[];
  customers: CustomerBrief[];
  warehouses: Warehouse[];
};

export function getSessionRouteContext(sessionId: string) {
  return apiRequest<RouteContext>(
    `${API_PREFIX}/vehicle-sessions/${sessionId}/route-context`
  );
}
```

### Query key

```typescript
// plugins/logistics/frontend/api/keys.ts

routeContext: (id: string) => 
  [...logisticsKeys.vehicleSessions.detail(id), "route-context"] as const,
```

### Controller refactor

```typescript
// plugins/logistics/frontend/components/vehicle-sessions/useSessionRouteTabController.ts

// ANTES: 10 queries individuales
// DESPUÉS: 1 query agregado

const routeContextQuery = useQuery({
  queryKey: logisticsKeys.vehicleSessions.routeContext(sessionId),
  queryFn: () => getSessionRouteContext(sessionId),
  enabled: open,
  staleTime: 30 * 1000, // 30 segundos
});

// Mapear datos del contexto a las variables que el componente espera
const stops = routeContextQuery.data?.stops ?? [];
const routeOperations = routeContextQuery.data?.operations ?? [];
const composition = routeContextQuery.data?.composition;
const waybillState = routeContextQuery.data?.waybill;
const waybillHistory = routeContextQuery.data?.waybill_history ?? [];
const routeIncidents = routeContextQuery.data?.incidents ?? [];
const routeStopProgress = routeContextQuery.data?.stop_progress ?? [];
const routeStopResults = routeContextQuery.data?.stop_results ?? [];
const stopOptions = buildStopOptions(stops);
const customerOptions = buildCustomerOptions(routeContextQuery.data?.customers ?? []);
const warehouseOptions = getRealWarehouses(routeContextQuery.data?.warehouses ?? []).map(...);
```

### Invalidación selectiva

```typescript
// En onSuccess de cada mutación, solo invalidar routeContext
await queryClient.invalidateQueries({
  queryKey: logisticsKeys.vehicleSessions.routeContext(sessionId)
});
```

## Optimización de caché

### `staleTime` para datos estáticos

| Query | staleTime | Justificación |
|-------|-----------|---------------|
| `listWarehouses` | 10 min | Datos casi estáticos |
| `listCustomers` | 5 min | Cambios poco frecuentes |
| `listDriverOptions` | 10 min | Datos de catálogo |
| `listRoutes` | 2 min | Cambios moderados |

## Reglas de negocio

1. El endpoint agregado es de **solo lectura**
2. No muta estado, solo agrega datos existentes
3. Si el endpoint falla, el frontend puede degradarse a endpoints individuales
4. Los datos estáticos se cachean agresivamente
5. Las mutaciones invalidan solo el contexto de ruta, no todas las queries

## Riesgos

| Riesgo | Impacto | Mitigación |
|--------|---------|------------|
| Endpoint agregado más lento que individuales | bajo | Queries en paralelo, sin N+1 |
| Breaking change si se eliminan endpoints viejos | alto | No se eliminan, solo se agrega |
| Frontend se rompe si el endpoint falla | medio | Fallback a endpoints individuales |
| Datos stale por staleTime agresivo | bajo | Invalidación explícita en mutaciones |

## Criterios de aceptación

1. Abrir modal de ruta genera **1 request** en vez de 10+
2. Los endpoints individuales siguen funcionando
3. `VehicleJornadasDialog` no se ve afectado
4. Las mutaciones invalidan solo el contexto de ruta
5. Datos estáticos se cachean con staleTime apropiado
6. Tests de integración para el nuevo endpoint
7. Tests unitarios para la función de servicio

## Plan de implementación por commits

### added: route-context dto

**Archivos:**
- `plugins/logistics/backend/dto/route_context.py` (crear)

**Alcance:**
- `RouteContextRead` schema
- Schemas dependientes importados de DTOs existentes

**Resultado:**
- Contrato de datos claro para el endpoint agregado

---

### added: route-context service

**Archivos:**
- `plugins/logistics/backend/services/route_context.py` (crear)

**Alcance:**
- `build_route_context()` function
- Queries en paralelo para cada sección
- Manejo de errores y edge cases (route_id None)

**Resultado:**
- Service function que agrega todos los datos en un solo request

---

### added: route-context router

**Archivos:**
- `plugins/logistics/backend/routers/route_context.py` (crear)
- `plugins/logistics/backend/router.py` (modificar - registrar router)

**Alcance:**
- `GET /vehicle-sessions/{session_id}/route-context`
- Autenticación y permisos existentes
- Response model `RouteContextRead`

**Resultado:**
- Endpoint funcional y registrado

---

### added: route-context test

**Archivos:**
- `plugins/logistics/backend/tests/test_route_context.py` (crear)

**Alcance:**
- Test de integración con `TestClient`
- Test de response completa
- Test de 404 para session inexistente
- Test de datos vacíos (session sin ruta)

**Resultado:**
- Cobertura de tests para el nuevo endpoint

---

### modified: frontend route-context api

**Archivos:**
- `plugins/logistics/frontend/api/sessions.ts` (modificar)
- `plugins/logistics/frontend/api/keys.ts` (modificar)

**Alcance:**
- Tipo `RouteContext`
- Función `getSessionRouteContext()`
- Key `routeContext`

**Resultado:**
- Frontend puede consumir el nuevo endpoint

---

### modified: controller route-context

**Archivos:**
- `plugins/logistics/frontend/components/vehicle-sessions/useSessionRouteTabController.ts` (modificar)

**Alcance:**
- Eliminar 10 queries individuales
- Agregar `routeContextQuery`
- Mapear datos del contexto a variables existentes
- Actualizar invalidaciones en mutaciones

**Resultado:**
- Controller usa 1 query en vez de 10

---

### modified: session-route-tab cleanup

**Archivos:**
- `plugins/logistics/frontend/components/vehicle-sessions/SessionRouteTab.tsx` (modificar)

**Alcance:**
- Eliminar queries duplicadas (`stopsQuery`, `stopProgressQuery`)
- Usar datos del controller en vez de queries propias
- Eliminar imports no usados

**Resultado:**
- SessionRouteTab usa datos del controller, no queries propias

---

### modified: stale-time cache

**Archivos:**
- `plugins/logistics/frontend/components/vehicle-sessions/useSessionRouteTabController.ts` (modificar)
- `plugins/logistics/frontend/pages/VehicleSessionsPage.tsx` (modificar)

**Alcance:**
- `staleTime: 10 * 60 * 1000` para warehouses
- `staleTime: 5 * 60 * 1000` para customers
- `staleTime: 10 * 60 * 1000` para drivers
- `staleTime: 2 * 60 * 1000` para routes

**Resultado:**
- Datos estáticos se cachean agresivamente

---

### test: frontend route-context

**Archivos:**
- `plugins/logistics/frontend/components/vehicle-sessions/__tests__/useSessionRouteTabController.test.ts` (crear)

**Alcance:**
- Test de que el controller usa routeContextQuery
- Test de mapeo de datos
- Test de invalidación selectiva

**Resultado:**
- Cobertura de tests para el frontend

## Orden obligatorio

```text
added: route-context dto
-> added: route-context service
-> added: route-context router
-> added: route-context test
-> modified: frontend route-context api
-> modified: controller route-context
-> modified: session-route-tab cleanup
-> modified: stale-time cache
-> test: frontend route-context
```

## Impacto esperado

| Métrica | Antes | Después |
|---------|-------|---------|
| Requests al abrir ruta | 10+ | **1** |
| Requests al abrir jornada | ~27 | **~17** |
| Invalidaciones post-mutación | 7 | **1** |
| Tiempo percibido (dev) | ~2-4s | ~300-500ms |
