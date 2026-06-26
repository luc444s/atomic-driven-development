# 02 — Mapeo Base de Datos: SQL Server 2014 → PostgreSQL 16

## 1. Reglas Generales de Transformación de Tipos

| SQL Server | PostgreSQL | Notas |
|-----------|-----------|-------|
| int | INTEGER | mismo |
| bigint | BIGINT | mismo |
| smallint | SMALLINT | mismo |
| tinyint | SMALLINT | SQL Server tinyint = 0-255 |
| bit | BOOLEAN | |
| nvarchar(n) | VARCHAR(n) | mismo comportamiento |
| varchar(n) | VARCHAR(n) | |
| nvarchar(MAX) | TEXT | |
| ntext | TEXT | obsoleto en SQL Server |
| text | TEXT | |
| datetime | TIMESTAMP | |
| datetime2 | TIMESTAMP | |
| date | DATE | |
| time | TIME | |
| smallmoney | NUMERIC(10,4) | |
| money | NUMERIC(19,4) | |
| decimal(p,s) | NUMERIC(p,s) | |
| float | DOUBLE PRECISION | |
| real | REAL | |
| image | BYTEA | |
| varbinary(max) | BYTEA | |
| uniqueidentifier | UUID | |
| char(n) | CHAR(n) | |
| nchar(n) | CHAR(n) | |
| timestamp | BYTEA (no usar) | rowversion en SQL, no timestamp real |
| tinyint identity | SMALLINT GENERATED ALWAYS AS IDENTITY | |
| int identity | INTEGER GENERATED ALWAYS AS IDENTITY | |
| bigint identity | BIGINT GENERATED ALWAYS AS IDENTITY | |

## 2. Mapeo de Tablas por Módulo

### 2.1 Core — Personas / Clientes / Proveedores

**Persona_Nuevo → personas**
- Cod_Persona (int PK) → id (INTEGER PK GENERATED ALWAYS AS IDENTITY)
- Nro_Persona (nvarchar(50)) → codigo (VARCHAR(50))
- Nom_Persona (nvarchar(200)) → nombre (VARCHAR(200))
- Dni_Persona (nvarchar(20)) → dni (VARCHAR(20))
- Ruc_Persona (nvarchar(20)) → ruc (VARCHAR(20))
- Cod_TipoPersona (int FK) → tipo_persona_id (INTEGER FK → tipos_persona)
- Sexo_Persona (nvarchar(10)) → sexo (VARCHAR(10))
- FNac_Personal (date) → fecha_nacimiento (DATE)
- mail_Persona (nvarchar(100)) → email (VARCHAR(100))
- Telefono_Persona (nvarchar(50)) → telefono (VARCHAR(50))
- Activo (bit) → activo (BOOLEAN DEFAULT true)
- Login_Persona (nvarchar(50)) → login (VARCHAR(50)) [login de usuario del sistema]
- Pass_Persona (nvarchar(50)) → password_hash (VARCHAR(255)) [se hashea con bcrypt]
- Documento_Principal (nvarchar(50)) → documento_principal (VARCHAR(50))
- Tipo_facturacion (nvarchar(50)) → tipo_facturacion (VARCHAR(50))
- Id_FormaPago (int FK) → forma_pago_id (INTEGER FK)
- Id_Direccion_Fiscal (int FK) → direccion_fiscal_id (INTEGER FK → direcciones)
- PaisCodigo (varchar(5)) → pais_codigo (VARCHAR(5))
- observaciones (nvarchar(MAX)) → observaciones (TEXT)
- Fecha_Registro implícita → created_at (TIMESTAMP DEFAULT NOW())
- Usuario_Registro implícito → created_by (INTEGER FK → usuarios)

⚠️ Pass_Persona legacy usa MD5 (inseguro). En OSS usar bcrypt.

**Direccion → direcciones**
- Solo como referencia. Tabla separada para direcciones múltiples.

