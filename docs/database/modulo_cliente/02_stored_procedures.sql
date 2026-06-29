/*
SPs del modulo Clientes - extraidos de 02_stored_procedures.txt
Total encontrados: 80
*/

-- =============================================
-- SP: PERSONA_Buscarxruc (lÃ­neas 12049-12053)
-- =============================================
CREATE  PROCEDURE [dbo].[PERSONA_Buscarxruc]
	@Ruc_Persona        nvarchar(50)
AS
SELECT * FROM Persona
WHERE Ruc_Persona  like  @Ruc_Persona 

GO

-- =============================================
-- SP: PERSONA_BuscarxrucTipo (lÃ­neas 12054-12068)
-- =============================================
CREATE  PROCEDURE [dbo].[PERSONA_BuscarxrucTipo]
	@Ruc_Persona        nvarchar(50),
	@Cod_TipoPersona int
AS
SELECT        dbo.Persona_Nuevo.Cod_Persona, dbo.Persona_Nuevo.Nro_Persona, dbo.Persona_Nuevo.Nom_Persona, dbo.Persona_Nuevo.Dni_Persona, dbo.Persona_Nuevo.Ruc_Persona, dbo.Persona_Nuevo.Cod_TipoPersona, 
                         dbo.Persona_Nuevo.Sexo_Persona, dbo.Persona_Nuevo.FNac_Personal, dbo.Persona_Nuevo.mail_Persona, dbo.Persona_Nuevo.Telefono_Persona, dbo.Persona_Nuevo.Activo, dbo.Persona_Nuevo.Login_Persona, 
                         dbo.Persona_Nuevo.Pass_Persona, dbo.Persona_Nuevo.Nick_Persona, dbo.Persona_Nuevo.Fotografia, dbo.Persona_Nuevo.id_clave_Operacion, dbo.Persona_Nuevo.clave_op_intracomunitaria, 
                         dbo.Persona_Nuevo.nombre_comercial, dbo.Persona_Nuevo.observaciones, dbo.Vehiculo_cliente_nuevo.Direccion, dbo.Creditos.Linea_Credito, dbo.Creditos.Dias_Credito, dbo.Creditos.Id_Credito, 
                         dbo.Vehiculo_cliente_nuevo.Id_ClientePersona, dbo.Creditos.Cod_VehiculoCliente
FROM            dbo.Persona_Nuevo INNER JOIN
                         dbo.Vehiculo_cliente_nuevo ON dbo.Persona_Nuevo.Cod_Persona = dbo.Vehiculo_cliente_nuevo.Id_ClientePersona AND dbo.Persona_Nuevo.Cod_Persona = dbo.Vehiculo_cliente_nuevo.Id_ClientePersona INNER JOIN
                         dbo.Creditos ON dbo.Persona_Nuevo.Cod_Persona = dbo.Creditos.Cod_VehiculoCliente
WHERE        (dbo.Persona_Nuevo.Ruc_Persona LIKE @Ruc_Persona) AND (dbo.Persona_Nuevo.Cod_TipoPersona = @Cod_TipoPersona)



GO

-- =============================================
-- SP: PERSONA_BuscarxNomVendedor (lÃ­neas 12041-12048)
-- =============================================
create PROCEDURE [dbo].[PERSONA_BuscarxNomVendedor]
 
 @Nom_Persona         nvarchar(50)
AS
SELECT * FROM Persona
WHERE  Nom_Persona  like @Nom_Persona
order by Nom_Persona


GO

-- =============================================
-- SP: PERSONA_BuscarxNom (lÃ­neas 12000-12034)
-- =============================================
CREATE PROCEDURE [dbo].[Persona_BuscarXnom]
    @Nom_Persona NVARCHAR(200)
AS
BEGIN
    SET NOCOUNT ON;

    SELECT TOP (100) PERCENT 
        dbo.Persona_Nuevo.Cod_Persona,
        dbo.Persona_Nuevo.Nom_Persona,
        dbo.Ecargos_funciones.CargoFuncion,
        dbo.Persona_Nuevo.Dni_Persona,
        dbo.Persona_Nuevo.Ruc_Persona,
        dbo.Persona_Nuevo.Cod_TipoPersona,
        dbo.Persona_Nuevo.mail_Persona,
        dbo.Persona_Nuevo.Login_Persona,
        dbo.Persona_Nuevo.Pass_Persona,
        dbo.Persona_Nuevo.Nick_Persona,
        dbo.Persona_Nuevo.Activo,
        dbo.Ecargos_funciones.Id_CargoFuncion,
        dbo.Direcciones_NoClientes.Direccion_Linea_1,
        dbo.Persona_Nuevo.Telefono_Persona,
        dbo.Almacen.Desc_Almacen,
        dbo.Almacen.Cod_Almacen,
        dbo.Direcciones_NoClientes.Id_Direccion,
        dbo.Persona_Nuevo.Sexo_Persona,
        dbo.Persona_Nuevo.FNac_Personal,
        dbo.Ecargos_funciones.Fecha_Asignacion
    FROM dbo.Persona_Nuevo
    INNER JOIN dbo.Ecargos_funciones ON dbo.Persona_Nuevo.Cod_Persona = dbo.Ecargos_funciones.Cod_Persona
    INNER JOIN dbo.Almacen ON dbo.Ecargos_funciones.Cod_Sucursal = dbo.Almacen.Cod_Almacen
    LEFT OUTER JOIN dbo.Direcciones_NoClientes ON dbo.Persona_Nuevo.Cod_Persona = dbo.Direcciones_NoClientes.Cod_Persona
    WHERE dbo.Persona_Nuevo.Nom_Persona LIKE '%' + @Nom_Persona + '%'
    ORDER BY dbo.Persona_Nuevo.Nom_Persona;
END;


GO

-- =============================================
-- SP: PERSONA_BuscarxNom1 (lÃ­neas 12035-12040)
-- =============================================
CREATE PROCEDURE PERSONA_BuscarxNom1
	@Paciente	        nvarchar(50)
AS
SELECT * FROM Persona
WHERE Nom_Persona  like  @Paciente
order by Nom_Persona

GO

-- =============================================
-- SP: Ruta_PuntoEntrega_Asignar (lÃ­neas 14415-14469)
-- =============================================
CREATE PROCEDURE dbo.Ruta_PuntoEntrega_Asignar
  @Id_Ruta        INT,
  @Id_Punto       INT,    -- = Vehiculo_cliente_nuevo.Codigo
  @Secuencia      INT = NULL,
  @Activo         BIT = 1,
  @Id_RutaPunto   INT OUTPUT
AS
BEGIN
  SET NOCOUNT ON;
  BEGIN TRY
    BEGIN TRAN;

    -- Validaciones básicas
    IF NOT EXISTS (SELECT 1 FROM dbo.Ruta WHERE Id_Ruta=@Id_Ruta AND Activo=1)
      RAISERROR(N'La ruta no existe o está inactiva.', 16, 1);

    IF NOT EXISTS (SELECT 1 FROM dbo.Vehiculo_cliente_nuevo WHERE Codigo=@Id_Punto)
      RAISERROR(N'El punto (establecimiento) no existe.', 16, 1);

    -- Si no viene secuencia, usa siguiente correlativo de la ruta (sólo entre activos)
    IF @Secuencia IS NULL
      SELECT @Secuencia = ISNULL(MAX(Secuencia),0) + 1
      FROM dbo.Ruta_PuntoEntrega
      WHERE Id_Ruta = @Id_Ruta AND Activo = 1;

    -- ¿Ya existe la relación?
    DECLARE @IdExistente INT;
    SELECT @IdExistente = Id_RutaPunto
    FROM dbo.Ruta_PuntoEntrega
    WHERE Id_Ruta = @Id_Ruta AND Id_Punto = @Id_Punto;

    IF @IdExistente IS NULL
    BEGIN
      INSERT INTO dbo.Ruta_PuntoEntrega (Id_Ruta, Id_Punto, Secuencia, VentanaOverride, Activo)
      VALUES (@Id_Ruta, @Id_Punto, @Secuencia, NULL, @Activo);
      SET @Id_RutaPunto = SCOPE_IDENTITY();
    END
    ELSE
    BEGIN
      UPDATE dbo.Ruta_PuntoEntrega
         SET Activo   = @Activo,
             Secuencia= COALESCE(@Secuencia, Secuencia)
       WHERE Id_RutaPunto = @IdExistente;
      SET @Id_RutaPunto = @IdExistente;
    END

    COMMIT TRAN;
  END TRY
  BEGIN CATCH
    IF XACT_STATE() <> 0 ROLLBACK TRAN;
    DECLARE @m nvarchar(4000)=ERROR_MESSAGE();
    RAISERROR(@m,16,1);
  END CATCH
END


GO

-- =============================================
-- SP: SHOW_DireccionesXCliente (lÃ­neas 14719-14776)
-- =============================================
-- =============================================
-- Author:		<Author,,Name>
-- Create date: <Create Date,,>
-- Description:	<Description,,>
-- =============================================
CREATE PROCEDURE SHOW_DireccionesXCliente
	-- Add the parameters for the stored procedure here
	@search varchar(20),
	@type int
AS
BEGIN
	-- SET NOCOUNT ON added to prevent extra result sets from
	-- interfering with SELECT statements.
	SET NOCOUNT ON;
	DECLARE @RUC AS VARCHAR(20)

	IF (@search>0)
	BEGIN
		IF(LEN(@search)=8)
		BEGIN
		SELECT codigo,direccion,telefono,P.contacto FROM vehiculo_cliente V LEFT JOIN Persona P on v.cliente=P.Cod_Persona where Dni_Persona=@search
		END

		IF(LEN(@search)=11)
		BEGIN
		SELECT codigo,direccion,telefono,P.contacto FROM vehiculo_cliente V LEFT JOIN Persona P on v.cliente=P.Cod_Persona where Ruc_Persona=@search
		END
		
	END
	ELSE
	BEGIN

		IF(LEN(@search)=8)
		BEGIN
			SET @RUC = '10'+@RUC
		END

		SELECT 0 as CODIGO,[ RUC] as ruc_persona,
			CASE WHEN [TIPO DE VÍA]='-' THEN '' ELSE [TIPO DE VÍA] + ' ' END +
			CASE WHEN [NOMBRE DE VÍA]='-' THEN '' ELSE [NOMBRE DE VÍA] + ' ' END +
			CASE WHEN [KILÓMETRO]='-' THEN '' ELSE ' KM. ' + [KILÓMETRO] END +
			CASE WHEN [NÚMERO]='-' THEN '' ELSE ' NRO. ' + [NÚMERO] END +
			CASE WHEN [MANZANA]='-' THEN '' ELSE ' MZA. ' + [MANZANA] END +
			CASE WHEN [LOTE]='-' THEN '' ELSE ' LOTE. ' + [LOTE] END +
			CASE WHEN [DEPARTAMENTO]='-' THEN '' ELSE ' DPTO. ' + [DEPARTAMENTO] END +
			CASE WHEN [INTERIOR]='-' THEN '' ELSE ' INT. ' + [INTERIOR] END +
			CASE WHEN [CÓDIGO DE ZONA]='-' THEN '' ELSE + ' '+ [CÓDIGO DE ZONA] + ' ' END +
			CASE WHEN [TIPO DE ZONA]='-' THEN '' ELSE [TIPO DE ZONA] END as DIRECCION,
			'' AS TELEFONO,
			'' AS CONTACTO,
			[UBIGEO] AS UBIGEO,
			'' AS CORREOresp,
			'' AS ZONAresp
			FROM ruc_Direcciones WHERE [ RUC] LIKE @RUC +'%'
	END

END


GO

-- =============================================
-- SP: Personal_Modificar (lÃ­neas 12163-12195)
-- =============================================
CREATE PROCEDURE [dbo].[Personal_Modificar]
@Cod_Persona  int ,
@Nom_Persona nvarchar(50),
@dni_Persona nvarchar(10),
@Ruc_Persona nvarchar(10),
@FNac_Personal datetime,
@Login_Persona nvarchar(50),
@Pass_Persona nvarchar(50),
@Nick_Persona nvarchar(50),
@Sexo_Persona nvarchar(15),
@Mail_Persona nvarchar(50),
@Telefono_Persona nvarchar(50),
@Direccion_Persona nvarchar(50),
@cod_TipoPersona int
AS 
UPDATE Persona
SET
Nom_Persona=@Nom_Persona,
dni_Persona=@dni_Persona,
Ruc_Persona=@Ruc_Persona,
FNac_Personal=@FNac_Personal,
Login_Persona=@Login_Persona,
Pass_Persona=@Pass_Persona,
Nick_Persona=@Nick_Persona,
Sexo_Persona=@Sexo_Persona,
Mail_Persona=@Mail_Persona,
Telefono_Persona=@Telefono_Persona,
Direccion_Persona=@Direccion_Persona,
cod_TipoPersona=@cod_TipoPersona
WHERE
cod_Persona = @cod_Persona



GO

-- =============================================
-- SP: Personal_Insertar (lÃ­neas 12069-12116)
-- =============================================
CREATE PROCEDURE dbo.Personal_Insertar

@Cod_Persona INT OUTPUT,
@Nom_Persona NVARCHAR(200),
@dni_Persona NVARCHAR(20),
@Ruc_Persona NVARCHAR(20),
@FNac_Personal DATETIME,
@Login_Persona NVARCHAR(50),
@Pass_Persona NVARCHAR(50),
@Nick_Persona NVARCHAR(50),
@Sexo_Persona NVARCHAR(15),
@Mail_Persona NVARCHAR(200),
@Telefono_Persona NVARCHAR(50),
@Direccion_Persona NVARCHAR(500),
@cod_TipoPersona INT

AS
BEGIN

    SET NOCOUNT ON

    INSERT INTO Persona_Nuevo
    (
        Nom_Persona,
        Dni_Persona,

        Ruc_Persona,
        Cod_TipoPersona,
        mail_Persona,
        Telefono_Persona,
        Activo
    )
    VALUES
    (
        @Nom_Persona,
        @dni_Persona,
        @Ruc_Persona,
        @cod_TipoPersona,
        @Mail_Persona,
        
@Telefono_Persona,
        1
    )

    SET @Cod_Persona = SCOPE_IDENTITY()

END


GO

-- =============================================
-- SP: Personal_LineaCredito (lÃ­neas 12117-12162)
-- =============================================
CREATE PROCEDURE dbo.Personal_LineaCredito
    @Cod_Persona INT,
    @LineaCredito_Persona DECIMAL(18,2),
    @Dias_Credito INT,
    @Fecha_Registro DATE,
    @Activo BIT
AS
BEGIN
    SET NOCOUNT ON;

    IF EXISTS (
        SELECT 1 
        FROM dbo.Creditos 
        WHERE Cod_VehiculoCliente = @Cod_Persona
    )
    BEGIN
        UPDATE dbo.Creditos
        SET
            Linea_Credito = @LineaCredito_Persona,
            Dias_Credito = @Dias_Credito,
            Fecha_Registro = @Fecha_Registro,
            Activo = @Activo
        WHERE Cod_VehiculoCliente = @Cod_Persona;
    END
    ELSE
    BEGIN
        INSERT INTO dbo.Creditos
        (
            Cod_VehiculoCliente,
            Linea_Credito,
            Dias_Credito,
            Fecha_Registro,
            Activo
        )
        VALUES
        (
            @Cod_Persona,
            @LineaCredito_Persona,
            @Dias_Credito,
            @Fecha_Registro,
            @Activo
        );
    END
END;



GO

-- =============================================
-- SP: mostrarOrdenCompraxCliente (lÃ­neas 10825-10862)
-- =============================================
CREATE PROCEDURE [dbo].[mostrarOrdenCompraxCliente]
	@idPersona int
AS

DECLARE @TipoCambio as money = (SELECT TCVentaComercial FROM TipoCambioDiario where Fecha=CAST (GETDATE() AS DATE))

--SELECT Cod_Movimiento,Fecha,Total,
--case WHEN moneda = 'DOLARES' THEN  CAST(CAST((Total/TCsunat) AS MONEY) AS varchar(50)) + ' USD' ELSE CAST(Total AS varchar(50)) + ' S/' END AS MontoRegistrado,
--case WHEN moneda = 'DOLARES' THEN  CAST(CAST(((Total/TCsunat)*TCsunat) AS MONEY) AS varchar(50)) + '  S/' ELSE CAST(Total AS varchar(50)) + ' S/' END AS SolesRegistrados,
--case WHEN moneda = 'DOLARES' THEN  CAST(CAST(((Total/TCsunat)*TCsunat) AS MONEY) AS varchar(50)) + '  S/' ELSE CAST(Total AS varchar(50)) + ' S/' END AS SolesHoy,
--moneda, ocompra,CASE TipoAtencion WHEN 11 THEN 'ORDEN COMPRA' ELSE 'COTIZACION' END AS TipoEstado  FROM Movimiento WHERE TipoAtencion IN (11,10) and Estado=1 and Persona=@idPersona

