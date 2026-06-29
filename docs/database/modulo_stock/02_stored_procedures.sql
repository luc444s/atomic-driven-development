-- ============================================================
-- MÓDULO STOCK/INVENTARIO — SYSTUTOR LEGACY
-- SPs extraídos de BD ACONCAGUA.Sys_GMS_ES
-- Fecha: 2026-06-28
-- ============================================================
-- NOTA: Los bodies completos deben extraerse con:
--   sqlcmd -S ACONCAGUA -d Sys_GMS_ES -U sa -P RedSystutor#2026#
--     -Q "SELECT OBJECT_DEFINITION(OBJECT_ID('SP_NAME'))"
-- ============================================================

-- ============================================================
-- GRUPO 1: KARDEX (7 SPs)
-- ============================================================

-- 1.1 sp_kardex_Insertar
-- Propósito: Insertar registro en tabla kardex
-- Parámetros: @fecha, @factped, @proveedor, @costo, @ingreso, 
--             @salida, @saldo, @lote, @fechav, @insumo, 
--             @desde, @hasta, @AREA
-- Output: @codigo (identidad del registro insertado)
-- Transacción: Sí (Serializable)
-- SQL Injection: Bajo (usa SP parametrizado)
-- Llamado desde: CProducto.Insertarkardex()

-- 1.2 sp_kardex_Eliminar
-- Propósito: Eliminar TODOS los registros de kardex (sin WHERE)
-- Parámetros: Ninguno
-- Transacción: Sí
-- RIESGO: Elimina TODO el kardex, no hay filtro por producto/fecha
-- Llamado desde: CProducto.Eliminarkardex()

-- 1.3 sp_Kardex_listarxfechas
-- Propósito: Listar kardex por producto y rango de fechas
-- Parámetros: @codigo, @FECHAI, @FECHAF, @almacen
-- Llamado desde: CProducto.BuscarKardex()

-- 1.4 sp_Kardex_listarxfechas1
-- Propósito: Listar kardex por producto, fechas y razón social
-- Parámetros: @codigo, @FECHAI, @FECHAF, @Cod_RazonS
-- Llamado desde: CProducto.BuscarKARDEX01()

-- 1.5 mostrarprodkardex
-- Propósito: Buscar productos para mostrar en kardex
-- Parámetros: @Desc_Producto
-- Llamado desde: CProducto.BuscarProductoxkardex()

-- 1.6 Producto_mostrarkARDEX
-- Propósito: Mostrar kardex detallado de un producto
-- Parámetros: @codproducto, @ALMACEN, @Fecha1, @Fecha2
-- Llamado desde: CProducto.MostrarkARDEX()

-- 1.7 Producto_mostrarkARDEXCerveza
-- Propósito: Kardex específico para productos de cerveza
-- Parámetros: @ALMACEN, @Fecha1, @Fecha2
-- Llamado desde: CProducto.MostrarkARDEXcerveza()

-- ============================================================
-- GRUPO 2: INVENTARIO FÍSICO (8 SPs)
-- ============================================================

-- 2.1 PRODUCTO_MOSTRARinventario
-- Propósito: Listar productos con stock de sistema para inventario
-- Parámetros: @codalmacen
-- Llamado desde: CMovimiento.MOSTRARinventario() → FrmInventario.Button7_Click

-- 2.2 PRODUCTO_MOSTRARinventariolinea
-- Propósito: Inventario filtrado por línea de producto
-- Parámetros: @codalmacen, @codlinea
-- Llamado desde: CMovimiento.MOSTRARinventarioxlinea() → FrmInventario

-- 2.3 PRODUCTO_MOSTRARinventarioSUBlinea
-- Propósito: Inventario filtrado por sublínea
-- Parámetros: @codalmacen, @codlinea
-- Llamado desde: CMovimiento.MOSTRARinventarioxSUBlinea() → FrmInventario

-- 2.4 PRODUCTO_MOSTRARinventarioNegativoMovimientos
-- Propósito: Productos con stock negativo en movimientos
-- Parámetros: @codalmacen
-- Llamado desde: CMovimiento.MOSTRARinventarioNegativo_Mov() → FrmInventario.Button4_Click

-- 2.5 Producto_inventario
-- Propósito: Actualizar datos de inventario de un producto
-- Parámetros: @Nro_Producto, @Desc_Producto, @StoCK, @pRECIO_INV, @COSTO_INV
-- Transacción: Sí (desde CProducto.Inventario())
-- Llamado desde: CProducto.Inventario() → FrmInventario.Button1_Click

-- 2.6 Producto_INVENTARIO_Cerrar
-- Propósito: Cerrar/actualizar inventario de un producto
-- Parámetros: @CodProducto, @stock, @pRECIO_INV, @COSTO_INV
-- Transacción: Sí
-- Llamado desde: CProducto.PRODUCTO_INVENTARIO_Cerrar() → FrmInventario.Button6_Click, Button9_Click

-- 2.7 UPDATE_InventarioEstado
-- Propósito: Actualizar estado del inventario en comprobante
-- Parámetros: @codComprobante, @estado
-- Transacción: Sí
-- Llamado desde: CProducto.UPDATE_InventarioEstado()

-- 2.8 Producto_INVENTARIO_COSTOS (referenciado en DAL)
-- Propósito: Actualizar costos masivos de inventario
-- Parámetros: @CodProducto, @Costo_Producto, @Costo_Rep, @costo_total,
--             @Precio_Producto, @Precio_Interm, @PrecioCja_Producto,
--             @UtilidadxUnid, @Utilidadxint, @Utilidadxcja,
--             @UtilidadEstxunid, @UtilidadEstxInterm, @UtilidadEstxCja
-- Transacción: Sí

