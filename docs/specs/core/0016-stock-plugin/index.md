# SPEC 0016 — Stock Plugin: Ledger de Inventario

## 1. Descripción

Plugin ledger de inventario para SYSTUTOR OSS. Maneja el stock de productos por almacén usando un ledger inmutable como fuente de verdad, con tabla de balance sincronizada para consultas rápidas, y configuración de mínimos/máximos.

No incluye kardex valorizado, inventario físico cíclico, ni deducción automática desde logística/ventas en el MVP.

---

## 2. Modelo de datos

### 2.1 stk_ledger — Fuente de verdad

```sql
CREATE TABLE stk_ledger (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL,
    product_id      UUID NOT NULL,
    warehouse_id    UUID NOT NULL,
    operation       VARCHAR(20) NOT NULL CHECK (operation IN (
                        'initial', 'adjust', 'transfer_in', 'transfer_out'
                    )),
    quantity        NUMERIC(12,3) NOT NULL,
    balance_after   NUMERIC(12,3) NOT NULL,
    reference_type  VARCHAR(50),       -- ej. 'adjustment', 'transfer'
    reference_id    UUID,               -- id de la entidad origen
    notes           TEXT,
    created_by      UUID NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, id)
);
```

- `balance_after` se computa al insertar dentro de una transacción serializable para la fila `(tenant_id, product_id, warehouse_id)`.
- El servicio debe bloquear la fila de `stk_balance` con `SELECT ... FOR UPDATE`; si no existe, debe crearla de forma segura antes de persistir el movimiento.
- Toda operación de ajuste o transferencia debe recalcular `balance_after` desde el saldo bloqueado, no desde un valor leído fuera de la sección crítica.
- `operation` controla el signo: `initial`, `adjust`, `transfer_in` → suma; `transfer_out` → resta.
- `reference_type`/`reference_id` permiten rastrear el origen (ej. una transferencia, un ajuste manual, una compra futura).

### 2.2 stk_balance — Tabla de balance sincronizada

```sql
CREATE TABLE stk_balance (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL,
    product_id      UUID NOT NULL,
    warehouse_id    UUID NOT NULL,
    quantity        NUMERIC(12,3) NOT NULL DEFAULT 0,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by      UUID NOT NULL,
    UNIQUE (tenant_id, product_id, warehouse_id)
);
```

- Se inserta o actualiza en la misma transacción que el ledger.
- `quantity` siempre es el `balance_after` del último movimiento en el ledger.
- No se puede escribir directo (solo desde el servicio de ledger).

### 2.3 stk_config — Mínimos y máximos

```sql
CREATE TABLE stk_config (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL,
    product_id      UUID NOT NULL,
    warehouse_id    UUID NOT NULL,
    min_quantity    NUMERIC(12,3) NOT NULL DEFAULT 0,
    max_quantity    NUMERIC(12,3),
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by      UUID NOT NULL,
    UNIQUE (tenant_id, product_id, warehouse_id)
);
```

### 2.4 Relaciones lógicas

- `stk_ledger.product_id` → FK real a `prod_products.id`
- `stk_balance.product_id` → FK real a `prod_products.id`
- `stk_config.product_id` → FK real a `prod_products.id`
- `stk_ledger.warehouse_id` → FK real a `lg_warehouses.id`
- `stk_balance.warehouse_id` → FK real a `lg_warehouses.id`
- `stk_config.warehouse_id` → FK real a `lg_warehouses.id`

Las FKs son reales porque el módulo stock no se trata como MVP desechable. La integridad referencial es obligatoria para evitar saldos huérfanos, configuraciones sin producto y movimientos apuntando a almacenes inexistentes.

### 2.4.1 Orden de migraciones

- `plugins/productos/` y `plugins/logistics/` deben migrarse antes que `plugins/stock/`.
- `plugin.json` declara `requires: ["logistics", "productos"]` para reflejar esta dependencia estructural.
- Si una instalación no tiene `productos` o `logistics`, `stock` no debe poder habilitarse.

