# Módulo Clientes — Vistas con CREATE VIEW (Extraídas desde BD)

Extraído desde: `Sys_GMS_ES` en `ACONCAGUA`
Total vistas que referencian `Persona_Nuevo`: **25**
Total vistas que referencian `Vehiculo_cliente_nuevo`: **17**
Total vistas que referencian `Direccion`: **41**

---

## Vistas del Módulo Clientes (con definición completa)

### v_Agenda_RutaDelDia
```sql
CREATE VIEW dbo.v_Agenda_RutaDelDia
AS
SELECT a.Id_Agenda, a.Fecha_Programada, CONVERT(VARCHAR(5), a.Hora_Programada, 108) AS Hora,
       a.Cod_Repartidor, a.Cod_Cliente, a.Cod_Sucursal, a.Tipo_Tarea, a.Descripcion_Tarea,
       a.Estado_Tarea, a.Ubicacion_Entrega, a.Referencias_Cliente, a.Observaciones_Resultado,
       a.Documento_Asociado, dbo.Persona_Nuevo.Nom_Persona AS Repartidor,
       Persona_Nuevo_1.Nom_Persona AS Cliente
FROM dbo.AGENDA_REPARTIDOR AS a
INNER JOIN dbo.Persona_Nuevo ON a.Cod_Repartidor = dbo.Persona_Nuevo.Cod_Persona
INNER JOIN dbo.Persona_Nuevo AS Persona_Nuevo_1 ON a.Cod_Cliente = Persona_Nuevo_1.Cod_Persona;
```

### vClienteDireccionFiscal
```sql
CREATE VIEW dbo.vClienteDireccionFiscal
AS
SELECT P.Cod_Persona, P.Nom_Persona, D.Id_Direccion, D.Linea1, D.Ubigeo, D.Latitud, D.Longitud
FROM dbo.Persona_Nuevo P
INNER JOIN dbo.Direccion D ON P.Id_Direccion_Fiscal = D.Id_Direccion;
```

### vw_PuntosEntrega_Canonico
```sql
CREATE VIEW dbo.vw_PuntosEntrega_Canonico
AS
SELECT V.Codigo AS Id_PuntoEntrega, V.Id_ClientePersona AS Id_Cliente,
       COALESCE(D.Linea1, V.Direccion) AS Direccion,
       COALESCE(D.Codigo_Postal, V.ubigeo) AS CodigoPostal_o_Ubigeo,
       COALESCE(D.Id_Zona, V.Id_Zona) AS Id_Zona,
       D.Latitud, D.Longitud, V.NombrePunto, V.Contacto, V.Telefono, V.Correoresp,
       V.VentanaHorario, V.Indicaciones, V.Id_RutaAsignada, V.Principal AS EsPrincipal,
       V.Activo AS Estado, V.UsuarioCrea, V.FechaCrea, V.UsuarioMod, V.FechaMod
FROM dbo.Vehiculo_cliente_nuevo V
LEFT JOIN dbo.Direccion D ON D.Id_Direccion = V.Id_Direccion;
```

### vw_PuntoEntrega_UltimaCoord
```sql
CREATE VIEW dbo.vw_PuntoEntrega_UltimaCoord
AS
SELECT x.Id_SucursalCliente AS Codigo, x.Latitud, x.Longitud, x.Fecha_Hora
FROM (
  SELECT rc.*, ROW_NUMBER() OVER(
    PARTITION BY rc.Id_SucursalCliente ORDER BY rc.Fecha_Hora DESC, rc.Id_Registro DESC
  ) AS rn
  FROM dbo.Registro_Coordenadas rc
) x
WHERE x.rn = 1;
```