**Vehiculo_cliente_nuevo → establecimientos (client_sucursales)**
- Tabla clave en logística: representa los puntos de entrega de cada cliente.
- Codigo (int PK) → id (INTEGER PK)
- Contacto (nvarchar(100)) → contacto (VARCHAR(100))
- Direccion (nvarchar(200)) → direccion (VARCHAR(200))
- Id_ClientePersona (int FK) → cliente_id (INTEGER FK → personas)
- Telefono (nvarchar(50)) → telefono (VARCHAR(50))
- Id_Zona (int FK) → zona_id (INTEGER FK)
- Principal (bit) → es_principal (BOOLEAN)
- Dreparto (nvarchar(50)) → dia_reparto (VARCHAR(50))
- Enlace_GPS (nvarchar(200)) → enlace_gps (VARCHAR(200))
- Activo (bit) → activo (BOOLEAN DEFAULT true)

### 2.2 Core — Productos

**Producto → productos**
- cod_producto (int PK) → id (INTEGER PK)
- Nro_Producto (nvarchar(20)) → codigo (VARCHAR(20)) [usado como SERIE del cilindro]
- Desc_Producto (nvarchar(3000)) → descripcion (VARCHAR(500))
- cod_grupo (int FK self) → grupo_id (INTEGER FK → productos) [apunta al "gas padre"]
- Cod_Linea (int FK) → linea_id (INTEGER FK)
- Cod_SubCategoria (int FK) → subcategoria_id (INTEGER FK)
- Cod_Unidad (int FK) → unidad_id (INTEGER FK)
- Cod_TipoInsumo (int FK) → tipo_insumo_id (INTEGER FK)
- Marca_Producto (int FK) → marca_id (INTEGER FK)
- Estado_Producto (int FK) → estado_producto_id (INTEGER FK)
- Precio_Producto (money) → precio (NUMERIC(19,4))
- Costo_Producto (money) → costo (NUMERIC(19,4))
- StockMin_Producto (float) → stock_minimo (DOUBLE PRECISION)
- peso_producto (float) → peso (DOUBLE PRECISION)
- Cont (float) → contenido (DOUBLE PRECISION) [kg de gas]
- servicio (int) → es_servicio (BOOLEAN) [1 = es servicio, 0 = es producto físico]
- ADR_Categoria (nvarchar(50)) → adr_categoria (VARCHAR(50))
- ADR_UN (varchar(10)) → adr_un_numero (VARCHAR(10))
- ADR_Etiqueta (varchar(50)) → adr_etiqueta (VARCHAR(50))
- ADR_Tunel (varchar(10)) → adr_tunel (VARCHAR(10))
- ADR_Puntos (int) → adr_puntos (INTEGER)
- ADR_PesoKg (decimal) → adr_peso_kg (NUMERIC)
- ADR_M3 (decimal) → adr_volumen_m3 (NUMERIC)
- condicion (nvarchar(50)) → condicion (VARCHAR(50)) [NUEVO, USADO, etc.]
- activo implícito por Estado_Producto → activo (BOOLEAN DEFAULT true)
- created_at (TIMESTAMP), updated_at (TIMESTAMP)

⚠️ Legacy tiene 2 columnas barcode (image y varchar). En OSS usar solo VARCHAR(150).

### 2.3 Core — Almacenes

**Almacen → almacenes**
- Cod_Almacen (int PK) → id (INTEGER PK)
- Desc_Almacen (nvarchar(100)) → nombre (VARCHAR(100))
- Direccion_Almacen (nvarchar(100)) → direccion (VARCHAR(200))
- Ruc_Almacen (nvarchar(50)) → ruc (VARCHAR(20))
- Telf_Almacen (nvarchar(2500)) → telefono (VARCHAR(50))
- Cod_RazonSocial (int FK) → razon_social_id (INTEGER FK)
- Activo (bit) → activo (BOOLEAN DEFAULT true)

