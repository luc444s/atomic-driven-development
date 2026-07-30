# SPEC 0029B — Stock bridge transaccional (v2)

## Estado

Implementado — v2 (2026-07-28)

## Estado anterior

Propuesta — v2 (feedback de arquitectura incorporado)

## Contexto

SPEC 0016.2 implementó operaciones transaccionales en stock. Pero el bridge (`logistics/services/stock_bridge.py`) sigue usando `adjust_stock` genérico. Esto rompe costeo, trazabilidad y la semántica de negocio.

Esta spec reemplaza `adjust_stock` por las operaciones reales y cierra 4 problemas críticos detectados en revisión.

## Principio

**0029B no cambia el bridge. Lo convierte en parte del sistema financiero.**

---

## 🔴 Problema 1: IC no referencia el SC original

### Error actual

El bridge buscaba `sale_out` por `movement.id`. Pero IC y SC son movimientos distintos con IDs distintos.

### Solución

Agregar `origin_movement_id` a `lg_movements`:

```sql
ALTER TABLE lg_movements ADD COLUMN origin_movement_id VARCHAR(36);
```

Cuando `route_operations.py` crea un movimiento IC desde un EXCHANGE o PICKUP, setea `origin_movement_id` al ID del SC que entregó esos cilindros originalmente.

El bridge para IC usa `origin_movement_id` para buscar el `sale_out` en `stk_ledger`:

```python
# Buscar el sale_out original via origin_movement_id
original_ledger = db.execute(
    select(StockLedger).where(
        StockLedger.reference_type == "movement",
        StockLedger.reference_id == movement.origin_movement_id,
        StockLedger.operation == "sale_out",
    )
).scalar_one_or_none()

return_in_stock(
    original_sale_ledger_id=original_ledger.id,
    unit_cost=original_ledger.unit_cost,  # costo histórico
)
```

### Manejo cuando no hay origin_movement_id

Si `origin_movement_id` es NULL (movimiento IC sin SC previo), el bridge **rechaza la operación** con `stock_sync_status = ERROR`. Solo se permite si el feature flag `ALLOW_LEGACY_STOCK_FALLBACK=true` está activo.

### Restricción conceptual: IC solo referencia SC

`origin_movement_id` debe apuntar a un movimiento de tipo `SC` (salida a cliente). No se permite que un IC referencie otro IC o un IP. El bridge valida esto antes de ejecutar la operación:

```python
origin = db.execute(select(LogisticsMovement).where(
    LogisticsMovement.id == movement.origin_movement_id
)).scalar_one_or_none()

if origin and origin.type_code != "SC":
    raise ValueError("origin_movement_id must reference an SC movement")
```

Esto evita errores silenciosos donde una devolución referencia otra devolución.

---

## 🔴 Problema 2: Fallback silencioso a adjust_stock

### Error actual

"Si no encuentra sale_out → fallback a adjust_stock". Esto oculta errores y produce datos inconsistentes.

### Solución

**No hay fallback silencioso.** Si el bridge no puede ejecutar la operación transaccional correcta:

1. `stock_sync_status = ERROR`
2. Log de auditoría con nivel CRÍTICO
3. El movimiento NO se confirma (rollback)

Excepción controlada: feature flag `ALLOW_LEGACY_STOCK_FALLBACK=true` permite `adjust_stock` como último recurso, pero registra warning explícito.

---

## 🔴 Problema 3: product_id desde cylinder (deprecated)

### Error actual

"Si no hay product_id → resolver desde cylinder". Esto es frágil y debe eliminarse.

### Solución

1. El bridge **prefiere** `movement_item.product_id` (columna definida en SPEC 0029 Gap 2)
2. Si no existe, intenta resolver desde cylinder **solo si** `ALLOW_CYLINDER_PRODUCT_FALLBACK=true`
3. Cada uso del fallback se registra en `stock_bridge_log` con tag `deprecated:cylinder_product_fallback`
4. Métrica expuesta: `fallback_product_resolution_count` para monitorear eliminación

---

## 🔴 Problema 4: purchase_in sin unit_cost

### Error actual

"IP → purchase_in(unit_cost=...)" sin definir de dónde sale.

### Solución

Resolución de `unit_cost` para `purchase_in`, en orden:

1. **Purchase Order** — si el movimiento referencia una OC con precio unitario
2. **Precio configurado del producto** — `prod_costs` con `cost_type=BASE`, `valid_from <= now()`. Si hay múltiples costos válidos (ej. dos rangos de fecha solapados), se usa el de `valid_from` más reciente.
3. **ERROR** — no se permite `purchase_in` sin costo. El bridge rechaza con `stock_sync_status=ERROR`.

El llamador (`route_operations.py` o quien cree el movimiento) es responsable de proveer `unit_cost` en el movimiento.

---

## 🚀 Mejora 1: stock_sync_status en movimiento

Columna calculada (no persistida) expuesta en `GET /movements/{id}`:

| Valor | Significado |
|---|---|
| `PENDING` | Movimiento no confirmado |
| `SYNCED` | Todos los items en `stk_ledger` |
| `ERROR` | Falló la sincronización con stock |

El bridge setea este estado durante `confirm_movement()`.

Para preservar historial de errores sin persistir el estado actual, se agrega una columna:

