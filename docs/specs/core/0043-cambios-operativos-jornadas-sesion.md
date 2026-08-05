# SPEC 0043 — Cambios operativos en jornadas (sesion 2026-08-04/05)

**Estado**: vigente (implementado)  
**Tipo**: documentativo  
**Modulos**: logistics (backend + frontend)  
**Creado**: 2026-08-05

## Resumen

Sesion intensiva de correcciones y mejoras en el TMS/jornadas. Se cubrieron 6 areas: entrega desde composicion, contexto operativo automatico, fix de seriales en ruta, fix de carta porte, fix de transiciones SC para envases vacios, y ajustes de UI.

---

## 1. Entrega desde composicion y serial rapido (SPEC 0041)

**Archivos**: `RouteOperationForm.tsx`, `useSessionRouteTabUiState.ts`, `useSessionRouteTabController.ts`, `SessionRouteTabDialogs.tsx`

Cuando `operationType === "DELIVERY"`, el formulario muestra:

- **Input de serial rapido**: escanea/escribe un serial y lo agrega automaticamente detectando el producto desde el cilindro.
- **Cards de composicion**: productos disponibles en el camion (`CurrentComposition.product_lines`). Clic agrega linea de entrega.
- Seccion "Entregado" con cantidades y seleccion de seriales.

Para PICKUP y EXCHANGE: sin cambios.

---

## 2. Contexto operativo inferido automaticamente

### 2a. Dropdown de parada por defecto

`openEventModal(defaultStopId)` ahora recibe y selecciona automaticamente la primera parada de la ruta al abrir el modal de evento.

### 2b. Inferencia automatica de almacen vs cliente

En `_resolve_operation_context` (`route_operations.py`):

- Si el `delivery_point.warehouse_id` no es nulo → `context_type = "WAREHOUSE"`.
- Si el `route_stop.delivery_point_id` es NULL pero `route_stop.customer_id` esta presente → usa los datos del stop directamente.
- `_delivery_point_for_operation` ahora continua al fallback de `operation.customer_id` cuando el delivery_point es None.

### 2c. Simplificacion de contexto manual

`CUSTOMER_EMERGENCY` → `CUSTOMER`, `WAREHOUSE_EMERGENCY` → `WAREHOUSE` en frontend y backend.

**Archivos**: `RouteOperationForm.tsx`, `useSessionRouteTabUiState.ts`, `useSessionRouteTabController.ts`, `route_operations.py`

---

## 3. Fix de seriales en ruta

### 3a. Orden de chequeos en `select_load_serial`

En `load_serials.py:356`: se movio el chequeo de `active_assignment` **antes** del chequeo de estado compatible. Un serial ya confirmado en la misma jornada (aunque este en `EN_RUTA`) ahora se acepta directamente sin validar estado.

### 3b. Contexto de seleccion por tipo de operacion

`LoadSerialsDialog` en `SessionRouteTabDialogs.tsx` ahora recibe:
- `selectionContext="LOAD_PLAN"` para DELIVERY (acepta `EN_RUTA`, `EN_ALMACEN_VACIO`, `LLENADO_OK`)
- `selectionContext="ROUTE_PICKUP"` para PICKUP (solo `EN_CLIENTE_VACIO`)

### 3c. Fix de contador a 0 en LoadSerialsDialog

El `useEffect` que emite `onSelectionCountChange` ahora espera a que `selectedQuery` termine de cargar (`isFetching`), evitando que el contador baje a 0 durante la carga inicial.

**Archivos**: `load_serials.py`, `LoadSerialsDialog.tsx`, `SessionRouteTabDialogs.tsx`

---

## 4. Fix de carta porte y migracion

### 4a. Ampliacion de `source_id` en ledger

Columna `lg_customer_cylinder_ledger.source_id`: `VARCHAR(36)` → `VARCHAR(255)` porque el codigo genera `movement_id:item_id` (~73 chars).

**Migracion**: `050_widen_ledger_source_id.py`

### 4b. Fix de `_delivery_point_for_operation`

Cuando el `route_stop` existe pero no tiene `delivery_point_id`, la funcion ahora continua al fallback de `operation.customer_id` en vez de retornar None.

**Archivos**: `route_operations.py`, `migrations/050_widen_ledger_source_id.py`

---

## 5. Transiciones SC para envases vacios

### 5a. Nueva transicion en catalogo

Agregada `EN_RUTA → EN_CLIENTE_VACIO` ("Entrega de envase vacio") en `catalog.py` y en la DB.

### 5b. Seleccion de destino segun contenido

En `movements.py::apply_cylinder_effects_for_movement`: cuando el movimiento es SC, el target state ahora depende de `content_kg`:

```python
if movement.movement_type == "SC" and _cylinder_is_empty(cylinder):
    target_state = "EN_CLIENTE_VACIO"
```

`_cylinder_is_empty`: `content_kg <= 0`.

### 5c. DB: transicion insertada

```sql
INSERT INTO lg_state_transitions (from_state, to_state, description)
VALUES ('EN_RUTA', 'EN_CLIENTE_VACIO', 'Entrega de envase vacio');
```

**Archivos**: `catalog.py`, `movements.py`, `lg_state_transitions` (DB)

---

## 6. Ajustes de UI

### 6a. Modal "Contexto de ruta"

`RouteModal.tsx`: ancho `max-w-4xl` → `max-w-[1800px]`, alto `max-h-[85vh]` → `max-h-[92vh]`. `Dialog` ahora acepta `maxHeightClassName`.

### 6b. Auto-fit en mapa de ruta

`RouteContextMap.tsx`: agregado `autoFit` al `LocationMap` para que enfoque automaticamente todos los markers y la polyline al abrir.

**Archivos**: `RouteModal.tsx`, `dialog.tsx`, `RouteContextMap.tsx`

---

## Cambios posteriores a la sesion

- Fix: se amplio `max-h` del Dialog generico agregando prop `maxHeightClassName` en `dialog.tsx:12`.
- Se elimino swap de HyperOS (mejora de rendimiento general).

---

## Archivos tocados (total: 15)

| Archivo | Cambio |
|---------|--------|
| `RouteOperationForm.tsx` | Seccion DELIVERY con serial rapido + cards; simplificacion CUSTOMER/WAREHOUSE |
| `useSessionRouteTabUiState.ts` | `addDeliveryProduct`, `fastSerialInput`, `openEventModal(defaultStopId)` |
| `useSessionRouteTabController.ts` | `submitFastSerial`, `fastSerialError` |
| `SessionRouteTabDialogs.tsx` | Pasar `composition`, `fastSerialInput`, `selectionContext` dinamico |
| `LoadSerialsDialog.tsx` | `useEffect` con `isFetching` guard |
| `route_operations.py` | `_resolve_operation_context`, `_delivery_point_for_operation`, validacion STOP |
| `load_serials.py` | Reorden de chequeos en `select_load_serial` |
| `catalog.py` | Transicion `EN_RUTA → EN_CLIENTE_VACIO` |
| `movements.py` | `_cylinder_is_empty`, target state condicional en SC |
| `dialog.tsx` | Prop `maxHeightClassName` |
| `RouteModal.tsx` | `max-w-[1800px]`, `max-h-[92vh]` |
| `RouteContextMap.tsx` | `autoFit` en `LocationMap`, `height={400}` |
| `session_waybills.py` | (sin cambios directos, fixes en dependencias) |
| `migrations/050_widen_ledger_source_id.py` | Ampliar `source_id` a VARCHAR(255) |
| `lg_state_transitions` (DB) | Insert `EN_RUTA → EN_CLIENTE_VACIO` |