### 2.4 Core — Movimiento + DetalleMovimiento

**Movimiento → movimientos**
- Cod_Movimiento (int PK) → id (INTEGER PK)
- Fecha (datetime) → fecha (TIMESTAMP)
- fecha_emision (datetime) → fecha_emision (TIMESTAMP)
- NroGuia (nvarchar(100)) → nro_guia (VARCHAR(100))
- NroDocumento (nvarchar(50)) → nro_documento (VARCHAR(50))
- TipoMovimiento (int FK) → tipo_movimiento_id (INTEGER FK)
- TipoDocumento (nvarchar(50)) → tipo_documento (VARCHAR(50))
- SerieDoc (nvarchar(20)) → serie_doc (VARCHAR(20))
- NroDocCorrelativo (int) → nro_doc_correlativo (INTEGER)
- FullDoc (nvarchar(27)) → documento_completo (VARCHAR(27)) [Serie + Nro]
- Persona (int FK) → persona_id (INTEGER FK)
- Almacen (int FK) → almacen_id (INTEGER FK)
- Total (money) → total (NUMERIC(19,4))
- IGV (float) → igv (NUMERIC(19,4))
- DEscuento (money) → descuento (NUMERIC(19,4))
- Estado (int) → estado_id (INTEGER FK)
- EstadoPago (int) → estado_pago_id (INTEGER FK)
- EstadoTraslado (nvarchar(50)) → estado_traslado (VARCHAR(50))
- Id_Cpedido (nvarchar(50)) → pedido_envase_id (INTEGER FK → ecabecera_pedido)
- Observacion (nvarchar(4000)) → observaciones (TEXT)
- Moneda (nvarchar(50)) → moneda (VARCHAR(10))
- TC (money) → tipo_cambio (NUMERIC(19,4))
- Transportista (nvarchar(50)) → transportista (VARCHAR(100))
- Placa (nvarchar(50)) → placa_vehiculo (VARCHAR(20))
- LugarDestino (nvarchar(500)) → lugar_destino (VARCHAR(200))
- DirDestino (nvarchar(4000)) → direccion_destino (VARCHAR(500))
- TipoAtencion (int FK) → tipo_atencion_id (INTEGER FK)
- Usuario (int FK) → usuario_id (INTEGER FK)
- Suc_cliente (int FK) → establecimiento_id (INTEGER FK)
- CodFactura (int FK) → comprobante_id (INTEGER FK)
- Id_MovimientoPadre (int FK self) → movimiento_padre_id (INTEGER FK)
- created_at (TIMESTAMP), updated_at (TIMESTAMP)

**DetalleMovimiento → detalle_movimientos**
- Ids (int PK) → id (INTEGER PK)
- CodMovimiento (int FK) → movimiento_id (INTEGER FK NOT NULL)
- CodProducto (int FK) → producto_id (INTEGER FK)
- StkIngreso (float) → cantidad_ingreso (NUMERIC(19,4) DEFAULT 0)
- StkEgreso (float) → cantidad_egreso (NUMERIC(19,4) DEFAULT 0)
- CANT (int) → cantidad (INTEGER DEFAULT 0)
- PVenta (money) → precio_venta (NUMERIC(19,4))
- Pcompra (money) → precio_compra (NUMERIC(19,4))
- Total_items (money) → total_item (NUMERIC(19,4))
- descuento (money) → descuento (NUMERIC(19,4) DEFAULT 0)
- Estadoitem (nvarchar(50)) → estado_item (VARCHAR(20)) ['R'=Registrado, etc.]
- Serie (varchar(50)) → serie (VARCHAR(50))
- CantPlanificada (decimal) → cantidad_planificada (NUMERIC(19,4) DEFAULT 0)
- Glosa (nvarchar(100)) → glosa (VARCHAR(200))
- Obs (nvarchar(4000)) → observaciones (TEXT)
- created_at (TIMESTAMP), updated_at (TIMESTAMP)

