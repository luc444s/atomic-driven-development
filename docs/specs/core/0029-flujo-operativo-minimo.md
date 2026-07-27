# SPEC 0029 — Flujo operativo mínimo: cotización → retorno al almacén

## Estado

Propuesta — v2 (incorpora feedback de revisión de arquitectura)

## Contexto

Las specs 0026, 0027 y 0028 ya construyeron el flujo de cotización con integración al planning. SPEC 0016.2 cerró los gaps transaccionales de stock (reservas, costeo, movimientos). Logistics ya tiene vehicle sessions, movements, cylinders y carta porte completos.

Pero el sistema todavía no conecta la capa logística con la capa de stock, y el ciclo operativo no tiene un cierre formal. Para un primer demo ante el cliente, se necesita un flujo mínimo que recorra el ciclo completo:

```
cotización → planning → sesión → movimientos → cilindros retornan al almacén
```

## Principio de consistencia

**Regla**: un movimiento `CONFIRMED` solo existe si stock se actualizó correctamente en la misma transacción. No se admite confirmación de movimiento sin escritura exitosa en stock.

Esto elimina el problema de eventual consistency y el riesgo de inconsistencias silenciosas.

Esta spec define los 3 puentes que faltan para cerrar ese flujo, manteniendo el principio de comunicación por eventos (ADR 0005) sin acoplar logistics a stock directamente.

## Objetivo

Cerrar el flujo operativo mínimo con 3 componentes:

1. **Event bridge logistics → stock**: los movimientos SC/IC confirmados disparan `sale_out` / `return_in` en stock
2. **Cierre de sesión**: endpoint para pasar VehicleSession de RETURNING a CLOSED
3. **Vista de estado de sesión**: panel mínimo en el frontend de logistics que muestra el ciclo completo de una jornada

## No objetivos

- No es un refactor de logistics ni de stock
- No toca el modelo de planning, vehículos ni rutas
- No implementa facturación, cobros ni pagos
- No genera PDFs ni reportes nuevos
- No modifica el state machine de cylinders

---

## 1. Stock bridge: sincrónico dentro de confirm_movement

### Problema

Cuando logistics confirma un movimiento SC (salida a cliente), los cilindros transicionan a `EN_CLIENTE_LLENO`, pero el stock no se actualiza. Misma situación para IC, IP, etc.

### Decisión

**Opción A (elegida): sincrónico transaccional.** El bridge se ejecuta **dentro** de `confirm_movement()`, en la misma transacción DB. Si stock falla, el movimiento no se confirma.

```
confirm_movement(db, movement_id):
    1. Validar movimiento
    2. Para cada item del movimiento:
       → llamar stock_bridge.push_movement_item(db, item)
       → si stock rechaza → ROLLBACK, error 409
    3. Cylinders: aplicar transiciones de estado
    4. Movimiento: status = CONFIRMED
    5. Emitir logistics.movement.confirmed
    6. COMMIT
```

**Esto garantiza**: no existe un movimiento CONFIRMED con stock desincronizado. Es imposible.

### El bridge NO es un listener de eventos

A diferencia de la v1, el bridge no escucha `logistics.movement.confirmed`. Es llamado **directamente** por `confirm_movement()`. Esto elimina el problema de eventual consistency y la necesidad de reintentos.

El evento `logistics.movement.confirmed` sigue emitiéndose (para otros consumidores como auditoría, notificaciones), pero el bridge no lo consume.

### product_id en movement_item

Cada `movement_item` debe almacenar `product_id` directamente. No se deriva del cylinder → product_type. Esto evita:
- Fragilidad si el cylinder no tiene product_type
- Inconsistencia si el tipo de producto del cylinder cambia

```sql
ALTER TABLE lg_movement_items ADD COLUMN product_id VARCHAR(36) REFERENCES prod_products(id);
```

Si el item ya tiene `product_id`, el bridge lo usa. Si no (movements legacy), el bridge lo resuelve desde el cylinder como fallback, pero emite warning.

### Mapeo de movimientos → operaciones stock

