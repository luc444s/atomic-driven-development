-- =============================================================================
-- STORED PROCEDURES — Módulo Productos/Catálogos
-- Extraído de docs/legacy/database/02_stored_procedures.txt
-- Agrupado por: Producto (CRUD + búsquedas), Catálogos, Promociones/Descuentos,
--               Actualización de precios, Bombonas
-- =============================================================================

-- NOTA: Este archivo lista los SPs referenciados. Para el texto completo,
-- ver docs/legacy/database/02_stored_procedures.txt (~945KB).
-- Aquí se documentan nombre, parámetros y riesgos.

-- =============================================================================
-- 1. PRODUCTO — CRUD
-- =============================================================================

-- SP_1: Producto_Insertar
-- Propósito: Insertar un nuevo producto (38 parámetros)
-- Llamado desde: CProducto.InsertarProducto (FrmCatProductos.cmdgrabar_Click)
-- Riesgo: ALTO - 38 parámetros, sin validación de duplicados en SP
-- Parámetros: Ver CProducto.InsertarProducto

-- SP_2: Producto_Modificar
-- Propósito: Modificar un producto existente (38 parámetros)
-- Llamado desde: CProducto.ModificarProducto (FrmCatProductos.cmdgrabar_Click Case 2)
-- Riesgo: ALTO - 38 parámetros, actualiza TODO el registro

-- SP_3: Producto_cambiarestado
-- SP_4: Producto_cambiarnombre

-- SP_5: Producto_Modificarcont
-- Propósito: Modificar campo "cont" (pack)
-- Llamado desde: CProducto.Actcont
-- Parámetros: @Cod_Producto, @cont (float)

-- SP_6: Producto_ModificarPrecio
-- SP_7: Producto_Modificarprecios

-- SP_8: Producto_codRapido
-- Propósito: Marcar/desmarcar código rápido
-- Llamado desde: CProducto.Codrapido

-- SP_9: Producto_costoadicional
-- SP_10: Producto_difPrecios

-- =============================================================================
-- 2. PRODUCTO — BÚSQUEDAS (~40 SPs)
-- =============================================================================

-- SP_11: Producto_Buscar (3 variantes encontradas)
-- Propósito: Buscar producto por código
-- Llamado desde: CProducto.BuscarProducto

-- SP_12: Producto_BuscarxNom
-- Propósito: Buscar producto por nombre
-- Llamado desde: CProducto.BuscarProductoxDesc, FrmBuscarProducto

-- SP_13: Producto_BuscarxNomCB
-- Propósito: Buscar producto por nombre combo box

-- SP_14: Producto_BuscarxNom01
-- Propósito: Buscar producto para precios
-- Llamado desde: CProducto.BuscarProductoxPRECIOS

-- SP_15: Producto_BuscarxNom1

-- SP_16: Producto_BuscarxTipo
-- Propósito: Buscar por tipo de insumo + descripción
-- Llamado desde: CProducto.BuscarProdxTipo

-- SP_17: Producto_BuscarxTipo1
-- SP_18: Producto_BuscarxTipo12
-- SP_19: Producto_BuscarxTipo2
-- SP_20: Producto_BuscarxTipo3
-- SP_21: Producto_BuscarxTipo4

-- SP_22: Producto_BuscarxTipoMiltiple
-- SP_23: Producto_BuscarxTipoMiltiple_GAS
-- SP_24: Producto_BuscarxTipoMiltipleGAS
-- Riesgo: DUPLICADO - Producto_BuscarxTipoMiltiple_GAS y Producto_BuscarxTipoMiltipleGAS
--          son variantes casi idénticas. Posible refactor pendiente.

-- SP_25: Producto_BuscarxMARCA
-- Propósito: Buscar productos por marca
-- Llamado desde: CProducto.BuscarProdxMARCA

-- SP_26: Producto_BuscarxPROVEEDOR
-- Llamado desde: CProducto.BuscarProdxPROV

-- SP_27: Producto_BuscarxNroSerie (+ variantes 1, 11, 2)
-- Propósito: Buscar por número de serie (cilindros)
-- Llamado desde: CProducto.BuscarProductoxns, BuscarProductoxns01, BuscarProductoxns02

-- SP_28: Producto_BuscarxNroSerieCilindros
-- Propósito: Buscar cilindros por serie
-- Llamado desde: CProducto.BuscarProductoxnsCilindro

-- SP_29: Producto_BuscarxFormula
-- SP_30: Producto_Buscarxgrupo
-- SP_31: Producto_BuscarDeModprodxNom
-- SP_32: Producto_BuscarVentasxcod
-- SP_33: Producto_BuscarPesoRealCilindro
-- SP_34: Producto_buscar_Unidad
-- SP_35: Producto_Buscargrupoxcod
-- SP_36: Producto_BuscarxNomxCODEBARR
-- SP_37: Producto_BuscarxNomxCODEBARRproberton