### 2.5 GLP — Envases / Cilindros

**ECilindroEstadoCatalogo → cilindro_estados_catalogo**
- Estado (varchar(30) PK) → codigo (VARCHAR(30) PK)
- EsFinal (bit) → es_final (BOOLEAN DEFAULT false)

**ECilindroEstadoTransicion → cilindro_estados_transiciones**
- EstadoOrigen (varchar(30) FK) → estado_origen (VARCHAR(30) FK)
- EstadoDestino (varchar(30) FK) → estado_destino (VARCHAR(30) FK)
- PK compuesta (origen, destino)

**ECilindroEstadoRegla → cilindro_estados_reglas**
- EstadoDesde (varchar(30) FK) → estado_desde (VARCHAR(30) FK)
- EstadoHasta (varchar(30) FK) → estado_hasta (VARCHAR(30) FK)

**ECilindroEstadoLog → cilindro_estados_log**
- IdEstado (bigint PK) → id (BIGINT PK)
- Serie (nvarchar(100)) → serie (VARCHAR(100))
- Estado (varchar(50)) → estado (VARCHAR(50) FK)
- Fecha (datetime) → fecha (TIMESTAMP DEFAULT NOW())
- Usuario (int FK) → usuario_id (INTEGER FK)
- Observacion (nvarchar(300)) → observacion (VARCHAR(300))
- Origen (nvarchar(100)) → origen (VARCHAR(100))
- MotivoCodigo (varchar(30)) → motivo_codigo (VARCHAR(30))
- AlmacenId (int FK) → almacen_id (INTEGER FK)
- INDEX ON (serie, fecha DESC)

**ECilindroEstadoActual → cilindro_estados_actual** (vista materializada o tabla)
- Serie (varchar(50) PK) → serie (VARCHAR(50) PK)
- ProductoId (int FK) → producto_id (INTEGER FK)
- Estado (varchar(80)) → estado (VARCHAR(50) FK)
- Fecha (datetime) → ultima_fecha (TIMESTAMP)
- UsuarioId (int FK) → usuario_id (INTEGER FK)
- AlmacenId (int FK) → almacen_id (INTEGER FK)
- Origen (varchar(100)) → origen (VARCHAR(100))

**ECabecera_pedido → pedidos_envases (envase_orders)**
- cod_cpedido (int PK) → id (INTEGER PK)
- fecha_pedido (datetime) → fecha_pedido (TIMESTAMP)
- persona (int FK) → cliente_id (INTEGER FK)
- tipo_movimiento (nvarchar(50)) → tipo_movimiento (VARCHAR(50))
- serie (nvarchar(50)) → serie_documento (VARCHAR(50))
- nro (int) → numero_documento (INTEGER)
- forma_mov (nvarchar(50)) → forma_movimiento (VARCHAR(50))
- motivo (nvarchar(50)) → motivo (VARCHAR(50))
- documento_asoc (nvarchar(1500)) → documento_asociado (VARCHAR(100))
- Almacen (int FK) → almacen_id (INTEGER FK)
- Transportista (nvarchar(50)) → transportista (VARCHAR(100))
- FechaCompromiso (datetime) → fecha_compromiso (TIMESTAMP)
- VentanaDesde (datetime) → ventana_desde (TIMESTAMP)
- VentanaHasta (datetime) → ventana_hasta (TIMESTAMP)
- EstadoEnvio (nvarchar(50)) → estado_envio (VARCHAR(50))
- EstadoPreparacion (tinyint) → estado_preparacion (SMALLINT)
- ObservacionesDetalladas (nvarchar(MAX)) → observaciones (TEXT)
- created_at (TIMESTAMP), updated_at (TIMESTAMP)