SELECT Cod_Movimiento,Fecha,Total,
case WHEN moneda = 'DOLARES' THEN  CAST(CAST((Total/TCsunat) AS MONEY) AS varchar(50)) + ' USD' ELSE CAST(Total AS varchar(50)) + ' S/' END AS MontoRegistrado,
case WHEN moneda = 'DOLARES' THEN  CAST(CAST(((Total/TCsunat)*TCsunat) AS MONEY) AS varchar(50)) + '  S/' ELSE CAST(Total AS varchar(50)) + ' S/' END AS SolesRegistrados,
case WHEN moneda = 'DOLARES' THEN  CAST(CAST(((Total/TCsunat)*@TipoCambio) AS MONEY) AS varchar(50)) + '  S/' ELSE CAST(Total AS varchar(50)) + ' S/' END AS SolesHoy,
moneda, ocompra INTO #TABLA FROM Movimiento WHERE TipoAtencion IN (1,9) and Estado=1 and Persona=@idPersona

SELECT M.Cod_Movimiento,M.Fecha,M.Persona,SUM(C.Monto) AS SALDO INTO #SALDO FROM Movimiento M 
INNER JOIN ComprobantePedido CP ON M.Cod_Movimiento=CP.CodPedido
INNER JOIN Comprobante P ON P.CodComprobante=CP.CodComprobante
INNER JOIN Cancelaciones C ON C.Documento=P.CodComprobante
 WHERE TipoAtencion IN(1,9,10) and M.Estado=1 and Persona=@idPersona AND C.TipoMovimiento<>2
 GROUP BY Cod_Movimiento,M.Fecha,M.Persona

 SELECT T.Cod_Movimiento,SUM(C.Total) as TotalRecibo into #Recibos FROM #TABLA T INNER JOIN Comprobante C ON T.Cod_Movimiento=C.Referencia
 GROUP BY T.Cod_Movimiento

 SELECT T.*,
 CASE WHEN (R.TotalRecibo> 0.01) AND (T.Total-R.TotalRecibo<=0) THEN 'PAGO COMPLETO' 
 WHEN  (R.TotalRecibo> 0.01) AND (T.Total-R.TotalRecibo>0) THEN 'PAGO PARCIAL'
 ELSE 'SIN PAGOS' END  AS Estado FROM  #TABLA T LEFT JOIN #Recibos R ON T.Cod_Movimiento=R.Cod_Movimiento

 --SELECT Total FROM Comprobante WHERE Referencia=@codMov
 --DECLARE @RECIBOS AS MONEY = (SELECT Total FROM Comprobante WHERE Referencia=@codMov)

--SELECT T.*,ISNULL(T.TOTAL -X.SALDO,0) AS SALDO FROM #TABLA T LEFT JOIN #SALDO X ON T.Cod_Movimiento=X.Cod_Movimiento


GO

-- =============================================
-- SP: MostrarPersona_empresapropia (lÃ­neas 10863-10881)
-- =============================================
CREATE PROCEDURE MostrarPersona_empresapropia
    @Cod_Almacen INT = NULL, -- Filtro opcional
    @PROCESO NVARCHAR(50) = NULL -- Filtro opcional
AS
BEGIN
    BEGIN TRY
       SELECT        dbo.Persona_Proceso_Almacen.Cod_Persona, dbo.Persona_Nuevo.Nom_Persona, dbo.Persona_Proceso_Almacen.Cod_Almacen, dbo.Persona_Proceso_Almacen.PROCESO, dbo.Vehiculo_cliente_nuevo.Codigo, 
                         dbo.Vehiculo_cliente_nuevo.Principal, dbo.Vehiculo_cliente_nuevo.Contacto
FROM            dbo.Persona_Proceso_Almacen INNER JOIN
                         dbo.Persona_Nuevo ON dbo.Persona_Proceso_Almacen.Cod_Persona = dbo.Persona_Nuevo.Cod_Persona INNER JOIN
                         dbo.Vehiculo_cliente_nuevo ON dbo.Persona_Nuevo.Cod_Persona = dbo.Vehiculo_cliente_nuevo.Id_ClientePersona AND dbo.Persona_Nuevo.Cod_Persona = dbo.Vehiculo_cliente_nuevo.Id_ClientePersona
WHERE        (dbo.Persona_Proceso_Almacen.PROCESO = @PROCESO) AND (dbo.Persona_Proceso_Almacen.Cod_Almacen = @Cod_Almacen) AND (dbo.Vehiculo_cliente_nuevo.Principal = 1)
    END TRY
    BEGIN CATCH
        -- Manejo de errores
        SELECT ERROR_MESSAGE() AS Error;
    END CATCH
END


GO

-- =============================================
-- SP: Mostrardeudasxcliente (lÃ­neas 10748-10762)
-- =============================================
CREATE PROCEDURE [dbo].[Mostrardeudasxcliente]
	@Cliente		int
AS
SELECT        dbo.Comprobante.CodComprobante, dbo.TipoDoc.Desc_TipoDoc, dbo.Comprobante.NroSerie, dbo.Comprobante.NroDoc, 
                         dbo.Comprobante.Total / dbo.Movimiento.TCsunat AS Total, dbo.Comprobante.Estado, dbo.Comprobante.Cliente, dbo.Comprobante.TipoComprobante, 
                         dbo.Comprobante.moneda, dbo.Comprobante.Fecha, dbo.Movimiento.TC, dbo.Movimiento.TCsunat, dbo.Movimiento.Cod_Movimiento
FROM            dbo.Comprobante INNER JOIN
                         dbo.TipoDoc ON dbo.Comprobante.TipoComprobante = dbo.TipoDoc.Cod_TipoDoc INNER JOIN
                         dbo.ComprobantePedido ON dbo.Comprobante.CodComprobante = dbo.ComprobantePedido.CodComprobante INNER JOIN
                         dbo.Movimiento ON dbo.ComprobantePedido.CodPedido = dbo.Movimiento.Cod_Movimiento
WHERE        (dbo.TipoDoc.Desc_TipoDoc <> N'Guia Salida') AND (dbo.Comprobante.Pago = 2) AND (dbo.Comprobante.Cliente = @Cliente) AND 
                         (dbo.Comprobante.TipoComprobante IN (1, 2, 3, 6, 9, 10, 12,17)) AND (dbo.Comprobante.Total / dbo.Movimiento.TCsunat > 0)



GO

-- =============================================
-- SP: MOSTRAR_PERSONAresponsable (lÃ­neas 10411-10429)
-- =============================================
CREATE PROCEDURE [dbo].[MOSTRAR_PERSONAresponsable]
	
	@Paciente	        nvarchar(4000)
AS
begin
SELECT        TOP (100) PERCENT dbo.Persona.Cod_Persona, dbo.Persona.Nro_MOZO, dbo.Persona.Nom_Persona, dbo.Persona.Dni_Persona, dbo.Persona.Ruc_Persona, 
                         dbo.Persona.FNac_Personal, dbo.Persona.Login_Persona, dbo.Persona.Pass_Persona, dbo.Persona.Nick_Persona, dbo.Persona.Sexo_Persona, 
                         dbo.Persona.mail_Persona, dbo.Persona.Telefono_Persona, dbo.Persona.Direccion_Persona, dbo.Persona.Cod_TipoPersona, dbo.Persona.cmp_Persona, 
                         dbo.Persona.nextel, dbo.Persona.celular, dbo.Persona.nrocuenta, dbo.Persona.banco, dbo.Persona.LineaCredito_Persona, dbo.Persona.R, dbo.Persona.V1, 
                         dbo.Persona.V2, dbo.Persona.DNIS, dbo.Persona.DNIR, dbo.Persona.DNIV1, dbo.Persona.DNIV2, dbo.Persona.TELEFONOS, dbo.Persona.TELEFONOR, 
                         dbo.Persona.TELEFONOV1, dbo.Persona.TELEFONOV2, dbo.Persona.dvisita, dbo.Persona.dreparto, dbo.Persona.urbanizacion, dbo.Persona.puntos_acumulados, 
                         dbo.Persona.tarjeta, dbo.Persona.fotografia, dbo.Persona.hijos, dbo.Persona.profesion, dbo.Persona.descurb, dbo.Persona.diascred, dbo.vehiculo_cliente.codigo, 
                         dbo.vehiculo_cliente.direccion, dbo.vehiculo_cliente.telefono, dbo.vehiculo_cliente.contacto, dbo.vehiculo_cliente.ubigeo, dbo.vehiculo_cliente.cliente
FROM            dbo.Persona INNER JOIN
                         dbo.vehiculo_cliente ON dbo.Persona.Cod_Persona = dbo.vehiculo_cliente.cliente
WHERE        (dbo.Persona.Nom_Persona LIKE '%' + @Paciente + '%') or (dbo.vehiculo_cliente.contacto LIKE '%' + @Paciente + '%')
ORDER BY dbo.Persona.Nom_Persona
end


GO

-- =============================================
-- SP: mostrar_zona_persona (lÃ­neas 10553-10563)
-- =============================================
CREATE PROCEDURE [dbo].[mostrar_zona_persona]
	@Cod_Persona      int
AS
SELECT        dbo.ZONA.Cod_Zona, dbo.ZONA.Zona, dbo.DISTRITO.Cod_Distrito, dbo.DISTRITO.Desc_Distrito, dbo.PROVINCIA.Cod_Provincia, dbo.PROVINCIA.Provincia, dbo.DEPARTAMENTO.Cod_Departamento, 
                         dbo.DEPARTAMENTO.Desc_Departamento, dbo.Vehiculo_cliente_nuevo.Codigo, dbo.Vehiculo_cliente_nuevo.Id_ClientePersona, dbo.Vehiculo_cliente_nuevo.Contacto
FROM            dbo.PROVINCIA INNER JOIN
                         dbo.DEPARTAMENTO ON dbo.PROVINCIA.Cod_Departamento = dbo.DEPARTAMENTO.Cod_Departamento INNER JOIN
                         dbo.DISTRITO ON dbo.PROVINCIA.Cod_Provincia = dbo.DISTRITO.Cod_Provincia INNER JOIN
                         dbo.ZONA ON dbo.DISTRITO.Cod_Distrito = dbo.ZONA.Cod_Distrito INNER JOIN
                         dbo.Vehiculo_cliente_nuevo ON dbo.ZONA.Cod_Zona = dbo.Vehiculo_cliente_nuevo.Id_Zona INNER JOIN
                         dbo.Persona_Nuevo ON dbo.Vehiculo_cliente_nuevo.Id_ClientePersona = dbo.Persona_Nuevo.Cod_Persona AND dbo.Vehiculo_cliente_nuevo.Id_ClientePersona = dbo.Persona_Nuevo.Cod_Persona

GO

-- =============================================
-- SP: PERSONA_Buscarxdni (lÃ­neas 11935-11952)
-- =============================================
CREATE PROCEDURE [dbo].[PERSONA_Buscarxdni]
	@Dni_Persona	        nvarchar(50)
AS
SELECT     dbo.Persona.Cod_Persona, dbo.Persona.Nro_MOZO, dbo.Persona.Nom_Persona, dbo.Persona.Dni_Persona, dbo.Persona.Ruc_Persona, 
                      dbo.Persona.FNac_Personal, dbo.Persona.Login_Persona, dbo.Persona.Pass_Persona, dbo.Persona.Nick_Persona, dbo.Persona.Sexo_Persona, 
                      dbo.Persona.mail_Persona, dbo.Persona.Telefono_Persona, dbo.Persona.Direccion_Persona, dbo.Persona.Cod_TipoPersona, dbo.Persona.cmp_Persona, 
                      dbo.Persona.contacto, dbo.Persona.nextel, dbo.Persona.celular, dbo.Persona.nrocuenta, dbo.Persona.banco, dbo.Persona.LineaCredito_Persona, dbo.Persona.R, 
                      dbo.Persona.V1, dbo.Persona.V2, dbo.Persona.DNIS, dbo.Persona.DNIR, dbo.Persona.DNIV1, dbo.Persona.DNIV2, dbo.Persona.TELEFONOS, 
                      dbo.Persona.TELEFONOR, dbo.Persona.TELEFONOV1, dbo.Persona.TELEFONOV2, dbo.Persona.dvisita, dbo.Persona.dreparto, dbo.Persona.urbanizacion, 
                      dbo.Persona.puntos_acumulados, dbo.Persona.tarjeta, dbo.Persona.fotografia, dbo.Persona.hijos, dbo.Persona.profesion, dbo.Persona.descurb, dbo.ZONA.Zona, 
                      dbo.DISTRITO.Desc_Distrito, dbo.PROVINCIA.Provincia, dbo.DEPARTAMENTO.Desc_Departamento
FROM         dbo.DEPARTAMENTO INNER JOIN
                      dbo.PROVINCIA ON dbo.DEPARTAMENTO.Cod_Departamento = dbo.PROVINCIA.Cod_Departamento INNER JOIN
                      dbo.DISTRITO ON dbo.PROVINCIA.Cod_Provincia = dbo.DISTRITO.Cod_Provincia INNER JOIN
                      dbo.ZONA ON dbo.DISTRITO.Cod_Distrito = dbo.ZONA.Cod_Distrito INNER JOIN
                      dbo.Persona ON dbo.ZONA.Cod_Zona = dbo.Persona.urbanizacion
WHERE Dni_Persona  like  @Dni_Persona 

GO

-- =============================================
-- SP: Persona_BuscarXfiltro (lÃ­neas 11953-11999)
-- =============================================
CREATE PROCEDURE [dbo].[Persona_BuscarXfiltro]
    @Filtro NVARCHAR(1000) = ''
AS
BEGIN
    SET NOCOUNT ON;
SELECT        TOP (100) PERCENT dbo.Persona_Nuevo.Cod_Persona, dbo.Persona_Nuevo.Nom_Persona, dbo.Persona_Nuevo.Dni_Persona, dbo.Persona_Nuevo.Ruc_Persona, dbo.Persona_Nuevo.Cod_TipoPersona, 
                         dbo.Persona_Nuevo.mail_Persona, dbo.Persona_Nuevo.Pass_Persona, dbo.Persona_Nuevo.Nick_Persona, dbo.Persona_Nuevo.Activo, dbo.Persona_Nuevo.Telefono_Persona, 
                         COUNT(DISTINCT dbo.Ecargos_funciones.Cod_Sucursal) AS Cantidad_Almacenes, dbo.Almacen.Desc_Almacen, dbo.Ecargos_funciones.CargoFuncion
FROM            dbo.Ecargos_funciones INNER JOIN
                         dbo.Almacen ON dbo.Ecargos_funciones.Cod_Sucursal = dbo.Almacen.Cod_Almacen RIGHT OUTER JOIN
                         dbo.Persona_Nuevo ON dbo.Ecargos_funciones.Cod_Persona = dbo.Persona_Nuevo.Cod_Persona
WHERE        (dbo.Ecargos_funciones.Activo = 1)
GROUP BY dbo.Persona_Nuevo.Cod_Persona, dbo.Persona_Nuevo.Nom_Persona, dbo.Persona_Nuevo.Dni_Persona, dbo.Persona_Nuevo.Ruc_Persona, dbo.Persona_Nuevo.Cod_TipoPersona, dbo.Persona_Nuevo.mail_Persona, 
                         dbo.Persona_Nuevo.Pass_Persona, dbo.Persona_Nuevo.Nick_Persona, dbo.Persona_Nuevo.Activo, dbo.Persona_Nuevo.Telefono_Persona, dbo.Almacen.Desc_Almacen, dbo.Ecargos_funciones.CargoFuncion
ORDER BY dbo.Persona_Nuevo.Nom_Persona
END;
  --  SELECT 
  --      Persona_Nuevo.Cod_Persona, 
  --      Persona_Nuevo.Nom_Persona, 
  --      Ecargos_funciones.CargoFuncion, 
  --      Persona_Nuevo.Dni_Persona, 
  --      Persona_Nuevo.Ruc_Persona, 
  --      Persona_Nuevo.Cod_TipoPersona, 
  --      Persona_Nuevo.mail_Persona, 
  --      Persona_Nuevo.Login_Persona, 
  --      Persona_Nuevo.Pass_Persona, 
  --      Persona_Nuevo.Nick_Persona, 
  --      Persona_Nuevo.Activo, 
  --      Ecargos_funciones.Id_CargoFuncion, 
  --      Direcciones_NoClientes.Direccion_Linea_1, 
  --      Persona_Nuevo.Telefono_Persona, 
  --      Almacen.Desc_Almacen, 
  --      Almacen.Cod_Almacen,
		--Ecargos_funciones.Activo
  --  FROM Persona_Nuevo
  --  INNER JOIN Ecargos_funciones ON Persona_Nuevo.Cod_Persona = Ecargos_funciones.Cod_Persona
  --  INNER JOIN Almacen ON Ecargos_funciones.Cod_Sucursal = Almacen.Cod_Almacen
  --  LEFT OUTER JOIN Direcciones_NoClientes ON Persona_Nuevo.Cod_Persona = Direcciones_NoClientes.Cod_Persona
  --  WHERE 
  --      @Filtro = '' OR  
  --      --Persona_Nuevo.Nom_Persona LIKE '%' + @Filtro + '%' OR 
  --      --Ecargos_funciones.CargoFuncion LIKE '%' + @Filtro + '%' OR 
  --      --Almacen.Desc_Almacen LIKE '%' + @Filtro + '%' or
		--Ecargos_funciones.Activo = 1
  --  ORDER BY Persona_Nuevo.Nom_Persona;