### VresponsableClienteProveedor
```sql
CREATE VIEW dbo.VresponsableClienteProveedor
AS
SELECT TOP (100) PERCENT dbo.vehiculo_cliente.codigo, dbo.vehiculo_cliente.contacto,
       dbo.vehiculo_cliente.direccion, dbo.Persona.Cod_Persona, dbo.Persona.Nom_Persona,
       dbo.vehiculo_cliente.telefono, dbo.vehiculo_cliente.ubigeo, dbo.Persona.Dni_Persona,
       dbo.Persona.Ruc_Persona, dbo.Persona.garantia, dbo.TipoPersona.Desc_TipoPersona,
       dbo.Persona.Cod_TipoPersona
FROM dbo.vehiculo_cliente
INNER JOIN dbo.Persona ON dbo.vehiculo_cliente.cliente = dbo.Persona.Cod_Persona
INNER JOIN dbo.TipoPersona ON dbo.Persona.Cod_TipoPersona = dbo.TipoPersona.Cod_TipoPersona
WHERE (dbo.Persona.Cod_TipoPersona = 1) OR (dbo.Persona.Cod_TipoPersona = 4);
```

### VresponsablesxCliente
```sql
CREATE VIEW dbo.VresponsablesxCliente
AS
SELECT dbo.vehiculo_cliente.codigo, dbo.Persona.Nom_Persona, dbo.vehiculo_cliente.contacto,
       dbo.vehiculo_cliente.direccion, dbo.Persona.garantia, dbo.Persona.Cod_Persona,
       dbo.vehiculo_cliente.correoresp, dbo.vehiculo_cliente.telefono, dbo.Persona.Cod_TipoPersona,
       dbo.vehiculo_cliente.ubigeo, dbo.Persona.Dni_Persona, dbo.Persona.Ruc_Persona,
       dbo.vehiculo_cliente.zonaresp, dbo.Persona.mail_Persona, dbo.vehiculo_cliente.cliente,
       dbo.Persona.diascred, dbo.Persona.LineaCredito_Persona
FROM dbo.vehiculo_cliente INNER JOIN dbo.Persona ON dbo.vehiculo_cliente.cliente = dbo.Persona.Cod_Persona;
```

### VresponsablesxClientePRO
```sql
CREATE VIEW dbo.VresponsablesxClientePRO
AS
SELECT dbo.Vehiculo_cliente_nuevo.Codigo, dbo.Vehiculo_cliente_nuevo.Direccion,
       dbo.Vehiculo_cliente_nuevo.Contacto, dbo.Vehiculo_cliente_nuevo.Telefono,
       dbo.Vehiculo_cliente_nuevo.Correoresp, dbo.Vehiculo_cliente_nuevo.Enlace_GPS,
       dbo.Vehiculo_cliente_nuevo.Id_Zona, dbo.Vehiculo_cliente_nuevo.Dreparto,
       dbo.Vehiculo_cliente_nuevo.Id_Agente_Asignado, dbo.Vehiculo_cliente_nuevo.Observ_Responsable,
       dbo.Vehiculo_cliente_nuevo.Principal, dbo.Vehiculo_cliente_nuevo.Activo,
       dbo.Vehiculo_cliente_nuevo.Fecha_Registro, dbo.Vehiculo_cliente_nuevo.Id_ClientePersona AS Cliente,
       dbo.Persona_Nuevo.Nom_Persona, dbo.Persona_Nuevo.Dni_Persona, dbo.Persona_Nuevo.Ruc_Persona,
       dbo.Persona_Nuevo.mail_Persona, dbo.Persona_Nuevo.Telefono_Persona, dbo.Persona_Nuevo.Cod_TipoPersona,
       dbo.Creditos.Cod_VehiculoCliente, dbo.Creditos.Linea_Credito, dbo.Creditos.Dias_Credito,
       dbo.Creditos.Activo AS CredActivo, dbo.Persona_Nuevo.Activo AS garantia,
       dbo.Vehiculo_cliente_nuevo.ubigeo, dbo.Persona_Nuevo.Cod_Persona
FROM dbo.Vehiculo_cliente_nuevo
INNER JOIN dbo.Persona_Nuevo ON dbo.Vehiculo_cliente_nuevo.Id_ClientePersona = dbo.Persona_Nuevo.Cod_Persona
LEFT OUTER JOIN dbo.Creditos ON dbo.Persona_Nuevo.Cod_Persona = dbo.Creditos.Cod_VehiculoCliente;
```