**EDetalle_cpedido → detalle_pedidos_envases**
- id_detalle (int PK) → id (INTEGER PK)
- cod_pedido (int FK) → pedido_id (INTEGER FK)
- cod_producto (int FK) → producto_id (INTEGER FK)
- motivo (nvarchar(50)) → motivo (VARCHAR(50))
- condicion (nvarchar(50)) → condicion (VARCHAR(50))
- total (money) → cantidad_solicitada (NUMERIC(19,4))
- estado (int) → estado (INTEGER)
- ubicacion (nvarchar(50)) → ubicacion (VARCHAR(50)) ['ALMACEN', 'CLIENTE']
- CantidadPlanificada (decimal) → cantidad_planificada (NUMERIC(19,4))
- descripcion (nvarchar(500)) → descripcion (VARCHAR(500))

**Ecil_duenio → cilindros_duenos_historial**
- Id_cambio (int PK) → id (INTEGER PK)
- Id_persona (int FK) → persona_id (INTEGER FK)
- Id_producto (int FK) → producto_id (INTEGER FK)
- Edet_movimiento (int FK) → detalle_movimiento_id (INTEGER FK)
- Fecha_cambio (datetime) → fecha_cambio (TIMESTAMP DEFAULT NOW())
- Estado_condicion (nvarchar(50)) → estado_condicion (VARCHAR(50))

**EGarantia → garantias_envases**
- cod_garantia (int PK) → id (INTEGER PK)
- fecha_garantia (datetime) → fecha_garantia (TIMESTAMP)
- cliente (int FK) → cliente_id (INTEGER FK)
- tipo_garantia (nvarchar(50)) → tipo_garantia (VARCHAR(50))
- detalle (nvarchar(500)) → detalle (VARCHAR(500))
- estado (nvarchar(50)) → estado (VARCHAR(50))
- fecha_devolucion (datetime) → fecha_devolucion (TIMESTAMP)
- nro_seriegar (nvarchar(50)) → serie_cilindro (VARCHAR(50))
- nro_docgar (int) → numero_documento (INTEGER)

**Eph → pruebas_hidraulicas**
- Id_Cilindro (int FK) → producto_id (INTEGER FK)
- Fecha_PH (date) → fecha_prueba (DATE)
- Estado (nvarchar(50)) → estado (VARCHAR(50))
- Modificado_por (nvarchar(100)) → modificado_por (VARCHAR(100))
- Fecha_PH_Anterior (date) → fecha_prueba_anterior (DATE)
- Cod_Movimiento (int FK) → movimiento_id (INTEGER FK)
- PK compuesta (Id_Cilindro, Fecha_PH)

**Edetalle_retimbrado → retimbrados_detalle**
- Id (int PK) → id (INTEGER PK)
- Cod_producto (int FK) → producto_id (INTEGER FK)
- Codigo_fabricacion (varchar(50)) → codigo_fabricacion (VARCHAR(50))
- Anio_fabricacion (int) → anio_fabricacion (INTEGER)
- Nro_Bombona (varchar(50)) → numero_bombona (VARCHAR(50))
- Peso_origen (decimal) → peso_origen (NUMERIC(10,2))
- Peso_actual (decimal) → peso_actual (NUMERIC(10,2))
- Presion_servicio (decimal) → presion_servicio (NUMERIC(10,2))
- Presion_prueba (decimal) → presion_prueba (NUMERIC(10,2))
- Nro_aprobacion (varchar(50)) → numero_aprobacion (VARCHAR(50))
- Clase_peligro (varchar(50)) → clase_peligro (VARCHAR(50))
- Marcado1 (varchar(50)) → marcado_1 (VARCHAR(50))
- Marcado2 (varchar(50)) → marcado_2 (VARCHAR(50))
- Formato_Bulto (nvarchar(50)) → formato_bulto (VARCHAR(50))
- Etiqueta (nvarchar(50)) → etiqueta_adr (VARCHAR(50))
- Tuneles (nvarchar(50)) → tuneles_adr (VARCHAR(50))
- Nro_ONU (nvarchar(50)) → numero_onu (VARCHAR(50))

