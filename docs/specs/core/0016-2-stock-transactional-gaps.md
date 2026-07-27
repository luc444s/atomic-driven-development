# SPEC 0016.2 — Stock Plugin: Cierre de gaps transaccionales

## Estado

Propuesta — v2 (incorpora feedback de revisión de arquitectura)

## Contexto

SPEC 0016 implementó el ledger base de inventario. SPEC 0016.1 cubre gaps de producción (claims warehouse_id, branch_id en lg_warehouses, concurrencia PostgreSQL, cierre UX).

Esta spec cubre los **3 gaps que bloquean la operación de los módulos transaccionales futuros**, con 6 protecciones críticas adicionales detectadas en revisión de arquitectura:

1. **Reservas/asignaciones** — `stk_balance.quantity` no distingue disponible de reservado
2. **Tipos de operación insuficientes** — solo 4 tipos; se necesitan 12+
3. **Costeo por movimiento** — promedio ponderado con reglas estrictas por tipo de operación

### Protecciones críticas (incorporadas)

1. **Over-reservation protection** — `SELECT ... FOR UPDATE` obligatorio en allocate
2. **consume vs sale_out** — se elimina `consume`; `sale_out` unifica con parámetro `source`
3. **adjust+ sin costo prohibido** — `unit_cost` REQUERIDO en ajustes positivos
4. **return_in usa costo histórico** — lookup al `sale_out` original
5. **Política de stock negativo** — `allow_negative_stock` en config
6. **Transferencias respetan reservas** — `transfer_out` solo sobre `available_quantity`

---

## Gap 1 — Reservas y asignaciones de stock

### 1.1 Modelo de datos

#### `stk_balance` — nuevas columnas

```sql
ALTER TABLE stk_balance ADD COLUMN reserved_quantity NUMERIC(12,3) NOT NULL DEFAULT 0;
ALTER TABLE stk_balance ADD COLUMN total_cost NUMERIC(14,4) NOT NULL DEFAULT 0;
ALTER TABLE stk_balance ADD COLUMN allow_negative_stock BOOLEAN NOT NULL DEFAULT FALSE;
```

Semántica:
- `quantity` = cantidad total (física + en tránsito)
- `reserved_quantity` = cantidad bloqueada por cotizaciones/pedidos confirmados
- `available_quantity` = `quantity - reserved_quantity` (calculado, nunca persistido)
- `allow_negative_stock` = si FALSE, rechaza operaciones que lleven `quantity` a negativo

Reglas de integridad (enforced en aplicación + CHECK si es viable):
- `reserved_quantity >= 0`
- `reserved_quantity <= quantity` (salvo si `allow_negative_stock = true`)
- `quantity >= 0` (salvo si `allow_negative_stock = true`)

#### `stk_allocation` — nueva tabla

```sql
CREATE TABLE stk_allocation (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES tenants(id),
    allocation_group_id UUID,                          -- agrupa líneas de una misma cotización/pedido
    product_id          UUID NOT NULL REFERENCES prod_products(id),
    warehouse_id        UUID NOT NULL REFERENCES lg_warehouses(id),
    quantity            NUMERIC(12,3) NOT NULL CHECK (quantity > 0),
    remaining_quantity  NUMERIC(12,3) NOT NULL,        -- decrece en consumes parciales
    reference_type      VARCHAR(50) NOT NULL,           -- 'quote', 'order', 'waybill'
    reference_id        UUID NOT NULL,
    status              VARCHAR(20) NOT NULL DEFAULT 'active'
                        CHECK (status IN ('active', 'partially_consumed', 'consumed', 'released', 'expired')),
    created_by          UUID NOT NULL REFERENCES users(id),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at          TIMESTAMPTZ,                    -- NULL = no expira
    released_at         TIMESTAMPTZ,
    released_by         UUID REFERENCES users(id),
    release_reason      TEXT,
    UNIQUE (tenant_id, reference_type, reference_id, product_id, warehouse_id)
);

CREATE INDEX idx_stk_allocation_group ON stk_allocation(tenant_id, allocation_group_id) WHERE status IN ('active', 'partially_consumed');
CREATE INDEX idx_stk_allocation_expires ON stk_allocation(tenant_id, expires_at) WHERE status = 'active' AND expires_at IS NOT NULL;
```

