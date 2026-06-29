# DDL Tablas — Módulo Stock/Inventario SYSTUTOR Legacy

---

## Stock_Actual

Tabla de resumen de stock por grupo de producto y almacén. Actúa como cache/summary de stock actual.

### Columnas

| Columna | Tipo | Nulo | Default | Descripción |
|---------|------|------|---------|-------------|
| Cod_Grupo | int | NO | - | Código de grupo de producto (PK compuesta) |
| IdAlmacen | int | NO | - | Código de almacén/sucursal (PK compuesta) |
| Stock | decimal(18,0) | NO | (0) | Cantidad de stock actual |
| FechaActualizacion | datetime | NO | (getdate()) | Última actualización |

### Restricciones

- **PK:** `PK_Stock_Actual` (Cod_Grupo, IdAlmacen) — clúster
- **FK:** **NINGUNA** — no hay FK a Producto.Cod_Grupo ni a Almacen.IdAlmacen
- **CHECK:** **NINGUNO** — Stock puede ser negativo
- **Trigger:** **NINGUNO** — sin auditoría de cambios

### Relaciones esperadas (deben existir pero NO están en BD)

| Columna | Debería apuntar a | Estado |
|---------|-------------------|--------|
| Cod_Grupo | Producto.Cod_Grupo | **NO EXISTE** |
| IdAlmacen | Almacen.IdAlmacen | **NO EXISTE** |

### Notas de diseño

- Almacena stock por **GRUPO** de producto, no por producto individual
- No tiene columna de producto individual (CodProducto)
- `Stock` es `decimal` sin escala definida (equivale a `decimal(18,0)` = entero)
- No hay columna de versión/concurrencia para optimistic locking

---

## kardex

Registro histórico de movimientos de inventario por producto (kardex valorizado).

### Columnas

| Columna | Tipo | Nulo | Default | Descripción |
|---------|------|------|---------|-------------|
| codigo | int | NO | - | ID único (PK) — identity? NO, se inserta manual |
| fecha | datetime | SÍ | NULL | Fecha del movimiento |
| factped | datetime | SÍ | NULL | Fecha de factura/pedido |
| proveedor | nvarchar(100) | SÍ | NULL | Nombre del proveedor |
| costo | money | SÍ | NULL | Costo unitario |
| ingreso | money | SÍ | NULL | Cantidad de ingreso |
| salida | money | SÍ | NULL | Cantidad de salida |
| saldo | money | SÍ | NULL | Saldo después del movimiento |
| lote | nvarchar(50) | SÍ | NULL | Número de lote |
| fechav | nvarchar(50) | SÍ | NULL | Fecha de vencimiento (texto) |
| insumo | nvarchar(100) | SÍ | NULL | Nombre del insumo/producto |
| desde | datetime | SÍ | NULL | Fecha inicio del período |
| hasta | datetime | SÍ | NULL | Fecha fin del período |
| AREA | nvarchar(50) | SÍ | NULL | Área/departamento |

### Restricciones

- **PK:** `PK_kardex` (codigo) — clúster
- **FK:** **NINGUNA** — codigo no tiene FK a Producto.Cod_Producto
- **CHECK:** **NINGUNO**
- **Trigger:** **NINGUNO**
- **Identity:** NO — `codigo` se inserta manualmente (desde `sp_kardex_Insertar` con OUTPUT)

### Relaciones esperadas (deben existir pero NO están en BD)

| Columna | Debería apuntar a | Estado |
|---------|-------------------|--------|
| codigo | Producto.Cod_Producto | **NO EXISTE** |
| insumo | Producto.Desc_Producto | **NO EXISTE** (campo textual) |

### Notas de diseño

- `costo`, `ingreso`, `salida`, `saldo` son de tipo `money` — esto es inusual, normalmente deberían ser `decimal`
- `fechav` es `nvarchar` en lugar de `date` — permite datos inválidos
- Sin columna de almacén — no permite kardex multi-almacén
- Sin columna de tipo de movimiento — no se puede diferenciar ingreso/salida por tipo
- Sin columna de referencia a documento — no hay trazabilidad a factura/guía
- Sin columna de usuario que registró
- El kardex parece ser **temporal**: SP `sp_kardex_Eliminar` elimina **todos** los registros (sin parámetros)

---

## Producto (columnas de stock)

La tabla `Producto` contiene las siguientes columnas relacionadas con stock:

| Columna | Tipo | Nulo | Default | Descripción |
|---------|------|------|---------|-------------|
| StockMin_Producto | float | SÍ | NULL | Stock mínimo de seguridad |
| stock | int | NO | (0) | Stock actual (cached) |
| Cod_Grupo | int | SÍ | NULL | Grupo de producto (FK lógica a Stock_Actual) |

### Relaciones

- `Cod_Grupo` se relaciona lógicamente con `Stock_Actual(Cod_Grupo)` — sin FK
- `stock` en Producto es un cache redundante de `Stock_Actual.Stock`

---

## Tablas relacionadas de otros módulos

### DetalleMovimiento (módulo Ventas/Compras)

Columnas relevantes para stock:
- `CodProducto` — producto del movimiento
- `StkIngreso` — cantidad que ingresa a stock
- `StkEgreso` — cantidad que egresa de stock
- `CodMovimiento` — FK a Movimiento
- `Pcompra` — precio de compra (para valorización de inventario)

Relación: **TODAS las funciones de stock** (`fn_Stock*`) consultan `DetalleMovimiento` como fuente primaria de verdad para el stock.

### Movimiento (módulo Ventas/Compras/Logística)

Columnas relevantes para stock:
- `Cod_Movimiento` — PK
- `Almacen` — almacén del movimiento
- `Estado` — 1=Activo, 2=Anulado (filtro en funciones de stock)
- `TipoAtencion` — 1=Real (filtro en función planificador)
- `inventario` — 1=afecta inventario (filtro en función planificador)

### ECilindroEstadoActual (módulo Logística — ver modulo_logistica/01_ddl_tablas.md)

- `EstadoActual` — estado logístico del cilindro (LLENO_EN_ALMACEN, VACIO_EN_ALMACEN, etc.)
- Dependencia: `sp_StockCilindros_PorProducto` cruza stock de productos con estado de cilindros