### 2.5 Índices

- `stk_ledger`: (tenant_id, product_id, warehouse_id)
- `stk_ledger`: (tenant_id, created_at DESC)
- `stk_balance`: (tenant_id, product_id, warehouse_id) — cubre el UNIQUE
- `stk_config`: (tenant_id, product_id)

---

## 3. API

### 3.1 Saldos

| Método | Path | Descripción |
|--------|------|-------------|
| `GET` | `/stock/balance` | Listar saldos (filtros: product_id, warehouse_id, q search) |
| `GET` | `/stock/balance/{product_id}` | Saldo de un producto en todos los almacenes |
| `GET` | `/stock/balance/{product_id}/{warehouse_id}` | Saldo de un producto en un almacén específico |

### 3.2 Ledger

| Método | Path | Descripción |
|--------|------|-------------|
| `GET` | `/stock/ledger/{product_id}` | Histórico de movimientos de un producto (paginado, filtros: warehouse_id, operation, date_from, date_to) |
| `GET` | `/stock/ledger/{product_id}/{warehouse_id}` | Histórico por producto+almacén |

### 3.3 Ajustes

| Método | Path | Descripción |
|--------|------|-------------|
| `POST` | `/stock/adjust` | Registrar ajuste manual de stock (request: product_id, warehouse_id, quantity, reason) |

### 3.4 Transferencias

| Método | Path | Descripción |
|--------|------|-------------|
| `POST` | `/stock/transfer` | Transferir stock entre almacenes (request: product_id, from_warehouse_id, to_warehouse_id, quantity, notes) |

### 3.5 Configuración

| Método | Path | Descripción |
|--------|------|-------------|
| `GET` | `/stock/config` | Listar configuraciones (filtros: product_id, warehouse_id) |
| `PUT` | `/stock/config` | Crear o actualizar configuración de un producto+almacén (upsert: min_quantity, max_quantity) |

---

## 4. Permisos

```
stock.balance.read       — Ver saldos
stock.balance.adjust     — Realizar ajustes manuales
stock.transfer.create    — Crear transferencias entre almacenes
stock.config.read        — Ver configuraciones de mínimo/máximo
stock.config.manage      — Gestionar configuraciones de mínimo/máximo
```

Formato `<module>.<resource>.<action>` conforme a ADR 0003.

---

## 5. Eventos

```
stock.balance.adjusted       — Se realizó un ajuste manual
stock.transfer.completed     — Se completó una transferencia entre almacenes
```

Payload común:

```json
{
    "tenant_id": "uuid",
    "branch_id": "uuid",
    "product_id": "uuid",
    "warehouse_id": "uuid",
    "quantity": 10.0,
    "balance_after": 50.0,
    "reference_type": "adjustment",
    "reference_id": "uuid",
    "notes": "Ajuste por inventario físico",
    "actor_id": "uuid",
    "occurred_at": "2026-06-20T10:30:00Z"
}
```

---

## 6. Reglas de negocio

### 6.1 Ledger inmutable

No existe endpoint `DELETE` ni `PUT` para el ledger. Un ajuste incorrecto se corrige con un nuevo ajuste compensatorio.

### 6.2 Consistencia ledger ↔ balance

`stk_balance` se actualiza en la misma transacción que `stk_ledger`. No puede haber una entrada en el ledger que no tenga su balance reflejado.

### 6.2.1 Concurrencia y locking

- Toda escritura sobre un mismo `(tenant_id, product_id, warehouse_id)` debe ejecutarse dentro de una sección crítica con lock pesimista (`SELECT ... FOR UPDATE`) sobre `stk_balance`.
- Si dos requests concurrentes intentan ajustar el mismo producto+almacén, una espera a la otra; no se permite cálculo paralelo de `balance_after`.
- La transferencia bloquea primero el saldo origen y luego el destino en orden estable por `warehouse_id` para evitar deadlocks.
- Si la base detecta conflicto serializable o deadlock, la capa de aplicación debe hacer retry controlado e idempotente.