Campos clave:
- `allocation_group_id` — agrupa todas las líneas de una cotización (quote_id). Permite liberar/consumir en batch.
- `remaining_quantity` — inicia = `quantity`; decrece en cada `sale_out` con `source=allocation`. Llega a 0 → status = `consumed`.
- `expires_at` — si se configura, un job programado libera allocations expiradas.

### 1.2 🔴 Over-reservation protection (OBLIGATORIO)

El endpoint `/stock/allocate` **debe** usar lock pesimista:

```python
def allocate_stock(db, tenant_id, product_id, warehouse_id, quantity, ...):
    balance = db.execute(
        select(StockBalance)
        .where(
            StockBalance.tenant_id == tenant_id,
            StockBalance.product_id == product_id,
            StockBalance.warehouse_id == warehouse_id,
        )
        .with_for_update()          # ← OBLIGATORIO, no opcional
    ).scalar_one_or_none()

    if balance is None:
        raise NotFoundError(...)

    available = balance.quantity - balance.reserved_quantity
    if available < quantity:
        raise InsufficientStockError(...)

    balance.reserved_quantity += quantity
    # ... persistir stk_allocation, stk_ledger(reserve), auditoría ...
```

Sin `FOR UPDATE`, dos threads concurrentes pueden leer el mismo `available` y sobre-reservar.

### 1.3 🔴 consume ELIMINADO — sale_out unificado

**Problema**: `consume` y `sale_out` ambos hacen `-quantity`, generando ambigüedad sobre cuál usa facturación.

**Solución**: Se elimina `consume` como operación independiente. `sale_out` cubre ambos casos mediante el parámetro `source`:

| source | ¿Busca allocation? | ¿Toca reserved_quantity? | ¿Toca quantity? | Flujo |
|--------|-------------------|--------------------------|-----------------|-------|
| `allocation` | Sí (requiere `allocation_id`) | Sí (-N) | Sí (-N) | facturación consume reserva |
| `direct` | No | No | Sí (-N) | venta sin reserva previa |

Esto simplifica el modelo: el ledger solo tiene `sale_out` (nunca `consume`).

#### Flujo con reserva

```
ventas → POST /stock/allocate     → stk_allocation(status=active), reserved_quantity+N
facturacion → POST /stock/sale-out  { source: "allocation", allocation_id: "..." }
  → descuenta quantity
  → descuenta reserved_quantity
  → decrementa remaining_quantity en allocation
  → si remaining_quantity llega a 0: status = 'consumed'
  → ledger: sale_out
```

#### Flujo sin reserva (venta directa)

```
facturacion → POST /stock/sale-out  { source: "direct" }
  → descuenta quantity
  → NO toca reserved_quantity
  → ledger: sale_out
```

### 1.4 API de allocations

| Método | Path | Descripción |
|--------|------|-------------|
| `POST` | `/stock/allocate` | Reservar stock. Body: `product_id`, `warehouse_id`, `quantity`, `reference_type`, `reference_id`, `allocation_group_id?`, `expires_at?`. Usa `FOR UPDATE`. |
| `POST` | `/stock/allocate/{id}/release` | Liberar reserva individual. Opcional `reason`. |
| `POST` | `/stock/allocate/group/{group_id}/release` | Liberar todas las activas de un grupo (ej. cancelar cotización completa). |
| `GET` | `/stock/allocations` | Listar (filtros: `status`, `reference_type`, `allocation_group_id`, `product_id`, `warehouse_id`). |
| `GET` | `/stock/allocations/{id}` | Detalle de una allocation. |
| `GET` | `/stock/allocations/group/{group_id}` | Todas las allocations de un grupo. |