--END;


GO

-- =============================================
-- SP: PERSONA_Buscarxcod (lÃ­neas 11919-11934)
-- =============================================
CREATE PROCEDURE [dbo].[PERSONA_Buscarxcod]
	@Cod_Persona	    INT
AS
SELECT        dbo.Persona.Cod_Persona, dbo.Persona.Nro_MOZO, dbo.Persona.Nom_Persona, dbo.Persona.Dni_Persona, dbo.Persona.Ruc_Persona, dbo.Persona.FNac_Personal, dbo.Persona.Login_Persona, dbo.Persona.Pass_Persona, 
                         dbo.Persona.Nick_Persona, dbo.Persona.Sexo_Persona, dbo.Persona.mail_Persona, dbo.Persona.Telefono_Persona, dbo.Persona.Direccion_Persona, dbo.Persona.Cod_TipoPersona, dbo.Persona.cmp_Persona, 
                         dbo.Persona.contacto, dbo.Persona.nextel, dbo.Persona.celular, dbo.Persona.nrocuenta, dbo.Persona.banco, dbo.Persona.LineaCredito_Persona, dbo.Persona.R, dbo.Persona.V1, dbo.Persona.V2, dbo.Persona.DNIS, 
                         dbo.Persona.DNIR, dbo.Persona.DNIV1, dbo.Persona.DNIV2, dbo.Persona.TELEFONOS, dbo.Persona.TELEFONOR, dbo.Persona.TELEFONOV1, dbo.Persona.TELEFONOV2, dbo.Persona.dvisita, dbo.Persona.dreparto, 
                         dbo.Persona.urbanizacion, dbo.Persona.puntos_acumulados, dbo.Persona.tarjeta, dbo.Persona.fotografia, dbo.Persona.hijos, dbo.Persona.profesion, dbo.Persona.descurb, dbo.ZONA.Zona, dbo.DISTRITO.Desc_Distrito, 
                         dbo.PROVINCIA.Provincia, dbo.DEPARTAMENTO.Desc_Departamento, dbo.Persona.diascred, DATEADD(day, dbo.Persona.diascred, GETDATE()) AS fecha_pago, dbo.Persona.exento
FROM            dbo.DEPARTAMENTO INNER JOIN
                         dbo.PROVINCIA ON dbo.DEPARTAMENTO.Cod_Departamento = dbo.PROVINCIA.Cod_Departamento INNER JOIN
                         dbo.DISTRITO ON dbo.PROVINCIA.Cod_Provincia = dbo.DISTRITO.Cod_Provincia INNER JOIN
                         dbo.ZONA ON dbo.DISTRITO.Cod_Distrito = dbo.ZONA.Cod_Distrito RIGHT OUTER JOIN
                         dbo.Persona ON dbo.ZONA.Cod_Zona = dbo.Persona.urbanizacion
WHERE        (dbo.Persona.Cod_Persona LIKE @Cod_Persona)


GO

-- =============================================
-- SP: ObtenerPuntoEntregaCompleto (lÃ­neas 11322-11370)
-- =============================================
CREATE PROCEDURE dbo.ObtenerPuntoEntregaCompleto
    @IdVehiculo INT
AS
BEGIN
    SET NOCOUNT ON;

    SELECT 
        v.Codigo,
        v.Id_ClientePersona,
        v.NombrePunto,
        v.Contacto,
        v.Telefono,
        v.Correoresp,
        v.Principal,
        v.Id_Direccion,

        d.Linea1,
        d.Linea2,
        d.Codigo_Postal,
        d.Observaciones,
        d.Street_Name,
        d.Street_Number,
        d.Admin_Area_1,
        d.Admin_Area_2,
        d.Localidad,
        d.Id_Localidad,

        loc.Id_Municipio,
        mun.Id_Provincia,
        prov.Id_ComunidadAutonoma,

        loc.Nombre AS LocalidadNombre,
        mun.Nombre AS Municipio,
        prov.Nombre AS Provincia,
        ca.Nombre AS Comunidad

    FROM Vehiculo_cliente_nuevo v
    LEFT JOIN dbo.Direccion d
        ON v.Id_Direccion = d.Id_Direccion
    LEFT JOIN dbo.CP_Localidad loc
        ON d.Id_Localidad = loc.Id_Localidad
    LEFT JOIN dbo.CP_Municipio mun
        ON loc.Id_Municipio = mun.Id_Municipio
    LEFT JOIN dbo.CP_Provincia prov
        ON mun.Id_Provincia = prov.Id_Provincia
    LEFT JOIN dbo.CP_Comunidad_Autonoma ca
        ON prov.Id_ComunidadAutonoma = ca.Id_ComunidadAutonoma
    WHERE v.Codigo = @IdVehiculo
END

GO

-- =============================================
-- SP: Persona_BuscarXcargo (lÃ­neas 11871-11918)
-- =============================================
CREATE PROCEDURE [dbo].[Persona_BuscarXcargo]
    @Desc_Almacen NVARCHAR(1000) = NULL
AS
BEGIN
    SET NOCOUNT ON;

    SELECT DISTINCT
        Persona_Nuevo.Cod_Persona,
        Persona_Nuevo.Nom_Persona,
        Ecargos_funciones.CargoFuncion,
        Persona_Nuevo.Dni_Persona,
        Persona_Nuevo.Ruc_Persona,
        Persona_Nuevo.Cod_TipoPersona,
        Persona_Nuevo.mail_Persona,
        Persona_Nuevo.Login_Persona,
        Persona_Nuevo.Pass_Persona,
        Persona_Nuevo.Nick_Persona,
        Persona_Nuevo.Activo,
        Ecargos_funciones.Id_CargoFuncion,
        Direcciones_NoClientes.Direccion_Linea_1,
        Persona_Nuevo.Telefono_Persona,
        Almacen.Desc_Almacen,
        Almacen.Cod_Almacen,
        Direcciones_NoClientes.Id_Direccion,
        Persona_Nuevo.Sexo_Persona,
        Persona_Nuevo.FNac_Personal,
        Ecargos_funciones.Fecha_Asignacion

    FROM Persona_Nuevo
    INNER JOIN Ecargos_funciones 
        ON Persona_Nuevo.Cod_Persona = Ecargos_funciones.Cod_Persona
    INNER JOIN Almacen 
        ON Ecargos_funciones.Cod_Sucursal = Almacen.Cod_Almacen
    LEFT OUTER JOIN Direcciones_NoClientes 
        ON Persona_Nuevo.Cod_Persona = Direcciones_NoClientes.Cod_Persona
    WHERE 
        Persona_Nuevo.Activo = 1
        AND Ecargos_funciones.Activo = 1
        AND (
            @Desc_Almacen IS NULL 
            OR LTRIM(RTRIM(@Desc_Almacen)) = '' 
            OR Almacen.Desc_Almacen = @Desc_Almacen
        )
    ORDER BY Persona_Nuevo.Nom_Persona;
END




GO

-- =============================================
-- SP: SugerirRuta_MasCercana_PorPuntoEntrega (lÃ­neas 21469-21513)
-- =============================================
CREATE PROCEDURE dbo.SugerirRuta_MasCercana_PorPuntoEntrega
  @Id_PuntoEntrega INT,
  @DiaSemana TINYINT = NULL,
  @TopN INT = 3
AS
BEGIN
  SET NOCOUNT ON;

  DECLARE @Lat DECIMAL(9,6), @Lon DECIMAL(9,6);

  SELECT @Lat = D.Latitud, @Lon = D.Longitud
  FROM dbo.Vehiculo_cliente_nuevo AS V
  JOIN dbo.Direccion AS D
    ON D.Id_Direccion = V.Id_Direccion
  WHERE V.Codigo = @Id_PuntoEntrega;

  IF @Lat IS NULL OR @Lon IS NULL
  BEGIN
    RAISERROR('El punto de entrega no tiene coordenadas.', 16, 1);
    RETURN;
  END

  ;WITH Cand AS (
    SELECT C.Id_Ruta, C.CentroLat, C.CentroLon
    FROM dbo.vw_Ruta_Centroides AS C
    WHERE (@DiaSemana IS NULL OR EXISTS (
             SELECT 1
             FROM dbo.Ruta_DiaSemana AS RD
             WHERE RD.Id_Ruta = C.Id_Ruta 
             AND RD.DiaSemana = @DiaSemana
           ))
  )

  SELECT TOP (@TopN)
         R.Id_Ruta,
         R.Nombre,
         R.Descripcion,
         dbo.fn_HaversineKm(@Lat, @Lon, C.CentroLat, C.CentroLon) AS DistanciaKm,
         C.CentroLat,
         C.CentroLon
  FROM Cand AS C
  JOIN dbo.Ruta AS R ON R.Id_Ruta = C.Id_Ruta
  ORDER BY DistanciaKm ASC, R.Nombre;

END

GO

-- =============================================
-- SP: TARIFARIOPERSONA_Insertar (lÃ­neas 21514-21609)
-- =============================================
CREATE PROCEDURE [dbo].[TARIFARIOPERSONA_Insertar]
    @CODCLIENTE INT,
    @CODPRODUCTO INT,
    @precio MONEY,
    @PrecioBase MONEY = NULL,
    @PorcentajeDescuento MONEY = NULL,
    @PrecioFinal MONEY = NULL,
    @FechaCotizacion DATETIME = NULL,
    @CodDetalleMov INT = NULL
AS 
BEGIN
    SET NOCOUNT ON;

    -- Verificar si ya existe un registro con los mismos valores
    IF NOT EXISTS (
        SELECT 1
        FROM Tarifa_cliente
        WHERE CODCLIENTE = @CODCLIENTE
          AND CODPRODUCTO = @CODPRODUCTO
          AND precio = @precio
          AND (PrecioBase = @PrecioBase OR (PrecioBase IS NULL AND @PrecioBase IS NULL))
          AND (PorcentajeDescuento = @PorcentajeDescuento OR (PorcentajeDescuento IS NULL AND @PorcentajeDescuento IS NULL))
          AND (PrecioFinal = @PrecioFinal OR (PrecioFinal IS NULL AND @PrecioFinal IS NULL))
          AND CodDetalleMov = @CodDetalleMov
    )
    BEGIN
        -- Insertar un nuevo registro de precio para el cliente y producto
        INSERT INTO Tarifa_cliente (CODCLIENTE, CODPRODUCTO, precio, PrecioBase, PorcentajeDescuento, PrecioFinal, FechaCotizacion, CodDetalleMov, FechaInicio)
        VALUES 
        (
            @CODCLIENTE, 
            @CODPRODUCTO, 
            @precio, 
            @PrecioBase, 
            @PorcentajeDescuento, 
            @PrecioFinal, 
            @FechaCotizacion, 
            @CodDetalleMov, 
            GETDATE()
        );

        -- Manejo de errores opcional
        IF @@ERROR <> 0
        BEGIN
            -- Puedes manejar el error aquí, como registrar el error o lanzar una excepción
            RAISERROR('Error al insertar la tarifa', 16, 1);
        END
    END
    ELSE
    BEGIN
        PRINT 'El registro ya existe y no se realizará la inserción.';
    END
END;

--CREATE PROCEDURE [dbo].[TARIFARIOPERSONA_Insertar]
--    @CODCLIENTE INT,
--    @CODPRODUCTO INT,
--    @precio MONEY,
--    @PrecioBase MONEY = NULL,
--    @PorcentajeDescuento MONEY = NULL,
--    @PrecioFinal MONEY = NULL,
--    @FechaCotizacion DATETIME = NULL,
    
--@CodDetalleMov INT = NULL
--AS 
--BEGIN
--    SET NOCOUNT ON;

--    -- Insertar un nuevo registro de precio para el cliente y producto
--    INSERT INTO Tarifa_cliente (CODCLIENTE, CODPRODUCTO, precio, PrecioBase, PorcentajeDescuento, PrecioFinal, FechaCotizacion,
-- CodDetalleMov, FechaInicio)
--    VALUES 
--    (
--        @CODCLIENTE, 
--        @CODPRODUCTO, 
--        @precio, 
--        @PrecioBase, 
--        @PorcentajeDescuento, 
--        @PrecioFinal, 
--        @FechaCotizacion, 
--        @CodDetalleMov, 
--        GETDATE()
--  -- Fecha de inicio es la fecha actual
--    );

--    -- Manejo de errores opcional
--    IF @@ERROR <> 0
--    BEGIN
--        -- Puedes manejar el error aquí, como registrar el error o lanzar una excepción
--        RAISERROR('Error al insertar la tarifa', 16, 1)
--;
--    END
--END




GO

-- =============================================
-- SP: SucursalGeo_SetDefaults (lÃ­neas 21373-21399)
-- =============================================
CREATE PROCEDURE dbo.SucursalGeo_SetDefaults
  @Id_Sucursal          INT,
  @Id_ComunidadAutonoma INT = NULL,
  @Id_Provincia         INT = NULL,
  @Id_Municipio         INT = NULL,
  @Id_Localidad         INT = NULL,
  @Codigo_Postal        CHAR(5) = NULL,
  @Usuario              NVARCHAR(50) = NULL
AS
BEGIN
  SET NOCOUNT ON;

  MERGE dbo.Sucursal_Geografia_Default AS T
  USING (SELECT @Id_Sucursal AS Id_Sucursal) AS S
     ON T.Id_Sucursal = S.Id_Sucursal
  WHEN MATCHED THEN
    UPDATE SET Id_ComunidadAutonoma=@Id_ComunidadAutonoma,
               Id_Provincia=@Id_Provincia,
               Id_Municipio=@Id_Municipio,
               Id_Localidad=@Id_Localidad,
               Codigo_Postal=@Codigo_Postal,
               Usuario=@Usuario,
               FechaMod=SYSDATETIME()
  WHEN NOT MATCHED THEN
    INSERT (Id_Sucursal, Id_ComunidadAutonoma, Id_Provincia, Id_Municipio, Id_Localidad, Codigo_Postal, Usuario)
    VALUES (@Id_Sucursal, @Id_ComunidadAutonoma, @Id_Provincia, @Id_Municipio, @Id_Localidad, @Codigo_Postal, @Usuario);
END

GO

-- =============================================
-- SP: sp_PuntoEntrega_ListarPorCliente (lÃ­neas 20665-20675)
-- =============================================
-- Lista por cliente
CREATE PROCEDURE dbo.sp_PuntoEntrega_ListarPorCliente
  @Id_Cliente INT
AS
BEGIN
  SET NOCOUNT ON;
  SELECT * FROM dbo.vw_PuntosEntrega_Canonico
   WHERE Id_Cliente = @Id_Cliente
   ORDER BY EsPrincipal DESC, NombrePunto, Id_PuntoEntrega;
END


GO

-- =============================================
-- SP: SucursalGeo_GetDefaults (lÃ­neas 21364-21372)
-- =============================================
CREATE PROCEDURE dbo.SucursalGeo_GetDefaults
  @Id_Sucursal INT
AS
BEGIN
  SET NOCOUNT ON;
  SELECT *
  FROM dbo.Sucursal_Geografia_Default
  WHERE Id_Sucursal = @Id_Sucursal;
END

GO

-- =============================================
-- SP: Vehiculo_cliente_nuevo_ActualizarDireccion (lÃ­neas 24653-24663)
-- =============================================
CREATE PROCEDURE dbo.Vehiculo_cliente_nuevo_ActualizarDireccion
    @Codigo INT,
    @Direccion NVARCHAR(300)
AS
BEGIN
    SET NOCOUNT ON;

    UPDATE dbo.Vehiculo_cliente_nuevo
    SET Direccion = @Direccion
    WHERE Codigo = @Codigo;
END

GO

-- =============================================
-- SP: Vehiculo_cliente_nuevo_SetPrincipal (lÃ­neas 24664-24676)
-- =============================================
CREATE PROCEDURE dbo.Vehiculo_cliente_nuevo_SetPrincipal
    @Codigo INT,
    @IdCliente INT
AS
BEGIN
    UPDATE Vehiculo_cliente_nuevo
    SET Principal = 0
    WHERE Id_ClientePersona = @IdCliente

    UPDATE Vehiculo_cliente_nuevo
    SET Principal = 1
    WHERE Codigo = @Codigo
END

GO

-- =============================================
-- SP: vehiculo_cliente_Buscarxcodigo (lÃ­neas 24644-24652)
-- =============================================
CREATE  PROCEDURE [dbo].[vehiculo_cliente_Buscarxcodigo]
@codigo	int	