### 6.3 Cantidad negativa

`stk_balance.quantity` puede ser 0 pero no negativa. La API rechaza operaciones que resulten en saldo negativo.

### 6.4 Validación de almacén

El `warehouse_id` se valida con query directa a `lg_warehouses` (misma base de datos). No se usa import de servicios de logistics ni API HTTP para evitar acoplamiento entre plugins.

### 6.5 Validación de producto

El `product_id` se valida con query directa a `prod_products` (misma base de datos). No se usa API HTTP de productos.

Las validaciones en aplicación no reemplazan las FKs reales. Su objetivo es devolver errores de negocio claros antes de que la base rechace la operación.

### 6.6 Claims de autorización

Se aplica el claim `warehouse_id` (ADR 0003) para restringir qué almacenes puede ver y operar cada usuario. Los endpoints de stock filtran por los almacenes asignados al usuario autenticado, no solo por `tenant_id`.

### 6.7 Branch ID en eventos

Cuando el almacén origen o destino esté asociado a una sucursal (`branch_id`), los eventos de stock incluyen `branch_id` en su payload. La resolución de `branch_id` desde `warehouse_id` se consulta directamente en `lg_warehouses`.

### 6.8 Transferencia atómica

Una transferencia genera dos entradas en el ledger en una sola transacción: `transfer_out` en el almacén origen y `transfer_in` en el almacén destino. Si alguna falla, no se persiste ninguna.

### 6.9 Idempotencia operativa

- `POST /stock/adjust` y `POST /stock/transfer` deben aceptar un `idempotency_key` o `reference_id` único por tenant para evitar duplicados por reintento.
- Si llega la misma operación dos veces con la misma clave, el servicio retorna el resultado ya persistido y no crea nuevas entradas de ledger.

---

## 7. Frontend

### 7.1 StockBalancePage

Ruta: `/stock`

- Tabla con saldos por producto+almacén.
- Columnas: SKU, nombre del producto, almacén, cantidad, mín/máx configurados, indicador visual si está bajo mínimo.
- Filtros: producto (search + select), almacén (select), solo bajo mínimo (toggle).
- Paginación.

### 7.2 StockDetailPage

Ruta: `/stock/{product_id}/{warehouse_id}`

- Cabecera: producto, almacén, cantidad actual.
- Tabla de movimientos (ledger) paginada.
- Botones: Ajustar stock, Transferir.

### 7.3 ModalAjusteStock

Modal (Dialog) para ajuste manual de stock.

- Campos: producto (search+select), almacén (select), cantidad (numérico, con signo), motivo (textarea).
- Validación: cantidad no puede resultar en saldo negativo.
- Al guardar: `POST /stock/adjust`, refresca la tabla.

### 7.4 ModalTransferenciaStock

Modal (Dialog) para transferencia entre almacenes.

- Campos: producto (search+select, puede venir prefijado), almacén origen, almacén destino (select, no puede ser el mismo), cantidad, notas.
- Al guardar: `POST /stock/transfer`, refresca la tabla.

### 7.5 ModalConfigStock

Modal (Dialog) para configurar mínimo/máximo de un producto en un almacén.

- Campos: producto (search+select), almacén (select), cantidad mínima, cantidad máxima, activo/inactivo.
- Al guardar: `PUT /stock/config` (upsert).

### 7.6 Patrón frontend

Todos los modales siguen el mismo patrón establecido en `productos` y `crm`:
- Estado en el listado (`showAjuste`, `showTransferencia`, `showConfig`).
- Modal se abre con `Dialog` desde shadcn/ui.
- Fallback route con `asPage` para acceso directo por URL.

### 7.7 Componentes compartidos