### 1.5 Expiración automática

Si `expires_at` está configurado y `expires_at < now()` con status `active`:
- Un job programado (Dramatiq cron, cada 5 min) libera allocations vencidas
- status → `expired`, `reserved_quantity` liberado, ledger `release` con reason="auto-expired"

### 1.6 Permisos de allocation

```
stock.allocation.create   — Crear reservas
stock.allocation.release  — Liberar reservas
stock.allocation.read     — Ver reservas
```

(Se elimina `stock.allocation.consume` — reemplazado por `stock.movement.sale_out` con `source=allocation`)

### 1.7 Eventos de allocation

```
stock.allocation.reserved    — { product_id, warehouse_id, quantity, allocation_group_id, reference_type, reference_id, expires_at }
stock.allocation.released    — { product_id, warehouse_id, quantity, allocation_group_id, reference_type, reference_id, reason }
stock.allocation.expired     — { product_id, warehouse_id, quantity, allocation_group_id, reference_type, reference_id }
```

(Se elimina `stock.allocation.consumed` — el consumo de allocation emite `stock.movement.sale_out` con `source=allocation`)

### 1.8 🔴 Transferencias solo sobre available_quantity

`transfer_out` debe validar contra `available_quantity`, no contra `quantity`:

```python
def transfer_stock(db, ...):
    # ...
    available = origin.quantity - origin.reserved_quantity
    if available < quantity:
        raise ValueError(
            f"Stock insuficiente: disponible={available}, "
            f"reservado={origin.reserved_quantity}"
        )
```

Esto evita transferir stock que ya está comprometido con cotizaciones confirmadas.

---

## Gap 2 — Tipos de operación extendidos

### 2.1 CHECK constraint final

```sql
ALTER TABLE stk_ledger DROP CONSTRAINT ck_stk_ledger_operation;
ALTER TABLE stk_ledger ADD CONSTRAINT ck_stk_ledger_operation CHECK (
    operation IN (
        'initial', 'adjust',
        'transfer_in', 'transfer_out',
        'reserve', 'release',
        'sale_out', 'purchase_in', 'return_in', 'damage_out',
        'production_in', 'production_out'
    )
);
```

Nota: `consume` eliminado (absorbido en `sale_out` con `source=allocation`).

### 2.2 Matriz completa de operaciones

| Operación | Signo en quantity | Signo en reserved | Signo en total_cost | source | Dispara desde |
|-----------|-------------------|-------------------|---------------------|--------|---------------|
| `initial` | + | 0 | +unit_cost | — | migración |
| `adjust` | ± | 0 | ±unit_cost | — | manual (unit_cost REQUERIDO si positivo) |
| `transfer_in` | + | 0 | +cost | — | transferencia (hereda costo del origen) |
| `transfer_out` | - | 0 | -cost | — | transferencia (usa available_quantity) |
| `reserve` | 0 | + | 0 | — | ventas confirma cotización |
| `release` | 0 | - | 0 | — | cancelación / expiración |
| `sale_out` | - | - (si allocation) | -cost | `allocation` o `direct` | facturación / venta directa |
| `purchase_in` | + | 0 | +unit_cost | — | compras recibe proveedor |
| `return_in` | + | 0 | +cost_historico | — | devolución (usa costo del sale_out original) |
| `damage_out` | - | 0 | -cost | — | baja por rotura |
| `production_in` | + | 0 | +unit_cost | — | producción / llenado |
| `production_out` | - | 0 | -cost | — | consumo de materia prima |

### 2.3 API de movimientos

