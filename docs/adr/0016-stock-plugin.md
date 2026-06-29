# ADR 0016 — Plugin stock: Ledger de Inventario

## Estado

Aceptado

## Contexto

SYSTUTOR OSS no tiene un módulo de stock. El legacy maneja inventario de forma fragmentada:

| Problema | Impacto |
|----------|---------|
| `Stock_Actual` es un cache sin FKs, sin triggers, sin CHECKs, y **ninguna función lo consulta** | Tabla huérfana, posiblemente desactualizada |
| El stock real se calcula desde `DetalleMovimiento` (SUM de `StkIngreso - StkEgreso`) vía 4 funciones redundantes | Misma lógica en 4 lugares, sin fuente de verdad única |
| `Producto.stock` es un cache redundante de `Stock_Actual.Stock` | Inconsistencia garantizada |
| `kardex` es temporal (SP `sp_kardex_Eliminar` borra todo sin filtro), sin FKs, sin multi-almacén | Historial no confiable |
| `FrmMovTrasladoAlmacen` (~4300 líneas) mezcla traslados, guías, recepción y preparación de carga | Monolito imposible de mantener |
| 0 FKs en tablas de stock | Datos huérfanos |

Los ADRs existentes ya definen la dirección:

- ADR 0003 definió originalmente `inventory.stock.read`, `inventory.stock.adjust` como ejemplos de permisos y estableció `warehouse_id` como claim. Este ADR 0016 sobreescribe los ejemplos de permisos de ADR 0003 adoptando `stock.*.*` (el módulo es `stock`, no `inventory`).
- ADR 0005 definió originalmente `inventory.stock.adjusted` como ejemplo de evento. Este ADR 0016 sobreescribe ese ejemplo adoptando `stock.balance.adjusted`.
- ADR 0015-46: *"Stock actual (stock cache, Stock_Actual) → Módulo Stock (futuro). Stock se computa del ledger."*
- ADR 0015-47: *"Stock mínimo/máximo por almacén → Módulo Stock (futuro)."*
- ADR 0015-65: *"prod_stock_config → módulo stock (futuro)".*

Además, `docs/avances/productos.md` sección 2.8 confirma: *"stock actual, stock mínimo y stock por almacén no se implementan en productos; ese ownership queda para el futuro módulo stock."*

**Nota:** Los ejemplos `inventory.stock.*` en ADR 0003 y ADR 0005 fueron escritos antes de que existiera un plugin real llamado `stock`. Este ADR actualiza la nomenclatura: el módulo es `stock`, el recurso es `balance`, no `inventory.stock`.

## Decisión

Se crea el plugin `stock` como ledger de inventario de SYSTUTOR OSS.

### Principios de diseño

**Ledger como fuente de verdad única:**
- Todo cambio de stock se registra como una entrada inmutable en `stk_ledger`.
- `stk_balance` es una tabla de balance sincronizada (se escribe en la misma transacción que el ledger, nunca se escribe directo).
- No existe una tabla `Stock_Actual` ni un cache redundante en `prod_products`.

**Almacenes externalizados:**
- El catálogo de almacenes vive en `plugins/logistics/` como `lg_warehouses`.
- Stock lee `lg_warehouses` con query directa a la misma base de datos (no vía import de servicio ni API HTTP).
- No se crea un catálogo duplicado de almacenes en stock.

**Auditable por diseño:**
- Cada entrada del ledger registra `created_by` y `created_at`.
- Las operaciones de ajuste y transferencia emiten eventos y registros de auditoría.

**Tabla de balance sincronizada para consultas:**
- `stk_balance` se actualiza en la misma transacción que el ledger.
- Garantiza consistencia inmediata: el balance siempre refleja el ledger.

**No se reimplementa el kardex contable:**
- El MVP no incluye valorización de inventario (costo promedio, FIFO, etc.).
- El kardex valorizado depende del módulo de contabilidad (futuro).

### Tablas

```
stk_ledger          → fuente de verdad (inmutable, append-only)
stk_balance         → snapshot por producto+almacén
stk_config          → mínimos y máximos por producto+almacén
```

Prefijo: `stk_`.

### Dependencia con logistics

Stock no duplica almacenes. Lee `lg_warehouses` con query SQL directa a la misma base de datos. No usa import de servicios de logistics ni API HTTP para evitar acoplamiento entre plugins (ADR 0005:259).

Stock declara en `plugin.json`:

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

`requires` es necesario porque stock no puede operar sin almacenes (`lg_warehouses`) ni productos (`prod_products`).

### Integración con productos