- `ProductSearchDialog.tsx` — debe vivir en un espacio compartido (`packages/ui/` o `apps/web/src/components/`) para que stock no dependa de componentes internos de `plugins/productos/`.

---

## 8. Criterios de aceptación

### 8.1 Funcionales

1. Crear un ajuste manual (+10 unidades) para un producto en un almacén. → Ledger tiene 1 entrada con `balance_after=10`, balance muestra 10.
2. Crear un ajuste manual (+50 unidades) para el mismo producto. → Ledger tiene 2 entradas, balance muestra 60.
3. Transferir 20 unidades del almacén A al B. → Ledger tiene `transfer_out` en A y `transfer_in` en B, balances actualizados.
4. Consultar el histórico de movimientos de un producto. → Lista paginada en orden cronológico inverso.
5. Configurar mínimo=5 y máximo=50 para un producto+almacén. → Se guarda y recupera correctamente.
6. Intentar un ajuste que lleve el saldo a negativo. → Rechazado con error 422.
7. Ejecutar dos ajustes concurrentes sobre el mismo producto+almacén. → Los saldos finales son consistentes y el ledger conserva el orden transaccional correcto.

### 8.2 Integración

8. `npm run migrate:plugins` ejecuta migraciones de `plugins/stock/` sin errores.
9. `GET /stock/balance` devuelve vacío cuando no hay datos.
10. `POST /stock/adjust` con warehouse_id inválido → 422.
11. `POST /stock/adjust` con product_id inválido → 422.
12. Transferencia con `from_warehouse_id = to_warehouse_id` → 422.
13. Una operación repetida con la misma `idempotency_key` no duplica ledger ni balance.
14. No se puede insertar un movimiento con `product_id` o `warehouse_id` inexistente; la base rechaza la operación por FK.

### 8.3 Calidad

15. Se prueban emisión de `stock.balance.adjusted` y `stock.transfer.completed` en `event_log`.
16. Se prueba auditoría de ajustes y transferencias con `tenant_id`, `branch_id` cuando aplique, `actor_id` y `result`.
17. Se prueba filtrado por claim `warehouse_id` en lectura y escritura.
18. Se prueba retry/idempotencia ante conflicto serializable o reenvío del cliente.
19. Se prueban violaciones de FK para `product_id` y `warehouse_id` inexistentes.
20. `ruff check plugins/stock/` → 0 errores.
21. `pyright plugins/stock/` → 0 errores.
22. `pytest plugins/stock/` → todas las pruebas pasan.

---

## 9. Dependencias

Declaradas en `plugin.json`:

```json
{
    "id": "stock",
    "version": "0.1.0",
    "api_version": "1",
    "requires": ["logistics", "productos"],
    "backend_entrypoint": "backend.plugin:register",
    "frontend_entrypoint": "frontend/register.ts"
}
```

- Runtime de plugins.
- Kernel: auth JWT, multi-tenant, RBAC, auditoría, event bus.
- **Logistics plugin (`requires`)**: catálogo de almacenes en `lg_warehouses` (query directa, misma BD).
- **Productos plugin (`requires`)**: catálogo de productos en `prod_products` (query directa, misma BD).

No requiere CRM, ventas ni compras en el MVP.

---

## 10. Referencias

- ADR 0016: Plugin stock — decisión arquitectónica (sobrescribe ejemplos `inventory.stock.*` de ADR 0003 y `inventory.stock.adjusted` de ADR 0005)
- ADR 0015: Plugin productos (hereda `prod_stock_config`)
- ADR 0005: Event bus y auditoría
- ADR 0003: Modelo tenancy y permisos (claim `warehouse_id`)
- ADR 0006: Migración Legacy CSV Manifest
- `docs/database/modulo_stock/` — análisis completo del legacy (12 archivos)
- `docs/avances/productos.md` — confirma ownership de stock fuera de productos
- `docs/avances/logistics.md` — catálogo de almacenes en `lg_warehouses`