| Tipo logistics | Operación stock | Dirección |
|---|---|---|
| `SC` (salida a cliente) | `sale_out` (source=direct) | sale del almacén |
| `IC` (ingreso desde cliente) | `return_in` | entra al almacén |
| `IP` (ingreso proveedor) | `purchase_in` | entra al almacén |
| `IFP` (ingreso lleno proveedor) | `purchase_in` | entra al almacén |
| `SP` (salida a proveedor) | `sale_out` (source=direct) | sale del almacén |
| `MV` (envío a mantenimiento) | `damage_out` | sale del almacén |
| `TR` (traslado interno) | `transfer` | entre almacenes |

### Llamada a stock

El bridge llama a los servicios de stock **directamente** (misma DB, misma transacción), no por HTTP. Esto es más rápido y permite el rollback atómico.

```python
# stock_bridge.py
def push_movement_item(db, movement, item):
    if movement.type_code == "SC":
        return sale_out_stock(
            db,
            product_id=item.product_id,
            warehouse_id=movement.warehouse_id,
            quantity=item.quantity,
            source="direct",
            reference_type="movement",
            reference_id=movement.id,
            ...
        )
```

### Idempotencia

Cada llamada a stock incluye:
- `reference_type = "movement"`
- `reference_id = movement.id`
- `idempotency_key = f"{movement.type_code}:{movement.id}:{item.id}"`

Esto evita colisiones si un mismo movimiento tiene múltiples items del mismo producto.

### Trazabilidad

Cada entrada en `stk_ledger` referencia:
- `reference_type = "movement"`
- `reference_id = movement.id`
- `source = "direct"` (para sale_out)

Esto permite navegar: `stock → movement → session → planning → cotización`.

### Stock sync status en el movimiento

Cada movimiento gana un campo calculado (no persistido) `stock_sync_status`:

| Valor | Significado |
|---|---|
| `synced` | Todos los items se escribieron en stock correctamente |
| `pending` | Movimiento no confirmado aún (sin stock) |
| `error` | No debería ocurrir (si falla, el movimiento no se confirma) |

Este campo se expone en el endpoint `GET /movements/{id}` para que el frontend lo muestre.

### Archivos

```
plugins/logistics/backend/services/stock_bridge.py     NUEVO
plugins/logistics/backend/services/movements.py        MODIFICADO (llama al bridge)
plugins/logistics/backend/models/movement_items.py     MODIFICADO (+product_id)

---

## 2. Cierre de sesión (RETURNING → CLOSED)

### Problema

El state machine de VehicleSession termina en RETURNING. No hay forma de cerrar formalmente una sesión. El campo `closed_at` existe en el modelo pero nunca se escribe.

### Endpoint nuevo

```
POST /api/v1/plugins/logistics/vehicle-sessions/{session_id}/close
```

### Reglas

1. Solo se puede cerrar si `status == RETURNING`
2. Al cerrar:
   - `status` → `CLOSED`
   - `closed_at` → `now()`
   - Se emite evento `logistics.session.closed`
3. El cierre es **irreversible** (no hay re-open)
4. **No bloquea** por movimientos pendientes, pero **reporta warnings**:
   - movimientos en estado != COMPLETADO
   - movimientos con stock no sincronizado (no aplica en v2 porque es sincrónico)

### Schema de respuesta

```json
{
  "session_id": "...",
  "status": "CLOSED",
  "closed_at": "2026-07-27T22:00:00Z",
  "duration_minutes": 480,
  "warnings": [
    "Movimiento #55 (SC) está en estado PENDING",
    "Movimiento #56 (IC) no tiene items registrados"
  ],
  "summary": {
    "total_sc": 12,
    "total_ic": 10,
    "cylinders_delivered": 45,
    "cylinders_returned": 42,
    "stock_synced": true
  }
}
```

### Permiso

```
logistics.session.close
```

### Evento

```
logistics.session.closed → { session_id, vehicle_id, driver_id, closed_at, duration_minutes }
```

### Archivos modificados

```
plugins/logistics/backend/models/sessions.py          — agregar CLOSED al status
plugins/logistics/backend/routers/sessions.py         — nuevo endpoint
plugins/logistics/backend/services/sessions.py        — lógica de cierre
plugins/logistics/plugin.json                         — permiso + evento
plugins/logistics/backend/plugin.py                   — registrar permiso + evento
```

---

## 3. Vista de estado de sesión (SessionStatusPanel)

### Diseño actualizado

```
🚚 Sesión #42 — Vehículo 1234-ABC — Conductor: Juan Pérez

  ✅ 08:00  Cotizaciones planificadas (3)
  ✅ 08:15  Sesión creada (DRAFT)
  ✅ 08:30  Carga iniciada — 45 cilindros
  ✅ 09:00  Vehículo listo
  ✅ 09:15  En ruta

  📦 Movimientos:
  ✅  SC #55 — 10 cilindros a Cliente A  [stock: OK]
  ✅  SC #56 — 15 cilindros a Cliente B  [stock: OK]
  ✅  IC #57 — 8 vacíos de Cliente A     [stock: OK]
  ⏳  IC #58 — 5 vacíos de Cliente B     [stock: PENDING]

  ⏳ 16:30  Vehículo regresando
  ⬜ 17:00  Cierre de sesión

  Resumen: +25 salidas · +8 retornos · stock sincronizado ✅
