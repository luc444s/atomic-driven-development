-- ============================================================================
-- MÓDULO LOGÍSTICA — STORED PROCEDURES
-- SYSTUTOR Legacy
-- Generado a partir de análisis de formularios y base de datos
-- ============================================================================

-- ============================================================================
-- CATEGORÍA: PLANIFICACIÓN
-- ============================================================================

-- usp_Plan_ListarPendientes
-- Lista pedidos pendientes por almacén con stock
-- Parámetros: @IdAlmacen INT, @SoloPendientes BIT, @Desde DATE, @Hasta DATE
CREATE PROCEDURE usp_Plan_ListarPendientes
    @IdAlmacen INT,
    @SoloPendientes BIT,
    @Desde DATE,
    @Hasta DATE
AS
BEGIN
    SET NOCOUNT ON;
    -- Implementación: SELECT desde DetalleMovimiento con joins a productos y stock
    -- Filtra por IdAlmacenOrigen, fecha entre @Desde/@Hasta
    -- Si @SoloPendientes=1, excluye movimientos con atencion=1
END;
GO

-- usp_Plan_GuardarCantidad
-- Actualiza CantPlanificada en DetalleMovimiento
-- Parámetros: @IdsDetalleMov NVARCHAR(MAX), @Cantidad DECIMAL(18,2), @Usuario NVARCHAR(50)
CREATE PROCEDURE usp_Plan_GuardarCantidad
    @IdsDetalleMov NVARCHAR(MAX),
    @Cantidad DECIMAL(18,2),
    @Usuario NVARCHAR(50)
AS
BEGIN
    SET NOCOUNT ON;
    -- UPDATE DetalleMovimiento SET CantPlanificada = @Cantidad
    -- WHERE IdDetalleMov IN (SELECT Value FROM dbo.fn_Split(@IdsDetalleMov, ','))
END;
GO

-- usp_Plan_GuardarCantidadCILPRO
-- Upsert en Planificacion_DetalleMovimiento (CILPRO)
CREATE PROCEDURE usp_Plan_GuardarCantidadCILPRO
AS
BEGIN
    SET NOCOUNT ON;
    -- MERGE/INSERT-UPDATE sobre Planificacion_DetalleMovimiento
END;
GO

-- usp_Plan_GuardarLinea
-- Actualiza CantidadPlanificada en EDetalle_cpedido
-- Parámetros: @IdDetalle INT, @Cantidad DECIMAL(18,2), @Usuario NVARCHAR(50)
CREATE PROCEDURE usp_Plan_GuardarLinea
    @IdDetalle INT,
    @Cantidad DECIMAL(18,2),
    @Usuario NVARCHAR(50)
AS
BEGIN
    SET NOCOUNT ON;
    -- UPDATE EDetalle_cpedido SET CantidadPlanificada = @Cantidad WHERE IdDetalle = @IdDetalle
END;
GO

-- usp_Plan_GenerarPreCarga
-- Inserta cabecera en PLAN_PREPARACION_CARGA
CREATE PROCEDURE usp_Plan_GenerarPreCarga
AS
BEGIN
    SET NOCOUNT ON;
    -- INSERT INTO PLAN_PREPARACION_CARGA (Fecha, IdAlmacen, Estado, ...)
END;
GO

-- usp_Plan_InsertarDetallePreCarga
-- Inserta detalle en PLAN_PREPARACION_DETALLE
CREATE PROCEDURE usp_Plan_InsertarDetallePreCarga
AS
BEGIN
    SET NOCOUNT ON;
    -- INSERT INTO PLAN_PREPARACION_DETALLE (IdPreCarga, IdDetalleMov, Cantidad, ...)
END;
GO

-- usp_Plan_InsertarServiciosEnAgenda
-- Inserta servicios CILCLI en AGENDA_REPARTIDOR
-- Parámetros: @CodMovimiento NVARCHAR(20)
CREATE PROCEDURE usp_Plan_InsertarServiciosEnAgenda
    @CodMovimiento NVARCHAR(20)
AS
BEGIN
    SET NOCOUNT ON;
    -- INSERT INTO AGENDA_REPARTIDOR (...) SELECT ... FROM CILCLI WHERE CodMovimiento = @CodMovimiento
