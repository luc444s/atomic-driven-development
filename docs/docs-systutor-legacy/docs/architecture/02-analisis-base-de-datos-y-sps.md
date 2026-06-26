# Análisis de Base de Datos y Stored Procedures

**Fecha:** 26/06/2026

---

## 1. Base de Datos: Sys_GMS_ESCR

### Resumen de objetos

| Tipo | Cantidad |
|---|---|
| Tablas | 184 |
| Vistas | 144 |
| Procedimientos almacenados | 944 |
| Funciones | 22 |

### Conexión (app.config)

```xml
<connectionStrings>
  <add name="ConexionPrincipal"
       connectionString="Data Source=ACONCAGUA;Initial Catalog=Sys_GMS_ESCR;User Id=sa;Password=RedSystutor#2026#;MultipleActiveResultSets=True;"
       providerName="System.Data.SqlClient"/>
</connectionStrings>
```

> **⚠️ Atención:** La cadena de conexión incluye credenciales en texto plano. Debe protegerse o moverse a un archivo de configuración externo.

## 2. Stored Procedures — Distribución

### Por prefijo

| Prefijo | Cantidad | Propósito |
|---|---|---|
| `sp_` | 177 | CRUD estándar y operaciones modernas |
| `Mos` / `Mostrar_` | 103 | Consultas SELECT para grids, combos, reportes |
| `Bus` / `Buscar_` | 82 | Búsquedas por nombre, código, RUC, serie |
| `Pro` / `Producto_` | 76 | CRUD y lógica de productos, cilindros, envases |
| `usp_` | 56 | CRUD alternativo (mismo patrón que sp_) |
| `Mod` / `Modificar_` | 33 | Actualizaciones específicas |
| `CON_` / `Config_` | 32 | Configuraciones del sistema |
| `Act` / `Actualizar_` | 32 | Actualizaciones de estado |
| `ins` / `Insertar_` | 25 | Inserciones específicas |
| `CP_` | 22 | Códigos postales y geolocalización |
| `Eli` / `Eliminar_` | 13 | Eliminaciones |
| Otros | ~280 | Funciones auxiliares, reportes, utilidades |

### Por dominio funcional

**CRUD estándar:** `sp_`, `usp_`, `ins_`, `Eli_`, `Act_` — patrón: `_Insertar`, `_Actualizar`, `_Eliminar`, `_Listar`

**Catálogos:**
- Almacenes → `mostrar_almacen`, `Alm_*`
- Productos → `Producto_*`, `Buscar_*Producto*`
- Clientes → `Buscar_Clientex*`, `Per_*`, `Cli_*`
- Proveedores → `COM_Proveedor*`, `Buscar_*Prov*`
- Líneas / Sublíneas / Marcas → `mostrar_linea`, `Lin_*`, `Mar_*`
- Ubicaciones geográficas → `CP_*`, `Ubi_*`

**Movimientos / Transacciones:**
- `Mov_Ingreso_*`, `Mov_Salida_*` — movimientos de almacén
- `Mov_Compras_*`, `Mov_Ventas_*` — compras y ventas
- `Mov_Traslado_*` — traslados entre almacenes
- `Mov_Llenado*` — llenado de bombonas/cilindros

**Operaciones de negocio críticas:**
- Agenda de repartidor → `sp_AgendaRepartidor_*` (~20 SPs)
- Carga de repartidor → `sp_CargaRepartidor_*`
- Planificación → `sp_Planificacion_*`
- Intercambio de cilindros → `sp_IntercambioCliente_*`
- Retorno de vehículo → `sp_RetornoVehiculo_*`

**Facturación electrónica (SUNAT / Nubefact):**
- `sp_Facturacion_*`, `Fact_*`
- `sp_EnviarSunat*`
- `sp_AnularComprobante*`

## 3. SPs Relacionados con Trazabilidad de Cilindros

### Agenda repartidor