### VResponsableEmpresa
```sql
CREATE VIEW dbo.VResponsableEmpresa
AS
SELECT dbo.Vehiculo_cliente_nuevo.Codigo, dbo.Vehiculo_cliente_nuevo.Contacto,
       dbo.Vehiculo_cliente_nuevo.Direccion, dbo.Persona_Nuevo.Cod_Persona,
       dbo.Persona_Nuevo.Nom_Persona, dbo.Persona_Nuevo.Cod_TipoPersona,
       dbo.Vehiculo_cliente_nuevo.Telefono, dbo.Vehiculo_cliente_nuevo.ubigeo,
       dbo.Persona_Nuevo.Dni_Persona, dbo.Persona_Nuevo.Ruc_Persona,
       dbo.Vehiculo_cliente_nuevo.Correoresp, dbo.Persona_Nuevo.mail_Persona,
       dbo.Vehiculo_cliente_nuevo.garantia
FROM dbo.Vehiculo_cliente_nuevo
INNER JOIN dbo.Persona_Nuevo ON dbo.Vehiculo_cliente_nuevo.Id_ClientePersona = dbo.Persona_Nuevo.Cod_Persona
WHERE (dbo.Persona_Nuevo.Cod_TipoPersona = 1) OR (dbo.Persona_Nuevo.Cod_TipoPersona = 4);
```

### VTICKET (resumen columnas cliente)
```sql
CREATE VIEW dbo.VTICKET
AS
SELECT ...
       dbo.Persona_Nuevo.Cod_Persona, dbo.Persona_Nuevo.Nom_Persona AS Cliente_empresa,
       dbo.Creditos.Linea_Credito, dbo.Creditos.Dias_Credito,
       dbo.Persona_Nuevo.Dni_Persona, dbo.Persona_Nuevo.Ruc_Persona,
       dbo.Persona_Nuevo.mail_Persona, dbo.Persona_Nuevo.Telefono_Persona,
       ...
       dbo.Direccion.Linea1 AS Direccion, dbo.Persona_Nuevo.Id_Direccion_Fiscal
FROM dbo.Movimiento
...
INNER JOIN dbo.Persona_Nuevo ON dbo.Movimiento.Persona = dbo.Persona_Nuevo.Cod_Persona
INNER JOIN dbo.Formas_pago ON dbo.Persona_Nuevo.Id_FormaPago = dbo.Formas_pago.Id_FormaPago
INNER JOIN dbo.Direccion ON dbo.Persona_Nuevo.Id_Direccion_Fiscal = dbo.Direccion.Id_Direccion;
```
(Vista completa en `01_ddl_tablas.md` por límite de espacio. ~70 columnas, 15 JOINs)

### VTicketDatosCLI
```sql
-- Similar a VTICKET pero con datos adicionales de sucursal:
-- dbo.Vehiculo_cliente_nuevo.Direccion AS Direccion_empresa
-- dbo.Vehiculo_cliente_nuevo.Telefono, dbo.Vehiculo_cliente_nuevo.Correoresp
-- JOIN con DISTRITO, PROVINCIA, DEPARTAMENTO para ubicación completa
```

### Vreporte_persona
```sql
CREATE VIEW dbo.Vreporte_persona
AS
SELECT TOP (100) PERCENT dbo.ECabecera_pedido.cod_cpedido, dbo.ECabecera_pedido.fecha_pedido,
       dbo.Persona_Nuevo.Nom_Persona, dbo.Persona_Nuevo.Cod_Persona, ...
FROM dbo.Vehiculo_cliente_nuevo
INNER JOIN dbo.ECabecera_pedido
INNER JOIN dbo.Persona_Nuevo ON dbo.ECabecera_pedido.persona = dbo.Persona_Nuevo.Cod_Persona
    ON dbo.Vehiculo_cliente_nuevo.Id_ClientePersona = dbo.ECabecera_pedido.persona
LEFT OUTER JOIN dbo.Producto INNER JOIN dbo.EDetalle_cpedido ...
```
(Vista completa ~40 columnas, usada por CRreporte_persona)

