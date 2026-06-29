# SPEC 0016.1 — Stock Plugin: Cierre de Gaps de Producción

## Estado

Propuesta

## Contexto

La `SPEC 0016` ya permitió implementar un primer corte funcional del plugin `stock`.

Ese corte ya cubre:

- ledger de inventario;
- tabla de balance sincronizada;
- ajustes manuales;
- transferencias;
- configuración de mínimos/máximos;
- FKs reales hacia `prod_products` y `lg_warehouses`;
- auditoría y eventos;
- frontend inicial;
- prueba de integración principal.

Sin embargo, durante la implementación real aparecieron gaps que no pertenecen únicamente al plugin `stock`, sino al ecosistema alrededor de él:

1. el core actual sí soporta `tenant_id` y `branch_id`, pero no soporta claims reales por `warehouse_id`;
2. `lg_warehouses` no modela `branch_id`, por lo que el branch del almacén no puede resolverse correctamente;
3. la concurrencia quedó implementada en servicio, pero falta validación específica en PostgreSQL real;
4. la UX del frontend de stock quedó funcional, pero no cerrada al nivel operativo final.

Esta spec complementa a la `0016`, no la reemplaza.

---

## Objetivo

Cerrar los gaps de producción detectados después de la primera implementación de `stock`, para que el módulo cumpla completamente su contrato operativo y de seguridad.

---

## Arquitectura objetivo

La arquitectura final del dominio queda separada así:

### Core

El core sigue siendo dueño de:

- autenticación;
- `tenant_id`;
- `branch_id`;
- permisos RBAC;
- construcción de `TenantContext`.

El cambio nuevo en esta spec es extender ese modelo para soportar `warehouse_id` como claim contextual operativo.

### Logistics

`logistics` sigue siendo dueño del catálogo de almacenes:

- `lg_warehouses`

Y debe evolucionar para resolver correctamente la sucursal operativa del almacén cuando aplique.

### Productos

`productos` sigue siendo dueño del catálogo maestro:

- `prod_products`

### Stock

`stock` sigue siendo dueño de:

- `stk_ledger`;
- `stk_balance`;
- `stk_config`;
- reglas de ajuste;
- reglas de transferencia;
- auditoría y eventos del dominio stock.

`stock` no es dueño de:

- claims;
- seguridad contextual;
- catálogo de almacenes;
- catálogo de productos.

### Regla de arquitectura

La seguridad contextual no se implementa dentro de `stock`.

La regla es:

- el core resuelve alcance;
- `stock` consume alcance.

No se debe implementar:

- un sistema propio de claims dentro de `stock`;
- tablas de seguridad específicas de `stock` para almacenes permitidos;
- duplicación del catálogo de almacenes o del catálogo de productos.

---

## Flujo de autorización objetivo

1. el usuario se autentica;
2. el core valida JWT con `tenant_id` y `branch_id`;
3. el core construye `TenantContext`;
4. el core resuelve el alcance adicional por `warehouse_id`;
5. `stock` usa ese contexto para validar lecturas y escrituras.

Eso deja el modelo así:

- `tenant_id` = aislamiento base;
- `branch_id` = contexto organizacional;
- `warehouse_id` = alcance operativo fino.

---

## Alcance

### Incluye

1. soporte real de claims `warehouse_id` en el core de auth/tenancy;
2. propagación de `warehouse_id` en contexto autenticado cuando aplique;
3. modelado de `branch_id` en `lg_warehouses` o mecanismo equivalente explícito;
4. emisión de eventos de stock con `branch_id` derivado del almacén cuando corresponda;
5. pruebas de concurrencia real sobre PostgreSQL para ajustes y transferencias;
6. endurecimiento UX del frontend de stock.

### No incluye

1. kardex valorizado;
2. integración automática con ventas o logistics vía dual-write;
3. conteo físico cíclico;
4. RLS de PostgreSQL;
5. rediseño completo del kernel de permisos.

---

## 1. Gap A — Claims por `warehouse_id`

### Problema actual

ADR 0003 define claims contextuales como:

- `tenant_id`
- `branch_id`
- `warehouse_id`

Pero el core actual ya materializa correctamente en token y `TenantContext`:

- `tenant_id`
- `branch_id`

Lo que no existe aún es:

- claim persistido por almacén para usuario/rol;
- carga de claims de almacén en autenticación;
- filtro reutilizable en endpoints/plugins basado en `warehouse_id`.

### Resultado esperado

El sistema debe poder restringir operaciones a un subconjunto explícito de almacenes por usuario.

El ownership de ese alcance vive en el core, no en `stock`.

### Requisitos

1. El core debe introducir una estructura persistente para claims contextuales por usuario o rol.
2. Debe existir soporte mínimo para `warehouse_id` como claim resoluble.
3. El token no necesita incluir la lista completa de almacenes si eso complica demasiado el payload; puede resolverse en DB por request o por `TenantContext`.
4. `TenantContext` debe exponer los almacenes permitidos del usuario autenticado cuando existan.
5. Debe existir helper reutilizable para validar acceso a un almacén concreto.

