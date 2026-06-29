# Forms del Módulo Stock/Inventario — Análisis Completo

---

## 1. FrmInventario.vb (858 líneas + 85KB Designer)

### Propósito
Formulario principal de inventario físico. Permite:
- Buscar productos por código de barra
- Modificar productos (costo, precio, stock)
- Cargar listado de inventario por almacén
- Cargar inventario por línea/sublínea
- Ajustar stock (diferencias de inventario)
- Ver productos con stock negativo

### Objetos DAL declarados

| Variable | Clase | Propósito |
|----------|-------|-----------|
| obj | CProducto | Operaciones de producto |
| objc | CComprobante | Comprobantes |
| objmo | CMovimiento | Movimientos (inventario) |
| objSc | CSubcategoria | Subcategorías |
| objl | CLinea | Líneas |
| objI | CProducto | Búsqueda de productos |
| objd | CDetalleMovimiento | Detalle de movimientos |
| objsl | CsubLinea | Sublíneas |
| objg | CSucursal | Sucursales/almacenes |
| objP | CPaciente | Personas (clientes/proveedores) |

### Mapeo de eventos

| Evento/Control | Acción | Método DAL | SP | Tabla afectada |
|----------------|--------|------------|-----|----------------|
| `txtCodbarra_KeyPress` (Enter) | Buscar producto por código de barra | `obj.BuscarProductoxCODEBARR()` | `Producto_BuscarxNomxCODEBARR` | Producto |
| `Button1_Click` | Modificar producto (inventario) | `obj.Inventario()` | `Producto_inventario` | Producto |
| `Button6_Click` | Procesar diferencias de inventario (crear movimiento + comprobante + detalle + cerrar) | `objmo.Insertarmovimiento()`, `objc.InsertarComprobante()`, `objc.crearcomprobantepedido()`, `objd.InsertarDetalleMovimiento()`, `obj.PRODUCTO_INVENTARIO_Cerrar()` | Múltiples | Movimiento, Comprobante, DetalleMovimiento, Producto |
| `Button7_Click` | Cargar listado de inventario del almacén actual | `objmo.MOSTRARinventario()` | `PRODUCTO_MOSTRARinventario` | (lectura) |
| `Button2_Click` | Cargar inventario por línea o sublínea | `objmo.MOSTRARinventarioxlinea()`, `objmo.MOSTRARinventarioxSUBlinea()` | `PRODUCTO_MOSTRARinventariolinea`, `PRODUCTO_MOSTRARinventarioSUBlinea` | (lectura) |
| `Button4_Click` | Mostrar productos con stock negativo | `objmo.MOSTRARinventarioNegativo_Mov()` | `PRODUCTO_MOSTRARinventarioNegativoMovimientos` | (lectura) |
| `Button9_Click` | Procesar ajuste de stock (crea ingreso/egreso) | `objP.BuscarClientProvxnom()`, `objmo.Insertarmovimiento()`, `objc.InsertarComprobante()`, `objd.InsertarDetalleMovimiento()`, `obj.PRODUCTO_INVENTARIO_Cerrar()` | Múltiples | Movimiento, Comprobante, DetalleMovimiento, Producto |
| `PictureBox11_Click` | Ajustar stock manual (diferencia en ListView) | Solo UI | - | - |
| `CBAna_TextChanged` | Buscar productos por nombre (autocomplete) | `objI.BuscarProdxTipo()` | `Producto_BuscarxTipo` | (lectura) |
| `DataGridView3_DoubleClick` | Seleccionar producto de búsqueda | `objI.BuscarProducto()` | `Producto_Buscar` | (lectura) |

### Mapeo de campos a BD

| Control en Form | Columna BD | Tabla |
|-----------------|------------|-------|
| txtCodbarra | Nro_Producto | Producto |
| TxtCodigo | Cod_Producto | Producto |
| TxtDescripcion | Desc_Producto | Producto |
| NUDCosto | Costo_Producto | Producto |
| NUDPrecio | Precio_Producto | Producto |
| nudstock | stock | Producto |
| ComboBox1 (subcategoría) | Desc_rubro | Subcategoria |
| CBlinea | Desc_Linea | Linea |
| cbsublinea | Desc_SubLinea | SubLinea |
| ListView1 (SubItem 0) | Cod_Producto | Producto |
| ListView1 (SubItem 2) | STOCK_sistema | Producto.stock |
| ListView1 (SubItem 3) | stock (físico) | (ingresado por usuario) |
| ListView1 (SubItem 4) | Diferencia | Calculado (STOCK_sistema - stock) |
| ListView1 (SubItem 5) | Costo_Producto | Producto |