END;
GO

-- usp_Plan_ListarPedidosCILPRO
-- Lista pedidos CILPRO pendientes
CREATE PROCEDURE usp_Plan_ListarPedidosCILPRO
AS
BEGIN
    SET NOCOUNT ON;
    -- SELECT desde Pedidos CILPRO con estado pendiente
END;
GO

-- usp_Plan_ListarPreCargaDetalle
-- Detalle de pre-carga por IdPreCarga
-- Parámetros: @IdPreCarga INT
CREATE PROCEDURE usp_Plan_ListarPreCargaDetalle
    @IdPreCarga INT
AS
BEGIN
    SET NOCOUNT ON;
    -- SELECT detalle desde PLAN_PREPARACION_DETALLE WHERE IdPreCarga = @IdPreCarga
END;
GO

-- usp_Plan_ListarPreCargaPendiente
-- Lista pre-cargas en estado PENDIENTE
CREATE PROCEDURE usp_Plan_ListarPreCargaPendiente
AS
BEGIN
    SET NOCOUNT ON;
    -- SELECT desde PLAN_PREPARACION_CARGA WHERE Estado = 'PENDIENTE'
END;
GO

-- usp_Plan_PreparacionCarga
-- SELECT de EDetalle_cpedido para preparar carga
CREATE PROCEDURE usp_Plan_PreparacionCarga
AS
BEGIN
    SET NOCOUNT ON;
    -- SELECT desde EDetalle_cpedido con joins para preparación de carga
END;
GO

-- usp_Plan_AceptarGenerarTraslado
-- Acepta planificación y genera traslado
CREATE PROCEDURE usp_Plan_AceptarGenerarTraslado
AS
BEGIN
    SET NOCOUNT ON;
    -- Transacción: actualiza estado, inserta traslado, agenda
END;
GO

-- usp_Producto_StockPlanificado
-- Stock planificado desde AGENDA_REPARTIDOR
-- Parámetros: @CodProducto NVARCHAR(20)
CREATE PROCEDURE usp_Producto_StockPlanificado
    @CodProducto NVARCHAR(20)
AS
BEGIN
    SET NOCOUNT ON;
    -- SELECT SUM(Cantidad) FROM AGENDA_REPARTIDOR WHERE CodProducto = @CodProducto AND Estado IN (...)
END;
GO


-- ============================================================================
-- CATEGORÍA: AGENDA REPARTIDOR
-- ============================================================================

-- sp_AgendaRepartidor_Insertar
-- Inserta tarea en AGENDA_REPARTIDOR
CREATE PROCEDURE sp_AgendaRepartidor_Insertar
AS
BEGIN
    SET NOCOUNT ON;
    -- INSERT INTO AGENDA_REPARTIDOR (...)
END;
GO

-- sp_AgendaRepartidor_Upsert
-- Inserta o actualiza registro en AGENDA_REPARTIDOR
CREATE PROCEDURE sp_AgendaRepartidor_Upsert
AS
BEGIN
    SET NOCOUNT ON;
    -- MERGE/IF EXISTS UPDATE ELSE INSERT
END;
GO

-- sp_AgendaRepartidor_HistorialPorCliente
-- Historial de agenda por cliente
-- Parámetros: @Cod_Cliente NVARCHAR(20)
CREATE PROCEDURE sp_AgendaRepartidor_HistorialPorCliente
    @Cod_Cliente NVARCHAR(20)
AS
BEGIN
    SET NOCOUNT ON;
    -- SELECT ... FROM AGENDA_REPARTIDOR WHERE Cod_Cliente = @Cod_Cliente ORDER BY Fecha DESC
END;
GO

-- sp_AgendaRepartidor_ListarPorFiltros
-- Lista agenda con filtros (fecha, repartidor, estado, almacén)
CREATE PROCEDURE sp_AgendaRepartidor_ListarPorFiltros
AS
BEGIN
    SET NOCOUNT ON;
    -- SELECT con múltiples filtros opcionales
END;
GO