AS
SELECT        dbo.Vehiculo_cliente_nuevo.Codigo, dbo.Vehiculo_cliente_nuevo.Direccion, dbo.Vehiculo_cliente_nuevo.Telefono, dbo.Vehiculo_cliente_nuevo.Contacto, dbo.Vehiculo_cliente_nuevo.ubigeo, 
                         dbo.Vehiculo_cliente_nuevo.Id_ClientePersona, dbo.Persona_Nuevo.Nom_Persona, ISNULL(dbo.Vehiculo_cliente_nuevo.garantia, N'Sin garantia') AS garantia, dbo.Vehiculo_cliente_nuevo.Correoresp
FROM            dbo.Vehiculo_cliente_nuevo INNER JOIN
                         dbo.Persona_Nuevo ON dbo.Vehiculo_cliente_nuevo.Id_ClientePersona = dbo.Persona_Nuevo.Cod_Persona
WHERE        (dbo.Vehiculo_cliente_nuevo.Codigo = @codigo)

GO

-- =============================================
-- SP: ValidarIntegridadClienteSucursal (lÃ­neas 24580-24606)
-- =============================================
create PROCEDURE ValidarIntegridadClienteSucursal
AS
BEGIN
    SET NOCOUNT ON;

    -- Validar clientes sin registros válidos en Vehiculo_cliente_nuevo
    SELECT 
        Cliente_Sucursal.Id_Cliente,
        Vehiculo_cliente_nuevo.Contacto,
        Persona_Nuevo.Nom_Persona
    FROM Cliente_Sucursal
    LEFT JOIN Vehiculo_cliente_nuevo 
        ON Cliente_Sucursal.Id_Cliente = Vehiculo_cliente_nuevo.Codigo
    LEFT JOIN Persona_Nuevo 
        ON Vehiculo_cliente_nuevo.Id_ClientePersona = Persona_Nuevo.Cod_Persona
    WHERE Vehiculo_cliente_nuevo.Codigo IS NULL;

    -- Validar sucursales sin registros válidos en Almacen
    SELECT 
        Cliente_Sucursal.Id_Sucursal,
        Almacen.Desc_Almacen
    FROM Cliente_Sucursal
    LEFT JOIN Almacen 
        ON Cliente_Sucursal.Id_Sucursal = Almacen.Cod_Almacen
    WHERE Almacen.Cod_Almacen IS NULL;
END;


GO

-- =============================================
-- SP: vehiculo_cliente_Buscarxcliente (lÃ­neas 24607-24643)
-- =============================================
CREATE PROCEDURE [dbo].[vehiculo_cliente_Buscarxcliente]
    @Id_ClientePersona INT = NULL   -- si NULL o <=0, trae todos
AS
BEGIN
    SET NOCOUNT ON;

    SELECT
        V.Codigo AS EstablecimientoID,
        V.NombrePunto,
        V.Direccion,-- = COALESCE(D.Linea1, V.Direccion),
        V.ubigeo,
        Zona = Z.Zona,
        CONTACTO = V.Contacto,
        V.Telefono,
        V.Principal,
        Estado = V.Activo,
        V.Correoresp,
        V.Envio,  -- es bandera de envío de correo (no logística)

        Nombre_Agente = PN.Nom_Persona,
        A.Comision,
        Cod_Persona = PN.Cod_Persona,
		D.Id_Direccion,
		A.Activo
    FROM dbo.Vehiculo_cliente_nuevo AS V
    LEFT JOIN dbo.Direccion           AS D  ON D.Id_Direccion   = V.Id_Direccion
    LEFT JOIN dbo.ZONA              AS Z  ON Z.Cod_Zona      = V.Id_Zona
    LEFT JOIN dbo.Agentes_Sucursal    AS A  ON A.Cod_Responsable= V.Codigo
    LEFT JOIN dbo.Ecargos_funciones   AS EF ON EF.Id_CargoFuncion= A.Id_CargoFuncion
    LEFT JOIN dbo.Persona_Nuevo       AS PN ON PN.Cod_Persona   = EF.Cod_Persona

   WHERE 
    (@Id_ClientePersona IS NULL OR @Id_ClientePersona <= 0 OR V.Id_ClientePersona = @Id_ClientePersona)
    AND (A.Activo = 1 OR A.Activo IS NULL)
    ORDER BY V.Principal DESC, V.NombrePunto, Direccion;
END


GO

-- =============================================
-- SP: sp_Persona_ActividadFiscal_Guardar (lÃ­neas 19905-20007)
-- =============================================
create PROCEDURE sp_Persona_ActividadFiscal_Guardar
    @CodPersona INT,
    @PaisCodigo VARCHAR(5),
    @TipoIdentificacion VARCHAR(20),
    @NumeroIdentificacion VARCHAR(30),
    @CodigoActividad VARCHAR(20),
    @DescripcionActividad NVARCHAR(300),
    @EsPrincipal BIT,
    @Fuente VARCHAR(50)
AS
BEGIN
    SET NOCOUNT ON;

    BEGIN TRY

        BEGIN TRAN

        -- ?? EVITAR DUPLICADO EXACTO
        IF EXISTS (
            SELECT 1
            FROM Persona_ActividadFiscal
            WHERE CodPersona = @CodPersona
            AND CodigoActividad = @CodigoActividad
            AND Vigente = 1
        )
        BEGIN
            -- Ya existe ? solo marcar como principal si aplica
            IF @EsPrincipal = 1
            BEGIN
                UPDATE Persona_ActividadFiscal
                SET EsPrincipal = 0
                WHERE CodPersona = @CodPersona

                UPDATE Persona_ActividadFiscal
                SET EsPrincipal = 1
                WHERE CodPersona = @CodPersona
                AND CodigoActividad = @CodigoActividad
                AND Vigente = 1
            END
        END
        ELSE
        BEGIN
            -- ?? Si es principal ? quitar anteriores
            IF @EsPrincipal = 1
            BEGIN
                UPDATE Persona_ActividadFiscal
                SET EsPrincipal = 0
                WHERE CodPersona = @CodPersona
            END

            -- ?? Insertar nuevo
            INSERT INTO Persona_ActividadFiscal
            (
                CodPersona,
                PaisCodigo,
                TipoIdentificacion,
                NumeroIdentificacion,
                CodigoActividad,
                DescripcionActividad,
                EsPrincipal,
                Vigente,
                Fuente,
                FechaConsulta,
                UsuarioConsulta
            )
            VALUES
            (
                @CodPersona,
                @PaisCodigo,
                @TipoIdentificacion,
                @NumeroIdentificacion,
                @CodigoActividad,
                @DescripcionActividad,
                @EsPrincipal,
                1,
                @Fuente,
                GETDATE(),
                SYSTEM_USER
            )
        END

        -- ?? ACTUALIZAR PERSONA
        IF @EsPrincipal = 1
        BEGIN
            UPDATE Persona_Nuevo
            SET 
                CodigoActividadPrincipal = @CodigoActividad,
                DescripcionActividadPrincipal = @DescripcionActividad,
                ActividadValidada = 1,
                FechaValidacionActividad = GETDATE(),
                FuenteValidacionActividad = @Fuente
            WHERE Cod_Persona = @CodPersona
        END

        COMMIT

    END TRY
    BEGIN CATCH
        ROLLBACK
        RAISERROR('Error en sp_Persona_ActividadFiscal_Guardar',16,1)
    END CATCH

END

GO

-- =============================================
-- SP: sp_Persona_ActividadFiscal_ObtenerPrincipal (lÃ­neas 20008-20023)
-- =============================================
CREATE PROCEDURE sp_Persona_ActividadFiscal_ObtenerPrincipal
    @CodPersona INT
AS
BEGIN
    SET NOCOUNT ON;

    SELECT TOP 1
        CodigoActividad,
        DescripcionActividad
    FROM Persona_ActividadFiscal
    WHERE CodPersona = @CodPersona
    AND EsPrincipal = 1
    AND Vigente = 1
    ORDER BY FechaConsulta DESC

END

GO

-- =============================================
-- SP: sp_Establecimiento_ActualizarEnvio (lÃ­neas 18048-18062)
-- =============================================
create PROCEDURE dbo.sp_Establecimiento_ActualizarEnvio
(
    @Codigo INT,
    @Envio BIT
)
AS
BEGIN
    SET NOCOUNT ON;

    UPDATE dbo.Vehiculo_cliente_nuevo
    SET Envio = @Envio,
        UsuarioMod = SYSTEM_USER,
        FechaMod = SYSDATETIME()
    WHERE Codigo = @Codigo;
END

GO

-- =============================================
-- SP: sp_DatoBancario_ListarPorCliente (lÃ­neas 17371-17380)
-- =============================================
CREATE PROCEDURE sp_DatoBancario_ListarPorCliente
    @Id_ClientePersona INT
AS
BEGIN
    SELECT *
    FROM Datos_Bancarios
    WHERE Id_ClientePersona = @Id_ClientePersona
    ORDER BY Activo DESC, Fecha_Alta DESC
END


GO

-- =============================================
-- SP: sp_Direccion_Fiscal_Actualizar (lÃ­neas 17743-17785)
-- =============================================
CREATE PROCEDURE sp_Direccion_Fiscal_Actualizar
    @Id_Direccion INT,
    @Linea1 NVARCHAR(200),
    @Linea2 NVARCHAR(200),
    @Codigo_Postal NVARCHAR(12),
    @Id_Localidad INT,
    @Ubigeo NVARCHAR(6),
    @Latitud FLOAT,
    @Longitud FLOAT,
    @Observaciones NVARCHAR(200),

    -- ?? NUEVOS
    @Street_Name NVARCHAR(160),
    @Street_Number NVARCHAR(20),
    @Admin_Area_1 NVARCHAR(120),
    @Admin_Area_2 NVARCHAR(120),
    @Localidad NVARCHAR(120)
AS
BEGIN

UPDATE dbo.Direccion
SET
    Linea1 = @Linea1,
    Linea2 = @Linea2,
    Codigo_Postal = @Codigo_Postal,
    Id_Localidad = @Id_Localidad,
    Ubigeo = @Ubigeo,
    Latitud = @Latitud,
    Longitud = @Longitud,
    Observaciones = @Observaciones,

    -- ?? NUEVO
    Street_Name = @Street_Name,


    Street_Number = @Street_Number,
    Admin_Area_1 = @Admin_Area_1,
    Admin_Area_2 = @Admin_Area_2,
    Localidad = @Localidad

WHERE Id_Direccion = @Id_Direccion

END

GO

-- =============================================
-- SP: sp_PuntoEntrega_EstablecerPrincipal (lÃ­neas 20519-20599)
-- =============================================
CREATE PROCEDURE dbo.sp_PuntoEntrega_EstablecerPrincipal
(
    @Id_PuntoEntrega INT
)
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @Id_Cliente INT;
    DECLARE @Id_Direccion INT;

    BEGIN TRY
        BEGIN TRAN;

        -- ============================
        -- VALIDAR QUE EXISTE
        -- ============================
        IF NOT EXISTS (
            SELECT 1 
            FROM dbo.Vehiculo_cliente_nuevo 
            WHERE Codigo = @Id_PuntoEntrega
        )
        BEGIN
            RAISERROR('El punto de entrega no existe', 16, 1);
            ROLLBACK;
            RETURN;
        END

        -- ============================
        -- OBTENER CLIENTE Y DIRECCIÓN
        -- ============================
        SELECT 
            @Id_Cliente = Id_ClientePersona,
            @Id_Direccion = Id_Direccion
        FROM dbo.Vehiculo_cliente_nuevo
        WHERE Codigo = @Id_PuntoEntrega;

        -- ============================
        -- VALIDAR DIRECCIÓN
        -- ============================
        IF @Id_Direccion IS NULL
        BEGIN
            RAISERROR('El punto no tiene dirección válida', 16, 1);
            ROLLBACK;
            RETURN;
        END

        -- ============================
        -- QUITAR PRINCIPAL ACTUAL
        -- ============================
        UPDATE dbo.Vehiculo_cliente_nuevo
        SET Principal = 0
        WHERE Id_ClientePersona = @Id_Cliente
          AND Principal = 1;

        -- ============================
        -- SET NUEVO PRINCIPAL
        -- ============================
        UPDATE dbo.Vehiculo_cliente_nuevo
        SET Principal = 1,
            UsuarioMod = SYSTEM_USER,
            FechaMod = SYSDATETIME()
        WHERE Codigo = @Id_PuntoEntrega;

        -- ============================
        -- SINCRONIZAR DIRECCIÓN FISCAL
        -- ============================
        UPDATE dbo.Persona_Nuevo
        SET Id_Direccion_Fiscal = @Id_Direccion
        WHERE Cod_Persona = @Id_Cliente;

        COMMIT;

    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK;

        THROW;
    END CATCH
END

GO

-- =============================================
-- SP: sp_PuntoEntrega_Insertar (lÃ­neas 20600-20664)
-- =============================================
CREATE PROCEDURE dbo.sp_PuntoEntrega_Insertar
  @Id_ClientePersona INT,
  @NombrePunto     NVARCHAR(100) = NULL,
  @Linea1          NVARCHAR(200),
  @Codigo_Postal   NVARCHAR(12)  = NULL,
  @Id_Localidad    INT           = NULL,
  @Ubigeo          NVARCHAR(6)   = NULL,
  @Latitud         FLOAT         = NULL,
  @Longitud        FLOAT         = NULL,
  @Contacto        NVARCHAR(100) = NULL,
  @Telefono        NVARCHAR(50)  = NULL,
  @Correoresp      NVARCHAR(100) = NULL,
  @VentanaHorario  NVARCHAR(50)  = NULL,
  @Indicaciones    NVARCHAR(200) = NULL,
  @Id_RutaAsignada INT           = NULL,
  @EsPrincipal     BIT           = 0,
  @Estado          BIT           = 1,
  @Usuario         NVARCHAR(50)  = NULL,
  @Codigo          INT           OUTPUT          -- devuelve el nuevo V.Codigo
AS
BEGIN
  SET NOCOUNT ON;
  DECLARE @Id_Direccion INT;

  BEGIN TRY
    BEGIN TRAN;

    -- Si marcarás este como principal, apaga el anterior del cliente (evita UQ de principal)
    IF @EsPrincipal = 1
    BEGIN
      UPDATE dbo.Vehiculo_cliente_nuevo
         SET Principal = 0
       WHERE Id_ClientePersona = @Id_ClientePersona
         AND Principal = 1;
    END

    -- Crea Dirección (solo columnas relevantes; no usamos dbo.ZONA)
    INSERT INTO dbo.Direccion (Linea1, Codigo_Postal, Id_Localidad, Ubigeo, Latitud, Longitud, Observaciones)
    VALUES (@Linea1, @Codigo_Postal, @Id_Localidad, @Ubigeo, @Latitud, @Longitud, @Indicaciones);

    SET @Id_Direccion = SCOPE_IDENTITY();

    -- Crea Punto de entrega
    INSERT INTO dbo.Vehiculo_cliente_nuevo
    ( Id_ClientePersona, Direccion, Contacto, Telefono, Correoresp,
      NombrePunto, VentanaHorario, Indicaciones, Id_RutaAsignada,
      Principal, Activo, Fecha_Registro, Id_Direccion, ubigeo )
    VALUES
    ( @Id_ClientePersona, @Linea1, @Contacto, @Telefono, @Correoresp,
      @NombrePunto, @VentanaHorario, @Indicaciones, @Id_RutaAsignada,
      @EsPrincipal, @Estado, SYSDATETIME(), @Id_Direccion, @Ubigeo );

    SET @Codigo = SCOPE_IDENTITY();

    COMMIT TRAN;

    -- Devuelvo por SELECT (útil si no usas OUTPUT en cliente)
    SELECT @Codigo AS EstablecimientoID, @Id_Direccion AS Id_Direccion;
  END TRY
  BEGIN CATCH
    IF @@TRANCOUNT > 0 ROLLBACK TRAN;
    THROW;
  END CATCH
END


GO

-- =============================================
-- SP: sp_PuntoEntrega_Anular (lÃ­neas 20507-20518)
-- =============================================
-- Anular (inactivar)
CREATE PROCEDURE dbo.sp_PuntoEntrega_Anular
  @Id_PuntoEntrega INT,
  @Usuario NVARCHAR(50) = NULL
AS
BEGIN
  UPDATE dbo.Vehiculo_cliente_nuevo
     SET Activo=0, UsuarioMod=@Usuario, FechaMod=SYSDATETIME()
   WHERE Codigo=@Id_PuntoEntrega;
END


GO

-- =============================================
-- SP: SP_PERSONA_MOSTRARMOZO (lÃ­neas 20024-20031)
-- =============================================
CREATE  PROCEDURE dbo.SP_PERSONA_MOSTRARMOZO
	@Nro_MOZO	        nvarchar(50)
AS
SELECT   *     
FROM  PERSONA
                      
WHERE Nro_MOZO  like  @Nro_MOZO


GO

