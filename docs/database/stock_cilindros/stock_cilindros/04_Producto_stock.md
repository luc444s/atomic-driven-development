# Producto.stock — ¿Qué representa exactamente?

## Columnas relevantes de Producto

| Columna | Tipo | Default | Descripción |
|---|---|---|---|
| `stock` | **INT** (not null) | 0 | Stock actual del producto (cached) |
| `StockMin_Producto` | **FLOAT** (nullable) | NULL | Stock mínimo de seguridad |
| `Cod_Grupo` | **INT** (not null) | - | Grupo de producto |
| `Condicion` | **NVARCHAR(50)** | NULL | CILCLI, CILPROV, CILPRO, CILGAR, PRODUCTO |
| `Nro_Producto` | **NVARCHAR(20)** | NULL | Código de barra / serie del cilindro |

## ¿Es cache?

**Sí.** `Producto.stock` es un **cache** del stock actual. La fuente de verdad real es `DetalleMovimiento`, calculada por las funciones `fn_Stock*`.

## ¿Es derivado?

**Sí.** Se actualiza mediante `UPDATE_StockProducto` que recalcula desde `DetalleMovimiento`:

```sql
UPDATE Producto SET stock = (
    SELECT ISNULL(SUM(StkIngreso - StkEgreso), 0)
    FROM DetalleMovimiento
    WHERE CodProducto = Producto.Cod_Producto
)
```

## ¿Se usa en UI operativa?

**Sí, pero no de forma confiable.** Algunos forms pueden leer `Producto.stock` para mostrar stock rápido en grillas, pero:

- `fn_StockDisponible` — NO filtra por estado del movimiento (incluye anulados)
- `fn_StockReal` — filtra por `Estado = 1` (solo movimientos vigentes)
- `fn_StockFisico_Planificador` — filtra por `Estado=1 AND inventario=1 AND TipoAtencion=1` (versión más restrictiva, usada por logística)

## ¿La verdad real siempre sale de DetalleMovimiento?

**Sí, para cantidades.** Ninguna función `fn_Stock*` consulta `Producto.stock` ni `Stock_Actual`. Siempre calculan:

```sql
SELECT SUM(StkIngreso - StkEgreso) FROM DetalleMovimiento
```

## ¿Qué pasa con los envases?

Para un envase (ej: "Bombona 15KG" con Condicion = "CILPRO"):
- `Producto.stock` = número total de unidades de ese tipo de envase
- `fn_StockReal` devuelve el mismo número calculado desde `DetalleMovimiento`
- **Pero**: `fn_Stock*` no distingue entre cilindros llenos y vacíos — solo sabe "hay 50 unidades"
- El estado (lleno/vacío) solo se conoce consultando `ECilindroEstadoActual` o `Valmacen_Envases`

## Resumen

| Sistema | ¿Qué dice? | Confiable para |
|---|---|---|
| `Producto.stock` | "Hay 50 unds" | Cache rápido, puede estar desactualizado |
| `fn_StockReal` | "Hay 50 unds" | Stock real de movimientos vigentes |
| `fn_StockFisico_Planificador` | "Hay 45 unds" | Stock disponible (excluye planificado/no inventariable) |
| `sp_StockCilindros_PorProducto` | "20 llenos, 25 vacíos, 5 en tránsito" | Estados de cilindros |
| `ECilindroEstadoActual` | "BOM-001 = LLENO_EN_ALMACEN" | Estado individual por serie |