-- sp_AgendaRepartidor_ActualizarEstado
-- Actualiza estado de una tarea en AGENDA_REPARTIDOR
CREATE PROCEDURE sp_AgendaRepartidor_ActualizarEstado
AS
BEGIN
    SET NOCOUNT ON;
    -- UPDATE AGENDA_REPARTIDOR SET Estado = @Estado WHERE IdAgenda = @IdAgenda
END;
GO

-- sp_AgendaRepartidor_MarcarCargado
-- Marca tarea como cargada (estado = CARGADO)
CREATE PROCEDURE sp_AgendaRepartidor_MarcarCargado
AS
BEGIN
    SET NOCOUNT ON;
    -- UPDATE AGENDA_REPARTIDOR SET Cargado = 1 WHERE ...
END;
GO

-- sp_AgendaRepartidor_MarcarCargadoPorGuia
-- Marca como cargado usando número de guía
CREATE PROCEDURE sp_AgendaRepartidor_MarcarCargadoPorGuia
AS
BEGIN
    SET NOCOUNT ON;
    -- UPDATE AGENDA_REPARTIDOR SET Cargado = 1 WHERE NroGuia = @NroGuia
END;
GO

-- sp_AgendaRepartidor_ResumenDiario
-- Resumen del día (totales, estados, repartidores)
CREATE PROCEDURE sp_AgendaRepartidor_ResumenDiario
AS
BEGIN
    SET NOCOUNT ON;
    -- SELECT COUNT, SUM agrupado por estado y repartidor para fecha actual
END;
GO

-- sp_Agenda_Insertar
-- Insertar tarea en agenda (versión DAL)
CREATE PROCEDURE sp_Agenda_Insertar
AS
BEGIN
    SET NOCOUNT ON;
    -- INSERT agenda desde capa DAL
END;
GO

-- sp_Agenda_CambiarEstado
-- Cambiar estado de tarea en agenda
CREATE PROCEDURE sp_Agenda_CambiarEstado
AS
BEGIN
    SET NOCOUNT ON;
    -- UPDATE Agenda SET Estado = @Estado WHERE IdAgenda = @IdAgenda
END;
GO

-- sp_Agenda_ListarPorDia
-- Listar agenda por día
CREATE PROCEDURE sp_Agenda_ListarPorDia
AS
BEGIN
    SET NOCOUNT ON;
    -- SELECT ... FROM Agenda WHERE Fecha = @Fecha
END;
GO


-- ============================================================================
-- CATEGORÍA: CARGA REPARTIDOR
-- ============================================================================

-- sp_CargaRepartidor_Insertar
-- Asigna serie de cilindro a carga de repartidor
CREATE PROCEDURE sp_CargaRepartidor_Insertar
AS
BEGIN
    SET NOCOUNT ON;
    -- INSERT INTO AGENDA_PREPARACION_CARGA (Serie, IdAgenda, ...)
END;
GO

-- sp_CargaRepartidor_Eliminar
-- Quita serie de cilindro de carga de repartidor
CREATE PROCEDURE sp_CargaRepartidor_Eliminar
AS
BEGIN
    SET NOCOUNT ON;
    -- DELETE FROM AGENDA_PREPARACION_CARGA WHERE Serie = @Serie AND IdAgenda = @IdAgenda
END;
GO

-- sp_CargaRepartidor_ResumenPeso
-- Resumen de pesos por repartidor/agenda
CREATE PROCEDURE sp_CargaRepartidor_ResumenPeso
AS
BEGIN
    SET NOCOUNT ON;
    -- SELECT SUM(Peso) FROM ... agrupado por repartidor
END;
GO


-- ============================================================================
-- CATEGORÍA: REPARTIDOR
-- ============================================================================

-- sp_Repartidor_GuardarParametro
-- Guarda parámetros de configuración del repartidor
-- Parámetros: @CargoFuncion NVARCHAR(100), @EsRepartidor BIT, @Activo BIT
CREATE PROCEDURE sp_Repartidor_GuardarParametro
    @CargoFuncion NVARCHAR(100),
    @EsRepartidor BIT,
    @Activo BIT
AS
BEGIN
    SET NOCOUNT ON;
    -- INSERT/UPDATE parametros de repartidor
END;
GO

