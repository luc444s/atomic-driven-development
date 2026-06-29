# Módulo Clientes — Vistas y Funciones

## Estado de la documentación

| Tipo | Cantidad | Documentadas con CREATE |
|------|----------|------------------------|
| Vistas | **144** listadas por nombre | **0** con CREATE VIEW |
| Funciones | **22** en `02_stored_procedures.txt` | **22** con CREATE FUNCTION |

**Ninguna vista del módulo clientes tiene su definición CREATE VIEW documentada en los archivos actuales.**
Las 144 vistas están solo listadas por nombre en `01_tablas.txt` (líneas 187–330).

---

## Vistas candidatas del módulo clientes (por nombre)

Basado en análisis de nombres, estas vistas probablemente consultan `Persona_Nuevo`, `Direccion`, `Vehiculo_cliente_nuevo` o `Cliente_Sucursal`:

### Vistas que usan Persona_Nuevo

| Vista | Uso probable |
|-------|-------------|
| `v_ClientesEnRiesgo` | Clientes con crédito excedido o vencido |
| `vClienteDireccionFiscal` | JOIN Persona_Nuevo + Direccion |
| `Vreporte_persona` | Datos completos de persona para CRreporte_persona |
| `VTicketDatosCLI` | Datos del cliente en ticket/factura |
| `VresponsableClienteProveedor` | Responsables filtrados por tipo persona |
| `VresponsablesxCliente` | Responsables asignados a clientes |
| `VresponsablesxClientePRO` | Versión PRO de responsables |
| `Vista_Contratos_Alerta_Contacto` | Contratos con alertas de contacto |
| `Vista_Contratos_ProximosAVencer` | Contratos próximos a vencer |
| `Vista_Contratos_RecientementeVencidos` | Contratos recién vencidos |
| `Vista_Contratos_UltimoEvento` | Último evento de cada contrato |
| `Vista_Resumen_Contratos_PorCliente` | Resumen de contratos agrupados |
| `Estado_cuenta` | Estado de cuenta consolidado |
| `VESTADO_CUENTA_ADM` | Estado de cuenta administrativo (usado por CREstadoCtaAdm) |
| `vsaldo` | Saldo por cliente |
| `VlistarVentasImpagas` | Ventas impagas (usado por CRDeudasxCobrar) |

### Vistas que usan Vehiculo_cliente_nuevo y/o Direccion

| Vista | Uso probable |
|-------|-------------|
| `vw_PuntosEntrega_Canonico` | Vista canónica de puntos de entrega |
| `vw_PuntoEntrega_UltimaCoord` | Últimas coordenadas por punto |
| `v_Agenda_RutaDelDia` | Agenda con puntos de entrega por ruta |
| `v_AgendaRepartidor_PedidosPendientes` | Pedidos pendientes por repartidor |
| `v_AgendaRepartidor_ResumenPorProducto` | Resumen por producto |
| `v_AgendaRepartidor_ResumenPorProducto_Detalle` | Detalle por producto |
| `Vista_Envases_Servicios` | Envases por servicio/punto |
| `VistaEnvasesPorServicio` | Envases agrupados por servicio |
| `VDETALLE_ENVASE` / `VISTADETALLE_ENVASE` | Detalle de envases |
| `Vista_CodBar_Envases` | Códigos de barra de envases |
| `VMOSTRAR_ESTENVASES` | Estado de envases |

### Vistas de ticketería que usan cliente

| Vista | Uso probable |
|-------|-------------|
| `VTICKET` | Ticket de factura/venta (usado por vTICKETFAC) |
| `VTicketDatosCLI` | Datos del cliente para ticket |
| `VticketGuia` | Ticket de guía de remisión |
| `VticketCtrolEnvases` | Ticket control de envases |
| `Vimpresion_letra` | Impresión de letras (usado por CRLetras) |

### Vistas de ventas que referencian cliente

| Vista | Uso probable |
|-------|-------------|
| `Vventaslinea` / `vventaslinea1` | Ventas por línea |
| `Vventaslineasublinea` | Ventas por línea+sublinea |
| `vventassublinea1` | Ventas por sublinea |
| `VVentastotalesxsuc` | Ventas totales por sucursal |
| `VMostrarVentasDetalladas` | Ventas detalladas |
| `VMASVEND` | Productos más vendidos |
| `VUtilidades` | Utilidades por venta |
| `VColegiadoxUbigeo` | Colegiados por ubicación |

---

## Funciones

Las 22 funciones documentadas en `02_stored_procedures.txt`:

| Función | Tipo | Parámetros | ¿Toca tablas del módulo clientes? |
|---------|------|-----------|-----------------------------------|
| `fn_ADR_Points` | Scalar | `@CodProducto INT, @Cantidad DECIMAL` | ❌ |
| `fn_ContenidoCilindro` | Scalar | `@CodProducto int` | ❌ |
| `fn_diagramobjects` | Scalar | (ninguno) | ❌ |
| `fn_HaversineKm` | Scalar | `@lat1, @lon1, @lat2, @lon2 FLOAT` | ❌ (matemática) |
| `fn_split` | TVF | `@string, @delimiter` | ❌ (helper) |
| `fn_StockDisponible` | Scalar | `@CodProducto, @IdAlmacen` | ❌ |
| `fn_StockFisico_Planificador` | Scalar | `@CodProducto, @IdAlmacen` | ❌ |
| `fn_StockFisico_Planificador_Grupo` | Scalar | `@CodGrupo, @IdAlmacen` | ❌ |
| `fn_StockReal` | Scalar | `@CodProducto, @IdAlmacen` | ❌ |
| `fn_TaraCilindro` | Scalar | `@CodProducto int` | ❌ |
| `fn_TTE_Categoria` | TVF | `@CodProducto int` | ❌ |
| `fnJuntaTexto` | Scalar | `@Name int` | ❌ |
| `fnmostrar_costo` | Scalar | `@Name, @Almacen, @FI, @FF` | ❌ |
| `fnmostrar_prov` | Scalar | `@Name int` | ❌ (usa tabla `Persona`, no `Persona_Nuevo`) |
| `fnMOSTRAR_SALDO` | Scalar | `@Name int` | ❌ |
| `fnMOSTRARDIASDEVOLVER` | Scalar | `@fecha, @producto` | ❌ |
| `fnmostrarultimoenvase` | Scalar | `@Name int` | ❌ |
| `FormatNum` | Scalar | `@number, @format` | ❌ (formateo) |
| `udf_DistanciaKm` | Scalar | `@lat1, @lon1, @lat2, @lon2` | ❌ (matemática) |
| `ufn_ADR_Factor` | Scalar | `@Valor` | ❌ |
| `ufn_Valida_ADR` | Scalar | `@ProductoGasId` | ❌ |
| `ufn_Valida_PH` | Scalar | `@CilindroId` | ❌ |

**Ninguna función toca Persona_Nuevo, Direccion, Vehiculo_cliente_nuevo ni Cliente_Sucursal.**

---

## Acción requerida

Para obtener las definiciones faltantes de vistas, ejecutar en SQL Server:

```sql
SELECT
    SCHEMA_NAME(v.schema_id) AS [schema],
    v.name AS [view_name],
    m.definition
FROM sys.sql_modules m
JOIN sys.views v ON v.object_id = m.object_id
WHERE SCHEMA_NAME(v.schema_id) = 'dbo'
    AND (m.definition LIKE '%Persona_Nuevo%'
         OR m.definition LIKE '%Direccion%'
         OR m.definition LIKE '%Vehiculo_cliente_nuevo%'
         OR m.definition LIKE '%Cliente_Sucursal%')
ORDER BY v.name;
```