| SP | Uso |
|---|---|
| `sp_AgendaRepartidor_Insertar` | Insertar tarea en agenda |
| `sp_AgendaRepartidor_Upsert` | Insertar o actualizar |
| `sp_AgendaRepartidor_MarcarCargado` | Marcar como cargado |
| `sp_AgendaRepartidor_MarcarCargadoPorGuia` | Marcar por guía |
| `sp_AgendaRepartidor_MarcarPorMovimiento` | Marcar por movimiento |
| `sp_AgendaRepartidor_AceptarCargaPorGuia` | Aceptar carga |
| `sp_AgendaRepartidor_MarcarCargaObservadaPorGuia` | Marcar observación |
| `sp_AgendaRepartidor_HistorialPorCliente` | Historial por cliente |
| `usp_Agenda_InsertServicioDesdePlus` | Insertar servicio desde PLUS |
| `usp_Agenda_CerrarDesdePlus` | Cerrar desde PLUS |

### Cilindros / Envases

| SP | Uso |
|---|---|
| `InsertarECilindrosServicios` | Servicios SOLYGAS |
| `ActualizarECilindrosServicios` | Actualizar servicios |
| `ObtenerServiciosPendientes` | Servicios pendientes |
| `Insertar_Reporte_Carga_Peligrosa` | Carga peligrosa |
| `InsertarHistorialEstadoTraslado` | Historial de traslado |
| `ActualizarEstadoMovimiento` | Estado de movimiento |
| `InsertarChoferPorMovimiento` | Asignación chofer |
| `InsertarEquipoPorMovimiento` | Asignación equipo |
| `ECilindroEstadoTransicion` | Transición de estados |

## 4. Tablas Clave para Trazabilidad

| Tabla | Propósito |
|---|---|
| `AGENDA_REPARTIDOR` | Tareas planificadas por repartidor |
| `AGENDA_REPARTIDOR_HISTORIAL` | Auditoría de cambios de estado |
| `AGENDA_PREPARACION_CARGA` | Cilindros preparados para carga |
| `ECabecera_pedido` | Cabecera de pedidos/envases |
| `EDetalle_cpedido` | Detalle de cilindros por pedido |
| `Movimiento` | Movimientos de almacén |
| `DetalleMovimiento` | Detalle de productos en movimientos |
| `ECilindroEstadoActual` | Estado actual de cada cilindro |
| `ECilindroEstadoLog` | Historial de cambios de estado |
| `ECilindroEstadoCatalogo` | Catálogo de estados posibles |
| `ECilindroEstadoTransicion` | Transiciones válidas entre estados |
| `ECilindros_Servicios` | Servicios asociados (SOLYGAS) |
| `Persona_Nuevo` | Clientes, proveedores, repartidores |
| `Cliente_Sucursal` | Puntos de entrega |
| `EChoferesPorMovimiento` | Asignación choferes |
| `EEquiposPorMovimiento` | Asignación equipos/camiones |
| `HistorialEstadosTraslados` | Historial de traslados |
| `EReporte_Cargas_Peligrosas` | Documentos de carga peligrosa |

## 5. Vistas Útiles

| Vista | Propósito |
|---|---|
| `v_AgendaRepartidor_PedidosPendientes` | Pedidos pendientes por repartidor |
| `v_AgendaRepartidor_ResumenPorProducto` | Resumen de productos por agenda |
| `v_ResumenCarga_Repartidor` | Resumen de carga por repartidor |
| `vAgenda_PendienteCarga` | Agenda pendiente de carga |

## 6. Anomalías Detectadas en Cgas.vb

| # | Problema | Detalle |
|---|---|---|
| 1 | SQL texto plano | `BuscarTarifaCliente` (línea 2556) NO usa SP |
| 2 | Duplicación | `consulta_detalle_envase` vs `consultar_detalle_envase` llaman a SPs distintos con misma firma |
| 3 | Código comentado | `Insertarrepdetenv1` (línea 498), `consultar_envase_ventaBlanco` viejo (línea 600) |
| 4 | Calidad despareja | Métodos nuevos (SOLYGAS, post-línea 1575) usan `Using`/`DataTable`; métodos viejos dejan DataReader abierto |
| 5 | Sin transacción | `ActualizarEquipoTransporte` y `EliminarEquipoTransporte` no usan `BeginTransaction` |
