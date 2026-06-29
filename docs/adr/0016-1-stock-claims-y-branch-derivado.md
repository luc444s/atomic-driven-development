# ADR 0016.1 — Stock: Claims por Warehouse y Branch Derivado de Almacén

## Estado

Aceptado

## Contexto

El plugin `stock` ya tiene una implementación funcional inicial basada en `ADR 0016` y `SPEC 0016`.

Ese primer corte ya resolvió:

- ledger de inventario;
- balance sincronizado;
- ajustes manuales;
- transferencias;
- configuración de mínimos/máximos;
- FKs reales a `prod_products` y `lg_warehouses`;
- auditoría y eventos;
- frontend inicial.

Sin embargo, la implementación mostró dos vacíos arquitectónicos que no deben resolverse localmente dentro del plugin:

1. el core actual soporta `tenant_id` y `branch_id`, pero todavía no soporta `warehouse_id` como claim contextual operativo;
2. `stock` hoy usa el `branch_id` del usuario autenticado en eventos, pero el branch correcto del evento debería derivarse del almacén afectado.

Esto genera un problema de frontera de responsabilidades:

- si `stock` resuelve seguridad por su cuenta, rompe el ownership del core sobre auth y permisos;
- si `stock` deriva branch desde lógica propia, duplica semántica del dominio `logistics`.

Por lo tanto, se necesita una decisión explícita para cerrar esa arquitectura sin introducir atajos locales permanentes.

## Decisión

### 1. El core sigue siendo dueño del alcance de seguridad

El core mantiene el ownership de:

- autenticación;
- `tenant_id`;
- `branch_id`;
- permisos RBAC;
- construcción de `TenantContext`.

Se extiende ese modelo para soportar `warehouse_id` como claim contextual oficial.

`stock` no implementará su propio sistema de claims ni resolverá autorizaciones contextuales por almacén de forma ad hoc.

### 2. `warehouse_id` se resuelve en el core, no en el JWT como lista cerrada

La autorización por almacén debe resolverse desde base de datos al construir o completar `TenantContext`.

No se adopta como solución principal un JWT que cargue la lista completa de almacenes permitidos.

Motivos:

- evita inflar el token;
- evita permisos obsoletos hasta el próximo login;
- mantiene la lógica de seguridad dentro del core;
- facilita cambios de alcance sin reemitir tokens.

### 3. `TenantContext` se amplía con alcance por almacén

El core debe poder exponer el conjunto de almacenes autorizados del usuario autenticado, o un helper equivalente para validar si un almacén concreto está permitido.

El plugin `stock` consumirá ese mecanismo en sus endpoints y servicios.

### 4. `logistics` sigue siendo dueño del catálogo de almacenes

El catálogo `lg_warehouses` sigue perteneciendo a `logistics`.

No se creará una tabla duplicada de almacenes dentro de `stock`.

### 5. El branch operativo de stock debe derivarse del almacén

Para eventos y auditoría operativa, el `branch_id` correcto no debe inferirse solo del usuario autenticado.

Debe poder resolverse desde el almacén afectado.

Por eso, `lg_warehouses` debe incorporar una relación explícita con `branches.id`, o un mecanismo equivalente formalmente documentado.

### 6. `stock` consume contexto; no redefine contexto

El modelo final queda así:

- el core resuelve identidad y alcance;
- `logistics` resuelve el catálogo de almacenes y su branch operativo;
- `productos` resuelve el catálogo maestro de productos;
- `stock` aplica reglas de inventario usando esos contratos.

## Arquitectura resultante

### Core

Responsable de:

- JWT;
- `tenant_id`;
- `branch_id`;
- permisos RBAC;
- claims contextuales;
- `TenantContext`.

### Logistics

Responsable de:

- `lg_warehouses`;
- relación almacén → sucursal cuando aplique.

### Productos

Responsable de:

- `prod_products`.

### Stock

Responsable de:

- `stk_ledger`;
- `stk_balance`;
- `stk_config`;
- reglas de ajuste;
- reglas de transferencia;
- auditoría y eventos del dominio stock.

No responsable de:

- claims;
- seguridad contextual;
- ownership de almacenes;
- ownership de productos.

## Reglas derivadas

1. Un endpoint de `stock` no debe decidir por sí mismo qué almacenes puede usar un usuario fuera del mecanismo del core.
2. Un evento de `stock` debe usar el branch del almacén afectado cuando esa relación exista.
3. La seguridad por almacén debe ser reutilizable por otros módulos futuros, no solo por `stock`.
4. No se debe modelar `warehouse_id` como permiso distinto; sigue siendo claim contextual, no reemplazo del permiso.

## Consecuencias

### Positivas

- la autorización por almacén queda centralizada en el core;
- `stock` no se convierte en dueño accidental de seguridad;
- la trazabilidad de eventos mejora al reflejar la sucursal operativa real del almacén;
- otros módulos podrán reutilizar `warehouse_id` sin duplicar arquitectura.

### Negativas

- se requiere trabajo adicional en kernel/auth/tenancy;
- `logistics` debe evolucionar su modelo de almacenes para incluir branch explícito;
- la implementación completa depende de cambios cruzados entre core y plugins.

### Riesgos

- si el soporte de claims contextuales se implementa de forma demasiado específica para `stock`, se degradará la reutilización futura;
- si `lg_warehouses` no formaliza su relación con sucursal, los eventos seguirán reflejando branch de usuario y no branch operativo;
- si parte del alcance vive en token y parte en DB sin contrato claro, aparecerán inconsistencias difíciles de auditar.

## No decisiones

Esta ADR no decide todavía:

- el esquema exacto de tablas para claims contextuales;
- si el claim vive a nivel usuario, rol o ambos;
- si `branch_id` en `lg_warehouses` será `NULL` permitido o `NOT NULL` desde la primera migración;
- la estrategia concreta de testing concurrente en PostgreSQL.

Esas definiciones se cierran en la implementación técnica y en `SPEC 0016.1`.

## Referencias

- `docs/adr/0016-stock-plugin.md`
- `docs/specs/core/0016-stock-plugin/index.md`
- `docs/specs/core/0016-1-stock-plugin-gap-closure.md`
- `docs/avances/stock.md`
- ADR 0003 — Modelo tenancy y permisos
- ADR 0005 — Event bus y auditoría