### Vreporte_Documento
```sql
CREATE VIEW dbo.Vreporte_Documento
AS
SELECT ...
       dbo.Persona_Nuevo.Nom_Persona, dbo.Persona_Nuevo.Cod_Persona,
       dbo.Vehiculo_cliente_nuevo.Contacto, dbo.Vehiculo_cliente_nuevo.Id_ClientePersona
FROM dbo.Vehiculo_cliente_nuevo
INNER JOIN dbo.ECabecera_pedido INNER JOIN dbo.Persona_Nuevo
    ON dbo.ECabecera_pedido.persona = dbo.Persona_Nuevo.Cod_Persona
    ON dbo.Vehiculo_cliente_nuevo.Id_ClientePersona = dbo.ECabecera_pedido.persona;
```

### Vreporte_Documentoenvase
```sql
-- ~40 columnas, JOINs: Persona_Nuevo + Vehiculo_cliente_nuevo + Creditos + ZONA
-- Incluye: Nom_Persona, Dni_Persona, Ruc_Persona, nombre_comercial,
--          LineaCredito_Persona, diascred, Contacto, Direccion, Telefono, Correoresp
-- Usada por reportes de documento/envase
```

### Vreporte_Documentoenvase_SalidaRecojo
```sql
-- ~55 columnas, JOINs: Movimiento + Creditos + ZONA + Vehiculo_cliente_nuevo +
-- ECabecera_pedido + Persona_Nuevo + Ecargos_funciones + Comprobante + ...
-- Filtro: motivo='Venta', TipoComprobante=20, condicion<>'SERVICIO', CargoFuncion='chofer'
```

### Vreporte_Documentoenvase_Traslado
```sql
-- ~55 columnas, similar a SalidaRecojo pero sin filtro de motivo
```

### Vreporte_DocSalidaRecojoPro
```sql
-- ~60 columnas, JOINs complejos con Movimiento + DetalleMovimiento + Producto +
-- ECabecera_pedido + EDetalle_cpedido + Edetalle_Producto_Bombona +
-- Persona_Nuevo + Vehiculo_cliente_nuevo + Creditos
-- Filtro: TipoAtencion IN (1, 9)
```

### Vdetalle_EnvaseANTIGUO
```sql
-- ~30 columnas, JOINs con Persona_Nuevo + Reporte_mov_envases + ECabecera_pedido +
-- Producto + Eph + EsubVista_EstadoTraslado + Almacen
-- Incluye: Persona_Nuevo.Cod_Persona, Persona_Nuevo.Nom_Persona
```

### vECilindro_UbicacionActual
```sql
CREATE VIEW dbo.vECilindro_UbicacionActual
AS
SELECT dbo.ECilindroEstadoActual.ProductoId, ..., dbo.Persona_Nuevo.Cod_Persona AS Id_Persona,
       dbo.Persona_Nuevo.Nom_Persona AS RazonSocial, dbo.Persona_Nuevo.Cod_TipoPersona,
       CASE WHEN dbo.Persona_Nuevo.Cod_TipoPersona = 1 THEN 'CLIENTE'
            WHEN dbo.Persona_Nuevo.Cod_TipoPersona = 4 THEN 'PROVEEDOR'
            ELSE 'OTRO' END AS TipoPersonaDescripcion,
       ..., dbo.Vehiculo_cliente_nuevo.Contacto, dbo.Vehiculo_cliente_nuevo.Telefono,
       dbo.Vehiculo_cliente_nuevo.Direccion
FROM dbo.EDetalle_cpedido
INNER JOIN dbo.ECilindroEstadoActual ...
INNER JOIN dbo.ECabecera_pedido ...
INNER JOIN dbo.Vehiculo_cliente_nuevo
INNER JOIN dbo.Persona_Nuevo ON dbo.Vehiculo_cliente_nuevo.Id_ClientePersona = dbo.Persona_Nuevo.Cod_Persona
WHERE dbo.Persona_Nuevo.Cod_TipoPersona IN (1, 4);
```