-- sp_Repartidor_ListarCargos
-- Lista cargos/funciones de repartidores
CREATE PROCEDURE sp_Repartidor_ListarCargos
AS
BEGIN
    SET NOCOUNT ON;
    -- SELECT desde tabla de cargos
END;
GO


-- ============================================================================
-- CATEGORÍA: DESPACHO
-- ============================================================================

-- actualizar_despacho
-- Actualiza cantidad atendida en DetalleMovimiento
-- Parámetros: @IdDetalle INT, @Cantidad DECIMAL(18,2)
CREATE PROCEDURE actualizar_despacho
    @IdDetalle INT,
    @Cantidad DECIMAL(18,2)
AS
BEGIN
    SET NOCOUNT ON;
    -- UPDATE DetalleMovimiento SET CantAtencion = @Cantidad WHERE IdDetalleMov = @IdDetalle
END;
GO

-- cerrar_despacho
-- Cierra despacho cambiando atencion=1
-- Parámetros: @CodMovimiento NVARCHAR(20), @Atencion BIT
CREATE PROCEDURE cerrar_despacho
    @CodMovimiento NVARCHAR(20),
    @Atencion BIT
AS
BEGIN
    SET NOCOUNT ON;
    -- UPDATE Movimiento SET atencion = @Atencion WHERE CodMovimiento = @CodMovimiento
END;
GO

-- MOSTRAR_ATENCIONES_descargas
-- Lista movimientos tipo 4 pendientes de descarga
-- Parámetros: @Almacen INT
CREATE PROCEDURE MOSTRAR_ATENCIONES_descargas
    @Almacen INT
AS
BEGIN
    SET NOCOUNT ON;
    -- SELECT ... FROM Movimiento WHERE TipoMovimiento = 4 AND IdAlmacenDestino = @Almacen AND atencion = 0
END;
GO

-- MOSTRAR_detalle_ATENCIONESdescargas
-- Detalle de descarga por movimiento
-- Parámetros: @Almacen INT, @CodMovimiento NVARCHAR(20)
CREATE PROCEDURE MOSTRAR_detalle_ATENCIONESdescargas
    @Almacen INT,
    @CodMovimiento NVARCHAR(20)
AS
BEGIN
    SET NOCOUNT ON;
    -- SELECT detalle desde DetalleMovimiento WHERE CodMovimiento = @CodMovimiento
END;
GO

-- Movimiento_guia
-- Actualiza guía y transportista de movimiento
-- Parámetros: @CodMovimiento NVARCHAR(20), @NroGuia NVARCHAR(50), @Transportista NVARCHAR(100)
CREATE PROCEDURE Movimiento_guia
    @CodMovimiento NVARCHAR(20),
    @NroGuia NVARCHAR(50),
    @Transportista NVARCHAR(100)
AS
BEGIN
    SET NOCOUNT ON;
    -- UPDATE Movimiento SET NroGuia = @NroGuia, Transportista = @Transportista WHERE CodMovimiento = @CodMovimiento
END;
GO

-- Movimiento_nroguia
-- Actualiza solo NroGuia del movimiento
CREATE PROCEDURE Movimiento_nroguia
AS
BEGIN
    SET NOCOUNT ON;
    -- UPDATE Movimiento SET NroGuia = @NroGuia WHERE CodMovimiento = @CodMovimiento
END;
GO


-- ============================================================================
-- CATEGORÍA: RECEPCIÓN
-- ============================================================================

-- RECEPCION_lISTAR
-- Lista recepciones pendientes por sucursal
-- Parámetros: @Sucursal INT
CREATE PROCEDURE RECEPCION_lISTAR
    @Sucursal INT
AS
BEGIN
    SET NOCOUNT ON;
    -- SELECT ... FROM Movimiento WHERE IdAlmacenDestino = @Sucursal AND EstadoRecepcion = 'PENDIENTE'
END;
GO

-- sp_movimiento_aCTUALIZAR
-- Actualiza estado y/o tipo de movimiento
CREATE PROCEDURE sp_movimiento_aCTUALIZAR
AS
BEGIN
    SET NOCOUNT ON;
    -- UPDATE Movimiento SET Estado = @Estado, Tipo = @Tipo WHERE CodMovimiento = @CodMovimiento