### Flujo crítico: Ajuste de inventario (Button9_Click)

1. Determina si es ingreso o egreso comparando StockAnterior vs StockNuevo
2. Busca persona por concepto fijo "Egreso x cuadre stock" o "Ingreso x cuadre stock"
3. Crea movimiento (TipoMovimiento=6 para egreso, 1 para ingreso)
4. Crea comprobante
5. Para cada producto en ListView1:
   - Si diferencia != 0: crea detalle de movimiento con la diferencia
   - Llama a `PRODUCTO_INVENTARIO_Cerrar` para actualizar stock

### Bugs encontrados

1. **BUG CRÍTICO (línea 492-493):** `StockAnterior` y `StockNuevo` se inicializan ANTES del loop, con `i=0`. Solo compara el primer producto. Todos los demás productos se procesan con la misma decisión (ingreso/egreso) del primer producto.

2. **BUG (línea 546):** `total = precio * pcompra` — `precio` no está inicializado en este contexto. La variable `precio` se declaró pero nunca se asignó (las líneas que lo asignaban están comentadas). Total será 0 o error.

3. **Sin validación:** No se valida que el stock ingresado por el usuario sea positivo.

4. **Hardcoding de conceptos:** "Egreso x cuadre stock" e "Ingreso x cuadre stock" son búsquedas textuales — si alguien modifica la persona en BD, se rompe.

5. **Conexiones no cerradas en excepciones:** En varios lugares no hay `Finally` que cierre conexiones.

---

## 2. FrmMostrarSotck.vb (421 líneas + 18KB Designer)

### Propósito
Consulta de stock por almacén y sucursal, con filtros por línea/sublínea. Exporta a Excel y genera reporte Crystal.

### Eventos principales

| Evento | Acción | SP | 
|--------|--------|-----|
| `MyBase.Load` / `txtdescripcion.TextChanged` | Carga líneas y almacenes | Varios de catálogo |
| `CheckBox1_CheckedChanged` | Muestra todo el stock (sin filtro sublínea) | `Producto_BuscarxTipo` + `PRODUCTO_MOSTRARSTOCKALMACENESXSUC` |
| `cbsublinea_SelectedIndexChanged` | Filtra por sublínea | `Producto_Buscarxsublinea` + `PRODUCTO_MOSTRARSTOCKALMACENESXSUC` |
| `Button2_Click` | Exportar a Excel | - |
| `Button1_Click` | Generar reporte Crystal (CRalmacengen4) | `crearreporte()` escribe en tabla temporal |

### Patrón N+1 queries
Para CADA producto, ejecuta un `MOSTRARSTOCKALMACENESXSUC`. Si hay 500 productos, hace 500 consultas a BD. Esto es ineficiente.

---

## 3. FrmMostrarSotckGeneral.vb (672 líneas + 18KB Designer)

### Propósito
Stock general por almacenes (1-7), con costo unitario, precio venta, totales. Múltiples reportes.

### Diferencias con FrmMostrarSotck
- Muestra costo y precio
- Suma stocks de almacenes 1+4, 2+5, 3+6
- Usa `MOSTRARSTOCKALMACENES` (todos los almacenes) en lugar de `XSUC`
- Tiene coloreado condicional en ListView (amarillo para totales, rosa para ubicación)

### Método TC() (línea 610)
Función que busca tipo de cambio pero está **comentada** — solo asigna `LblTCS.Text = ""`.

---

## 4. FrmMostrarSotckMCERO.vb (403 líneas + 18KB Designer)

### Propósito
Stock con valor > 0 (excluye productos con stock cero). Similar a FrmMostrarSotck.

### Diferencia clave
Filtra `IF STOCK > 0` en lugar de `IF STOCK > -1`. Solo muestra productos con stock positivo.

---

## 5. FrmMostrarSotckRaz.vb (203 líneas + 16KB Designer)