| Método | Path | Descripción |
|--------|------|-------------|
| `POST` | `/stock/sale-out` | Salida por venta. Body: `product_id`, `warehouse_id`, `quantity`, `source` (`allocation`\|`direct`), `allocation_id?` (requerido si source=allocation), `reference_type`, `reference_id`, `idempotency_key?` |
| `POST` | `/stock/purchase-in` | Entrada por compra. Body: `product_id`, `warehouse_id`, `quantity`, `unit_cost` (REQUERIDO), `reference_type`, `reference_id`, `idempotency_key?` |
| `POST` | `/stock/return-in` | Devolución de cliente. Body: `product_id`, `warehouse_id`, `quantity`, `original_sale_ledger_id` (REQUERIDO — para lookup de costo histórico), `reference_type`, `reference_id`, `idempotency_key?` |
| `POST` | `/stock/damage-out` | Baja por rotura. Body: `product_id`, `warehouse_id`, `quantity`, `reason`, `reference_type`, `reference_id`, `idempotency_key?` |

### 2.4 Permisos de movimiento

```
stock.movement.sale_out      — Registrar salidas por venta
stock.movement.purchase_in   — Registrar entradas por compra
stock.movement.return_in     — Registrar devoluciones
stock.movement.damage_out    — Registrar bajas
```

### 2.5 🔴 Negative stock policy

`stk_balance.allow_negative_stock` (default FALSE):

- **FALSE**: `sale_out`, `damage_out`, `transfer_out` rechazan si `quantity - requested < 0`
- **TRUE**: permite stock negativo. El balance queda con `quantity < 0`. Se emite evento `stock.balance.negative_warning` para alertar a operaciones.

Endpoint para configurarlo:

```
PUT /stock/config  → body incluye allow_negative_stock: bool
```

El config existente (`stk_config`) gana esta columna:

```sql
ALTER TABLE stk_config ADD COLUMN allow_negative_stock BOOLEAN NOT NULL DEFAULT FALSE;
```

---

## Gap 3 — Costeo por movimiento

### 3.1 🔴 Regla 1: adjust positivo → unit_cost REQUERIDO

**Problema**: ajuste +10 sin costo sobre balance de 10u a 10€ → unit_cost pasa de 10€ a 5€, lo cual es falso.

**Solución**: `POST /stock/adjust` con `quantity > 0` → `unit_cost` REQUERIDO.

```python
# Schema
class StockAdjustRequest(BaseModel):
    product_id: str
    warehouse_id: str
    quantity: float
    unit_cost: float | None = None     # REQUERIDO si quantity > 0
    reason: str | None = None
    idempotency_key: str | None = None

# Validación en servicio
def adjust_stock(db, *, quantity, unit_cost, ...):
    if quantity > 0 and unit_cost is None:
        raise ValueError("unit_cost es obligatorio para ajustes positivos")
    if quantity < 0:
        # usa costo promedio del balance (misma lógica que sale_out)
        unit_cost = balance.total_cost / balance.quantity
```

Esto garantiza que el costo promedio nunca se diluya artificialmente.

### 3.2 🔴 Regla 2: return_in usa costo histórico del sale_out original

**Problema**: cliente devuelve producto comprado a 6€ pero el promedio actual es 8€. ¿Qué costo se usa?

**Solución**: `return_in` recibe `original_sale_ledger_id` y busca el `unit_cost` de ese ledger entry.

```python
def return_in_stock(db, *, original_sale_ledger_id, ...):
    original = db.execute(
        select(StockLedger).where(StockLedger.id == original_sale_ledger_id)
    ).scalar_one_or_none()

    if original is None or original.operation != 'sale_out':
        raise ValueError("original_sale_ledger_id debe referenciar un sale_out válido")

    unit_cost = original.unit_cost  # costo histórico
    # ... registrar return_in con ese unit_cost
```

Esto mantiene la consistencia contable: la devolución entra al mismo costo con que salió.

### 3.3 Regla 3: transferencia hereda costo

Sin cambios respecto a v1: la salida usa costo promedio del origen, la entrada recibe ese mismo `unit_cost`.