END;
GO

-- Sp_Movimiento_recuperarenvio
-- Recupera datos de envío para recepción
CREATE PROCEDURE Sp_Movimiento_recuperarenvio
AS
BEGIN
    SET NOCOUNT ON;
    -- SELECT datos de envío desde Movimiento WHERE CodMovimiento = @CodMovimiento
END;
GO


-- ============================================================================
-- CATEGORÍA: TRASLADO
-- ============================================================================

-- usp_Traslado_ListarParaCarga
-- Lista traslados pendientes para carga
-- Parámetros: @IdTraslado INT
CREATE PROCEDURE usp_Traslado_ListarParaCarga
    @IdTraslado INT
AS
BEGIN
    SET NOCOUNT ON;
    -- SELECT ... FROM Traslados WHERE IdTraslado = @IdTraslado AND Estado = 'PENDIENTE'
END;
GO

-- InsertarHistorialEstadoTraslado
-- Inserta registro en HistorialEstadosTraslados
CREATE PROCEDURE InsertarHistorialEstadoTraslado
AS
BEGIN
    SET NOCOUNT ON;
    -- INSERT INTO HistorialEstadosTraslados (IdTraslado, Estado, Fecha, Usuario, ...)
END;
GO

-- usp_HistorialTraslado_Registrar
-- Registra historial de estado de traslado
CREATE PROCEDURE usp_HistorialTraslado_Registrar
AS
BEGIN
    SET NOCOUNT ON;
    -- INSERT INTO HistorialEstadosTraslados (...)
END;
GO


-- ============================================================================
-- CATEGORÍA: PREPARACIÓN DE CARGA
-- ============================================================================

-- sp_PreparacionCarga_ListarPendientes
-- Lista pendientes de preparación de carga
CREATE PROCEDURE sp_PreparacionCarga_ListarPendientes
AS
BEGIN
    SET NOCOUNT ON;
    -- SELECT ... FROM vPreparacionCarga WHERE Estado = 'PENDIENTE'
END;
GO

-- sp_PreparacionCarga_MarcarCargado
-- Marca ítem como cargado
CREATE PROCEDURE sp_PreparacionCarga_MarcarCargado
AS
BEGIN
    SET NOCOUNT ON;
    -- UPDATE ... SET Cargado = 1 WHERE ...
END;
GO

-- sp_PreparacionCarga_Comparar
-- Compara carga vs pedido para detectar diferencias
CREATE PROCEDURE sp_PreparacionCarga_Comparar
AS
BEGIN
    SET NOCOUNT ON;
    -- SELECT diferencia entre cantidad cargada y cantidad pedida
END;
GO


-- ============================================================================
-- CATEGORÍA: CILINDROS (usados en logística)
-- ============================================================================

-- usp_Cilindro_CambiarEstado
-- Cambia estado de cilindro con validación de reglas de negocio
-- Parámetros: @Serie NVARCHAR(50), @EstadoNuevo NVARCHAR(50), @Usuario NVARCHAR(50)
CREATE PROCEDURE usp_Cilindro_CambiarEstado
    @Serie NVARCHAR(50),
    @EstadoNuevo NVARCHAR(50),
    @Usuario NVARCHAR(50)
AS
BEGIN
    SET NOCOUNT ON;
    -- Validación de transición de estado permitida
    -- UPDATE ECilindroEstadoActual SET Estado = @EstadoNuevo WHERE Serie = @Serie
    -- INSERT INTO ECilindroEstadoLog (Serie, Estado, Usuario, Fecha)
END;
GO

-- usp_Cilindro_Estado_LogBulk
-- Bulk insert de estados de cilindros usando Table-Valued Parameter
CREATE PROCEDURE usp_Cilindro_Estado_LogBulk
    @Estados CilindroEstadoTVP READONLY
AS
BEGIN
    SET NOCOUNT ON;
    -- INSERT INTO ECilindroEstadoLog (Serie, Estado, Usuario, Fecha)
    -- SELECT Serie, Estado, Usuario, GETDATE() FROM @Estados
END;
GO

