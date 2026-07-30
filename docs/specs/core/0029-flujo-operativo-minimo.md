# SPEC 0029 — Cierre del flujo operativo: gaps reales

## Estado

Propuesta — v4 (incorpora revisión completa de arquitectura)

## Contexto

Un audit completo del código (`plugins/logistics/`, `plugins/ventas/`, `plugins/stock/`) reveló que el flujo operativo ya está implementado en ~90%:

- El stock bridge **ya existe** (`logistics/services/stock_bridge.py` → `adjust_required_product_stock`)
- El session close **ya existe** (`routers/reconciliation.py` → `close_vehicle_session`)
- Las route operations **ya crean SC/IC automáticamente** al confirmarse
- El state machine de cilindros **ya tiene 18 estados y 34 transiciones**
- La conciliación **ya existe** con conteo físico vs esperado

Los gaps reales son 4. Esta spec reemplaza completamente las versiones anteriores.

## Principios

1. **Logistics nunca calcula stock.** Logistics solicita operaciones de stock. Stock es el único owner del inventario.
2. **Stock no conoce logistics.** El bridge vive en logistics y traduce movimientos a operaciones de stock.
3. **Un movimiento CONFIRMED implica stock sincronizado.** Si stock falla, el movimiento no se confirma.
4. **Almacenes técnicos no son visibles al usuario.** `MOB-{PLATE}` existen solo para operaciones internas de sesión.

---

## Gap 1 — Stock allocation al confirmar cotización

**Problema**: `PATCH /cotizaciones/{id}/status` → CONFIRMED solo cambia `draft.status = "CONFIRMED"`. No llama al sistema de allocations de stock (SPEC 0016.2). El stock nunca se reserva al confirmar.

**Solución**: `patch_cotizacion_status` debe llamar al servicio de allocation de stock por cada item de la cotización cuando el status transiciona a `CONFIRMED`.

```python
# En patch_cotizacion_status, después de setear status = CONFIRMED:
if body.status == "CONFIRMED":
    for item in items:
        allocate_stock(
            db,
            product_id=item.product_id,
            warehouse_id=resolve_warehouse(draft),  # ver nota abajo
            quantity=item.quantity,
            reference_type="quote",
            reference_id=draft.id,
            allocation_group_id=draft.id,
            action_context=...,
        )
```

**Regla**: si stock no tiene inventario suficiente para algún item, la confirmación FALLA con 409. No se confirma una cotización que no puede cumplirse.

**Nota sobre `warehouse_id`**: La resolución del almacén que reserva (por defecto del producto, por sucursal de la cotización, por elección del vendedor, o por planificación) es una decisión de negocio que pertenece a la capa de ventas/stock. Esta spec no fija esa política. La implementación usará un helper `resolve_warehouse(draft)` cuya lógica se define en una spec futura de ventas.

**Archivos**:
```
plugins/ventas/cotizacion/backend/router.py  — allocate_stock en CONFIRMED
```

---

## Gap 2 — Cotización → Planning sin FK

**Problema**: `lg_planning_reservations` no tiene columna `quote_id`. El link se guarda como texto en `notes` (`"Cotización #1234 — ..."`). No es una relación, es únicamente texto.

**Solución**: Agregar `quote_id` como FK real. La arquitectura ya usa FKs entre plugins (stock → productos, stock → logistics, ventas → crm). Mantener consistencia.

```sql
ALTER TABLE lg_planning_reservations ADD COLUMN quote_id VARCHAR(36);
```

El `CreatePlanningReservationDialog` ya tiene el `quote_id` disponible vía `quotePrefill`. Solo falta persistirlo en el payload y en el backend.

**Archivos**:
```
plugins/logistics/backend/models/planning.py                — +quote_id
plugins/logistics/backend/routers/planning_reservations.py   — aceptar quote_id en payload
plugins/logistics/frontend/planning/dialogs/...dialog.tsx    — enviar quote_id
plugins/logistics/migrations/                                — ADD COLUMN
```

---

## Gap 3 — RETURNING como estado interno, retorno automático

**Problema**: La sesión se queda en RETURNING hasta que alguien llama explícitamente `POST /return-remaining`. Si el operador olvida ese paso, la sesión nunca avanza a AWAITING_RECONCILIATION.

**Solución**: `mark-returning` ejecuta el retorno completo en un solo paso. RETURNING se mantiene como estado interno/transitorio (dura milisegundos), pero el endpoint avanza directo a AWAITING_RECONCILIATION.