- `stk_ledger.product_id` → FK real a `prod_products.id`
- `stk_balance.product_id` → FK real a `prod_products.id`
- `stk_config.product_id` → FK real a `prod_products.id`
- Stock valida `product_id` con query directa a `prod_products` (misma BD), no vía API HTTP de productos.

### Integridad referencial

- `stk_ledger.warehouse_id` → FK real a `lg_warehouses.id`
- `stk_balance.warehouse_id` → FK real a `lg_warehouses.id`
- `stk_config.warehouse_id` → FK real a `lg_warehouses.id`
- Stock usa FKs reales porque no es un MVP y el costo de un acoplamiento explícito es menor que el riesgo de saldos huérfanos o referencias inválidas.
- `requires: ["logistics", "productos"]` y el orden de migraciones deben garantizar que las tablas referenciadas existan antes de crear las tablas `stk_*`.

### Tenancy y claims

- Todas las tablas incluyen `tenant_id` y se filtran por aplicación (ADR 0003).
- Se aplica el claim `warehouse_id` definido en ADR 0003:132 para restringir acceso a almacenes específicos según el rol del usuario.
- El claim `branch_id` (ADR 0003:131) se incluye en eventos cuando el warehouse esté asociado a una sucursal.
- La resolución de `branch_id` desde `warehouse_id` queda a cargo del módulo de logística (stock no duplica esa relación).

### Eventos

Formato `<module>.<resource>.<past_action>` conforme a ADR 0005.

```
stock.balance.adjusted    → ajuste manual de stock
stock.transfer.completed  → transferencia entre almacenes
```

Los eventos incluyen `tenant_id`, `warehouse_id`, y `branch_id` cuando el almacén esté asociado a una sucursal.

### Permisos

Formato `<module>.<resource>.<action>` conforme a ADR 0003.

```
stock.balance.read       — Ver saldos
stock.balance.adjust     — Realizar ajustes manuales
stock.transfer.create    — Crear transferencias entre almacenes
stock.config.read        — Ver configuraciones de mínimo/máximo
stock.config.manage      — Gestionar configuraciones de mínimo/máximo
```

Se aplica el claim `warehouse_id` para restringir qué almacenes puede ver/operar cada usuario.

## Consecuencias

**Positivas:**
- Fuente de verdad única para el stock (ledger inmutable).
- Sin cache huérfano tipo `Stock_Actual`.
- Balance siempre consistente con el ledger.
- Almacenes no duplicados (lee `lg_warehouses` directo).
- Integridad referencial real entre stock, productos y almacenes.
- Sin acoplamiento entre plugins (query directa, no import de servicios ni API HTTP).
- Preparado para integración event-driven con logistics y ventas en el futuro.
- Sigue el mismo patrón arquitectónico que `productos` y `crm`.

**Negativas:**
- Dependencia de logistics y productos (declarada en `requires`).
- Acoplamiento estructural explícito por FKs entre plugins.
- El balance inicial requiere poblar datos legacy (no hay datos todavía).
- Las consultas de stock en logistics/ventas requieren migración para apuntar a stock en vez de sus propios cálculos.

**Riesgos:**
- Si logistics renombra o elimina `lg_warehouses`, stock se ve afectado (mitigación: `requires` previene que logistics se deshabilite mientras stock dependa de él).
- La migración de datos legacy de stock requerirá mapear `DetalleMovimiento` → `stk_ledger`.
- La decisión de no incluir kardex valorizado puede presionar para implementarlo antes de lo previsto.

## Dependencias

- Runtime de plugins (existe y funciona).
- Kernel: auth JWT, multi-tenant, RBAC, auditoría, event bus.
- **Logistics plugin**: catálogo de almacenes en `lg_warehouses` (lectura directa, misma BD). Declarado en `requires`.
- **Productos plugin**: catálogo de productos en `prod_products` (lectura directa, misma BD). Declarado en `requires`.
- No requiere CRM, ventas ni compras en el MVP.

## Referencias

- SPEC 0016: `docs/specs/core/0016-stock-plugin/index.md`
- ADR 0015: Plugin productos (hereda `prod_stock_config`)
- ADR 0005: Event bus y auditoría (define `inventory.stock.adjusted`; ADR 0016 sobreescribe ese ejemplo)
- ADR 0003: Modelo tenancy y permisos (define `inventory.stock.*` y `warehouse_id` claim; ADR 0016 sobreescribe los ejemplos de permisos)
- `docs/database/modulo_stock/` — análisis completo del legacy (12 archivos)
- `docs/avances/productos.md` — confirma ownership de stock fuera de productos
- `docs/avances/logistics.md` — catálogo de almacenes en `lg_warehouses`