### 3.4 Regla 4: sale_out con source=allocation

Cuando `sale_out` consume una allocation, calcula el costo normalmente del promedio. El allocation no almacena costo (el costo se determina en el momento de la salida real, no en el momento de la reserva).

### 3.5 Nuevos campos en modelos

#### `stk_ledger`

```sql
ALTER TABLE stk_ledger ADD COLUMN unit_cost NUMERIC(14,4);
ALTER TABLE stk_ledger ADD COLUMN total_cost NUMERIC(14,4);
ALTER TABLE stk_ledger ADD COLUMN cost_after NUMERIC(14,4);
ALTER TABLE stk_ledger ADD COLUMN source VARCHAR(20);       -- 'allocation' | 'direct' | NULL
```

`source` solo se puebla en operaciones `sale_out`; NULL para el resto.

---

## Modelo de datos consolidado

```sql
-- stk_ledger (columnas nuevas marcadas con ★)
ALTER TABLE stk_ledger ADD COLUMN unit_cost NUMERIC(14,4);        -- ★ Gap 3
ALTER TABLE stk_ledger ADD COLUMN total_cost NUMERIC(14,4);       -- ★ Gap 3
ALTER TABLE stk_ledger ADD COLUMN cost_after NUMERIC(14,4);       -- ★ Gap 3
ALTER TABLE stk_ledger ADD COLUMN source VARCHAR(20);             -- ★ Gap 1 (allocation|direct)

-- stk_balance (columnas nuevas marcadas con ★)
ALTER TABLE stk_balance ADD COLUMN reserved_quantity NUMERIC(12,3) NOT NULL DEFAULT 0;   -- ★ Gap 1
ALTER TABLE stk_balance ADD COLUMN total_cost NUMERIC(14,4) NOT NULL DEFAULT 0;          -- ★ Gap 3
ALTER TABLE stk_balance ADD COLUMN allow_negative_stock BOOLEAN NOT NULL DEFAULT FALSE;  -- ★ Gap 2.5

-- stk_allocation (tabla nueva)
CREATE TABLE stk_allocation ( ... );   -- ★ Gap 1

-- stk_config (columna nueva)
ALTER TABLE stk_config ADD COLUMN allow_negative_stock BOOLEAN NOT NULL DEFAULT FALSE;   -- ★ Gap 2.5

-- CHECK constraint (reemplazado)
-- operation IN ('initial','adjust','transfer_in','transfer_out','reserve','release',
--               'sale_out','purchase_in','return_in','damage_out','production_in','production_out')
```

---

## API consolidada final

| Método | Path | Permiso | Gap |
|--------|------|---------|-----|
| `GET` | `/stock/balance` | `stock.balance.read` | existente |
| `GET` | `/stock/balance/{pid}` | `stock.balance.read` | existente |
| `GET` | `/stock/balance/{pid}/{wid}` | `stock.balance.read` | existente |
| `GET` | `/stock/ledger` | `stock.balance.read` | existente |
| `GET` | `/stock/ledger/{pid}` | `stock.balance.read` | existente |
| `GET` | `/stock/ledger/{pid}/{wid}` | `stock.balance.read` | existente |
| `POST` | `/stock/adjust` | `stock.balance.adjust` | schema ampliado (unit_cost requerido si +) |
| `POST` | `/stock/transfer` | `stock.transfer.create` | lógica ampliada (usa available_quantity) |
| `GET` | `/stock/config` | `stock.config.read` | schema ampliado |
| `PUT` | `/stock/config` | `stock.config.manage` | schema ampliado (allow_negative_stock) |
| **`POST`** | **`/stock/allocate`** | **`stock.allocation.create`** | **Gap 1** |
| **`POST`** | **`/stock/allocate/{id}/release`** | **`stock.allocation.release`** | **Gap 1** |
| **`POST`** | **`/stock/allocate/group/{gid}/release`** | **`stock.allocation.release`** | **Gap 1** |
| **`GET`** | **`/stock/allocations`** | **`stock.allocation.read`** | **Gap 1** |
| **`GET`** | **`/stock/allocations/{id}`** | **`stock.allocation.read`** | **Gap 1** |
| **`GET`** | **`/stock/allocations/group/{gid}`** | **`stock.allocation.read`** | **Gap 1** |
| **`POST`** | **`/stock/sale-out`** | **`stock.movement.sale_out`** | **Gap 2+3** |
| **`POST`** | **`/stock/purchase-in`** | **`stock.movement.purchase_in`** | **Gap 2+3** |
| **`POST`** | **`/stock/return-in`** | **`stock.movement.return_in`** | **Gap 2+3** |
| **`POST`** | **`/stock/damage-out`** | **`stock.movement.damage_out`** | **Gap 2+3** |