```

Cada movimiento muestra su `stock_sync_status` como badge: `OK ✅` o `PENDING ⏳`.

### Navegación

Se accede desde la grilla de sesiones (`/logistics/sessions`) → clic en una fila.

---

## Criterios de aceptación

### Bridge logistics → stock (sincrónico)

1. Confirmar movimiento SC con items → stock registra `sale_out` en la misma transacción.
2. Confirmar movimiento IC con items → stock registra `return_in` en la misma transacción.
3. Si stock rechaza (sin inventario) → movimiento NO se confirma, error 409, rollback completo.
4. Movimiento confirmado → `stock_sync_status = synced`, todos los items escritos en `stk_ledger`.
5. Trazabilidad: `stk_ledger.reference_type = "movement"`, `reference_id = movement.id`.

### Cierre de sesión

6. `POST /vehicle-sessions/{id}/close` con RETURNING → 200, `status=CLOSED`, warnings incluidos.
7. `POST /vehicle-sessions/{id}/close` con OUTBOUND → 409.
8. Sesión con movimientos PENDING → cierra igual, pero warnings en respuesta.
9. Sesión cerrada → evento `logistics.session.closed` en `event_log`.

### Vista de sesión

10. Panel muestra timeline con todos los hitos de la sesión.
11. Cada movimiento muestra badge `stock: OK` o `stock: PENDING`.
12. Sesión CLOSED → resumen final con totales de cilindros entregados/retornados.
13. Ruff + pyright limpios.
14. Tests existentes de logistics pasan sin cambios.

---

## Archivos afectados

### Logistics

```
plugins/logistics/backend/services/stock_bridge.py         NUEVO — lógica de push a stock
plugins/logistics/backend/services/movements.py            MODIFICADO — llama al bridge en confirm
plugins/logistics/backend/models/movement_items.py         MODIFICADO — +product_id FK
plugins/logistics/backend/models/sessions.py               MODIFICADO — +CLOSED en status
plugins/logistics/backend/routers/sessions.py              MODIFICADO — +POST close
plugins/logistics/backend/services/sessions.py             MODIFICADO — +close_session()
plugins/logistics/migrations/                              NUEVA — product_id en movement_items
plugins/logistics/plugin.json                              MODIFICADO — +permiso +evento
plugins/logistics/backend/plugin.py                        MODIFICADO — registrar
plugins/logistics/frontend/sessions/SessionStatusPanel.tsx NUEVO — timeline
```

### Stock

```
(sin cambios — el bridge importa servicios directamente, misma transacción)
```

---

## Dependencias

- SPEC 0016.2 — stock con allocations, costeo y movimientos (implementada)
- SPEC 0028 — DraftOverlay en planning (implementada)
- ADR 0005 — event bus (implementado)
- `plugins/logistics/` — vehicle sessions, movements, cylinders (implementado)
- `plugins/stock/` — servicios de movimientos (implementado)

---

## Referencias

- `docs/specs/core/0016-2-stock-transactional-gaps.md`
- `docs/specs/core/0028-draft-overlay-planificacion.md`
- `docs/adr/0005-event-bus-auditoria.md`
- `docs/adr/0021-core-internal-api.md`
- `plugins/logistics/` — código actual
- `plugins/stock/` — código actual