### Decisión recomendada

La resolución de `warehouse_id` debe hacerse desde base de datos al construir o completar `TenantContext`, no embebiendo toda la lista de almacenes en el JWT.

Motivos:

- evita inflar el token;
- evita permisos obsoletos hasta el próximo login;
- mantiene la lógica de seguridad dentro del core y no en el token.

### Efecto en `stock`

Los endpoints de `stock` deben:

1. rechazar lectura de balances de almacenes fuera del claim;
2. rechazar ajustes sobre almacenes fuera del claim;
3. rechazar transferencias cuando el origen o destino no esté autorizado;
4. auditar los rechazos relevantes.

---

## 2. Gap B — `branch_id` por almacén

### Problema actual

La implementación actual de `stock` emite eventos usando el `branch_id` del contexto autenticado.

Eso no garantiza que el evento refleje correctamente la sucursal del almacén afectado.

### Resultado esperado

Cada almacén debe poder asociarse explícitamente a una sucursal cuando el dominio lo requiera.

### Requisitos

1. `lg_warehouses` debe incorporar `branch_id` FK a `branches.id`, o definirse otra relación explícita equivalente.
2. El catálogo y CRUD de almacenes deben exponer ese campo.
3. `stock` debe resolver `branch_id` desde el almacén afectado, no desde el usuario autenticado, para los eventos de dominio.
4. Si una operación involucra dos almacenes de distintas sucursales, el payload del evento debe modelarlo explícitamente.

### Efecto en la arquitectura

Esto mantiene la trazabilidad correcta:

- el actor viene del core autenticado;
- la sucursal operativa viene del almacén;
- el plugin `stock` no inventa esa relación ni la duplica.

### Payload esperado para transferencia

```json
{
  "product_id": "uuid",
  "from_warehouse_id": "uuid",
  "from_branch_id": "uuid",
  "to_warehouse_id": "uuid",
  "to_branch_id": "uuid",
  "quantity": 20.0,
  "reference_type": "transfer",
  "reference_id": "uuid"
}
```

---

## 3. Gap C — Concurrencia real en PostgreSQL

### Problema actual

La lógica del plugin ya implementa:

- `SELECT ... FOR UPDATE`;
- orden estable de locking;
- idempotencia.

Pero la validación automatizada actual se ejecutó sobre SQLite, no sobre PostgreSQL real.

### Resultado esperado

La semántica de concurrencia debe validarse sobre el motor objetivo del proyecto.

### Requisitos

1. Deben existir pruebas de integración sobre PostgreSQL real para:
   - dos ajustes concurrentes sobre el mismo producto+almacén;
   - dos transferencias concurrentes sobre el mismo origen;
   - reintentos con la misma `idempotency_key`;
   - conflictos serializables o deadlocks controlados.
2. La prueba debe verificar:
   - saldo final correcto;
   - cantidad correcta de filas en ledger;
   - ausencia de doble aplicación;
   - consistencia entre `stk_ledger` y `stk_balance`.

### Criterio mínimo

Si la infraestructura de tests por defecto sigue en SQLite, se debe agregar una vía explícita de test complementaria para PostgreSQL y documentarla.

---

## 4. Gap D — Cierre UX del frontend

### Problema actual

El frontend actual de `stock` ya es usable, pero todavía es un primer corte operativo.

### Resultado esperado

La UI debe permitir trabajo diario con menor fricción.

### Requisitos

1. filtros más claros por producto, almacén y estado bajo mínimo;
2. mejor presentación del ledger con labels legibles de operación;
3. navegación más rápida desde balance hacia ajuste/transferencia/config;
4. feedback visual más explícito para alertas de mínimo;
5. control más claro de errores de validación en formularios.

### No objetivo

No se requiere rediseño visual completo del shell ni nuevo design system.

---

## 5. Criterios de aceptación

1. Un usuario con claim limitado a almacén A no puede leer ni operar stock del almacén B.
2. Un ajuste exitoso emite evento con `branch_id` derivado del almacén cuando exista relación explícita.
3. Una transferencia entre almacenes de distintas sucursales registra ambos branches en el payload.
4. Dos ajustes concurrentes sobre PostgreSQL mantienen saldo final correcto.
5. Una transferencia concurrente no duplica ni corrompe `stk_balance`.
6. La misma `idempotency_key` no duplica el movimiento aunque el cliente reintente.
7. El frontend muestra claramente balances bajo mínimo y permite abrir acciones desde la misma grilla.
8. `ruff check`, `pyright` y `pytest` siguen pasando después del cierre.

---

## 6. Dependencias

- ADR 0003 — modelo de tenancy y permisos;
- ADR 0005 — event bus y auditoría;
- ADR 0016 — decisión arquitectónica del plugin stock;
- SPEC 0016 — implementación base del plugin stock;
- plugin `logistics` para evolucionar `lg_warehouses`;
- kernel auth/tenancy para extender soporte de claims contextuales.

---

## 7. Referencias

- `docs/specs/core/0016-stock-plugin/index.md`
- `docs/adr/0016-stock-plugin.md`
- `docs/avances/stock.md`