### Propósito
Stock por razón social (multisucursal). Suma stocks por grupos de almacenes: SUCURSAL_01 (1+4), SUCURSAL_02 (2+5), SUCURSAL_03 (3+6), DISTRIBUIDORA (3).

### Reporte Crystal
Usa `CRalmacengen1`.

---

## 6. FrmMostrarSotckxMarca.vb (330 líneas + 17KB Designer)

### Propósito
Stock filtrado por marca de producto. Usa `CMarca` DAL en lugar de `CLinea`.

### SP usado
`Producto_BuscarxMARCA` para filtrar productos por marca.

---

## 7. FrmMostrarSotckxpROV.vb (295 líneas + 17KB Designer)

### Propósito
Stock filtrado por proveedor. Usa `CPaciente` DAL para buscar proveedores.

### SP usado
`Producto_BuscarxPROVEEDOR` para filtrar productos por proveedor. Calcula total = costo * stock.

---

## 8. FrmMovTrasladoAlmacen.vb (~4300 líneas + 154KB Designer) — CRÍTICO

### Propósito
Formulario de traslado entre almacenes. Permite:
- Crear traslados de productos entre almacenes
- Gestionar cilindros llenos y vacíos por separado
- Generar guías de remisión electrónicas
- Preparar carga para repartidores
- Recepcionar traslados
- Integración con facturación electrónica SUNAT

### Objetos DAL declarados

| Variable | Clase | Propósito |
|----------|-------|-----------|
| obji | CProducto | Productos |
| obj | CMovimiento | Movimientos |
| objg | Cgas | Gas/cilindros |
| objp | CPaciente | Personas |
| objc | CComprobante | Comprobantes |
| objsuc | CSucursal | Sucursales |
| objd | CDetalleMovimiento | Detalles |
| objRptLocal | CReportesCartaPorte | Reportes PDF |

### Funcionalidades principales (estimadas por tamaño)

Debido a las ~4300 líneas, este formulario contiene MÚLTIPLES funcionalidades:

1. **Traslado entre almacenes** — Selección de origen/destino, productos, cilindros
2. **Gestión de cilindros** — Llenos y vacíos como pedidos separados
3. **Guía de remisión** — Generación de guías (integración SUNAT)
4. **Preparación de carga** — Asignación de cilindros a repartidores
5. **Recepción de traslados** — Confirmación de recepción con diferencias
6. **Reportes** — Carta porte, guías
7. **Carga/descarga de bombonas** — Registro de series

### SPs que probablemente utiliza

- `sp_Movimiento_Insertar` — Crear movimiento de traslado
- `UPDATE_StockProducto` — Actualizar stock
- `sp_StockCilindros_PorProducto` — Consultar cilindros disponibles
- `SHOW_ValidarStockProductoMovimiento` — Validar stock
- `usp_Producto_StockPlanificado` — Stock planificado

### Riesgos del formulario

1. **EXTREMADAMENTE GRANDE** (~4300 líneas) — difícil de mantener, probar o migrar
2. **Mezcla responsabilidades** — traslados, guías, recepción, preparación de carga
3. **Conexiones directas a BD** — tiene método local `Conectar()` y `Desconectar()` (bypassea la capa DAL)
4. **Integración SUNAT** — lógica de facturación electrónica mezclada con logística
5. **Sin manejo de errores unificado** — mezcla MsgBox, excepciones, y RaiseEvent

### Pendiente: Análisis detallado por ser muy extenso
Se recomienda leer el form completo con:
```
Read a FrmMovTrasladoAlmacen.vb en bloques de 500 líneas
```

---

## Resumen de reportes Crystal por form

| Form | Reporte Crystal | Clase Reporte |
|------|----------------|---------------|
| FrmMostrarSotck | Stock por almacén (general) | CRalmacengen4 |
| FrmMostrarSotckGeneral | Stock general con costos | CRalmacengen |
| FrmMostrarSotckRaz | Stock por razón social | CRalmacengen1 |
| FrmMostrarSotckxMarca | Stock por marca | CRalmacengen2 |
| FrmMostrarSotckxpROV | Stock por proveedor | CRalmacengen3 |
| FrmMostrarSotckMCERO | Stock > 0 | CRalmacengen4 |
| FrmMovTrasladoAlmacen | Carta porte, guías | CReportesCartaPorte |