(20 endpoints total, 5 existentes ampliados, 11 nuevos)

---

## Permisos consolidados

```json
{
  "permissions": [
    "stock.balance.read",
    "stock.balance.adjust",
    "stock.transfer.create",
    "stock.config.read",
    "stock.config.manage",
    "stock.allocation.create",
    "stock.allocation.release",
    "stock.allocation.read",
    "stock.movement.sale_out",
    "stock.movement.purchase_in",
    "stock.movement.return_in",
    "stock.movement.damage_out"
  ]
}
```

(12 permisos — se eliminó `stock.allocation.consume`)

---

## Eventos consolidados

```json
{
  "events": [
    "stock.balance.adjusted",
    "stock.balance.negative_warning",
    "stock.transfer.completed",
    "stock.allocation.reserved",
    "stock.allocation.released",
    "stock.allocation.expired",
    "stock.movement.sale_out",
    "stock.movement.purchase_in",
    "stock.movement.return_in",
    "stock.movement.damage_out"
  ]
}
```

(10 eventos — se eliminó `stock.allocation.consumed`, se agregó `stock.allocation.expired` y `stock.balance.negative_warning`)

---

## Conexión con el sistema existente

```
Cotización (ventas)
  QuoteDraft → CONFIRMED → POST /stock/allocate
    allocation_group_id = quote_id
    expires_at = now() + 24h (configurable)

Planificación (logistics)
  PlanningEntry → NO toca stock directamente

VehicleSession (logistics)
  RouteOperation → NO toca stock directamente

Movimiento / Albarán (logistics)
  Movement → SÍ toca stock:
    - entrega → POST /stock/sale-out { source: "allocation", allocation_id }
    - devolución → POST /stock/return-in { original_sale_ledger_id }
    - traslado → ya cubierto por /stock/transfer

Facturación (futuro)
  Emitir factura → POST /stock/sale-out { source: "allocation", allocation_id }
  Nota de crédito / devolución → POST /stock/return-in { original_sale_ledger_id }

Compras (futuro)
  Recepción proveedor → POST /stock/purchase-in { unit_cost, reference_type: "purchase_order" }
```

---

## Criterios de aceptación

### Gap 1 — Reservas + protecciones

1. Dos threads concurrentes intentan reservar 10u con solo 10u disponibles → uno crea la reserva, el otro recibe 409 (gracias a `FOR UPDATE`).
2. `POST /stock/allocate` con `allocation_group_id` → allocation agrupada.
3. `POST /stock/allocate/group/{gid}/release` → todas las allocations del grupo liberadas.
4. Allocation con `expires_at` en pasado → job la marca `expired` y libera `reserved_quantity`.
5. `sale_out` con `source=allocation` y `allocation_id` → descuenta `quantity`, decrementa `remaining_quantity`, y si llega a 0 marca `consumed`.
6. `sale_out` con `source=direct` → descuenta `quantity`, no toca allocations ni `reserved_quantity`.
7. `transfer_out` con stock reservado → solo transfiere `available_quantity`, rechaza si `available < requested`.

