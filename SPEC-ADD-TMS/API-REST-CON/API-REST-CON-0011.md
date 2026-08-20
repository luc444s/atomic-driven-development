# A.SPEC API-REST-CON-0011 — Endpoint GET /api/stock

## WHY
TMS/`stock` necesita el stock de productos del legacy. El legacy tiene
reporte de stock, pero su cache (`Producto.stock`, `VExistencias.stock`) es
**no confiable** (vimos valores negativos: -31, -1).

## WHAT
`GET /api/stock` retorna el stock por `producto + almacen` usando la misma
fórmula del reporte legacy **"rep stock productos"** (`PRODUCTO_MOSTRARsoloSTOCK`):

```sql
SELECT Almacen, SUM(d.StkIngreso - d.StkEgreso) AS stock
FROM DetalleMovimiento d
JOIN Movimiento m ON d.CodMovimiento = m.Cod_Movimiento
WHERE d.CodProducto = @p
  AND m.inventario = 1 AND m.Estado = 1 AND m.TipoAtencion = 1
GROUP BY Almacen
```

Es decir: suma de ingresos−egresos de `DetalleMovimiento` filtrada por los
movimientos con `inventario=1, Estado=1, TipoAtencion=1`.

## SCOPE
- Lectura de `vkardex` (o cálculo equivalente sobre `Movimiento`).
- Campos: `cod_producto, almacen, saldo` (numérico).

## OUT OF SCOPE
- Exponer `Producto.stock` o `VExistencias.stock` como fuente de verdad
  (cache no confiable).
- Autenticación (A.SPEC 0004).

## CONTRACT
- `200 application/json` con array de balances.
- Cada item: `cod_producto`, `almacen`, `stock`.
- El `stock` = `SUM(StkIngreso - StkEgreso)` con filtros
  `inventario=1, Estado=1, TipoAtencion=1` (idéntico a `PRODUCTO_MOSTRARsoloSTOCK`).
- Fuente de verdad = el reporte legacy, NO `Producto.stock` ni
  `VExistencias.stock` (cache no confiable) ni `vkardex` sin filtro.

## INVARIANTS
- Solo lectura.
- No expone el cache no confiable como fuente de verdad.

## VERIFICATION (TEST REAL, NO MOCK)
- Contra `ERP-SYSTUTOR.API` real → `GET /api/stock` retorna balances
  operacionales desde `vkardex` real.
- Un producto conocido aparece con su stock del reporte legacy, ej.
  `ABRAZADERAS` (cod_producto 1868) → **53** (según `PRODUCTO_MOSTRARsoloSTOCK`
  con filtros `inventario=1, Estado=1, TipoAtencion=1`).
- Nota de discrepancia: `vkardex` sin filtro da **88** y `VExistencias.stock`
  da **112** para el mismo producto; ambos son cache/no confiables. El
  contrato usa el reporte (53) como fuente de verdad; el test valida contra
  ese valor.
- El response NO usa `Producto.stock`/`VExistencias.stock`/`vkardex` sin
  filtro como stock.
- Prohibido mock: debe golpear la BD legacy real.

## ROLLBACK
- Quitar handler de la ruta.

## CHANGE SURFACE
```yaml
allowed:
  - ERP-SYSTUTOR.API/Program.vb
prohibited:
  - plugins/**
```

## BLAST RADIUS
```yaml
direct:
  - lectura vkardex / Movimiento
indirect:
  - stock plugin (al consumirse en 0012)
must_not_affect:
  - escritura legacy
  - ERP app
```