```
OUTBOUND
   │
   ▼
RETURNING (transitorio, interno)
   │  ejecuta return_remaining_stock(mobile → origin)
   ▼
AWAITING_RECONCILIATION
   │
   ▼
CLOSED
```

El endpoint `POST /return-remaining` se mantiene como opción manual para casos excepcionales. El frontend nunca muestra RETURNING; desde la perspectiva del usuario el flujo es OUTBOUND → AWAITING_RECONCILIATION.

**Nota sobre el nombre**: `mark-returning` ya no solo "marca", ejecuta el retorno. Evaluar renombrar a `begin-return` en una iteración futura si la semántica actual genera confusión. Esta spec no impone el cambio de nombre.

**Archivos**:
```
plugins/logistics/backend/routers/sessions.py   — return-remaining automático
plugins/logistics/backend/services/sessions.py  — lógica
```

---

## Gap 4 — Almacenes MOBILE visibles en catálogos

**Problema**: Los almacenes `MOB-{PLATE}` (virtuales, creados automáticamente por sesión con `warehouse_type="MOBILE"`) aparecen en selectores de almacén de stock, logistics y cualquier tool que consuma `list_warehouses`. Son almacenes técnicos, no operativos.

**Solución**: Filtrar `warehouse_type != "MOBILE"` en las funciones de catálogo visibles al usuario. Las operaciones internas (transfers, stock bridge) siguen accediendo por `get_warehouse(id)`, sin filtro.

**Archivos**:
```
plugins/stock/backend/services/catalog.py       — list_warehouses +warehouse_type != "MOBILE"
plugins/logistics/backend/services/catalog.py    — list_warehouses_catalog +warehouse_type != "MOBILE"
plugins/logistics/backend/services/resources.py  — list_warehouses +warehouse_type != "MOBILE"
```

> **Nota**: Gap 4 ya fue implementado durante la revisión de esta spec. Se incluye aquí para trazabilidad.

---

## Compatibilidad

Los cambios propuestos son compatibles con sesiones existentes:
- Gap 1: afecta solo nuevas confirmaciones de cotización.
- Gap 2: columna nueva con default NULL, sin impacto en registros existentes.
- Gap 3: cambio de comportamiento en `mark-returning`; sesiones ya en RETURNING no se ven afectadas.
- Gap 4: solo afecta consultas de lectura, sin cambios estructurales.

No se requiere migración funcional. Solo la migración estructural de `quote_id` (Gap 2).

---

## Criterios de aceptación

### Gap 1 — Allocation en confirmación
1. Confirmar cotización con items → stock `reserved_quantity` incrementa por cada item.
2. Confirmar cotización sin stock suficiente → 409, cotización sigue DRAFT, rollback completo.
3. `stk_allocation` creada con `reference_type="quote"`, `allocation_group_id=quote_id`.

### Gap 2 — FK quote_id
4. Crear planning desde DraftOverlay → `quote_id` persiste en `lg_planning_reservations`.
5. `GET /planning/reservations/{id}` → response incluye `quote_id`.

### Gap 3 — Retorno automático
6. `POST /mark-returning` → sesión pasa a AWAITING_RECONCILIATION, stock transferido de mobile a origen.
7. `POST /return-remaining` sigue funcionando como endpoint independiente.
8. RETURNING no es visible en el frontend.

### Gap 4 — MOBILE filtrado
9. `GET /stock/catalog/warehouses` no incluye almacenes con `warehouse_type="MOBILE"`.
10. `GET /logistics/catalog/warehouses` no incluye almacenes MOBILE.
11. Transferencias internas siguen funcionando con `mobile_warehouse_id`.

---

## No incluye

- No define la política de resolución de `warehouse_id` para el allocation (decisión de ventas/stock)
- No modifica el stock bridge (ya existe y funciona)
- No modifica el session close (ya existe en reconciliation)
- No modifica route operations, movements, ni cylinders
- No modifica el DraftOverlay (ya funciona)

---

## Referencias

- Audit de código real (sesión 2026-07-27)
- SPEC 0016.2 — stock allocations
- SPEC 0028 — DraftOverlay
- `plugins/logistics/backend/services/stock_bridge.py`
- `plugins/logistics/backend/routers/reconciliation.py`
- `plugins/logistics/backend/services/route_operations.py`