-- =============================================
-- SP: sp_PuntoEntrega_Actualizar (lÃ­neas 20441-20506)
-- =============================================
CREATE PROCEDURE dbo.sp_PuntoEntrega_Actualizar
  @Id_PuntoEntrega INT,
  @NombrePunto     NVARCHAR(100) = NULL,
  @Linea1          NVARCHAR(200) = NULL,
  @Codigo_Postal   NVARCHAR(12)  = NULL,
  @Id_Zona         INT           = NULL,   -- sigue igual (compatibilidad)
  @Ubigeo          NVARCHAR(6)   = NULL,
  @Latitud         FLOAT         = NULL,
  @Longitud        FLOAT         = NULL,
  @DireccionLegacy NVARCHAR(200) = NULL,
  @Contacto        NVARCHAR(100) = NULL,
  @Telefono        NVARCHAR(50)  = NULL,
  @VentanaHorario  NVARCHAR(50)  = NULL,
  @Indicaciones    NVARCHAR(200) = NULL,
  @Id_RutaAsignada INT           = NULL,
  @EsPrincipal     BIT           = NULL,
  @Estado          BIT           = NULL,
  @Usuario         NVARCHAR(50)  = NULL,
  @Id_Localidad    INT           = NULL    -- << NUEVO
AS
BEGIN
  SET NOCOUNT ON;

  DECLARE @Id_Cliente INT, @Id_Direccion INT;
  SELECT @Id_Cliente = Id_ClientePersona, @Id_Direccion = Id_Direccion
  FROM dbo.Vehiculo_cliente_nuevo
  WHERE Codigo = @Id_PuntoEntrega;

  IF @EsPrincipal = 1
    UPDATE dbo.Vehiculo_cliente_nuevo
       SET Principal=0
     WHERE Id_ClientePersona=@Id_Cliente AND Principal=1 AND Codigo<>@Id_PuntoEntrega;

  -- Actualiza Direccion
  IF @Id_Direccion IS NOT NULL
  BEGIN
    UPDATE dbo.Direccion
       SET Linea1        = COALESCE(@Linea1, Linea1),
           Codigo_Postal = COALESCE(@Codigo_Postal, Codigo_Postal),
           Id_Zona       = COALESCE(@Id_Zona, Id_Zona),     -- compatibilidad
           Ubigeo        = COALESCE(@Ubigeo, Ubigeo),
           Latitud       = COALESCE(@Latitud, Latitud),
           Longitud      = COALESCE(@Longitud, Longitud),
           Observaciones = COALESCE(@Indicaciones, Observaciones),
           Id_Localidad  = COALESCE(@Id_Localidad, Id_Localidad) -- << nuevo
     WHERE Id_Direccion = @Id_Direccion;
  END

  -- Actualiza Vehiculo_cliente_nuevo (igual que ya tenías)
  UPDATE dbo.Vehiculo_cliente_nuevo
     SET Direccion       = COALESCE(@DireccionLegacy, Direccion),
         Contacto        = COALESCE(@Contacto,  Contacto),
         Telefono        = COALESCE(@Telefono,  Telefono),
         Id_Zona         = COALESCE(@Id_Zona,   Id_Zona),
         ubigeo          = COALESCE(@Ubigeo,    ubigeo),
         NombrePunto     = COALESCE(@NombrePunto, NombrePunto),
         VentanaHorario  = COALESCE(@VentanaHorario, VentanaHorario),
         Indicaciones    = COALESCE(@Indicaciones,   Indicaciones),
         Id_RutaAsignada = COALESCE(@Id_RutaAsignada, Id_RutaAsignada),
         Principal       = COALESCE(@EsPrincipal, Principal),
         Activo          = COALESCE(@Estado, Activo),
         UsuarioMod      = @Usuario,
         FechaMod        = SYSDATETIME()
   WHERE Codigo = @Id_PuntoEntrega;
END


GO

-- =============================================
-- SP: ConsultarClientesPorSucursal (lÃ­neas 3616-3643)
-- =============================================
create PROCEDURE ConsultarClientesPorSucursal
    @Id_Sucursal INT,
    @Filtro NVARCHAR(200) = NULL, -- Filtro opcional
    @Tipo_Filtro NVARCHAR(50) = NULL -- 'Empresa' o 'Establecimiento'
AS
BEGIN
    SET NOCOUNT ON;

    SELECT 
        Cliente_Sucursal.Id_Cliente,
        Persona_Nuevo.Nom_Persona AS Empresa,
        Vehiculo_cliente_nuevo.Contacto AS Representante,
        Vehiculo_cliente_nuevo.Direccion AS Direccion_Establecimiento,
        Almacen.Desc_Almacen AS Sucursal
    FROM Cliente_Sucursal
    INNER JOIN Vehiculo_cliente_nuevo 
        ON Cliente_Sucursal.Id_Cliente = Vehiculo_cliente_nuevo.Codigo
    INNER JOIN Persona_Nuevo 
        ON Vehiculo_cliente_nuevo.Id_ClientePersona = Persona_Nuevo.Cod_Persona
    INNER JOIN Almacen 
        ON Cliente_Sucursal.Id_Sucursal = Almacen.Cod_Almacen
    WHERE 
        Cliente_Sucursal.Id_Sucursal = @Id_Sucursal
        AND (@Filtro IS NULL OR 
             (@Tipo_Filtro = 'Empresa' AND Persona_Nuevo.Nom_Persona LIKE '%' + @Filtro + '%') OR
             (@Tipo_Filtro = 'Establecimiento' AND Vehiculo_cliente_nuevo.Contacto LIKE '%' + @Filtro + '%'));
END;


GO

-- =============================================
-- SP: ConsultarSucursalesPorCliente (lÃ­neas 3705-3730)
-- =============================================
CREATE PROCEDURE ConsultarSucursalesPorCliente
    @Id_Cliente INT
AS
BEGIN
    SET NOCOUNT ON;

    SELECT 
        Cliente_Sucursal.Id_Cliente,
        Persona_Nuevo.Nom_Persona AS Nombre_Empresa,
        Vehiculo_cliente_nuevo.Contacto AS Nombre_Establecimiento,
        Cliente_Sucursal.Id_Sucursal,
        Almacen.Desc_Almacen AS Nombre_Sucursal,
        Vehiculo_cliente_nuevo.Direccion AS Direccion_Establecimiento
    FROM 
        Cliente_Sucursal
    INNER JOIN Vehiculo_cliente_nuevo 
        ON Cliente_Sucursal.Id_Cliente = Vehiculo_cliente_nuevo.Codigo
    INNER JOIN Persona_Nuevo 
        ON Vehiculo_cliente_nuevo.Id_ClientePersona = Persona_Nuevo.Cod_Persona
    INNER JOIN Almacen 
        ON Cliente_Sucursal.Id_Sucursal = Almacen.Cod_Almacen
    WHERE 
        Cliente_Sucursal.Id_Cliente = @Id_Cliente;
END;



GO

-- =============================================
-- SP: ConsultarAuditoriaClienteSucursal (lÃ­neas 3592-3615)
-- =============================================
CREATE PROCEDURE ConsultarAuditoriaClienteSucursal
    @Id_Cliente INT = NULL,
    @Id_Sucursal INT = NULL
AS
BEGIN
    SET NOCOUNT ON;

    SELECT 
        Id_Cliente,
        Id_Sucursal,
        Accion,
        Fecha,
        Usuario
    FROM 
        Cliente_Sucursal_Auditoria
    WHERE 
        (@Id_Cliente IS NULL OR Id_Cliente = @Id_Cliente)
        AND (@Id_Sucursal IS NULL OR Id_Sucursal = @Id_Sucursal)
    ORDER BY Fecha DESC;
END;




GO

-- =============================================
-- SP: clienteexento_modificar (lÃ­neas 2975-2984)
-- =============================================
CREATE PROCEDURE clienteexento_modificar
@Cod_Persona int,
@exento  int
AS 
UPDATE Persona
SET
exento = @exento

WHERE
Cod_Persona = @Cod_Persona

GO

-- =============================================
-- SP: clienteRetencion_modificar (lÃ­neas 2985-2994)
-- =============================================
CREATE PROCEDURE clienteRetencion_modificar
@Cod_Persona int,
@retencion  int
AS 
UPDATE Persona
SET
retencion = @retencion

WHERE
Cod_Persona = @Cod_Persona

GO

-- =============================================
-- SP: DatosBancarios_HistoricoCliente (lÃ­neas 5097-5123)
-- =============================================
CREATE PROCEDURE dbo.DatosBancarios_HistoricoCliente
    @Id_ClientePersona INT
AS
BEGIN
    SET NOCOUNT ON;

    SELECT
        db.Id_DatoBancario,
        db.Numero_Cuenta,
        db.IdBanco,
        b.Codigo_BIC,          -- ? ahora sí se devuelve
        b.Nombre_Banco,
        db.Forma_Pago,
        db.Activo,
        db.Fecha_Alta,
        db.Fecha_Baja,
        db.Motivo_Baja
    FROM dbo.Datos_Bancarios AS db
    LEFT JOIN dbo.Banco AS b 
        ON b.IdBanco = db.IdBanco   -- ? unión correcta por ID
    WHERE db.Id_ClientePersona = @Id_ClientePersona
    ORDER BY 
        db.Activo DESC, 
        db.Fecha_Alta DESC, 
        db.Id_DatoBancario DESC;
END


GO

-- =============================================
-- SP: DatosBancarios_ObtenerPorCliente (lÃ­neas 5124-5149)
-- =============================================
CREATE PROCEDURE dbo.DatosBancarios_ObtenerPorCliente
  @Id_ClientePersona INT
AS
BEGIN
  SET NOCOUNT ON;

  SELECT TOP (1)
      db.Id_DatoBancario,
      db.Id_ClientePersona,
      db.Numero_Cuenta,
      db.IdBanco,
      b.Codigo_BIC,
      b.Nombre_Banco,
      db.Forma_Pago,
      db.Activo AS Activo_DatoBancario,
      ISNULL(b.Activo, 1) AS Activo_Banco,
      db.Fecha_Alta
  FROM dbo.Datos_Bancarios db WITH (NOLOCK)
  LEFT JOIN dbo.Banco b WITH (NOLOCK)
         ON b.IdBanco = db.IdBanco
  WHERE
 db.Id_ClientePersona = @Id_ClientePersona
  ORDER BY db.Activo DESC,
           db.Fecha_Alta DESC,
           db.Id_DatoBancario DESC;
END

GO

-- =============================================
-- SP: DatosBancarios_CambiarCuentaCliente (lÃ­neas 5051-5096)
-- =============================================
CREATE PROCEDURE dbo.DatosBancarios_CambiarCuentaCliente
  @Id_ClientePersona INT,
  @Numero_Cuenta     NVARCHAR(34),
  @IdBanco           INT,
  @Forma_Pago        NVARCHAR(50),
  @Cod_Responsable   INT           = NULL,
  @Motivo_Baja       NVARCHAR(200) = N'Cambió de cuenta',
  @Usuario_Baja      NVARCHAR(50)  = NULL
AS
BEGIN
  SET NOCOUNT ON;

  IF @Usuario_Baja IS NULL 
     SET @Usuario_Baja = SUSER_SNAME();

  BEGIN TRY
    BEGIN TRAN;

    -- Validar banco real
    IF NOT EXISTS (SELECT 1 FROM dbo.Banco WHERE IdBanco = @IdBanco AND Activo = 1)
      RAISERROR('El banco seleccionado no existe o está inactivo.',16,1);

    -- Desactivar cuenta activa anterior
    UPDATE dbo.Datos_Bancarios
       SET Activo      = 0,
           Fecha_Baja  = CONVERT(date, GETDATE()),
           Motivo_Baja = @Motivo_Baja,
           Usuario_Baja= @Usuario_Baja
     WHERE Id_ClientePersona = @Id_ClientePersona
       AND Activo = 1;

    -- Insertar nueva cuenta
    INSERT INTO dbo.Datos_Bancarios
      (Cod_Responsable, Id_ClientePersona, Numero_Cuenta,
       IdBanco, Forma_Pago, Activo, Fecha_Alta)
    VALUES
      (@Cod_Responsable, @Id_ClientePersona, @Numero_Cuenta,
       @IdBanco, @Forma_Pago, 1, CONVERT(date, GETDATE()));

    COMMIT TRAN;
  END TRY
  BEGIN CATCH
    IF @@TRANCOUNT > 0 ROLLBACK TRAN;
    THROW;
  END CATCH
END

GO

-- =============================================
-- SP: crear_personalm (lÃ­neas 4979-4992)
-- =============================================
-- =============================================
-- Author:		<Author,,Name>
-- Create date: <Create Date,,>
-- Description:	<Description,,>
-- =============================================
create PROCEDURE [dbo].[crear_personalm]
@empleado int,
@almacen  int
AS 
INSERT INTO dbo.empleado_almacen
	(empleado,almacen)
VALUES
	(@empleado,@almacen)


GO

-- =============================================
-- SP: crear_vehiculo_cliente (lÃ­neas 5013-5050)
-- =============================================
--CREATE  PROCEDURE [dbo].[crear_vehiculo_cliente]

--@codigo	int output,
--@direccion	nvarchar(1500),
--@telefono	nvarchar(50),
--@contacto	nvarchar(250),
--@cliente	int,
--@ubigeo	nvarchar (6),
--@correoresp	nvarchar(250),
--@zonaresp	int


--AS 
--INSERT INTO vehiculo_cliente
--(direccion,telefono,contacto,cliente,ubigeo,correoresp,zonaresp)
--VALUES
--(@direccion,@telefono,@contacto,@cliente,@ubigeo,@correoresp,@zonaresp)
--set @codigo = @@identity

CREATE PROCEDURE [dbo].[crear_vehiculo_cliente]
    @codigo int OUTPUT,
    @direccion nvarchar(1500),
    @telefono nvarchar(50),
    @contacto nvarchar(250),
    @cliente int,
    @ubigeo nvarchar(6),
    @correoresp nvarchar(250),
    @zonaresp int
AS
BEGIN
    SET NOCOUNT ON;

    INSERT INTO vehiculo_cliente (direccion, telefono, contacto, cliente, ubigeo, correoresp, zonaresp)
    VALUES (@direccion, @telefono, @contacto, @cliente, @ubigeo, @correoresp, @zonaresp);
    
    SET @codigo = SCOPE_IDENTITY();
END


GO

-- =============================================
-- SP: ActualizarClienteSucursal (lÃ­neas 950-989)
-- =============================================
CREATE PROCEDURE ActualizarClienteSucursal
    @Id_Cliente INT,
    @Id_Sucursal_Anterior INT,
    @Id_Sucursal_Nueva INT,
    @Modificado_Por NVARCHAR(50)
AS
BEGIN
    SET NOCOUNT ON;

    -- Verificar que la relación actual exista
    IF NOT EXISTS (
        SELECT 1 
        FROM Cliente_Sucursal 
        WHERE Id_Cliente = @Id_Cliente AND Id_Sucursal = @Id_Sucursal_Anterior
    )
    BEGIN
        RAISERROR('La relación cliente-sucursal no existe.', 16, 1);
        RETURN;
    END

    -- Verificar si la nueva relación ya existe
    IF EXISTS (
        SELECT 1 
        FROM Cliente_Sucursal 
        WHERE Id_Cliente = @Id_Cliente AND Id_Sucursal = @Id_Sucursal_Nueva
    )
    BEGIN
        RAISERROR('El cliente ya está asociado a la nueva sucursal.', 16, 1);
        RETURN;
    END

    -- Actualizar la sucursal del cliente con información de auditoría
    UPDATE Cliente_Sucursal
    SET Id_Sucursal = @Id_Sucursal_Nueva,
        Fecha_Modificacion = GETDATE(),
        Modificado_Por = @Modificado_Por
    WHERE Id_Cliente = @Id_Cliente AND Id_Sucursal = @Id_Sucursal_Anterior;
END;



GO

-- =============================================
-- SP: Buscar_buscarorden_compraxcliente (lÃ­neas 1427-1438)
-- =============================================
CREATE PROCEDURE [dbo].[Buscar_buscarorden_compraxcliente]
	@persona int
AS

SELECT        dbo.Movimiento.ocompra, dbo.Movimiento.Cod_Movimiento, dbo.DetalleMovimiento.CodMovimiento, dbo.DetalleMovimiento.despachado, dbo.Movimiento.Persona, 
                         dbo.Movimiento.TipoAtencion
FROM            dbo.Movimiento INNER JOIN
                         dbo.DetalleMovimiento ON dbo.Movimiento.Cod_Movimiento = dbo.DetalleMovimiento.CodMovimiento
GROUP BY dbo.Movimiento.Cod_Movimiento, dbo.Movimiento.ocompra, dbo.DetalleMovimiento.CodMovimiento, dbo.DetalleMovimiento.despachado, dbo.Movimiento.Persona, 
                         dbo.Movimiento.TipoAtencion
HAVING        (dbo.Movimiento.Persona = @persona) AND (dbo.Movimiento.TipoAtencion = 11) OR
                         (dbo.Movimiento.TipoAtencion = 10)