### Gap 2 — Tipos de operación + negative stock

8. `allow_negative_stock=false` + `sale_out` que llevaría a negativo → 422.
9. `allow_negative_stock=true` + `sale_out` que lleva a negativo → éxito, ledger muestra quantity negativo, se emite `stock.balance.negative_warning`.
10. `POST /stock/purchase-in` con `unit_cost` → ledger muestra `unit_cost`, balance actualiza `total_cost`.
11. `POST /stock/return-in` con `original_sale_ledger_id` → ledger muestra `unit_cost` igual al `sale_out` original.
12. Operación con tipo no soportado → CHECK constraint rechaza.

### Gap 3 — Costeo

13. Entrada compra 10u a 5€ → `total_cost=50`, `unit_cost=5`.
14. Segunda compra 10u a 7€ → `total_cost=120`, `unit_cost=6` (promedio ponderado).
15. `sale_out` 5u → `unit_cost=6`, `total_cost-30`, `cost_after=90`.
16. `transfer` 3u entre almacenes → destino recibe `unit_cost=6`.
17. `adjust +10` sin `unit_cost` → **RECHAZADO** con 422 (unit_cost requerido).
18. `adjust +10` con `unit_cost=8` → `total_cost` actualizado correctamente.
19. Stock llega a quantity=0 → `total_cost=0`, `unit_cost` en API = NULL.
20. `return_in` de producto vendido a 6€ cuando promedio actual es 9€ → entra a 6€ (costo histórico).

### Regresión

21. Todos los tests de SPEC 0016 y 0016.1 siguen pasando.
22. `ruff check plugins/stock/` → 0 errores.
23. `pyright plugins/stock/` → 0 errores.
24. `pytest plugins/stock/` → 100% pass.

---

## No incluye

1. Conteo físico cíclico (inventario físico).
2. Múltiples métodos de costeo (FIFO, LIFO, específico) — solo promedio ponderado.
3. Valuación fiscal o ajustes por inflación.
4. Integración automática con logistics vía eventos (se hará en specs futuras de los módulos transaccionales).
5. Kardex contable completo con asientos (sigue siendo del futuro módulo de contabilidad).
6. Job de expiración automática (Dramatiq) — se implementa pero su scheduling es parte de infraestructura, no de esta spec.

---

## Migraciones (orden de ejecución)

```
0016.2.1_add_reserved_quantity.py       — ALTER stk_balance ADD reserved_quantity
0016.2.2_create_stk_allocation.py       — CREATE TABLE stk_allocation
0016.2.3_add_allow_negative_stock.py    — ALTER stk_balance, stk_config ADD allow_negative_stock
0016.2.4_expand_operation_check.py      — DROP + ADD CONSTRAINT ck_stk_ledger_operation
0016.2.5_add_cost_columns.py            — ALTER stk_ledger ADD unit_cost, total_cost, cost_after, source
                                         — ALTER stk_balance ADD total_cost
```

---

## Dependencias

- SPEC 0016 — implementación base del plugin stock (implementada)
- SPEC 0016.1 — cierre de gaps de producción (propuesta)
- ADR 0016 — decisión arquitectónica del plugin stock (aceptado)
- ADR 0016.1 — claims y branch derivado (aceptado)
- `plugins/stock/` — código existente que se extiende
- `plugins/logistics/` — `lg_warehouses` (FK existente)
- `plugins/productos/` — `prod_products` (FK existente)
---

## Referencias

- `docs/specs/core/0016-stock-plugin/index.md`
- `docs/specs/core/0016-1-stock-plugin-gap-closure.md`
- `docs/adr/0016-stock-plugin.md`
- `docs/adr/0016-1-stock-claims-y-branch-derivado.md`
- `docs/specs/core/0023-logistics-operacion-real/0023XA-condiciones-comerciales-fiscales-y-cobro.md`
- `plugins/stock/` — implementación actual