**ECilindros_Servicios → servicios_cilindros**
- id_cilindro_servicio (int PK) → id (INTEGER PK)
- cod_pedido (int FK) → pedido_id (INTEGER FK)
- id_detalle (int FK) → detalle_pedido_id (INTEGER FK)
- cod_movimiento (int FK) → movimiento_id (INTEGER FK)
- cod_producto (int FK) → producto_id (INTEGER FK)
- id_servicio (int FK) → servicio_tipo_id (INTEGER FK)
- estado_servicio (nvarchar(50)) → estado (VARCHAR(50))
- fecha_inicio (datetime) → fecha_inicio (TIMESTAMP)
- fecha_fin (datetime) → fecha_fin (TIMESTAMP)
- observaciones (nvarchar(500)) → observaciones (VARCHAR(500))

### 2.6 Logística — Flota

**EEquipos → equipos_transporte**
- Cod_Equipo (int PK) → id (INTEGER PK)
- PlacaEquipo (varchar(20)) → placa (VARCHAR(20))
- TipoEquipo (varchar(50)) → tipo (VARCHAR(50))
- Marca (varchar(50)) → marca (VARCHAR(50))
- Modelo (varchar(50)) → modelo (VARCHAR(50))
- Capacidad (decimal) → capacidad (NUMERIC)
- Estado (varchar(20)) → estado (VARCHAR(20))
- Cod_Almacen (int FK) → almacen_id (INTEGER FK)
- Carga_util (decimal) → carga_util (NUMERIC)
- ADR (nvarchar(50)) → clase_adr (VARCHAR(50))

**EChoferesPorMovimiento → movimientos_choferes**
- IdChoferMovimiento (int PK) → id (INTEGER PK)
- Cod_Movimiento (int FK) → movimiento_id (INTEGER FK)
- Cod_Persona (int FK) → chofer_id (INTEGER FK)
- FechaAsignacion (datetime) → fecha_asignacion (TIMESTAMP)
- Confirmado (bit) → confirmado (BOOLEAN)

**EEquiposPorMovimiento → movimientos_equipos**
- IdEquipoMovimiento (int PK) → id (INTEGER PK)
- Cod_Movimiento (int FK) → movimiento_id (INTEGER FK)
- PlacaEquipo (varchar(20)) → placa_equipo (VARCHAR(20))

### 2.7 Logística — Agenda

**AGENDA_REPARTIDOR → agenda_repartidor**
- Id_Agenda (int PK) → id (INTEGER PK)
- Cod_Repartidor (int FK) → repartidor_id (INTEGER FK)
- Cod_Cliente (int FK) → cliente_id (INTEGER FK)
- Cod_SucursalCliente (int FK) → establecimiento_id (INTEGER FK)
- Cod_Contrato (int FK) → contrato_id (INTEGER FK)
- Tipo_Tarea (nvarchar(50)) → tipo_tarea (VARCHAR(50))
- Descripcion_Tarea (nvarchar(1000)) → descripcion (VARCHAR(500))
- Fecha_Programada (date) → fecha_programada (DATE)
- Hora_Programada (time) → hora_programada (TIME)
- Fecha_Creacion (datetime) → created_at (TIMESTAMP)
- Fecha_Realizado (datetime) → fecha_realizado (TIMESTAMP)
- Estado_Tarea (nvarchar(50)) → estado (VARCHAR(50))
- Prioridad (int) → prioridad (INTEGER DEFAULT 0)
- Cod_Pedido (int FK) → pedido_id (INTEGER FK)
- Cod_DetallePedido (int FK) → detalle_pedido_id (INTEGER FK)
- Cod_Producto (int FK) → producto_id (INTEGER FK)
- Cantidad_Solicitada (int) → cantidad_solicitada (INTEGER)
- Cantidad_Atendida (int) → cantidad_atendida (INTEGER)
- Serie_Cilindro (nvarchar(50)) → serie_cilindro (VARCHAR(50))
- Confirmado_Cliente (bit) → confirmado_cliente (BOOLEAN)
- Requiere_Firma (bit) → requiere_firma (BOOLEAN)
- Evidencia_URL (nvarchar(300)) → evidencia_url (VARCHAR(300))
- Ubicacion_Entrega (nvarchar(1000)) → ubicacion_entrega (VARCHAR(200))
- Origen_Tarea (nvarchar(30)) → origen_tarea (VARCHAR(30))
- Estado_Carga (nvarchar(20)) → estado_carga (VARCHAR(20))
- Motivo_Carga (nvarchar(20)) → motivo_carga (VARCHAR(20))
- Condicion (nvarchar(20)) → condicion (VARCHAR(20))
- Peso (numeric) → peso (NUMERIC)