GO

-- =============================================
-- SP: Actualizar_TARIFAPERSONA (lÃ­neas 938-949)
-- =============================================
CREATE PROCEDURE [dbo].[Actualizar_TARIFAPERSONA]
@CODCLIENTE INT,
@CODPRODUCTO INT,
@precio MONEY
AS 

update dbo.Tarifa_cliente
set
   PRECIO=@PRECIO
where CODCLIENTE=@CODCLIENTE AND CODPRODUCTO=@CODPRODUCTO


GO

-- =============================================
-- SP: Actualizar_Establecimiento (lÃ­neas 672-721)
-- =============================================
CREATE PROCEDURE [dbo].[Actualizar_Establecimiento]
    @Codigo INT,
    @Id_ClientePersona INT,
    @Direccion NVARCHAR(200),
    @Contacto NVARCHAR(100),
    @Telefono NVARCHAR(50),
    @Correoresp NVARCHAR(100),
    @Enlace_GPS NVARCHAR(200),
    @Id_Zona INT,
    @Dreparto NVARCHAR(50),
    @Id_Agente_Asignado INT = NULL,
    @Id_DatoBancario INT = NULL,
    @Observ_Responsable NVARCHAR(200),
    @Principal BIT,
    @Activo BIT,
    @Fecha_Registro DATE,
    @Ubigeo NVARCHAR(6),
    @Dvisita NVARCHAR(50),
    @Garantia NVARCHAR(50),
    @Envio INT,
    @Id_Sucursal INT
AS
BEGIN
    SET NOCOUNT ON;

    UPDATE Vehiculo_cliente_Nuevo
    SET
        Id_ClientePersona = @Id_ClientePersona,
        Direccion         = @Direccion,
        Contacto          = @Contacto,
        Telefono          = @Telefono,
        Correoresp        = @Correoresp,
        Enlace_GPS        = @Enlace_GPS,
        Id_Zona           = @Id_Zona,
        Dreparto          = @Dreparto,
        Id_Agente_Asignado = @Id_Agente_Asignado,
        Id_DatoBancario    = @Id_DatoBancario,
        Observ_Responsable = @Observ_Responsable,
        Principal         = @Principal,
        Activo            = @Activo,
        Fecha_Registro    = @Fecha_Registro,
        Ubigeo            = @Ubigeo,
        Dvisita           = @Dvisita,
        Garantia          = @Garantia,
        Envio             = @Envio,
        Id_Sucursal       = @Id_Sucursal
    WHERE
        Codigo = @Codigo;
END


GO

-- =============================================
-- SP: Actualizar_estadoOCCliente (lÃ­neas 770-782)
-- =============================================
CREATE PROCEDURE [dbo].[Actualizar_estadoOCCliente]

@ids int,
@mostrar int

AS

UPDATE Detalle_orden
SET
mostrar=@mostrar

WHERE
ids=@ids

GO

-- =============================================
-- SP: Buscar_FormasPago (lÃ­neas 2051-2071)
-- =============================================
CREATE PROCEDURE [dbo].[Buscar_FormasPago]
    @descripcion NVARCHAR(50) = NULL
AS
BEGIN
    SET NOCOUNT ON;

    SELECT 
        Id_FormaPago,
        Descripcion,
        TipoOperacion,
        RequiereAutorizacion,
        PlazoPago,
        Activo
    FROM 
        Formas_pago
    WHERE 
        (@descripcion IS NULL OR Descripcion LIKE '%' + @descripcion + '%')
    ORDER BY 
        Id_FormaPago;
END;


GO

-- =============================================
-- SP: BuscarClientesAnotificar (lÃ­neas 2576-2596)
-- =============================================
CREATE PROCEDURE BuscarClientesAnotificar
    @fechai DATE,
    @fechaf DATE,
    @codalmacen INT
AS
BEGIN
    SELECT        GETDATE() AS Fecha_Hoy, dbo.Almacen.Desc_Almacen, dbo.Almacen.Direccion_Almacen, ECabecera_pedido_1.Almacen, 
                         CASE WHEN COUNT(DISTINCT CASE WHEN ECabecera_pedido_1.motivo = 'prestamo' THEN 'Arriendo' ELSE ECabecera_pedido_1.motivo END) 
                         > 1 THEN 'Mixto' ELSE MAX(CASE WHEN ECabecera_pedido_1.motivo = 'prestamo' THEN 'Arriendo' ELSE ECabecera_pedido_1.motivo END) END AS Motivo2, dbo.Persona.Cod_Persona, dbo.Persona.Nom_Persona, 
                         dbo.Persona.mail_Persona, GETDATE() AS FechaInsercion, dbo.Persona.Ruc_Persona, dbo.Persona.Direccion_Persona
FROM            dbo.vehiculo_cliente INNER JOIN
                         dbo.Persona ON dbo.vehiculo_cliente.cliente = dbo.Persona.Cod_Persona INNER JOIN
                         dbo.ECabecera_pedido AS ECabecera_pedido_1 ON dbo.vehiculo_cliente.codigo = ECabecera_pedido_1.persona INNER JOIN
                         dbo.EDetalle_cpedido AS EDetalle_cpedido_1 ON ECabecera_pedido_1.cod_cpedido = EDetalle_cpedido_1.cod_pedido INNER JOIN
                         dbo.Almacen ON ECabecera_pedido_1.Almacen = dbo.Almacen.Cod_Almacen
WHERE        (ECabecera_pedido_1.forma_mov = N'Salida') AND (ECabecera_pedido_1.fecha_pedido BETWEEN @fechai AND @fechaf) AND (ECabecera_pedido_1.Almacen = @codalmacen)
GROUP BY dbo.Almacen.Desc_Almacen, dbo.Almacen.Direccion_Almacen, ECabecera_pedido_1.Almacen, dbo.Persona.Cod_Persona, dbo.Persona.Nom_Persona, dbo.Persona.mail_Persona, dbo.Persona.Ruc_Persona, 
                         dbo.Persona.Direccion_Persona
HAVING        (dbo.Persona.Nom_Persona <> N'Activación de Cilindro Lleno') AND (MAX(DATEDIFF(DAY, ECabecera_pedido_1.fecha_pedido, GETDATE())) > 10)
END


GO

-- =============================================
-- SP: Buscar_ClientexnomFiscal (lÃ­neas 1546-1663)
-- =============================================
CREATE PROCEDURE dbo.Buscar_ClientexnomFiscal
    @Cod_TipoPersona INT,
    @Nom_Persona NVARCHAR(200) = NULL
