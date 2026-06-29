# Extracción BD — Módulo Stock/Inventario SYSTUTOR Legacy

**Base de datos:** ACONCAGUA.Sys_GMS_ES
**Fecha extracción:** 2026-06-28

---

## Resumen de objetos identificados

| Tipo | Cantidad | Notas |
|------|----------|-------|
| Tablas principales | 2 | `Stock_Actual`, `kardex` (más `Producto` con columnas de stock) |
| Triggers | 0 | **Ningún trigger** en `Stock_Actual` ni `kardex` |
| Índices no clúster | 0 | **Ningún índice no clusterizado** — solo PK clúster |
| FK (Foreign Keys) | 0 | **Ninguna FK** en `Stock_Actual` ni `kardex` |
| CHECK constraints | 0 | **Ningún CHECK** en `Stock_Actual` ni `kardex` |
| Vistas | 4 | `CRstockCySMilton`, `kardex_final`, `kardex_final1`, `vkardex` |
| Funciones escalares | 4 | `fn_StockDisponible`, `fn_StockFisico_Planificador`, `fn_StockFisico_Planificador_Grupo`, `fn_StockReal` |
| Stored Procedures | 33 | SPs relacionados con stock/inventario/kardex |
| SQL Agent Jobs | 0 | Sin automatización programada detectada |

---

## Triggers

**No hay triggers** en ninguna tabla del módulo stock (`Stock_Actual`, `kardex`). Esto significa que:
- No hay auditoría automática de cambios en stock
- No hay sincronización automática entre `kardex` y `Stock_Actual`
- La integridad referencial se maneja exclusivamente en capa de aplicación (SPs)

---

## Índices

Solo existen los PK clúster:
- `PK_kardex` en `kardex.codigo`
- `PK_Stock_Actual` en `Stock_Actual(Cod_Grupo, IdAlmacen)`

**No hay índices no clusterizados** para optimizar búsquedas por producto, almacén o fecha.

---

## Foreign Keys

**Stock_Actual** no tiene FK a:
- `Producto` (Cod_Grupo debería referenciar Producto.Cod_Grupo)
- `Almacen` (IdAlmacen debería referenciar Almacen.IdAlmacen)

**kardex** no tiene FK a:
- `Producto` (codigo debería referenciar Producto.Cod_Producto)

**Riesgo:** Integridad referencial no garantizada a nivel BD. Posibles huérfanos.

---

## CHECK Constraints

**No hay CHECK constraints** en `Stock_Actual` ni `kardex`.

- `Stock_Actual.Stock` no tiene restricción de valor mínimo (podría ser negativo)
- `kardex.saldo` no tiene restricción de valor mínimo

---

## Funciones escalares

| Función | Propósito | Usa Stock_Actual? |
|---------|-----------|-------------------|
| `fn_StockDisponible` | Stock = SUM(StkIngreso - StkEgreso) de DetalleMovimiento | NO |
| `fn_StockFisico_Planificador` | Stock filtrado (Estado=1, inventario=1, TipoAtencion=1) | NO |
| `fn_StockFisico_Planificador_Grupo` | Stock por grupo de producto | NO |
| `fn_StockReal` | Stock = SUM(StkIngreso - StkEgreso) con Estado=1 | NO |

**Hallazgo crítico:** Ninguna función de stock consulta la tabla `Stock_Actual`. Todas calculan stock desde `DetalleMovimiento` + `Movimiento`. `Stock_Actual` parece ser una tabla SUMMARY/CACHE no utilizada por las funciones de consulta.

---

## Vistas

| Vista | Propósito |
|-------|-----------|
| `CRstockCySMilton` | Vista para reporte Crystal de stock |
| `kardex_final` | Vista del kardex |
| `kardex_final1` | Vista del kardex (variante) |
| `vkardex` | Vista del kardex |

---

## Stored Procedures

### SPs de Kardex (6)
- `mostrarprodkardex` — Búsqueda de productos para kardex
- `sp_kardex_Eliminar` — Elimina registros de kardex
- `sp_kardex_Insertar` — Inserta en kardex
- `sp_Kardex_listarxfechas` — Lista kardex por rango de fechas
- `sp_Kardex_listarxfechas1` — Lista kardex por rango (variante con razón social)
- `Producto_mostrarkARDEX` — Muestra kardex de producto
- `Producto_mostrarkARDEXCerveza` — Kardex específico para cerveza

### SPs de Inventario (8)
- `Producto_inventario` — Actualiza datos de inventario
- `Producto_INVENTARIO_Cerrar` — Cierra inventario de producto
- `PRODUCTO_MOSTRARinventario` — Lista inventario por almacén
- `PRODUCTO_MOSTRARinventariolinea` — Inventario filtrado por línea
- `PRODUCTO_MOSTRARinventarioNegativoMovimientos` — Productos con stock negativo
- `PRODUCTO_MOSTRARinventarioSUBlinea` — Inventario filtrado por sublínea
- `UPDATE_InventarioEstado` — Actualiza estado de inventario en comprobante

### SPs de Stock (10)
- `PRODUCTO_MOSTRARSTOCKALMACENES` — Stock por producto en todos los almacenes
- `PRODUCTO_MOSTRARSTOCKALMACENESXSUC` — Stock por producto + almacén específico
- `PRODUCTO_MOSTRARsoloSTOCK` — Stock simple
- `PRODUCTO_MOSTRARsoloSTOCKXSUC` — Stock simple por sucursal
- `PRODUCTO_MOSTRARstocks` — Stock por usuario/sucursal
- `PRODUCTO_MOSTRARstocks_proveedor` — Stock por proveedor
- `MOSTRARstocksxentregas` — Stock cruzado con entregas
- `MOSTRARstocksxsucxfechas` — Stock por sucursal y fechas
- `UPDATE_StockProducto` — Actualiza stock de producto
- `SHOW_ValidarStockProductoMovimiento` — Valida stock antes de movimiento (ventas)
- `SHOW_ValidarStockProductoMovimientoCOMPRA` — Valida stock antes de movimiento (compras)
- `usp_Producto_StockPlanificado` — Stock planificado

### SPs de Cilindros/Bombonas (2)
- `sp_StockBombonasDisponibles` — Bombonas disponibles en stock
- `sp_StockCilindros_PorProducto` — Cilindros en stock por producto

---

## Jobs

**No se detectaron jobs del SQL Agent** relacionados con stock/inventario.

---

## Bypasses identificados

1. **Sin FK**: Se pueden insertar registros en `Stock_Actual` con `Cod_Grupo` o `IdAlmacen` inexistentes.
2. **Sin triggers**: No hay registro automático de quién/cuándo modificó `Stock_Actual`.
3. **Stock_Actual no es usado por funciones**: Las funciones `fn_Stock*` calculan stock desde `DetalleMovimiento`, ignorando `Stock_Actual`.
4. **Sin restricción de stock negativo**: `Stock_Actual.Stock` puede ser negativo sin CHECK constraint.