### 2.8 Facturación

**Comprobante → comprobantes**
- CodComprobante (int PK) → id (INTEGER PK)
- NroSerie (nvarchar(50)) → serie (VARCHAR(20))
- NroDoc (int) → numero (INTEGER)
- Cliente (int FK) → cliente_id (INTEGER FK)
- Fecha (datetime) → fecha_emision (TIMESTAMP)
- TipoComprobante (int FK) → tipo_comprobante_id (INTEGER FK)
- Venta_Bruta (money) → venta_bruta (NUMERIC(19,4))
- Descuento (money) → descuento (NUMERIC(19,4))
- Igv_Total (money) → igv_total (NUMERIC(19,4))
- Total (money) → total (NUMERIC(19,4))
- Estado (int) → estado_id (INTEGER FK)
- EstadoMap (0=pendiente, 1=emitido, 2=anulado) → estado (VARCHAR(20))
- ESTADO_SUNAT (int) → estado_sunat (INTEGER) [0=pend, 1=enviado, 2=aceptado, 3=rechazado, 4=baja]
- ClaveElectronica (varchar(50)) → clave_electronica (VARCHAR(50))
- CODALMACEN (int FK) → almacen_id (INTEGER FK)
- Usuario (int FK) → usuario_id (INTEGER FK)
- Moneda (nvarchar(50)) → moneda (VARCHAR(10))
- base_imponible (money) → base_imponible (NUMERIC(19,4))
- total_exonerado (money) → total_exonerado (NUMERIC(19,4))
- total_igv (money) → total_igv (NUMERIC(19,4))

### 2.9 Configuración

**ConfiguracionRegional → configuraciones_regionales**
- IdConfiguracion (int PK) → id (INTEGER PK)
- PaisCodigo (varchar(5)) → pais_codigo (VARCHAR(5) UNIQUE)
- PaisNombre (varchar(100)) → pais_nombre (VARCHAR(100))
- NombreDocumentoFiscal (varchar(100)) → nombre_documento_fiscal (VARCHAR(100))
- LongitudDocumento (int) → longitud_documento (INTEGER)
- SoloNumerico (bit) → solo_numerico (BOOLEAN)
- NombreMoneda (varchar(50)) → nombre_moneda (VARCHAR(50))
- SimboloMoneda (varchar(10)) → simbolo_moneda (VARCHAR(10))
- CodigoMonedaISO (varchar(10)) → codigo_moneda_iso (VARCHAR(10))
- NombreImpuesto (varchar(50)) → nombre_impuesto (VARCHAR(50))
- TasaImpuesto (decimal) → tasa_impuesto (NUMERIC(5,2))
- Terminos regionalizados → termino_unidad, termino_repartidor, termino_almacen, etc.

### 2.10 Catálogos Auxiliares

