# DAL CProducto.vb — Métodos de Stock

**Archivo:** `Libreria_GMS PRO_2.0/CAtencion/CProducto.vb`
**Total líneas:** 2,607
**Clase:** `CProducto`

---

## Métodos de Stock/Inventario

### 1. Insertarkardex (línea 31)

```vb.net
Public Function Insertarkardex(ByRef codigo As Integer, ByVal fecha As Date, 
    ByVal factped As String, ByVal proveedor As String, ByVal costo As Double, 
    ByVal ingreso As Double, ByVal salida As Double, ByVal saldo As Double, 
    ByVal lote As String, ByVal fechav As String, ByVal insumo As String, 
    ByVal desde As Date, ByVal hasta As Date, ByVal AREA As String) As Integer
```

**SP:** `sp_kardex_Insertar`
**Transacción:** Serializable
**Retorna:** ID insertado (0 si error)
**Riesgo:** `factped` es `nvarchar(200)` — no se valida formato de fecha

### 2. Eliminarkardex (línea 99)

```vb.net
Public Function Eliminarkardex() As Boolean
```

**SP:** `sp_kardex_Eliminar`
**Transacción:** Sí
**Retorna:** True/False
**RIESGO CRÍTICO:** Elimina **TODO** el kardex. No se puede deshacer.

### 3. BuscarKardex (línea 122)

```vb.net
Public Function BuscarKardex(ByVal codigo As Integer, ByVal FECHAI As Date, 
    ByVal FECHAF As Date, ByVal almacen As Integer) As SqlDataReader
```

**SP:** `sp_Kardex_listarxfechas`
**Parámetros:** código producto, fecha inicio, fecha fin, almacén
**Transacción:** No (solo lectura)
**Retorna:** SqlDataReader

### 4. BuscarKARDEX01 (línea 157)

```vb.net
Public Function BuscarKARDEX01(ByVal codigo As Integer, ByVal FECHAI As Date, 
    ByVal FECHAF As Date, ByVal Cod_RazonS As Integer) As SqlDataReader
```

**SP:** `sp_Kardex_listarxfechas1`
**Diferencia:** Usa `Cod_RazonS` en lugar de almacén

### 5. BuscarProductoxkardex (línea 180)

```vb.net
Public Function BuscarProductoxkardex(ByVal Desc_Producto As String) As SqlDataReader
```

**SP:** `mostrarprodkardex`
**Propósito:** Buscar productos para seleccionar en kardex

### 6. Inventario (línea 1582) [renombrado a Producto_inventario]

```vb.net
Public Function Inventario(ByVal Nro_Producto As String, ByVal Desc_Producto As String, 
    ByVal SOTCK As Integer, ByVal pRECIO_INV As String, ByVal COSTO_INV As String) As Boolean
```

**SP:** `Producto_inventario`
**Transacción:** Sí
**Propósito:** Actualizar producto (inventario individual)
**Riesgo:** Parámetros `pRECIO_INV` y `COSTO_INV` son String pero se envían como Money

### 7. PRODUCTO_INVENTARIO_COSTOS_ (línea 1630)

```vb.net
Public Function PRODUCTO_INVENTARIO_COSTOS_(ByVal CodProducto As Integer, 
    ByVal Costo_Producto As Double, ... 13 parámetros) As Boolean
```

**SP:** `Producto_INVENTARIO_COSTOS`
**Transacción:** Sí
**Propósito:** Actualización masiva de costos y precios

### 8. PRODUCTO_INVENTARIO_Cerrar (línea 1674)

```vb.net
Public Function PRODUCTO_INVENTARIO_Cerrar(ByVal CodProducto As Integer, 
    ByVal stock As Double, ByVal pRECIO_INV As Double, ByVal COSTO_INV As Double) As Boolean
```

**SP:** `Producto_INVENTARIO_Cerrar`
**Transacción:** Sí
**CRÍTICO:** Este SP actualiza el stock final del producto al cerrar inventario. Si `stock=0`, pone el stock a cero aunque el producto tenga movimientos posteriores.

### 9. Mostrar_cantidades (línea 1853)

```vb.net
Public Function Mostrar_cantidades(ByVal name As Integer, ByVal sucu As Integer) As SqlDataReader
```

**SP:** `PRODUCTO_MOSTRARstocks`
**Propósito:** Stock por usuario y sucursal (faltantes)

### 10. Mostrar_faltantesprov (línea 1986)

```vb.net
Public Function Mostrar_faltantesprov(ByVal prov As Integer, ByVal sucu As Integer) As SqlDataReader
```

**SP:** `PRODUCTO_MOSTRARstocks_proveedor`
**Propósito:** Productos faltantes por proveedor

### 11. UPDATE_InventarioEstado (línea 2074)

```vb.net
Public Function UPDATE_InventarioEstado(ByVal CodComprobante As Integer, 
    ByVal Estado As Integer) As Boolean
```

**SP:** `UPDATE_InventarioEstado`
**Transacción:** Sí
**Propósito:** Cambiar estado del comprobante de inventario

### 12. SHOW_ValidarStockProductoMovimiento (línea 2099)

```vb.net
Public Function SHOW_ValidarStockProductoMovimiento(ByVal codMovimiento As Integer) As DataTable
```

**SP:** `SHOW_ValidarStockProductoMovimiento`
**Retorna:** DataTable (no DataReader como los demás)
**Propósito:** Validar stock disponible para un movimiento (ventas)