AS
BEGIN
    SET NOCOUNT ON;

    SET @Nom_Persona = NULLIF(LTRIM(RTRIM(@Nom_Persona)), N'');

    SELECT
        Persona_Nuevo.Cod_Persona,
        Persona_Nuevo.Nro_Persona,
        Persona_Nuevo.Nom_Persona,
        Persona_Nuevo.Dni_Persona,
        Persona_Nuevo.Ruc_Persona,
        Persona_Nuevo.Cod_TipoPersona,
        Persona_Nuevo.Sexo_Persona,
        Persona_Nuevo.FNac_Personal,
        Persona_Nuevo.mail_Persona,
        Persona_Nuevo.Telefono_Persona,
        Persona_Nuevo.Activo,
        Persona_Nuevo.Login_Persona,
        Persona_Nuevo.Pass_Persona,
        Persona_Nuevo.Nick_Persona,
        Persona_Nuevo.Fotografia,
        Persona_Nuevo.id_clave_Operacion,
        Persona_Nuevo.clave_op_intracomunitaria,
        Persona_Nuevo.nombre_comercial,
        Persona_Nuevo.observaciones,

 --       -- ?? DIRECCIÓN INTELIGENTE
 --       CASE 
 --           WHEN Vehiculo_cliente_nuevo.Direccion

 --IS NOT NULL THEN Vehiculo_cliente_nuevo.Direccion
 --           ELSE Direccion.Linea1
 --       END AS Direccion,
		Direccion.Linea1 AS Direccion,

        Vehiculo_cliente_nuevo.Contacto,
        Vehiculo_cliente_nuevo.garantia,
        Vehiculo_cliente_nuevo.Telefono,
        Vehiculo_cliente_nuevo.Correoresp,
        Vehiculo_cliente_nuevo.Dvisita,
        Vehiculo_cliente_nuevo.Codigo,
        Vehiculo_cliente_nuevo.Id_ClientePersona,
        Vehiculo_cliente_nuevo.Envio,

        Agentes_Sucursal.Comision,
        Ecargos_funciones.Cod_Persona AS Persona_Cargo,
        Ecargos_funciones.Cod_Sucursal,
        Ecargos_funciones.CargoFuncion,
        Persona_Nuevo_Agente.Nom_Persona AS Nom_Agente,
        Ecargos_funciones.Id_CargoFuncion AS Id_Agente_Asignado,

        CreditosSeleccionados.Linea_Credito,
        CreditosSeleccionados.Dias_Credito,

        Persona_Nuevo.Documento_Principal,
        Persona_Nuevo.Tipo_facturacion,
        Persona_Nuevo.Id_FormaPago,

        Eclaves_operacion.codigo_clave,
        Eclaves_operacion.tipo_iva,
        CAST(Eclaves_operacion.descripcion AS NVARCHAR(MAX)) AS descripcion_clave,
        Eclaves_operacion.tipo_operacion,
        Eclaves_operacion.regimen_iva,
        Eclaves_operacion.requiere_nif_iva,
   
     Eclaves_operacion.afecta_intracomunitario,
        Eclaves_operacion.afecta_exportacion,

        CASE 
            WHEN Eclaves_operacion.id_clave IS NOT NULL THEN
                Eclaves_operacion.codigo_clave + ' - ' +
                CAST(Eclaves_operacion.tipo_iva AS VARCHAR(10)) + '% - ' +
                CAST(Eclaves_operacion.descripcion AS NVARCHAR(MAX))
            ELSE ''
        END AS ClaveOperacion_Texto,

        CASE
            WHEN CreditosSeleccionados.Dias_Credito IS NOT NULL
    
        THEN DATEADD(DAY, CreditosSeleccionados.Dias_Credito, CAST(GETDATE() AS DATE))
        END AS fecha_pago

    FROM Persona_Nuevo

    -- ?? DIRECCIÓN FISCAL
    LEFT JOIN Direccion
        ON Direccion.Id_Direccion = Persona_Nuevo.Id_Direccion_Fiscal

    -- ?? PRINCIPAL (1 SOLO)
    OUTER APPLY (
        SELECT TOP 1 *
        FROM Vehiculo_cliente_nuevo
        WHERE Vehiculo_cliente_nuevo.Id_ClientePersona = Persona_Nuevo.Cod_Persona
          AND Vehiculo_cliente_nuevo.Principal = 1
    ) AS Vehiculo_cliente_nuevo

    LEFT JOIN Agentes_Sucursal
        ON Agentes_Sucursal.Cod_Responsable = Vehiculo_cliente_nuevo.Codigo

    LEFT JOIN Ecargos_funciones
        ON Ecargos_funciones.Id_CargoFuncion = Agentes_Sucursal.Id_CargoFuncion

    LEFT JOIN Persona_Nuevo AS Persona_Nuevo_Agente
        ON Persona_Nuevo_Agente.Cod_Persona = Ecargos_funciones.Cod_Persona

    LEFT JOIN Eclaves_operacion
        ON Eclaves_operacion.id_clave = Persona_Nuevo.id_clave_Operacion

    OUTER APPLY (
        SELECT TOP 1
               Creditos.Linea_Credito,
               Creditos.Dias_Credito
        FROM Creditos
        WHERE Creditos.Cod_VehiculoCliente = Persona_Nu

GO

-- =============================================
-- SP: Buscar_Claves (lÃ­neas 1466-1519)
-- =============================================
CREATE PROCEDURE [dbo].[Buscar_Claves]
    @id_clave INT = NULL,           
    @codigo_clave NVARCHAR(10) = NULL, 
    @activo BIT = NULL,
    @es_venta BIT = NULL -- Nuevo filtro para filtrar solo ventas en España
AS
BEGIN
    SET NOCOUNT ON;

    SELECT 
        id_clave,
        codigo_clave,
        descripcion,
        aplicable_a,
        activo,
        tipo_iva
    FROM 
        EClaves_operacion
    WHERE 
        (@id_clave IS NULL OR id_clave = @id_clave) AND
        (@codigo_clave IS NULL OR codigo_clave = @codigo_clave) AND
        (@activo IS NULL OR activo = @activo) AND
        (@es_venta IS NULL OR (aplicable_a = 'Nacional' AND tipo_operacion = 'Venta')) -- Filtra solo ventas en España
    ORDER BY 
        id_clave;
END;



--alter PROCEDURE [dbo].[Buscar_Claves]
--    @id_clave INT = NULL,           -- Filtro opcional por ID de la clave
--    @codigo_clave NVARCHAR(10) = NULL, -- Filtro opcional por código de la clave
--    @activo BIT = NULL              -- Filtro opcional por estado activo/inactivo
--AS
--BEGIN
--    SET NOCOUNT ON;

--    SELECT 
--        id_clave,
--        codigo_clave,
--        descripcion,
--        aplicable_a,
--        activo,
--        tipo_iva
--    FROM 
--        Eclaves_operacion
--    WHERE 
--        (@id_clave IS NULL OR id_clave = @id_clave) AND
--        (@codigo_clave IS NULL OR codigo_clave = @codigo_clave) AND
--        (@activo IS NULL OR activo = @activo)
--    ORDER BY 
--        id_clave; -- Orden por ID de clave
--END;


GO

-- =============================================
-- SP: Buscar_ClavesIC (lÃ­neas 1520-1545)
-- =============================================
CREATE PROCEDURE [dbo].[Buscar_ClavesIC]
    @id_clave INT = NULL,           
    @codigo_clave NVARCHAR(10) = NULL, 
    @activo BIT = NULL              
AS
BEGIN
    SET NOCOUNT ON;

    SELECT 
        id_clave,
        codigo_clave,
        descripcion,
        aplicable_a,
        activo,
        tipo_iva
    FROM 
        EClaves_operacion
    WHERE 
        (@id_clave IS NULL OR id_clave = @id_clave) AND
        (@codigo_clave IS NULL OR codigo_clave = @codigo_clave) AND
        (@activo IS NULL OR activo = @activo) AND
        (afecta_intracomunitario = 1)  -- Solo claves IC
    ORDER BY 
        id_clave;
END;


GO

-- =============================================
-- SP: Listar_Sucursales (lÃ­neas 7765-7770)
-- =============================================
CREATE PROCEDURE [dbo].[Listar_Sucursales]
@Direccion_Almacen	        nvarchar(4000)
AS
SELECT        Cod_Almacen, Desc_Almacen, Direccion_Almacen, Ruc_Almacen
FROM            dbo.Almacen


GO

-- =============================================
-- SP: Modificar_ClienteProveedor (lÃ­neas 7911-7991)
-- =============================================
CREATE PROCEDURE [dbo].[Modificar_ClienteProveedor]
    @Cod_Persona INT,
    @Nro_Persona NVARCHAR(50),
    @Nom_Persona NVARCHAR(200),
    @Dni_Persona NVARCHAR(20),
    @Ruc_Persona NVARCHAR(20),
    @Cod_TipoPersona INT,
    @Sexo_Persona NVARCHAR(10),
    @FNac_Personal DATE,
    @mail_Persona NVARCHAR(100),
    @Telefono_Persona NVARCHAR(50),
    @Activo BIT,
    @Login_Persona NVARCHAR(50),
    @Pass_Persona NVARCHAR(50),
    @Nick_Persona NVARCHAR(50),
    @Fotografia NVARCHAR(50),
    @id_clave_Operacion INT = NULL,
    @clave_op_intracomunitaria BIT,
    @nombre_comercial NVARCHAR(100),
    @observaciones NVARCHAR(MAX),
    @Documento_Principal NVARCHAR(50),
    @Tipo_facturacion NVARCHAR(50),
    @Direccion NVARCHAR(200),
	@Id_FormaPago INT = NULL
AS
BEGIN
    SET NOCOUNT ON;

    -- Validar existencia del registro
    IF NOT EXISTS (SELECT 1 FROM Persona_Nuevo WHERE Cod_Persona = @Cod_Persona)
    BEGIN
        RAISERROR('El registro con Cod_Persona especificado no existe.', 16, 1);
        RETURN;
    END

    -- Asignar valor predeterminado a id_clave_Operacion si está en NULL
    IF @id_clave_Operacion IS NULL
    BEGIN
        SELECT TOP 1 @id_clave_Operacion = id_clave FROM Eclaves_operacion WHERE Activo = 1;
    END

    -- Actualizar los datos en Persona_Nuevo
  

  UPDATE Persona_Nuevo
    SET
        Nro_Persona = @Nro_Persona,
        Nom_Persona = @Nom_Persona,
        Dni_Persona = @Dni_Persona,
        Ruc_Persona = @Ruc_Persona,
        Cod_TipoPersona = @Cod_TipoPersona,
        Sexo_Persona = @Sexo_Persona,
        FNac_Personal = @FNac_Personal,
        mail_Persona = @mail_Persona,
        Telefono_Persona = @Telefono_Persona,
        Activo = @Activo,
        Login_Persona = @Login_Persona,
        Pass_Persona = @Pass_Persona,
        Nick_Persona = @Nick_Persona,
        Fotografia = @Fotografia,
        id_clave_Operacion = @id_clave_Operacion,
        clave_op_intracomunitaria = @clave_op_intracomunitaria,
        nombre_comercial = @nombre_comercial,
        observaciones = @observaciones,
  Documento_Principal = @Documento_Principal,
        Tipo_facturacion = @Tipo_facturacion,
				Id_FormaPago = @Id_FormaPago
    WHERE
        Cod_Persona = @Cod_Persona;

    -- Actualizar datos de contacto en Vehiculo_Cliente_Nuevo si hay principal
    UPDATE Vehiculo_Cliente_Nuevo
    SET
        Telefono = @Telefono_Persona,
        Correoresp = @mail_Persona,
        Direccion = @Direccion
    WHERE
        Id_ClientePersona = @Cod_Persona
        AND Principal = 1;
END


GO

-- =============================================
-- SP: listar_pedidos_cliente_abiertos (lÃ­neas 7732-7764)
-- =============================================
CREATE PROCEDURE dbo.listar_pedidos_cliente_abiertos
    @ClienteId INT
AS
BEGIN
    SET NOCOUNT ON;

    SELECT
        Movimiento.Cod_Movimiento,
        Movimiento.Fecha,
        Movimiento.Total,
        Movimiento.Moneda,
        SUM(DetalleMovimiento.StkEgreso) AS CantPedida,
        SUM(ISNULL(DetalleMovimiento.CantPlanificada, 0)) AS CantEntregada,
        Movimiento.Observacion,
        Movimiento.FullDoc
    FROM dbo.Movimiento
    INNER JOIN dbo.DetalleMovimiento
        ON Movimiento.Cod_Movimiento = DetalleMovimiento.CodMovimiento
    WHERE Movimiento.Persona = @ClienteId
      AND Movimiento.Estado = 1
      AND Movimiento.TipoAtencion = 11
    GROUP BY 
        Movimiento.Cod_Movimiento,
        Movimiento.Fecha,
        Movimiento.Total,
 
       Movimiento.Moneda,
        Movimiento.Observacion,
        Movimiento.FullDoc
    ORDER BY Movimiento.Fecha DESC;

END


GO

-- =============================================
-- SP: Insertar_Persona_Nuevo (lÃ­neas 7256-7344)
-- =============================================
CREATE PROCEDURE Insertar_Persona_Nuevo
    @Nro_Persona NVARCHAR(50),
    @Nom_Persona NVARCHAR(200),
    @Dni_Persona NVARCHAR(20),
    @Ruc_Persona NVARCHAR(20),
    @Cod_TipoPersona INT,
    @Sexo_Persona NVARCHAR(10),
    @FNac_Personal DATE,
    @mail_Persona NVARCHAR(100),
    @Telefono_Persona NVARCHAR(50),
    @Activo BIT,
    @Login_Persona NVARCHAR(50),
    @Pass_Persona NVARCHAR(50),
    @Nick_Persona NVARCHAR(50),
    @Fotografia NVARCHAR(50),
    @id_clave_Operacion INT,
    @clave_op_intracomunitaria BIT,
    @nombre_comercial VARCHAR(100),
    @observaciones NVARCHAR(MAX),
    @Documento_Principal NVARCHAR(50),
    @Tipo_facturacion NVARCHAR(50),
    @Id_FormaPago INT,
    @Cod_Persona INT OUTPUT
AS
BEGIN
    SET NOCOUNT ON;

    BEGIN TRY

        INSERT INTO Persona_Nuevo (
            Nro_Persona,
            Nom_Persona,
            Dni_Persona,
            Ruc_Persona,
            Cod_TipoPersona,
            Sexo_Persona,
            FNac_Personal,
            mail_Persona,
          
  Telefono_Persona,
            Activo,
            Login_Persona,
            Pass_Persona,
            Nick_Persona,
            Fotografia,
            id_clave_Operacion,
            clave_op_intracomunitaria,
            nombre_comercial,
           
 observaciones,
            Documento_Principal,
            Tipo_facturacion,
            Id_FormaPago
        )
        VALUES (
            @Nro_Persona,
            @Nom_Persona,
            @Dni_Persona,
            @Ruc_Persona,
            @Cod_TipoPersona,
            @Sexo_Persona,
            @FNac_Personal,
            @mail_Persona,
            @Telefono_Persona,
            @Activo,
            @Login_Persona,
            @Pass_Persona,
            @Nick_Persona,
            @Fotografia,
    
        @id_clave_Operacion,
            @clave_op_intracomunitaria,
            @nombre_comercial,
            @observaciones,
            @Documento_Principal,
            @Tipo_facturacion,
            @Id_FormaPago
        );

        -- Obtener el ID de la nueva persona insertada
        SET @Cod_Persona = SCOPE_IDENTITY();

    END TRY
    BEGIN CATCH
        -- En caso de error, devolver un valor de error (-1)
        SET @Cod_Persona = -1;
    END CATCH;
END;


GO

-- =============================================
-- SP: InsertarClienteSucursal (lÃ­neas 7404-7427)
-- =============================================
CREATE PROCEDURE InsertarClienteSucursal
    @Id_Cliente INT,
    @Id_Sucursal INT,
    @Creado_Por NVARCHAR(50)
AS
BEGIN
    SET NOCOUNT ON;

    -- Verificar si el cliente ya está asociado a la sucursal
    IF EXISTS (
        SELECT 1 
        FROM Cliente_Sucursal 
        WHERE Id_Cliente = @Id_Cliente AND Id_Sucursal = @Id_Sucursal
    )
    BEGIN
        RAISERROR('El cliente ya está asociado a esta sucursal.', 16, 1);
        RETURN;
    END

    -- Insertar el nuevo registro con información de auditoría
    INSERT INTO Cliente_Sucursal (Id_Cliente, Id_Sucursal, Fecha_Creacion, Creado_Por)
    VALUES (@Id_Cliente, @Id_Sucursal, GETDATE(), @Creado_Por);
END;


GO

-- =============================================
-- SP: MOSTRAR_CPubigeoxDireccion (lÃ­neas 9091-9101)
-- =============================================
create PROCEDURE [dbo].[MOSTRAR_CPubigeoxDireccion]
	@Direccion_Almacen	        nvarchar(2500)
AS
begin
SELECT     Almacen.Cod_Almacen, Almacen.Desc_Almacen, Almacen.Direccion_Almacen, Almacen.Ruc_Almacen, Almacen.Telf_Almacen, 
                      Almacen.Cod_RazonSocial, Almacen.Mostrar, Almacen.Formato_precios, RazonSocial.Desc_RazonS
FROM         Almacen INNER JOIN
                      RazonSocial ON Almacen.Cod_RazonSocial = RazonSocial.Cod_RazonS
WHERE     Almacen.Direccion_Almacen = @Direccion_Almacen
ORDER BY Almacen.Direccion_Almacen
end

GO

-- =============================================
-- SP: MOSTRAR_PERSONA (lÃ­neas 10397-10410)
-- =============================================
CREATE PROCEDURE [dbo].[MOSTRAR_PERSONA]
	
	@Paciente	        nvarchar(4000)
AS
begin
SELECT     Cod_Persona, Nro_MOZO, Nom_Persona, Dni_Persona, Ruc_Persona, FNac_Personal, Login_Persona, Pass_Persona, Nick_Persona, Sexo_Persona, mail_Persona, 
                      Telefono_Persona, Direccion_Persona, Cod_TipoPersona, cmp_Persona, contacto, nextel, celular, nrocuenta, banco, LineaCredito_Persona, R, V1, V2, DNIS, DNIR, 
                      DNIV1, DNIV2, TELEFONOS, TELEFONOR, TELEFONOV1, TELEFONOV2, dvisita, dreparto, urbanizacion, puntos_acumulados, tarjeta, fotografia, hijos, profesion, 
                      descurb, diascred
FROM         dbo.Persona
WHERE        (dbo.Persona.Nom_Persona LIKE '%' + @Paciente + '%')
ORDER BY dbo.Persona.Nom_Persona
end


GO

-- =============================================
-- SP: Modificar_vehiculo_cliente (lÃ­neas 8565-8590)
-- =============================================
CREATE   PROCEDURE [dbo].[Modificar_vehiculo_cliente]
@codigo	int output,
@direccion	nvarchar(1500),
@telefono	nvarchar(50),
@contacto	nvarchar(250),
@Id_ClientePersona	int,
@ubigeo	nvarchar(6),
@correoresp	nvarchar(250),
@Id_Zona	int,
@NombrePunto nvarchar(250)
As
UPDATE vehiculo_cliente_Nuevo
SET
direccion=@direccion,
telefono=@telefono,
contacto=@contacto,
Id_ClientePersona=@Id_ClientePersona,
ubigeo=@ubigeo,
correoresp=@correoresp,
Id_Zona=@Id_Zona,
NombrePunto=@NombrePunto

WHERE
codigo = @codigo



GO

-- =============================================
-- SP: Modificar_Direccion_Persona (lÃ­neas 8246-8292)
-- =============================================
CREATE PROCEDURE [dbo].[Modificar_Direccion_Persona]
    @Id_Direccion INT,  -- ID de la dirección a modificar
    @Cod_Persona INT,
    @Direccion_Linea_1 NVARCHAR(200),
    @Direccion_Linea_2 NVARCHAR(200) = NULL,
    @Id_Zona INT = NULL,
    @Codigo_Postal NVARCHAR(10) = NULL,
    @Enlace_GPS NVARCHAR(200) = NULL,
    @Tipo_Direccion NVARCHAR(50) = 'Residencial',
    @Activo BIT = 1,
    @Fecha_Registro DATE = NULL,
    @Resultado BIT OUTPUT -- Devuelve 1 si se modifica, 0 si no se encuentra la dirección
AS
BEGIN
    SET NOCOUNT ON;

    -- Asignar fecha actual si no se proporciona
    IF @Fecha_Registro IS NULL
    BEGIN
        SET @Fecha_Registro = GETDATE();
    END

    -- Verificar si la dirección existe antes de actualizar
    IF EXISTS (SELECT 1 FROM Direcciones_NoClientes WHERE Id_Direccion = @Id_Direccion AND Cod_Persona = @Cod_Persona)
    BEGIN
        -- Actualizar la dirección
        UPDATE Direcciones_NoClientes
        SET Direccion_Linea_1 = @Direccion_Linea_1,
            Direccion_Linea_2 = @Direccion_Linea_2,
            Id_Zona = @Id_Zona,
            Codigo_Postal = @Codigo_Postal,
            Enlace_GPS = @Enlace_GPS,
            Tipo_Direccion = @Tipo_Direccion,
            Activo = @Activo,
            Fecha_Registro = @Fecha_Registro
        WHERE Id_Direccion = @Id_Direccion AND Cod_Persona = @Cod_Persona;

        -- Confirmar éxito
        SET @Resultado = 1;
    END
    ELSE
    BEGIN
        -- No se encontró la dirección
        SET @Resultado = 0;
    END
END;


GO

-- =============================================
-- SP: Modificar_Persona_Nuevo (lÃ­neas 8430-8493)
-- =============================================
CREATE PROCEDURE [dbo].[Modificar_Persona_Nuevo]
    @Cod_Persona INT,
    @Nro_Persona NVARCHAR(50),
    @Nom_Persona NVARCHAR(200),
    @Dni_Persona NVARCHAR(20),
    @Ruc_Persona NVARCHAR(20),
    @Cod_TipoPersona INT,
    @Sexo_Persona NVARCHAR(10),
    @FNac_Personal DATE,
    @mail_Persona NVARCHAR(100),
    @Telefono_Persona NVARCHAR(50),
    @Activo BIT,
    @Login_Persona NVARCHAR(50),
    @Pass_Persona NVARCHAR(50),
    @Nick_Persona NVARCHAR(50),
    @Fotografia NVARCHAR(50),
    @id_clave_Operacion INT,
    @clave_op_intracomunitaria BIT,
    @nombre_comercial VARCHAR(100),
    @observaciones NVARCHAR(MAX),
    @Documento_Principal NVARCHAR(50),
    @Tipo_facturacion NVARCHAR(50),
    @Id_FormaPago INT,
    @Resultado BIT OUTPUT  -- Retorna 1 si la actualización fue exitosa, 0 si no se encontró la persona
AS
BEGIN
    SET NOCOUNT ON;

    -- Verificar si la persona existe antes de actualizar
    IF NOT EXISTS (SELECT 1 FROM Persona_Nuevo WHERE Cod_Persona = @Cod_Persona)
    BEGIN
        SET @Resultado = 0; -- No se encontró la persona
        RETURN;
    END

    -- Actualizar los datos de la persona
    UPDATE Persona_Nuevo
    SET Nro_Persona = @Nro_Persona,
        Nom_Persona = @Nom_Persona,
        Dni_Persona = @Dni_Persona,
        Ruc_Persona = @Ruc_Persona,
        Cod_TipoPersona = @Cod_TipoPersona,
        Sexo_Persona = @Sexo_Persona,
        FNac_Personal = @FNac_Personal,
        mail_Persona = @mail_Persona,
        Telefono_Persona = @Telefono_Persona,
        Activo = @Activo,
        Login_Persona = @Login_Persona,
        Pass_Persona = @Pass_Persona,
        Nick_Persona = @Nick_Persona,
        Fotografia = @Fotografia,
        id_clave_Operacion = @id_clave_Operacion,
        clave_op_intracomunitaria = @clave_op_intracomunitaria,
        nombre_comercial = @nombre_comercial,
        observaciones = @observaciones,
        Documento_Principal = @Documento_Principal,
        Tipo_facturacion = @Tipo_facturacion,
        Id_FormaPago = @Id_FormaPago
    WHERE Cod_Persona = @Cod_Persona;

    -- Confirmar éxito de la actualización
    SET @Resultado = 1;
END;


GO

-- =============================================
-- SP: Direccion_ObtenerCoordenadasPorPunto (lÃ­neas 5556-5578)
-- =============================================
CREATE PROCEDURE dbo.Direccion_ObtenerCoordenadasPorPunto
  @Codigo INT  -- = dbo.Vehiculo_cliente_nuevo.Codigo (EstablecimientoID)
AS
BEGIN
  SET NOCOUNT ON;

  SELECT
      V.Codigo              AS Id_SucursalCliente,
      D.Id_Direccion,
      D.Latitud,            -- FLOAT (puede ser NULL)
      D.Longitud,           -- FLOAT (puede ser NULL)
      D.Linea1              AS Direccion,
      D.Codigo_Postal,
      V.NombrePunto,
      V.Principal,
      V.Activo
  FROM dbo.Vehiculo_cliente_nuevo AS V
 
 LEFT JOIN dbo.Direccion AS D
         ON D.Id_Direccion = V.Id_Direccion
  WHERE V.Codigo = @Codigo;
END


GO

-- =============================================
-- SP: eliminar_personalm (lÃ­neas 5891-5903)
-- =============================================
-- =============================================
-- Author:		<Author,,Name>
-- Create date: <Create Date,,>
-- Description:	<Description,,>
-- =============================================
CREATE PROCEDURE [dbo].[eliminar_personalm]
@empleado int,
@almacen int
AS 
delete from dbo.empleado_almacen
where empleado=@empleado and almacen=@almacen



GO

-- =============================================
-- SP: Direccion_ListarCoordenadasPorCliente (lÃ­neas 5532-5555)
-- =============================================
CREATE  PROCEDURE dbo.Direccion_ListarCoordenadasPorCliente
  @Id_ClientePersona INT
AS
BEGIN
  SET NOCOUNT ON;

  SELECT
      V.Id_ClientePersona,
      V.Codigo              AS Id_SucursalCliente,
      D.Id_Direccion,
      D.Latitud,
      D.Longitud,
      D.Linea1              AS Direccion,
      D.Codigo_Postal,
      V.NombrePunto,
      V.Principal,
      V.Activo
  FROM dbo.Vehiculo_cliente_nuevo AS V
  LEFT JOIN dbo.Direccion AS D
         ON D.Id_Direccion = V.Id_Direccion
  WHERE V.Id_ClientePersona = @Id_ClientePersona
  ORDER BY V.Principal DESC, V.NombrePunto, V.Codigo;
END


GO

-- =============================================
-- SP: DatosBancarios_ResumenCliente (lÃ­neas 5150-5176)
-- =============================================
CREATE PROCEDURE dbo.DatosBancarios_ResumenCliente
  @Id_ClientePersona INT
AS
BEGIN
  SET NOCOUNT ON;

  ;WITH Actual AS (
    SELECT TOP (1)
           db.Id_DatoBancario,
           db.Id_ClientePersona,
           db.Numero_Cuenta,
           db.IdBanco,
           db.Forma_Pago,
           db.Activo AS Activo_DatoBancario,
           db.Fecha_Alta,
           b.Nombre_Banco,
           ISNULL(b.Activo,1) AS Activo_Banco
    FROM dbo.Datos_Bancarios db
    LEFT JOIN dbo.Banco b ON b.IdBanco = db.IdBanco
    WHERE db.Id_ClientePersona = @Id_ClientePersona
    ORDER BY db.Activo DESC, db.Fecha_Alta DESC, db.Id_DatoBancario DESC
  )
  SELECT a.*,
         (SELECT COUNT(*) FROM dbo.Datos_Bancarios
           WHERE Id_ClientePersona=@Id_ClientePersona AND Activo=0) AS Cantidad_Historicas
  FROM Actual a;
END

GO

-- =============================================
-- SP: Direccion_CapturaEnSitio (lÃ­neas 5493-5531)
-- =============================================
CREATE PROCEDURE dbo.Direccion_CapturaEnSitio
  @Id_Direccion     INT,
  @Latitud          FLOAT,
  @Longitud         FLOAT,
  @Codigo_Postal    CHAR(5)      = NULL,
  @Formatted_Address NVARCHAR(255)= NULL,
  @Place_Id         NVARCHAR(64)  = NULL,
  @Country_Code     CHAR(2)       = NULL,
  @Admin_Area_1     NVARCHAR(120) = NULL,
  @Admin_Area_2     NVARCHAR(120) = NULL,
  @Localidad        NVARCHAR(120) = NULL,
  @Street_Name      NVARCHAR(160) = NULL,
  @Street_Number    NVARCHAR(20)  = NULL,
  @Fuente_Geocod    NVARCHAR(20)  = NULL,    -- GOOGLE/NOMINATIM/MANUAL
  @Precision_Metros INT            = NULL,
  @Usuario          NVARCHAR(50)   = NULL
AS
BEGIN
  SET NOCOUNT ON;

  UPDATE dbo.Direccion
     SET Latitud          = @Latitud,
         Longitud         = @Longitud,
         Codigo_Postal    = COALESCE(@Codigo_Postal, Codigo_Postal),
         Formatted_Address= COALESCE(@Formatted_Address, Formatted_Address),
         Place_Id         = COALESCE(@Place_Id, Place_Id),
         Country_Code     = COALESCE(@Country_Code, Country_Code),
         Admin_Area_1     = COALESCE(@Admin_Area_1, Admin_Area_1),
         Admin_Area_2     = COALESCE(@Admin_Area_2, Admin_Area_2),
         Localidad        = COALESCE(@Localidad, Localidad),
         Street_Name      = COALESCE(@Street_Name, Street_Name),
         Street_Number    = COALESCE(@Street_Number, Street_Number),
         Fuente_Geocod    = COALESCE(@Fuente_Geocod, Fuente_Geocod),
         Precision_Metros = COALESCE(@Precision_Metros, Precision_Metros),
         Capturado_Por    = @Usuario,
         Capturado_En     = SYSDATETIME()
   WHERE Id_Direccion = @Id_Direccion;
END


GO

-- =============================================
-- SP: Insertar_Direccion_Persona (lÃ­neas 7010-7069)
-- =============================================
CREATE PROCEDURE [dbo].[Insertar_Direccion_Persona]
    @Id_Direccion INT OUTPUT,  -- Parámetro de salida que devuelve el ID de la dirección insertada
    @Cod_Persona INT,
    @Direccion_Linea_1 NVARCHAR(200),
    @Direccion_Linea_2 NVARCHAR(200) = NULL,
    @Id_Zona INT = NULL,
    @Codigo_Postal NVARCHAR(10) = NULL,
    @Enlace_GPS NVARCHAR(200) = NULL,
    @Tipo_Direccion NVARCHAR(50) = 'Residencial', -- Por defecto "Residencial"
    @Activo BIT = 1, -- Activo por defecto
    @Fecha_Registro DATE = NULL -- Si no se envía, se usa la fecha actual
AS
BEGIN
    SET NOCOUNT ON;

    -- Si no se envía Fecha_Registro, usar la fecha actual
    IF @Fecha_Registro IS NULL
    BEGIN
        SET @Fecha_Registro = GETDATE();
    END

    -- Verificar si la dirección ya existe para la persona
    IF EXISTS (SELECT 1 FROM Direcciones_NoClientes WHERE Cod_Persona = @Cod_Persona)
    BEGIN
        -- Actualizar dirección existente
        UPDATE Direcciones_NoClientes
        SET Direccion_Linea_1 = @Direccion_Linea_1,
            Direccion_Linea_2 = @Direccion_Linea_2,
            Id_Zona = @Id_Zona,
            Codigo_Postal = @Codigo_Postal,
            Enlace_GPS = @Enlace_GPS,
            Tipo_Direccion = @Tipo_Direccion,
            Activo = @Activo,
            Fecha_Registro = @Fecha_Registro
        WHERE Cod_Persona = @Cod_Persona;

        -- Obtener el ID de la dirección actualizada
        SET @Id_Direccion = (SELECT Id_Direccion FROM Direcciones_NoClientes WHERE Cod_Persona = @Cod_Persona);

        PRINT 'Dirección actualizada correctamente.';
    END
    ELSE
    BEGIN
        -- Insertar nueva dirección
        INSERT INTO Direcciones_NoClientes (
            Cod_Persona, Direccion_Linea_1, Direccion_Linea_2, Id_Zona, 
            Codigo_Postal, Enlace_GPS, Tipo_Direccion, Activo, Fecha_Registro
        )
        VALUES (
            @Cod_Persona, @Direccion_Linea_1, @Direccion_Linea_2, @Id_Zona, 
            @Codigo_Postal, @Enlace_GPS, @Tipo_Direccion, @Activo, @Fecha_Registro
        );

        -- Obtener el ID de la dirección insertada
        SET @Id_Direccion = SCOPE_IDENTITY();

        PRINT 'Nueva dirección insertada correctamente.';
    END
END;


GO

-- =============================================
-- SP: Insertar_Establecimiento (lÃ­neas 7118-7242)
-- =============================================
CREATE PROCEDURE dbo.Insertar_Establecimiento
  @Id_ClientePersona INT,
  @NombrePunto NVARCHAR(100) = NULL,
  @Direccion NVARCHAR(200) = NULL,

  @Id_Zona INT = NULL,
  @Ubigeo NVARCHAR(6) = NULL,
  @Contacto NVARCHAR(100) = NULL,
  @Telefono NVARCHAR(50) = NULL,
  @VentanaHorario NVARCHAR(50) = NULL,
  @Indicaciones NVARCHAR(200) = NULL,
  @Envio INT = NULL,
  @Id_Sucursal INT,
  @EsPrincipal BIT = 0,

  @Latitud FLOAT = NULL,
  @Longitud FLOAT = NULL,
  @Codigo_Postal NVARCHAR(12) = NULL,
  @Id_DatoBancario INT = NULL,
  @Usuario NVARCHAR(50) = NULL,

  @Linea1 NVARCHAR(200) = NULL,
  @Linea2 NVARCHAR(200) = NULL,

  @Country_Code CHAR(2) = NULL,
  @Admin_Area_1 NVARCHAR(120) = NULL,
  @Admin_Area_2 NVARCHAR(120) = NULL,
  @Localidad NVARCHAR(120) = NULL,
  @Id_Localidad INT = NULL,

  @Street_Name NVARCHAR(160) = NULL,
  @Street_Number NVARCHAR(20) = NULL,

  @NuevoCodigo INT OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    BEGIN TRY
        BEGIN TRAN;

        DECLARE @Id_Direccion INT;
        DECLARE @Linea1_Limpia NVARCHAR(200);
        DECLARE @Linea2_Limpia NVARCHAR(200);
        DECLARE @DireccionVisual NVARCHAR(200);

        DECLARE @ProvinciaNombre NVARCHAR(120);
        DECLARE @MunicipioNombre NVARCHAR(120);
        DECLARE @LocalidadNombre NVARCHAR(120);

        -- ============================
        -- VALIDACIÓN PAÍS
        -- ============================
        IF @Country_Code IS NULL OR LTRIM(RTRIM(@Country_Code)) = ''
            SET @Country_Code = 'CR';

        -- ============================
        -- LIMPIEZA
        -- ============================
        SET @Linea1 = LTRIM(RTRIM(ISNULL(@Linea1, '')));
        SET @Linea2 = LTRIM(RTRIM(ISNULL(@Linea2, '')));
        SET @Direccion = LTRIM(RTRIM(ISNULL(@Direccion, '')));
        SET @Indicaciones = LTRIM(RTRIM(ISNULL(@Indicaciones, '')));

        -- ============================
        -- ?? NUEVA LÓGICA CR (USANDO CP_*)
        -- ============================
        IF @Country_Code = 'CR'
        BEGIN
            IF @Id_Localidad IS NULL
                RAISERROR('Debe seleccionar Localidad válida.',16,1);

            SELECT
                @ProvinciaNombre = p.Nombre,
                @MunicipioNombre = m.Nombre,
                @LocalidadNombre = l.Nombre
            FROM dbo.CP_Localidad l
            INNER JOIN dbo.CP_Municipio m ON l.Id_Municipio = m.Id_Municipio
            INNER JOIN dbo.CP_Provincia p ON m.Id_Provincia = p.Id_Provincia
            WHERE l.Id_Localidad = @Id_Localidad;

            IF @LocalidadNombre IS NULL
                RAISERROR('Id_Localidad no existe en CP_Localidad.',16,1);

            SET @Admin_Area_1 = @ProvinciaNombre;
            SET @Admin_Area_2 = @MunicipioNombre;
            SET @Localidad = @LocalidadNombre;

            SET @Linea1_Limpia = NULLIF(@Linea1, '');
            SET @Linea2_Limpia = NULLIF(@Linea2, '');

            SET @DireccionVisual = NULLIF(@Direccion, '');

            IF @DireccionVisual IS NULL
            BEGIN
                SET @DireccionVisual =
                    LTRIM(RTRIM(
                        CONCAT(
                            ISNULL(@Linea1_Limpia, ''),
                            CASE WHEN @Linea2_Limpia IS NOT NULL THEN ', ' + @Linea2_Limpia ELSE '' END,
                            ', ', @LocalidadNombre,
                            ', ', @MunicipioNombre
                        )
                    ));
            END
        END
        ELSE
        BEGIN
            -- ?? ESPAÑA (NO TOCAR)
            SET @Linea1_Limpia =
                CASE
                    WHEN @Linea1 <> '' THEN @Linea1
                    WHEN @Street_Name <> '' THEN @Street_Name
                    ELSE NULL
                END;

            SET @Linea2_Limpia = NULLIF(@Linea2, '');
            SET @DireccionVisual = NULLIF(@Direccion, '');
        END

        -- ============================
        -- INSERT DIRECCIÓN
        -- ============================
   

GO

-- =============================================
-- SP: Insertar_ClienteProveedor (lÃ­neas 6927-7009)
-- =============================================
CREATE PROCEDURE [dbo].[Insertar_ClienteProveedor]
@Cod_Persona INT OUTPUT,
@Nro_Persona NVARCHAR(50),
@Nom_Persona NVARCHAR(200),
@Dni_Persona NVARCHAR(20),
@Ruc_Persona NVARCHAR(20),
@Cod_TipoPersona INT,
@Sexo_Persona NVARCHAR(10),
@FNac_Personal DATE,


@mail_Persona NVARCHAR(100),
@Telefono_Persona NVARCHAR(50),
@Activo BIT,
@Login_Persona NVARCHAR(50),
@Pass_Persona NVARCHAR(50),
@Nick_Persona NVARCHAR(50),
@Fotografia NVARCHAR(50),
@id_clave_Operacion INT = NULL,
@clave_op_intracomunitaria BIT,
@nombre_comercial NVARCHAR(100),
@observaciones TEXT
AS
BEGIN
    SET NOCOUNT ON;

    -- Validar y establecer valor predeterminado para id_clave_Operacion si es NULL
    IF @id_clave_Operacion IS NULL
    BEGIN
        SET @id_clave_Operacion = (SELECT TOP 1 
id_clave FROM Eclaves_operacion WHERE activo = 1);
    END

    INSERT INTO Persona_Nuevo
    (
        Nro_Persona,
        Nom_Persona,
        Dni_Persona,
        Ruc_Persona,
        Cod_TipoPersona,
        Sexo_Persona,
        FNac_Personal,
     

   mail_Persona,
        Telefono_Persona,
        Activo,
        Login_Persona,
        Pass_Persona,
        Nick_Persona,
        Fotografia,
        id_clave_Operacion,
        clave_op_intracomunitaria,
        nombre_comercial,
        observaciones
    )
    VALUES
    (
        @Nro_Persona,
        @Nom_Persona,
        @Dni_Persona,
        @Ruc_Persona,
        @Cod_TipoPersona,
        @Sexo_Persona,
        @FNac_Personal,
        @mail_Persona,
        @Telefono_Persona,
        @Activo,
  

      @Login_Persona,
        @Pass_Persona,
        @Nick_Persona,
        @Fotografia,
        @id_clave_Operacion,
        @clave_op_intracomunitaria,
        @nombre_comercial,
        @observaciones
    );

    SET @Cod_Persona = SCOPE_IDENTITY();
END


GO

-- =============================================
-- SP: EliminarClienteSucursal (lÃ­neas 5951-5981)
-- =============================================
CREATE PROCEDURE EliminarClienteSucursal
    @Id_Cliente INT,
    @Id_Sucursal INT,
    @Usuario NVARCHAR(50)
AS
BEGIN
    SET NOCOUNT ON;

    -- Verificar que la relación exista
    IF NOT EXISTS (
        SELECT 1 
        FROM Cliente_Sucursal 
        WHERE Id_Cliente = @Id_Cliente AND Id_Sucursal = @Id_Sucursal
    )
    BEGIN
        RAISERROR('La relación cliente-sucursal no existe.', 16, 1);
        RETURN;
    END

    -- Registrar en una tabla de auditoría
    INSERT INTO Cliente_Sucursal_Auditoria (Id_Cliente, Id_Sucursal, Accion, Fecha, Usuario)
    VALUES (@Id_Cliente, @Id_Sucursal, 'Eliminación', GETDATE(), @Usuario);

    -- Eliminar la relación
    DELETE FROM Cliente_Sucursal
    WHERE Id_Cliente = @Id_Cliente AND Id_Sucursal = @Id_Sucursal;
END;




GO

-- =============================================
-- SP: Insertar_AgenteSucursal (lÃ­neas 6871-6926)
-- =============================================
CREATE PROCEDURE dbo.Insertar_AgenteSucursal
    @Cod_Responsable  INT,            -- = Vehiculo_cliente_nuevo.Codigo
    @Id_CargoFuncion  INT,            -- = Ecargos_funciones.Id_CargoFuncion
    @Comision         DECIMAL(5,2),
    @Activo           BIT,
    @Fecha_Asignacion DATE,
    @Id_AgenteSucursal INT OUTPUT     -- <== devuelve el nuevo ID
AS
BEGIN
    SET NOCOUNT ON;

    BEGIN TRY
        BEGIN TRAN;

        -- Validaciones
        IF NOT EXISTS (SELECT 1 FROM dbo.Vehiculo_cliente_nuevo WHERE Codigo = @Cod_Responsable)
        BEGIN
            RAISERROR(N'El responsable especificado no existe en Vehiculo_cliente_nuevo.', 16, 1);
            ROLLBACK TRAN; RETURN;
        END

        IF NOT EXISTS (SELECT 1 FROM dbo.Ecargos_funciones WHERE Id_CargoFuncion = @Id_CargoFuncion)
        BEGIN
            RAISERROR(N'El cargo especificado no existe en Ecargos_funciones.', 16, 1);
            ROLLBACK TRAN; RETURN;
        END

        -- (Opcional, recomendado) Si se marca como Activo, desactivar asignación activa anterior del mismo punto
        IF (@Activo = 1)
        BEGIN
            UPDATE dbo.Agentes_Sucursal
               SET Activo = 0
             WHERE Cod_Responsable = @Cod_Responsable
               AND Activo = 1;
        END

        INSERT INTO dbo.Agentes_Sucursal
        (
            Cod_Responsable, Id_CargoFuncion, Comision, Activo, Fecha_Asignacion
        )
        VALUES
        (
            @Cod_Responsable, @Id_CargoFuncion, @Comision, @Activo, @Fecha_Asignacion
        );

        SET @Id_AgenteSucursal = SCOPE_IDENTITY();

        COMMIT TRAN;
    END TRY
    BEGIN CATCH
        IF XACT_STATE() <> 0 ROLLBACK TRAN;
        DECLARE @m nvarchar(4000) = ERROR_MESSAGE();
        RAISERROR(@m, 16, 1);
    END CATCH
END


GO


-- =============================================
-- SPs NO ENCONTRADOS
-- =============================================