-- ============================================================
-- GRUPO 3: CONSULTA DE STOCK (12 SPs)
-- ============================================================

-- 3.1 PRODUCTO_MOSTRARSTOCKALMACENES
-- Propósito: Obtener stock de un producto en TODOS los almacenes
-- Parámetros: @CodProducto
-- Llamado desde: CMovimiento.MOSTRARSTOCKALMACENES() → FrmMostrarSotck*

-- 3.2 PRODUCTO_MOSTRARSTOCKALMACENESXSUC
-- Propósito: Obtener stock de un producto en un almacén específico
-- Parámetros: @CodProducto, @CodAlmacen
-- Llamado desde: CMovimiento.MOSTRARSTOCKALMACENESXSUC() → FrmMostrarSotck*

-- 3.3 PRODUCTO_MOSTRARsoloSTOCK
-- Propósito: Obtener stock simple de productos
-- Parámetros: ? (verificar)
-- Llamado desde: ?

-- 3.4 PRODUCTO_MOSTRARsoloSTOCKXSUC
-- Propósito: Stock simple por sucursal
-- Parámetros: @CodProducto, @Almacen
-- Llamado desde: CMovimiento.PRODUCTO_MOSTRAR_soloSTOCKXSUC()

-- 3.5 PRODUCTO_MOSTRARstocks
-- Propósito: Stock por usuario y sucursal (faltantes)
-- Parámetros: @name (usuario), @sucu (sucursal)
-- Llamado desde: CProducto.Mostrar_cantidades()

-- 3.6 PRODUCTO_MOSTRARstocks_proveedor
-- Propósito: Stock por proveedor y sucursal
-- Parámetros: @prov, @sucu
-- Llamado desde: CProducto.Mostrar_faltantesprov()

-- 3.7 MOSTRARstocksxentregas
-- Propósito: Stock cruzado con entregas por fechas
-- Parámetros: @CodProducto, @CodALMACEN, @FechaI, @FechaF
-- Llamado desde: CProducto.Mostrarstocksxentrega()

-- 3.8 MOSTRARstocksxsucxfechas
-- Propósito: Stock por sucursal y rango de fechas
-- Parámetros: @CodProducto, @CodALMACEN, @FechaI, @FechaF
-- Llamado desde: CProducto.Mostrarstocksxfecha()

-- 3.9 UPDATE_StockProducto
-- Propósito: Actualizar stock de producto (ingreso/egreso)
-- Parámetros: @Tipoingreso, @CodProducto, @cantidad, @codMovimiento
-- Transacción: Sí
-- Llamado desde: CProducto.UPDATE_StockProducto()

-- 3.10 SHOW_ValidarStockProductoMovimiento
-- Propósito: Validar stock disponible antes de movimiento (ventas)
-- Parámetros: @CodMovimiento
-- Retorna: DataTable con productos y su disponibilidad
-- Llamado desde: CProducto.SHOW_ValidarStockProductoMovimiento()

-- 3.11 SHOW_ValidarStockProductoMovimientoCOMPRA
-- Propósito: Validar stock para movimientos de compra
-- Parámetros: @CodMovimiento
-- Retorna: DataTable con productos y disponibilidad
-- Llamado desde: CProducto.SHOW_ValidarStockProductoMovimientoCOMPRA()

-- 3.12 usp_Producto_StockPlanificado
-- Propósito: Stock planificado para logística
-- Parámetros: ? (verificar)
-- Llamado desde: Módulo Logística (planificación de carga)

-- ============================================================
-- GRUPO 4: CILINDROS/BOMBONAS (2 SPs)
-- ============================================================

-- 4.1 sp_StockBombonasDisponibles
-- Propósito: Bombonas (cilindros) disponibles en stock
-- Parámetros: ? (verificar)
-- Llamado desde: Módulo Logística

-- 4.2 sp_StockCilindros_PorProducto
-- Propósito: Cilindros en stock agrupados por producto
-- Parámetros: @CodProducto (probable)
-- Llamado desde: CProducto (método por identificar)

-- ============================================================
-- GRUPO 5: PRODUCTO — MANTENIMIENTO (relacionado con stock)
-- ============================================================

-- Producto_Insertar (SP de InsertarProducto)
-- Incluye: @StockMin_Producto (stock mínimo de seguridad)

-- Producto_Modificar (SP de ModificarProducto)
-- Incluye: @StockMin_Producto

-- ============================================================
-- SPs NO IDENTIFICADOS EN BD (listados en requirements pero no confirmados)
-- ============================================================

-- Los siguientes SPs mencionados en el alcance NO se encontraron en BD:
-- ❌ sp_StockCilindros_PorProducto — NO CONFIRMADO en extracción
-- ❌ usp_Producto_StockPlanificado — NO CONFIRMADO en extracción

-- ============================================================
-- ANÁLISIS DE RIESGOS EN SPs
-- ============================================================

-- RIESGO ALTO: sp_kardex_Eliminar
--   Elimina TODOS los registros de kardex sin filtro. 
--   No hay respaldo automático. Pérdida total de histórico.

-- RIESGO ALTO: UPDATE_StockProducto
--   Modifica stock directamente sin validación de consistencia.
--   No registra auditoría de quién hizo el cambio.

-- RIESGO MEDIO: Producto_INVENTARIO_Cerrar
--   Puede sobrescribir stock con valores incorrectos.
--   No valida diferencia de inventario antes de aplicar.

-- RIESGO MEDIO: Sin transacciones en SPs de consulta
--   Los SPs de lectura no usan transacciones, OK para consultas.
--   Pero los SPs de escritura sí usan transacciones.

-- RIESGO BAJO: SQL Injection
--   Todos los SPs usan parámetros tipados → riesgo bajo.
--   Pero hay campos nvarchar sin validación de longitud adecuada.