### 13. SHOW_ValidarStockProductoMovimientoCOMPRA (línea 2119)

```vb.net
Public Function SHOW_ValidarStockProductoMovimientoCOMPRA(ByVal codMovimiento As Integer) As DataTable
```

**SP:** `SHOW_ValidarStockProductoMovimientoCOMPRA`
**Retorna:** DataTable
**Propósito:** Validar stock para un movimiento de compra

### 14. UPDATE_StockProducto (línea 2140)

```vb.net
Public Function UPDATE_StockProducto(ByVal Tipoingreso As Integer, 
    ByVal CodProducto As Integer, ByVal cantidad As Integer, 
    ByVal codMovimiento As Integer) As Boolean
```

**SP:** `UPDATE_StockProducto`
**Transacción:** Sí
**Propósito:** Actualizar stock después de un movimiento

### 15. Mostrarstocksxfecha (línea 1010)

```vb.net
Public Function Mostrarstocksxfecha(ByVal CodProducto As Integer, 
    ByVal CodALMACEN As Integer, ByVal FechaI As Date, ByVal FechaF As Date) As SqlDataReader
```

**SP:** `MOSTRARstocksxsucxfechas`

### 16. Mostrarstocksxentrega (línea 1033)

```vb.net
Public Function Mostrarstocksxentrega(ByVal CodProducto As Integer, 
    ByVal CodALMACEN As Integer, ByVal FechaI As Date, ByVal FechaF As Date) As SqlDataReader
```

**SP:** `MOSTRARstocksxentregas`

### 17. MostrarkARDEX (línea 1403)

```vb.net
Public Function MostrarkARDEX(ByVal codproducto As Integer, ByVal ALMACEN As Integer, 
    ByVal Fecha1 As Date, ByVal Fecha2 As Date) As SqlDataReader
```

**SP:** `Producto_mostrarkARDEX`

---

## Patrón de conexión recurrente en CProducto

Todos los métodos siguen el mismo patrón:
1. `Conectar()` — abre conexión desde cadena global
2. Crear `SqlCommand`
3. Opcional: crear `SqlTransaction`
4. Ejecutar
5. Commit o Rollback
6. `objcn.Close()` en Finally

**Problema común:** En métodos que retornan `SqlDataReader`, `Conectar()` abre la conexión y `CommandBehavior.CloseConnection` la cierra automáticamente al cerrar el DataReader. Pero en algunos métodos NO usan `CloseConnection` — la conexión queda abierta hasta que se llame manualmente `DesConnectar()`.

---

## Métodos con consultas inline (riesgo SQL injection)

**No se encontraron consultas SQL inline** en CProducto.vb. Todos los métodos usan SPs parametrizados. Sin embargo:

- `Trim()` se aplica a todos los parámetros, lo cual es correcto
- `SqlDbType.NVarChar` se usa con tamaño fijo — buena práctica
- No hay concatenación de strings SQL

**Riesgo medio:** El parámetro `@Nro_cja` en `InsertarProducto` y `ModificarProducto` es `SqlDbType.NVarChar` con tamaño 4000 — campo muy grande que podría usarse para inyección si el SP no lo valida.

---

## Métodos con Rollback comentado

En `ModificarComprasSerie_Insertar` (línea 2212-2213):
```vb.net
Catch ex As Exception
    'objTrans.Rollback()  ← COMENTADO
    RaiseEvent OnError(ex.Message)
```

**BUG:** El Rollback está comentado. Si hay error, la transacción queda abierta hasta que se cierre la conexión o haga timeout.

---

## Métodos de stock en CMovimiento.vb

**Archivo:** `Libreria_GMS PRO_2.0/CAtencion/CMovimiento.vb` (3628 líneas)

### Métodos de stock identificados

| Método (línea) | SP | Propósito |
|----------------|-----|-----------|
| MOSTRARSTOCKALMACENES (1269) | `PRODUCTO_MOSTRARSTOCKALMACENES` | Stock por producto en todos los almacenes |
| MOSTRARinventario (1347) | `PRODUCTO_MOSTRARinventario` | Lista para inventario |
| MOSTRARinventarioxSUBlinea (1368) | `PRODUCTO_MOSTRARinventarioSUBlinea` | Inventario por sublínea |
| MOSTRARinventarioxlinea (1390) | `PRODUCTO_MOSTRARinventariolinea` | Inventario por línea |
| MOSTRARSTOCKALMACENESXSUC (1412) | `PRODUCTO_MOSTRARSTOCKALMACENESXSUC` | Stock por producto + almacén |
| PRODUCTO_MOSTRAR_soloSTOCKXSUC (1434) | `PRODUCTO_MOSTRARsoloSTOCKXSUC` | Stock simple por sucursal |
| MOSTRARinventarioNegativo_Mov (3289) | `PRODUCTO_MOSTRARinventarioNegativoMovimientos` | Stock negativo |
| crearreporte (2156) | `crearreporte` | Escribe datos para reporte Crystal en tabla temporal |
| Eliminarreporte (2203) | `Eliminarreporte` | Limpia tabla temporal de reporte |

---

## Métodos de stock en CDetalleMovimiento.vb

No se encontraron métodos específicos de stock en CDetalleMovimiento.vb. Los métodos de detalle (`InsertarDetalleMovimiento`) son usados por stock para registrar diferencias de inventario como movimientos.
