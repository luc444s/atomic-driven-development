# Vistas y Funciones del Módulo Stock/Inventario

---

## FUNCIONES ESCALARES

### fn_StockDisponible

```sql
CREATE FUNCTION dbo.fn_StockDisponible
(
    @CodProducto INT,
    @IdAlmacen INT
)
RETURNS INT
AS
BEGIN
    DECLARE @Stock INT;
    SELECT @Stock = SUM(StkIngreso - StkEgreso)
    FROM DetalleMovimiento dm
    INNER JOIN Movimiento m ON dm.CodMovimiento = m.Cod_Movimiento
    WHERE dm.CodProducto = @CodProducto
      AND m.Almacen = @IdAlmacen;
    RETURN ISNULL(@Stock, 0);
END
```

**Propósito:** Calcula stock disponible como suma de ingresos - egresos desde DetalleMovimiento.

**Problemas:**
- Retorna `INT` — trunca decimales (pérdida de precisión en productos fraccionables como gases)
- No filtra por Estado del movimiento (incluye movimientos anulados)
- No filtra por TipoAtencion (incluye movimientos no reales)
- No usa `Stock_Actual` — calcula siempre desde detalle

**Usado por:** Reportes Crystal, Forms de consulta de stock

---

### fn_StockFisico_Planificador

```sql
CREATE FUNCTION dbo.fn_StockFisico_Planificador
(
    @CodProducto INT,
    @IdAlmacen   INT
)
RETURNS DECIMAL(18,3)
AS
BEGIN
    DECLARE @Stock DECIMAL(18,3);
    SELECT @Stock = ISNULL(SUM(dm.StkIngreso - dm.StkEgreso),0)
    FROM DetalleMovimiento dm
    INNER JOIN Movimiento m ON m.Cod_Movimiento = dm.CodMovimiento
    WHERE dm.CodProducto = @CodProducto
      AND m.Almacen = @IdAlmacen
      AND m.Estado = 1
      AND m.inventario = 1
      AND m.TipoAtencion = 1;
    RETURN @Stock;
END
```

**Propósito:** Stock físico disponible filtrado por movimientos válidos (Estado=1, inventario=1, TipoAtencion=1). Es la función oficial que usa el planificador logístico.

**Filtros aplicados:**
- `m.Estado = 1` — solo movimientos activos (no anulados)
- `m.inventario = 1` — solo movimientos que afectan inventario
- `m.TipoAtencion = 1` — solo movimientos reales

**Retorna:** `DECIMAL(18,3)` — precisión de 3 decimales, adecuado para productos gas.

**CRÍTICO para logística:** Esta función es la base del cálculo de stock disponible en `FrmPlanificarCarga` y `FrmPlanificarTraslado`.

---

### fn_StockFisico_Planificador_Grupo

```sql
CREATE FUNCTION dbo.fn_StockFisico_Planificador_Grupo
(
    @CodGrupo   INT,
    @IdAlmacen  INT
)
RETURNS DECIMAL(18,3)
AS
BEGIN
    DECLARE @Stock DECIMAL(18,3);
    SELECT @Stock = ISNULL(SUM(dm.StkIngreso - dm.StkEgreso), 0)
    FROM dbo.DetalleMovimiento dm
    INNER JOIN dbo.Producto p ON p.cod_producto = dm.CodProducto
    INNER JOIN dbo.Movimiento m ON m.Cod_Movimiento = dm.CodMovimiento
    WHERE p.Cod_Grupo = @CodGrupo
      AND m.Almacen = @IdAlmacen
      AND m.Estado = 1
      AND m.TipoAtencion = 1;
    RETURN @Stock;
END;
```

**Propósito:** Stock físico disponible agregado por GRUPO de producto (suma todos los productos del mismo grupo).

**Usado por:** Planificación logística cuando se planifica por grupo de producto.

**Diferencia con planificador individual:**
- No filtra por `m.inventario = 1` (incluye todos los que afectan inventario)
- Join con `Producto` para obtener el grupo

---

### fn_StockReal

```sql
CREATE FUNCTION dbo.fn_StockReal
(
    @CodProducto INT,
    @IdAlmacen   INT
)
RETURNS DECIMAL(18, 6)
AS
BEGIN
    DECLARE @resultado DECIMAL(18, 6);
    SELECT @resultado = ISNULL(SUM(dm.StkIngreso - dm.StkEgreso), 0)
    FROM DetalleMovimiento dm
    INNER JOIN Movimiento m ON dm.CodMovimiento = m.Cod_Movimiento
    WHERE dm.CodProducto = @CodProducto
      AND m.Almacen = @IdAlmacen
      AND m.Estado = 1;
    RETURN @resultado;
END;
```

**Propósito:** Stock real con máxima precisión (6 decimales). Similar a la planificadora pero con más precisión y sin filtrar `inventario` ni `TipoAtencion`.

**Precisión:** `DECIMAL(18,6)` — la más alta de las 4 funciones.

**Usado por:** Módulo de ventas, reportes de stock detallados.

---

## Comparativa de funciones de stock

| Función | Precisión | Filtro Estado | Filtro Inventario | Filtro TipoAtencion | Usa Stock_Actual? |
|---------|-----------|---------------|-------------------|---------------------|-------------------|
| fn_StockDisponible | INT | ❌ No | ❌ No | ❌ No | ❌ No |
| fn_StockFisico_Planificador | DECIMAL(18,3) | ✅ Sí (1) | ✅ Sí (1) | ✅ Sí (1) | ❌ No |
| fn_StockFisico_Planificador_Grupo | DECIMAL(18,3) | ✅ Sí (1) | ❌ No | ✅ Sí (1) | ❌ No |
| fn_StockReal | DECIMAL(18,6) | ✅ Sí (1) | ❌ No | ❌ No | ❌ No |

---

## VISTAS

### CRstockCySMilton

Vista utilizada por reporte Crystal `CRstockCySMilton` (stock por almacén).

### kardex_final

```sql
-- Vista: kardex_final
-- Propósito: Vista resumida del kardex
-- Tablas: kardex
```

### kardex_final1

```sql
-- Vista: kardex_final1
-- Propósito: Variante de kardex_final
-- Tablas: kardex
```

### vkardex

```sql
-- Vista: vkardex
-- Propósito: Vista general del kardex
-- Tablas: kardex
```

**Nota:** Los bodies completos de vistas deben extraerse con:
```sql
SELECT OBJECT_DEFINITION(OBJECT_ID('vkardex'))
```

---

## Dependencias con logística

Las funciones `fn_StockFisico_Planificador` y `fn_StockFisico_Planificador_Grupo` son CRÍTICAS para el módulo de logística. Son utilizadas por:

1. **FrmPlanificarCarga** — Planificación de carga de repartidores
2. **FrmPlanificarTraslado** — Planificación de traslados entre almacenes
3. **FrmPreparacionCarga** — Preparación de carga (verificación de stock disponible)
4. **usp_Producto_StockPlanificado** — SP de logística que calcula stock planificado

**Regla de negocio:** Ninguna función usa `Stock_Actual`. El stock siempre se calcula desde `DetalleMovimiento`. Esto significa que `Stock_Actual` podría estar desactualizado sin que las funciones lo reflejen.

**Bypass crítico:** Si se modifica `Stock_Actual` directamente (sin SP), las funciones `fn_Stock*` NO reflejarán el cambio porque no consultan esa tabla.