| Legacy | OSS | Notas |
|--------|-----|-------|
| Linea | lineas | Líneas de producto |
| Sublinea | sublineas | Sub-líneas |
| Marca | marcas | Marcas |
| Unidad | unidades | Unidades de medida |
| Familia | familias | Familias |
| Grupo | grupos (tabla separada) | Grupos de producto |
| SubCategoria | subcategorias | Sub-categorías |
| Ubicacion | ubicaciones | Ubicaciones de almacén |
| ZONA | zonas | Zonas geográficas |
| Monedas | monedas | Monedas |
| TipoA | tipos_atencion | Tipos de atención |
| TipoDoc | tipos_documento | Tipos de documento (con MueveEnvases, OrigenEnvase, DestinoEnvase) |
| Formas_pago | formas_pago | Formas de pago |
| EstadoMovimiento | estados_movimiento | Estados posibles de Movimiento |
| EstadoProducto | estados_producto | Estados de producto |
| RazonSocial | razones_sociales | Razones sociales/empresas |
| Serie | series_documento | Series de documentos fiscales |

## 3. Vistas Legacy → Vistas o Queries en OSS

Las vistas legacy (~144) se reemplazan con:
1. Vistas SQL en PostgreSQL para las más usadas (ej. v_CilindrosDisponibles, vw_EdetPB_Vigente)
2. Queries SQLAlchemy para las menos críticas
3. Endpoints específicos para las usadas en reportes

Vistas críticas a migrar como vistas PostgreSQL:
- vw_EdetPB_Vigente → vista adr_vigente_por_producto
- v_CilindrosDisponibles → vista cilindros_disponibles
- v_Cilindros_VaciosEnAlmacen → vista cilindros_vacios_almacen
- v_UltimoPH_porCilindro → vista ultimo_ph_por_cilindro
- vCilindroEstadoActualDet → vista cilindro_estado_actual_detalle
- VDETALLE_ENVASE → vista detalle_envase_actual

## 4. Constraints y Relaciones Clave

**TipoDoc** es la tabla que requirió más atención:
- Tiene campos MueveEnvases, OrigenEnvase, DestinoEnvase que controlan la máquina de estados
- Migrar como tabla tipos_documento con los mismos campos

**ECilindroEstadoLog** requiere:
- Índice compuesto (serie, fecha DESC) para performance
- FK a productos(serie) o al menos indexed

**Stock_Actual**:
- No tiene FK en legacy (es tabla de snapshot)
- En OSS: vista materializada o tabla actualizada por trigger/evento

## 5. Stored Procedures → Migración

Ver documento 04_sp_a_api.md para el mapeo completo de cada SP legacy a funciones/biz logic en OSS.

Patrón general:
- SPs de consulta (SELECT) → endpoint GET con query SQLAlchemy
- SPs de búsqueda (Buscar_, Mos_) → endpoint GET con filtros dinámicos
- SPs de inserción (Insertar_, Crear_, sp_Insertar) → endpoint POST con validación Pydantic
- SPs de actualización (Actualizar_, Modificar_) → endpoint PUT/PATCH
- SPs de eliminación (Eliminar_) → endpoint DELETE
- SPs complejos multi-paso (InsertarHistorialEstadoTraslado, usp_Scan_Procesar) → servicios de aplicación con transacciones

## 6. TVPs (Table-Valued Parameters)

Legacy usa TVPs para operaciones bulk:
- TipoListaSeries → lista de series de cilindros
- TVP_CargaBombonas → carga de bombonas en escaneo
- TVP_Series → series con observaciones

En OSS: reemplazar con listas JSON en el body del request o tablas temporales.

## 7. Secuencias y Correlativos

- CORRELATIVO_DOCUMENTO / CorrelativosDocumento: controlan numeración por serie/almacén/año
- En OSS: usar SEQUENCE de PostgreSQL o tabla con bloqueo optimista
- Ej: por cada nuevo movimiento, obtener siguiente correlativo + 1 para la serie/almacén/año