```sql
ALTER TABLE lg_movements ADD COLUMN last_stock_sync_error TEXT;
```

- Se puebla solo cuando ocurre un error (ej. "2026-07-27: stock insuficiente para producto GLP10")
- Se limpia (NULL) cuando una operación posterior tiene éxito
- `GET /movements/{id}` expone tanto `stock_sync_status` (calculado) como `last_stock_sync_error` (persistido)

Esto permite saber si un movimiento **alguna vez falló** sin necesidad de consultar `stock_bridge_log`. Para el historial completo de intentos → `stock_bridge_log`. Para el estado actual → `stock_sync_status` calculado. Para "falló antes pero ahora está bien" → `last_stock_sync_error`.

---

## 🚀 Mejora 2: Auditoría del bridge

Tabla nueva `lg_stock_bridge_log`:

```sql
CREATE TABLE lg_stock_bridge_log (
    id          VARCHAR(36) PRIMARY KEY,
    tenant_id   VARCHAR(36) NOT NULL REFERENCES tenants(id),
    movement_id VARCHAR(36) NOT NULL,
    operation   VARCHAR(20) NOT NULL,       -- sale_out, return_in, etc.
    product_id  VARCHAR(36),
    quantity    NUMERIC(12,3),
    unit_cost   NUMERIC(14,4),
    status      VARCHAR(20) NOT NULL,        -- success, error, fallback
    error_msg   TEXT,
    payload     JSONB,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

Cada operación del bridge escribe una entrada. Esto permite:
- Diagnosticar fallos en producción sin leer logs del servidor
- Auditar qué movimientos usaron fallback
- Trazabilidad completa: movement → bridge → stk_ledger

---

## 🚀 Mejora 3: Feature flag de migración

Settings:

```python
USE_TRANSACTIONAL_STOCK_BRIDGE: bool = True   # default: nuevo bridge
ALLOW_LEGACY_STOCK_FALLBACK: bool = False     # default: sin fallback
ALLOW_CYLINDER_PRODUCT_FALLBACK: bool = True  # default: permitido (transitorio)
```

Si `USE_TRANSACTIONAL_STOCK_BRIDGE=false`, el bridge usa `adjust_stock` (comportamiento anterior). Esto permite rollback inmediato en producción.

---

## 🚀 Mejora 4: Handlers separados

El bridge actual es un `if/elif` gigante. Se refactoriza a:

```python
# stock_bridge.py

def apply_stock_for_movement(db, movement, items):
    handlers = {
        "SC": _handle_sale_out,
        "IC": _handle_return_in,
        "IP": _handle_purchase_in,
        "IFP": _handle_purchase_in,
        "SP": _handle_sale_out,
        "MV": _handle_damage_out,
        "TR": _handle_transfer,
    }
    handler = handlers.get(movement.type_code)
    if handler is None:
        return  # movimiento sin impacto en stock
    for item in items:
        handler(db, movement, item)
```

---

## Mapeo final

| Movimiento | Handler | Operación stock | Datos extra |
|---|---|---|---|
| `SC` | `_handle_sale_out` | `sale_out(source=direct)` | `reference_type=movement`, `reference_id=movement.id` |
| `IC` | `_handle_return_in` | `return_in` | `original_sale_ledger_id` desde `origin_movement_id` |
| `IP` / `IFP` | `_handle_purchase_in` | `purchase_in` | `unit_cost` desde PO → config → ERROR |
| `SP` | `_handle_sale_out` | `sale_out(source=direct)` | ídem SC |
| `MV` | `_handle_damage_out` | `damage_out` | `reason=movement.notes` |
| `TR` | `_handle_transfer` | `transfer` | (sin cambios) |

---

## Archivos afectados

```
plugins/logistics/backend/services/stock_bridge.py   — REESCRITO (handlers + log)
plugins/logistics/backend/models/movements.py        — +origin_movement_id
plugins/logistics/backend/models/stock_bridge_log.py — NUEVO
plugins/logistics/migrations/                        — +origin_movement_id, +stock_bridge_log
plugins/logistics/backend/services/movements.py      — stock_sync_status calculado
apps/api/app/core/config.py                          — feature flags
```

---

## Criterios de aceptación

1. SC confirmado → `stk_ledger.operation=sale_out`, `source=direct`, `reference_type=movement`.
2. IC con `origin_movement_id` → `stk_ledger.operation=return_in`, `unit_cost` = costo del SC original.
3. IC sin `origin_movement_id` y `ALLOW_LEGACY_STOCK_FALLBACK=false` → movimiento NO se confirma, `stock_sync_status=ERROR`.
4. IP con `unit_cost` → `stk_ledger.operation=purchase_in`, `unit_cost` registrado.
5. IP sin `unit_cost` → movimiento NO se confirma, `stock_sync_status=ERROR`.
6. `USE_TRANSACTIONAL_STOCK_BRIDGE=false` → bridge usa `adjust_stock` (legacy).
7. Cada operación del bridge escribe `lg_stock_bridge_log`.
8. Tests existentes de `route_operations` y `stock` siguen pasando.

---

## Referencias

- SPEC 0016.2 — stock transaccional
- SPEC 0029 — gaps del flujo operativo
- `plugins/logistics/backend/services/stock_bridge.py`
- `plugins/stock/backend/services/movements.py`