### vCilindroEstadoActualDet, vCilindroEstadoLog, vCilindroEstadoLogDet
```sql
-- Las 3 vistas consultan Persona_Nuevo para obtener Nom_Persona del usuario
-- que realizó el cambio de estado del cilindro
-- vCilindroEstadoActualDet: Persona_Nuevo AS pu ON pu.Cod_Persona = va.Usuario
-- vCilindroEstadoLog: Persona_Nuevo AS U ON L.Usuario = U.Cod_Persona
-- vCilindroEstadoLogDet: Persona_Nuevo PN ON PN.Cod_Persona = L.Usuario
```

### Vista_Contratos_*
```sql
-- 5 vistas de contratos (Alerta_Contacto, ProximosAVencer, RecientementeVencidos,
-- UltimoEvento, Resumen_PorCliente)
-- Todas hacen INNER JOIN con Persona_Nuevo ON Contratos.Cod_Cliente = Persona_Nuevo.Cod_Persona
-- Incluyen: Nom_Persona, mail_Persona, Telefono_Persona
-- Filtran por Estado = 'VIGENTE' y fechas de vencimiento
```

### vw_Historial_Servicios_Cilindro
```sql
CREATE VIEW dbo.vw_Historial_Servicios_Cilindro AS
SELECT ecs.id_cilindro_servicio, mv.FullDoc, ..., mv.Persona AS Cod_Persona,
       pn.Nom_Persona, vc.Codigo AS Cod_SucursalCliente, vc.NombrePunto, ...
FROM dbo.ECilindros_Servicios ecs
JOIN dbo.Movimiento mv ON mv.Cod_Movimiento = ecs.cod_movimiento
LEFT JOIN dbo.Persona_Nuevo pn ON pn.Cod_Persona = mv.Persona
LEFT JOIN dbo.Vehiculo_cliente_nuevo vc ON vc.Codigo = mv.dnichofer
LEFT JOIN dbo.Producto pServ ON pServ.cod_producto = ecs.id_servicio;
```

### VticketGuia
```sql
-- Usa tabla dbo.Persona (antigua, no Persona_Nuevo)
-- INNER JOIN dbo.Persona ON dbo.Movimiento.Persona = dbo.Persona.Cod_Persona
```

### VticketCtrolEnvases
```sql
-- Usa tabla dbo.Persona (antigua, no Persona_Nuevo)
-- INNER JOIN dbo.Persona ON dbo.Movimiento.Persona = dbo.Persona.Cod_Persona
```

### VESTADO_CUENTA_ADM
```sql
-- NO usa Persona_Nuevo. Usa CAJA_ADM + Destino.
-- Solo datos de caja administrativa, no de clientes.
```

### Estado_cuenta
```sql
-- Usa tabla dbo.Persona (antigua, no Persona_Nuevo)
-- Comprobante + Persona + Cancelaciones + Almacen + TipoDoc
-- Filtro: TipoComprobante = 3
```

### vsaldo
```sql
-- No usa Persona_Nuevo. Solo Comprobante + Cancelaciones.
-- Calcula saldo como AVG(Total) - SUM(Monto)
```

---

## Vistas que usan tabla Persona (antigua, no Persona_Nuevo)

| Vista | Tabla usada | Nota |
|-------|-------------|------|
| `VresponsableClienteProveedor` | `dbo.Persona` | Usa `vehiculo_cliente` (antiguo) |
| `VresponsablesxCliente` | `dbo.Persona` | Usa `vehiculo_cliente` (antiguo) |
| `VticketGuia` | `dbo.Persona` | Facturación legacy |
| `VticketCtrolEnvases` | `dbo.Persona` | Facturación legacy |
| `Estado_cuenta` | `dbo.Persona` | Estado cuenta legacy |

---

## v_ClientesEnRiesgo

**NO EXISTE** físicamente en la BD. Probablemente era una vista planeada que nunca se creó, o existió en una versión anterior y fue eliminada.

---

## Resumen

| Grupo | Cantidad |
|-------|----------|
| Vistas con Persona_Nuevo (activo) | **25** |
| Vistas con Persona (antigua, legacy) | **5** |
| Vistas con Vehiculo_cliente_nuevo | **17** |
| Vistas con Direccion | **41** |
| Vistas ahora documentadas con CREATE VIEW | **~20** |
| Vistas pendientes (listadas pero extraer definición) | **~124** |