-- usp_Cilindro_Estado_LogSingle
-- Inserta log individual de cambio de estado
-- Parámetros: @Serie NVARCHAR(50), @Estado NVARCHAR(50), @Usuario NVARCHAR(50)
CREATE PROCEDURE usp_Cilindro_Estado_LogSingle
    @Serie NVARCHAR(50),
    @Estado NVARCHAR(50),
    @Usuario NVARCHAR(50)
AS
BEGIN
    SET NOCOUNT ON;
    -- INSERT INTO ECilindroEstadoLog (Serie, Estado, Usuario, Fecha) VALUES (@Serie, @Estado, @Usuario, GETDATE())
END;
GO


-- ============================================================================
-- CATEGORÍA: ADR (Acuerdo de Transporte de Mercancías Peligrosas)
-- ============================================================================

-- usp_ADR_CalcularPuntosDocumento
-- Calcula puntos ADR para un documento/movimiento
-- Parámetros: @CodMovimiento NVARCHAR(20)
CREATE PROCEDURE usp_ADR_CalcularPuntosDocumento
    @CodMovimiento NVARCHAR(20)
AS
BEGIN
    SET NOCOUNT ON;
    -- Calcula sumatoria de puntos ADR usando fn_ADR_Points para cada detalle
END;
GO

-- usp_ADR_EvaluarPedido
-- Evalúa si un pedido requiere ADR según producto y cantidad
-- Parámetros: @CodProducto NVARCHAR(20), @Cantidad DECIMAL(18,2)
CREATE PROCEDURE usp_ADR_EvaluarPedido
    @CodProducto NVARCHAR(20),
    @Cantidad DECIMAL(18,2)
AS
BEGIN
    SET NOCOUNT ON;
    -- SELECT desde vw_EdetPB_Vigente y compara con cantidad
END;
GO

-- usp_ADR_SeleccionarCamion
-- Selecciona camión compatible según puntos ADR y capacidad
CREATE PROCEDURE usp_ADR_SeleccionarCamion
AS
BEGIN
    SET NOCOUNT ON;
    -- Busca vehículo con capacidad ADR suficiente para el movimiento
END;
GO


-- ============================================================================
-- CATEGORÍA: CARTA PORTE
-- ============================================================================

-- usp_CartaPorte_Cabecera
-- Datos de cabecera para carta porte
-- Parámetros: @CodMovimiento NVARCHAR(20)
CREATE PROCEDURE usp_CartaPorte_Cabecera
    @CodMovimiento NVARCHAR(20)
AS
BEGIN
    SET NOCOUNT ON;
    -- SELECT cabecera desde Movimiento, cliente, transportista
END;
GO

-- usp_CartaPorte_Detalle
-- Detalle de productos para carta porte
-- Parámetros: @CodMovimiento NVARCHAR(20)
CREATE PROCEDURE usp_CartaPorte_Detalle
    @CodMovimiento NVARCHAR(20)
AS
BEGIN
    SET NOCOUNT ON;
    -- SELECT detalle desde DetalleMovimiento con productos
END;
GO

-- usp_CartaPorte_Resumen
-- Resumen para carta porte
-- Parámetros: @CodMovimiento NVARCHAR(20)
CREATE PROCEDURE usp_CartaPorte_Resumen
    @CodMovimiento NVARCHAR(20)
AS
BEGIN
    SET NOCOUNT ON;
    -- SELECT resumen de totales, bultos, peso, puntos ADR
END;
GO


-- ============================================================================
-- CATEGORÍA: RUTA
-- ============================================================================

-- sp_RutaPto_Compactar
-- Compacta puntos de ruta (reordena secuencias)
CREATE PROCEDURE sp_RutaPto_Compactar
AS
BEGIN
    SET NOCOUNT ON;
    -- Reasigna números de secuencia en RutaPto
END;
GO

-- sp_RutaPto_Mover
-- Mueve puntos de ruta (cambia orden)
CREATE PROCEDURE sp_RutaPto_Mover
AS
BEGIN
    SET NOCOUNT ON;
    -- UPDATE RutaPto SET Orden = @NuevoOrden WHERE IdRuta = @IdRuta AND IdPunto = @IdPunto
END;
GO