-- SP_38: Producto_Distcaotica
-- SP_39: Producto_ACT_CONDENVASE

-- =============================================================================
-- 3. PRODUCTO — ACTUALIZACIÓN DE PRECIOS
-- =============================================================================

-- SP_40: Producto_ActualizaCosto
-- Llamado desde: CProducto.ActualizarCosto

-- SP_41: Producto_Actualizagrupo
-- Llamado desde: CProducto.Modificargrupo

-- SP_42: Producto_ActualizarPrecios
-- SP_43: Producto_ActualizarPreciosEst
-- SP_44: Producto_ActualizarUtilidad

-- SP_45: Producto_listadoprecios

-- SP_46: ActualizaProducto_CodGrupo
-- SP_47: actualizar_Producto_CodGrupo
-- Riesgo: DUPLICADO - Dos SPs con nombre similar que hacen lo mismo
-- Llamado desde: CProducto.Actualiza_ProductoCodGrupo y Actualizar_ProductoCodGrupo

-- SP_48: Producto_mostrar_cant
-- SP_49: Producto_mostrarBarcode
-- SP_50: Producto_mostrarcodrap

-- SP_51: Producto_mostrarCompras
-- Llamado desde: CProducto.Mostrarcompras

-- SP_52: Producto_mostrarkARDEX
-- Llamado desde: CProducto.MostrarkARDEX

-- SP_53: Producto_mostrarTipocambioUltimo

-- SP_54: Producto_nuevocosto

-- =============================================================================
-- 4. CATÁLOGOS
-- =============================================================================

-- === Linea ===
-- Linea_BuscarxNom, Linea_BuscarxNomCB, Linea_BuscarxNomCBxrubro
-- Linea_BuscarxNomXRubro, Linea_Insertar, Linea_Modificar

-- === SubLinea ===
-- SubLinea_BuscarxNom, SubLinea_BuscarxNomCB, SubLinea_BuscarxNomCB1
-- SubLinea_BuscarxNomXLinea, SubLinea_BuscarxNomXLineaxcod
-- SubLinea_BuscarxNomXLineaxrubro, SubLinea_Insertar, SubLinea_Modificar
-- CodSubLinea_BuscarxNomXrubro

-- === Marca ===
-- Marca_BuscarxNom, Marca_BuscarxNomCB, Marca_Insertar, Marca_Modificar

-- === Rubro ===
-- Rubro_BuscarxNom, Rubro_BuscarxNomCB, Rubro_Insertar, Rubro_Modificar

-- === TipoInsumo ===
-- TipoInsumo_BuscarDescCB, TipoInsumo_Insertar, TipoInsumo_Modificar

-- === Unidad ===
-- Unidad_BuscarxNom, Unidad_BuscarxNomCB, Unidad_Insertar, Unidad_Modificar

-- === Subcategoria ===
-- Subcategoria_BuscarxNomCB, Subcategoria_Modificar (sin Insertar aparente)

-- === EstadoProducto ===
-- EstadoProducto_BuscarxNom, EstadoProducto_BuscarxNomCB
-- EstadoProducto_Insertar, EstadoProducto_Modificar

-- === Grupo ===
-- Grupo_BuscarxNom, buscar_Grupo

-- === Otros ===
-- Buscar_mostrarlinea, Buscar_mostrarSublinea
-- BuscarPorCodSublinea

-- =============================================================================
-- 5. PROMOCIONES Y DESCUENTOS
-- =============================================================================

-- Promocion_BuscarxProd, Promocion_Insertar, Promocion_Modificar
-- Promocion_mostrar, Promocion_mostrarActiva
-- Mil_BuscarPromProducto
-- descuento_Buscar, sp_Descuento_Buscarxproducto, sp_Descuento_BuscarxLinea
-- sp_Descuento_Insertar, sp_Descuento_Modificar, TicketDescuento_*

-- =============================================================================
-- 6. BOMBONAS / RETIMBRADO
-- =============================================================================

-- Retimbrado_Insertar, Retimbrado_Modificar, Retimbrado_Buscar
-- Buscar_MatriculaBombona
-- usp_EdetPB_ObtenerVigente, usp_EdetPB_ReemplazarVigencia

-- =============================================================================
-- 7. SPs con RIESGO IDENTIFICADO
-- =============================================================================

-- RIESGO P0: Varios SPs Producto_BuscarxTipo* duplicados
-- RIESGO P0: ActualizaProducto_CodGrupo vs actualizar_Producto_CodGrupo
-- RIESGO P1: 38 parámetros en Producto_Insertar/Modificar sin validación
-- RIESGO P1: Sin transacciones en la mayoría de SPs de búsqueda
-- RIESGO P2: Muchos SPs sin esquema definido (dbo vs no)
-- RIESGO P2: Parámetros NVARCHAR(50) truncantes para barcode1 que es NVARCHAR(150)
-- RIESGO P3: Sin logging ni auditoría en SPs de modificación
