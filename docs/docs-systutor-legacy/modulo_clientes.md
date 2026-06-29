# Módulo de Clientes — Análisis Completo del Legacy

## 1. Tablas del Módulo

### 1.1 Persona_Nuevo (Entidad universal)

**Propósito:** Tabla única que almacena clientes, proveedores, empleados, repartidores y usuarios del sistema. Es la tabla central de personas.

| Columna | Tipo | Nulleable | Descripción |
|---------|------|-----------|-------------|
| `Cod_Persona` | int (PK) | NO | ID único |
| `Nro_Persona` | nvarchar(50) | SI | Código externo del cliente |
| `Nom_Persona` | nvarchar(200) | NO | Razón social / Nombre completo |
| `Dni_Persona` | nvarchar(20) | SI | DNI (persona natural) |
| `Ruc_Persona` | nvarchar(20) | SI | RUC (persona jurídica) |
| `Cod_TipoPersona` | int (FK) | NO | 1=Cliente, 2=Proveedor, 3=Empleado, etc. |
| `Sexo_Persona` | nvarchar(10) | SI | Sexo |
| `FNac_Personal` | date | SI | Fecha de nacimiento |
| `mail_Persona` | nvarchar(100) | SI | Correo electrónico |
| `Telefono_Persona` | nvarchar(50) | SI | Teléfono |
| `Activo` | bit | NO | 1=Activo, 0=Inactivo |
| `Login_Persona` | nvarchar(50) | SI | Login de usuario del sistema |
| `Pass_Persona` | nvarchar(50) | SI | Password (MD5 - inseguro) |
| `Nick_Persona` | nvarchar(50) | SI | Apodo/alias |
| `Fotografia` | nvarchar(50) | SI | Ruta de foto |
| `id_clave_Operacion` | int (FK) | SI | Clave de operación fiscal (España) → EClaves_operacion |
| `clave_op_intracomunitaria` | bit | SI | Es operación intracomunitaria (EU) |
| `nombre_comercial` | varchar(100) | SI | Nombre comercial |
| `observaciones` | nvarchar(MAX) | SI | Notas |
| `Documento_Principal` | nvarchar(50) | SI | Documento principal de identificación |
| `Tipo_facturacion` | nvarchar(50) | SI | "mensual", "por_operacion", etc. |
| `Id_FormaPago` | int (FK) | SI | Forma de pago por defecto → Formas_pago |
| `Id_Direccion_Fiscal` | int (FK) | SI | Dirección fiscal → Direccion |
| `PaisCodigo` | varchar(5) | SI | Código de país (PER, ESP, CRI) |
| `TipoIdentificacionFiscal` | varchar(20) | SI | "RUC", "DNI", "NIF", "CÉDULA FÍSICA", etc. |
| `NumeroIdentificacionFiscal` | varchar(30) | SI | Número de identificación fiscal |
| `CodigoActividadPrincipal` | varchar(20) | SI | Código de actividad económica |
| `DescripcionActividadPrincipal` | nvarchar(300) | SI | Descripción de actividad |
| `ActividadValidada` | bit | NO | Si la actividad fue validada contra SUNAT/Hacienda |
| `FechaValidacionActividad` | datetime | SI | Fecha de validación |
| `FuenteValidacionActividad` | varchar(50) | SI | "SUNAT", "HACIENDA_CR", "MANUAL" |

---

### 1.2 Cliente_Sucursal (Cliente ↔ Almacén)

**Propósito:** Relación muchos-a-muchos entre clientes y sucursales/almacenes.

| Columna | Tipo | Nulleable | Descripción |
|---------|------|-----------|-------------|
| `Id_Cliente` | int (FK) | NO | → Persona_Nuevo.Cod_Persona |
| `Id_Sucursal` | int (FK) | NO | → Almacen.Cod_Almacen |
| `Fecha_Creacion` | datetime | NO | Fecha de creación |
| `Creado_Por` | nvarchar(50) | SI | Usuario que creó |
| `Fecha_Modificacion` | datetime | SI | Fecha de modificación |
| `Modificado_Por` | nvarchar(50) | SI | Usuario que modificó |

---

### 1.3 Direccion (Direcciones)

**Propósito:** Direcciones fiscales y de entrega. Con geolocalización.

| Columna | Tipo | Nulleable | Descripción |
|---------|------|-----------|-------------|
| `Id_Direccion` | int (PK) | NO | ID único |
| `Linea1` | nvarchar(200) | NO | Dirección línea 1 |
  | `Linea2` | nvarchar(200) | SI | Dirección línea 2 |
| `Codigo_Postal` | nvarchar(12) | SI | Código postal |
| `Id_Zona` | int (FK) | SI | → ZONA |
| `Ubigeo` | nvarchar(6) | SI | Código ubigeo (Perú) |
| `Latitud` | float | SI | GPS latitud |
| `Longitud` | float | SI | GPS longitud |
| `Observaciones` | nvarchar(250) | SI | Notas |
| `Activo` | bit | NO | 1=Activo |
| `Fecha_Alta` | date | NO | Fecha de registro |
| `Id_Localidad` | int | SI | → Localidad (geografía) |
| `Formatted_Address` | nvarchar(255) | SI | Dirección formateada (Google Maps) |
| `Place_Id` | nvarchar(64) | SI | Google Place ID |
| `Country_Code` | char(2) | SI | Código país ISO |
| `Admin_Area_1` | nvarchar(120) | SI | Departamento/Provincia |
| `Admin_Area_2` | nvarchar(120) | SI | Provincia/Cantón |
| `Localidad` | nvarchar(120) | SI | Distrito/Localidad |
| `Street_Name` | nvarchar(160) | SI | Nombre de calle |
| `Street_Number` | nvarchar(20) | SI | Número |
| `Fuente_Geocod` | nvarchar(20) | SI | "GOOGLE", "MANUAL", "OSM" |
| `Precision_Metros` | int | SI | Precisión de geocodificación |
| `Capturado_Por` | nvarchar(50) | SI | Usuario que capturó |
| `Capturado_En` | datetime2 | SI | Cuándo se capturó |

---

### 1.4 Vehiculo_cliente_nuevo (Puntos de Entrega / Establecimientos)

**Propósito:** Cada registro representa un punto de entrega o establecimiento del cliente. Es la tabla más importante para logística: aquí se entregan los cilindros.

| Columna | Tipo | Nulleable | Descripción |
|---------|------|-----------|-------------|
| `Codigo` | int (PK) | NO | ID único |
| `Id_ClientePersona` | int (FK) | NO | → Persona_Nuevo.Cod_Persona (cliente dueño) |
| `Direccion` | nvarchar(200) | NO | Dirección del punto |
| `Contacto` | nvarchar(100) | SI | Nombre de contacto |
| `Telefono` | nvarchar(50) | SI | Teléfono del punto |
| `Correoresp` | nvarchar(100) | SI | Correo del responsable |
| `Enlace_GPS` | nvarchar(200) | SI | Link a Google Maps |
| `Id_Zona` | int (FK) | NO | → ZONA (zona de reparto) |
| `Dreparto` | nvarchar(50) | SI | Día de reparto (LUNES, MARTES, etc.) |
| `Id_Agente_Asignado` | int (FK) | SI | → Persona_Nuevo (vendedor/agente) |
| `Id_DatoBancario` | int (FK) | SI | → DatosBancarios |
| `Observ_Responsable` | nvarchar(200) | SI | Observaciones |
| `Principal` | bit | NO | 1=Es el punto principal |
| `Activo` | bit | NO | 1=Activo |
| `Fecha_Registro` | date | NO | Fecha de alta |
| `ubigeo` | nvarchar(6) | SI | Código ubigeo |
| `Dvisita` | nvarchar(50) | SI | Día de visita alternativo |
| `garantia` | nvarchar(50) | SI | Garantía aplicable |
| `Id_Sucursal` | int (FK) | NO | → Almacen.Cod_Almacen |
| `Id_Direccion` | int (FK) | SI | → Direccion |
| `NombrePunto` | nvarchar(100) | SI | Nombre del punto de entrega |
| `VentanaHorario` | nvarchar(50) | SI | Ventana horaria (ej. "08:00-12:00") |
| `Indicaciones` | nvarchar(200) | SI | Indicaciones de entrega |
| `Id_RutaAsignada` | int (FK) | SI | → Ruta |
| `TiempoServicioMin` | int | SI | Tiempo estimado de servicio en minutos |
| `DemandaUnidades` | int | SI | Demanda estimada en unidades |
| `DemandaPesoKg` | decimal | SI | Demanda estimada en kg |
| `PaisCodigo` | varchar(5) | SI | País |
| `Documento_Fiscal_Operacion` | nvarchar(50) | SI | Documento fiscal de operación |
| `TipoOperacionFiscal` | varchar(30) | SI | Tipo de operación fiscal |

---

### 1.5 Tablas auxiliares del módulo

| Tabla | Propósito | Relación |
|-------|-----------|----------|
| `Formas_pago` | Catálogo de formas de pago | Persona_Nuevo.Id_FormaPago |
| `EClaves_operacion` | Claves de operación fiscal (España/EU) | Persona_Nuevo.id_clave_Operacion |
| `Direcciones_NoClientes` | Direcciones de personas que NO son clientes | Persona_Nuevo |
| `Telefonos` | Teléfonos adicionales por persona | Cod_Persona |
| `Correos` | Correos adicionales por persona | Cod_Persona |
| `Persona_Proceso_Almacen` | Procesos de persona por almacén | Cod_Persona + Cod_Almacen |
| `Ecargos_funciones` | Cargos/funciones de empleados | Cod_Persona + Cod_Sucursal |
| `Ecil_duenio` | Historial de dueño de cilindro por persona | Id_persona |
| `Tarifa_cliente` | Precios especiales por cliente/producto | Id_Cliente |
| `Creditos` | Líneas de crédito por persona | Id_Persona |
| `Cliente_Sucursal_Auditoria` | Auditoría de cambios en Cliente_Sucursal | Id_Cliente + Id_Sucursal |
| `CONTRATOS` | Contratos de alquiler de cilindros | Cod_Cliente |

---

## 2. Stored Procedures del Módulo

### 2.1 CRUD de Persona (84 SPs)

| SP | Tipo | Propósito |
|----|------|-----------|
| `Insertar_Persona_Nuevo` | PROCEDURE | Crear persona/cliente nuevo |
| `Modificar_Persona_Nuevo` | PROCEDURE | Actualizar datos de persona |
| `PERSONA_Buscarxcod` | PROCEDURE | Buscar por código |
| `PERSONA_BuscarxNom` | PROCEDURE | Buscar por nombre |
| `PERSONA_BuscarxNom1` | PROCEDURE | Buscar por nombre (alternativo) |
| `PERSONA_BuscarxNomVendedor` | PROCEDURE | Buscar por nombre de vendedor |
| `PERSONA_Buscarxdni` | PROCEDURE | Buscar por DNI |
| `PERSONA_Buscarxruc` | PROCEDURE | Buscar por RUC |
| `PERSONA_BuscarxrucTipo` | PROCEDURE | Buscar por RUC + tipo persona |
| `Persona_BuscarXfiltro` | PROCEDURE | Buscar con filtros dinámicos |
| `Persona_BuscarXcargo` | PROCEDURE | Buscar por cargo/función |
| `MOSTRAR_PERSONA` | PROCEDURE | Listar personas con filtros |
| `MOSTRAR_PERSONAresponsable` | PROCEDURE | Listar personas responsables |
| `Buscar_ClientexnomFiscal` | PROCEDURE | Buscar cliente por nombre fiscal |
| `Personal_Insertar` | PROCEDURE | Insertar personal/empleado |
| `Personal_Modificar` | PROCEDURE | Modificar personal |
| `Personal_LineaCredito` | PROCEDURE | Obtener línea de crédito del personal |
| `Insertar_ClienteProveedor` | PROCEDURE | Insertar cliente o proveedor |
| `Modificar_ClienteProveedor` | PROCEDURE | Modificar cliente o proveedor |
| `Actualizar_TARIFAPERSONA` | PROCEDURE | Actualizar tarifa de persona |
| `sp_Persona_ActividadFiscal_Guardar` | PROCEDURE | Guardar actividad fiscal |
| `sp_Persona_ActividadFiscal_ObtenerPrincipal` | PROCEDURE | Obtener actividad fiscal principal |
| `MostrarPersona_empresapropia` | PROCEDURE | Mostrar empresa propia |
| `SP_PERSONA_MOSTRARMOZO` | PROCEDURE | Mostrar mozos (histórico) |
| `crear_personalm` | PROCEDURE | Crear personal (legacy) |
| `eliminar_personalm` | PROCEDURE | Eliminar personal (legacy) |
| `BuscarClientesAnotificar` | PROCEDURE | Clientes para notificación |
| `Actualizar_estadoOCCliente` | PROCEDURE | Actualizar estado orden de compra cliente |

### 2.2 CRUD de Puntos de Entrega / Establecimientos (12 SPs)

| SP | Tipo | Propósito |
|----|------|-----------|
| `Insertar_Establecimiento` | PROCEDURE | Crear punto de entrega |
| `Actualizar_Establecimiento` | PROCEDURE | Modificar punto de entrega |
| `Modificar_vehiculo_cliente` | PROCEDURE | Modificar vehículo/cliente (nombre legacy) |
| `crear_vehiculo_cliente` | PROCEDURE | Crear vehículo/cliente (legacy) |
| `vehiculo_cliente_Buscarxcliente` | PROCEDURE | Buscar puntos por cliente |
| `vehiculo_cliente_Buscarxcodigo` | PROCEDURE | Buscar punto por código |
| `Vehiculo_cliente_nuevo_ActualizarDireccion` | PROCEDURE | Actualizar dirección del punto |
| `Vehiculo_cliente_nuevo_SetPrincipal` | PROCEDURE | Marcar punto como principal |
| `sp_PuntoEntrega_ListarPorCliente` | PROCEDURE | Listar puntos de entrega por cliente |
| `sp_Establecimiento_ActualizarEnvio` | PROCEDURE | Actualizar envío de establecimiento |
| `Eliminar_persona_vehiculo` | (inline en CPaciente) | Eliminar punto de entrega |
| `sp_Despacho_ListarPuntosEntrega` | PROCEDURE | Listar puntos activos para despacho |

### 2.3 CRUD de Dirección (8 SPs)

| SP | Tipo | Propósito |
|----|------|-----------|
| `Insertar_Direccion_Persona` | PROCEDURE | Insertar dirección de persona |
| `Modificar_Direccion_Persona` | PROCEDURE | Modificar dirección de persona |
| `sp_Direccion_Fiscal_Actualizar` | PROCEDURE | Actualizar dirección fiscal |
| `SHOW_DireccionesXCliente` | PROCEDURE | Mostrar direcciones por cliente |
| `Direccion_CapturaEnSitio` | PROCEDURE | Capturar coordenadas en sitio |
| `Direccion_ListarCoordenadasPorCliente` | PROCEDURE | Listar coordenadas por cliente |
| `Direccion_ObtenerCoordenadasPorPunto` | PROCEDURE | Obtener coordenadas de un punto |
| `MOSTRAR_CPubigeoxDireccion` | PROCEDURE | Mostrar código postal por dirección |

### 2.4 CRUD de Sucursal/Cliente_Sucursal (8 SPs)

| SP | Tipo | Propósito |
|----|------|-----------|
| `InsertarClienteSucursal` | PROCEDURE | Vincular cliente a sucursal |
| `ActualizarClienteSucursal` | PROCEDURE | Actualizar vínculo |
| `EliminarClienteSucursal` | PROCEDURE | Eliminar vínculo |
| `ConsultarClientesPorSucursal` | PROCEDURE | Clientes de una sucursal |
| `ConsultarSucursalesPorCliente` | PROCEDURE | Sucursales de un cliente |
| `ConsultarAuditoriaClienteSucursal` | PROCEDURE | Auditoría de cambios |
| `ValidarIntegridadClienteSucursal` | PROCEDURE | Validar integridad |
| `Listar_Sucursales` | PROCEDURE | Listar sucursales |

### 2.5 Formas de Pago y Claves Fiscales (4 SPs)

| SP | Tipo | Propósito |
|----|------|-----------|
| `Buscar_FormasPago` | PROCEDURE | Listar formas de pago |
| `Buscar_Claves` | PROCEDURE | Listar claves de operación (filtro nacional) |
| `Buscar_ClavesIC` | PROCEDURE | Listar claves intracomunitarias |
| `clienteexento_modificar` | PROCEDURE | Modificar cliente exento |
| `clienteRetencion_modificar` | PROCEDURE | Modificar retención de cliente |
| `TARIFARIOPERSONA_Insertar` | PROCEDURE | Insertar tarifa de persona |

### 2.6 Datos Bancarios (5 SPs)

| SP | Tipo | Propósito |
|----|------|-----------|
| `DatosBancarios_ObtenerPorCliente` | PROCEDURE | Obtener datos bancarios del cliente |
| `DatosBancarios_ResumenCliente` | PROCEDURE | Resumen de cuentas |
| `DatosBancarios_HistoricoCliente` | PROCEDURE | Histórico de cambios bancarios |
| `DatosBancarios_CambiarCuentaCliente` | PROCEDURE | Cambiar cuenta bancaria |
| `sp_DatoBancario_ListarPorCliente` | PROCEDURE | Listar datos bancarios |

### 2.7 Agentes y Comisiones (3 SPs)

| SP | Tipo | Propósito |
|----|------|-----------|
| `Insertar_AgenteSucursal` | PROCEDURE | Asignar agente a sucursal cliente |
| `Agentes_Sucursal_Insertar` | PROCEDURE | Insertar agente de sucursal |
| `mostrar_zona_persona` | PROCEDURE | Mostrar zona de persona |

### 2.8 Geografía (2 SPs)

| SP | Tipo | Propósito |
|----|------|-----------|
| `SucursalGeo_GetDefaults` | PROCEDURE | Obtener defaults geográficos de sucursal |
| `SucursalGeo_SetDefaults` | PROCEDURE | Establecer defaults geográficos |

---

## 3. Forms del Módulo

### 3.1 Forms de Mantenimiento de Clientes (5 forms)

| Form | Tamaño | Propósito | SPs que usa |
|------|--------|-----------|-------------|
| **FrmCatClientes** | 818KB | **Formulario principal.** Multi-pestaña, multi-país. CRUD completo de cliente + puntos de entrega + dirección fiscal + datos bancarios + contratos + estado de cuenta. | Insertar_Persona_Nuevo, Modificar_Persona_Nuevo, Insertar_Establecimiento, Actualizar_Establecimiento, PERSONA_Buscarxcod, PERSONA_BuscarxNom, PERSONA_Buscarxdni, PERSONA_Buscarxruc, Buscar_FormasPago, Buscar_Claves, DatosBancarios_*, sp_PuntoEntrega_ListarPorCliente |
| **FrmRegClientePRO** | 545KB | Versión PRO con más campos fiscales. Usada en España/Perú. | Insertar_Persona_Nuevo, Modificar_Persona_Nuevo, PERSONA_Buscarx* |
| **FrmRegClientePLUS** | 199KB | Versión PLUS (simplificada). | Insertar_Persona_Nuevo, Modificar_Persona_Nuevo |
| **FrmRegCliente** | 65KB | Versión básica legacy (antigua). | Usa tabla `Persona` (antigua, no Persona_Nuevo) |
| **FrmCatProveedores** | — | Catálogo de proveedores (misma tabla Persona_Nuevo, Cod_TipoPersona=2) | Insertar_ClienteProveedor, Modificar_ClienteProveedor |

### 3.2 Forms de Búsqueda de Clientes (5 forms)

| Form | Tamaño | Propósito | Quién lo llama |
|------|--------|-----------|----------------|
| **FBusPacPRO** | 15KB | Búsqueda modal de clientes (versión PRO) | FrmRegClientePRO |
| **FBusPacPLUS** | 12KB | Búsqueda modal (versión PLUS) | FrmRegClientePLUS, FrmRegCliente |
| **FBusPacPROcr** | 16KB | Búsqueda modal (Costa Rica) | FrmCatClientes |
| **FBusPacProv** | 9KB | Búsqueda modal de proveedores | — |
| **FrmBuscarCompra** | — | Búsqueda de compras (asigna lblcodigo3 con cod_persona) | Varios |

---

## 4. Impacto del Módulo — ¿Qué formularios usan datos de clientes?

### 4.1 Formularios que LEEN datos de cliente (vía lblcodigo3, Persona, Cliente)

| Formulario | Módulo | Cómo usa el cliente | Tipo de uso |
|------------|--------|---------------------|-------------|
| **FrmMovFacturacion** | Facturación | Asigna cliente a factura via lblcodigo3 (cod_persona) | **CRÍTICO** |
| **FrmMovFacturacionDirecta** | Facturación | Asigna cliente a factura directa | **CRÍTICO** |
| **FrmMovCompras** | Compras | Asigna proveedor/cliente a compra | **CRÍTICO** |
| **FrmMovPresupuestoCliente** | Presupuestos | Asigna cliente a presupuesto | **CRÍTICO** |
| **FrmMovPlanificacionOperaciones** | Logística | Asigna cliente a planificación de ruta | **CRÍTICO** |
| **FrmMovIntercambioCliente** | Logística | Cliente destino de intercambio de cilindros | **CRÍTICO** |
| **FrmMovPreparacionCarga** | Logística | Carga datos del cliente destino | **CRÍTICO** |
| **FrmMovTrasladoAlmacen** | Logística | Cliente origen/destino de traslado | Alto |
| **FrmMovRetornoVehiculo** | Logística | Cliente de retorno | Alto |
| **FrmMovLlenadoBombonas** | Cilindros | Cliente/proveedor de llenado | Alto |
| **FrmMovIngresoProveedor** | Cilindros | Proveedor que ingresa cilindros | Alto |
| **FrmMovSalidaProveedor** | Cilindros | Proveedor destino de cilindros | Alto |
| **FrmRecepcion** | Logística | Cliente destino de recepción | Alto |
| **FrmOrdenSalida** | Logística | Cliente destino | Alto |
| **FrmOrdenIngresoC** | Logística | Cliente origen | Alto |
| **FrmAgendaRepartidor** | Logística | Cod_Cliente en agenda de reparto | Alto |
| **FrmCargaRepartidor** | Logística | Filtra por repartidor (Persona_Nuevo) | Alto |
| **FrmAmortizaciones** | Finanzas | Cliente en cobranza/cancelaciones | **CRÍTICO** |
| **FrmAmortizaciones01** | Finanzas | Cliente en cobranza | Alto |
| **FrmAmortizaProv2** | Finanzas | Proveedor en pagos | Alto |
| **FrmFacturacionProgramada** | Facturación | Clientes con facturación mensual | Medio |
| **FrmRegVentasgOC** | Ventas | Cliente en orden de compra | **CRÍTICO** |
| **FrmRegVentasgOCcotiz** | Ventas | Cliente en cotización | Alto |
| **FrmRegVentasgEntregasSUCunaSerie** | Ventas | Cliente en entrega | Alto |
| **FrmRegCompras** | Compras | Persona en compra | Alto |
| **FrmRegOCproveedor** | Compras | Proveedor en orden de compra | Alto |
| **FrmCatProductos** | Maestros | Cliente en fabricación de producto | Bajo |
| **FrmCatBombonas** | Maestros | Cliente en creación de cilindro | Bajo |
| **FrmGarantia** | Cilindros | Cliente en garantía | Medio |
| **FrmRegcaja** | Finanzas | Cliente en movimiento de caja | Medio |
| **FrmRegcajaA** | Finanzas | Cliente en caja administrativa | Medio |
| **FrmRegCVmoneda** | Finanzas | Cliente en compra/venta moneda | Bajo |
| **Frmcomision** | Finanzas | Cliente en comisiones | Bajo |
| **FrmReporteEntregas** | Reportes | ~30 consultas inline con Persona_Nuevo | **CRÍTICO** |
| ~30 reportes Crystal | Reportes | Filtran por cliente en vistas auxiliares | Medio |

### 4.2 Tablas que referencian a Persona_Nuevo (FK directa o indirecta)

| Tabla | Columna FK | Módulo |
|-------|-----------|--------|
| `Movimiento` | Persona | Logística/Ventas |
| `Comprobante` | Cliente | Facturación |
| `ECabecera_pedido` | persona | Pedidos envases |
| `AGENDA_REPARTIDOR` | Cod_Cliente | Logística |
| `AGENDA_REPARTIDOR` | Cod_Repartidor | Logística (es Persona_Nuevo) |
| `Vehiculo_cliente_nuevo` | Id_ClientePersona | Logística (puntos entrega) |
| `Vehiculo_cliente_nuevo` | Id_Agente_Asignado | Logística |
| `Cancelaciones` | (varias vistas con Persona_Nuevo) | Finanzas |
| `Ecil_duenio` | Id_persona | Cilindros |
| `EGarantia` | cliente | Cilindros |
| `CONTRATOS` | Cod_Cliente | Cilindros (alquiler) |
| `Tarifa_cliente` | Id_Cliente | Ventas |
| `Creditos` | Id_Persona | Ventas/Finanzas |
| `Ecargos_funciones` | Cod_Persona | RRHH |
| `EChoferesPorMovimiento` | Cod_Persona | Logística |
| `Parametros_Repartidor` | (relacionado por cargo) | Logística |
| `Permiso` | (hereda de Persona_Nuevo via Login) | Seguridad |
| `Comprobante` | Cliente | Facturación |
| `Direccion` | (via Persona_Nuevo.Id_Direccion_Fiscal) | Maestros |
| `Stock_Actual` | (trigger indirecto por Movimiento.Persona) | Inventario |

---

## 5. Reglas de Negocio

### 5.1 Tipos de Persona (Cod_TipoPersona)

| Código | Tipo | Descripción |
|--------|------|-------------|
| 1 | Cliente | Comprador de productos/servicios |
| 2 | Proveedor | Vendedor de insumos/servicios |
| 3 | Empleado | Trabajador interno |
| 4 | Repartidor | Empleado con función de reparto |
| 5 | Agente/Vendedor | Fuerza de ventas externa |
| 6-9 | Otros | Varios (mozo, etc.) |

### 5.2 Identificación Fiscal por País

| País | Documento 1 | Documento 2 | Validación |
|------|-------------|-------------|------------|
| Perú | RUC (11 dígitos) | DNI (8 dígitos) | Módulo 11, dígito verificador |
| Costa Rica | Cédula Física (9 dígitos) | Cédula Jurídica (10 dígitos) | Formato 0-0000-0000 |
| España | NIF (8+1 letra) | NIE (X/Y/Z+7+1 letra) | Módulo 23 |

### 5.3 Formas de Pago (Formas_pago)

| Id_FormaPago | Descripción | Tipo Operación |
|--------------|-------------|----------------|
| 1 | Contado | CONTADO |
| 2 | Crédito 15 días | CREDITO |
| 3 | Crédito 30 días | CREDITO |
| 4 | Crédito 60 días | CREDITO |
| 5 | Tarjeta | TARJETA |
| 6 | Transferencia | TRANSFERENCIA |

### 5.4 Tipos de Facturación (Tipo_facturacion)

| Valor | Descripción |
|-------|-------------|
| "mensual" | Cliente facturado mensualmente (todo junto) |
| "por_operacion" | Cada movimiento genera factura individual |
| NULL | Sin facturación automática |

### 5.5 Punto de Entrega — Reglas

1. Un cliente puede tener **1..N puntos de entrega** (Vehiculo_cliente_nuevo)
2. Cada punto tiene **1 dirección principal** (Id_Direccion)
3. Cada punto pertenece a **1 zona de reparto** (Id_Zona → ZONA)
4. Cada punto puede tener **1 ruta asignada** (Id_RutaAsignada → Ruta)
5. La entrega se hace en el punto de entrega, no en la dirección fiscal
6. `Principal = 1` marca el punto por defecto
7. La firma digital se registra contra el punto de entrega (quien recibe)

### 5.6 Línea de Crédito

- Se almacena en `Creditos` (tabla separada)
- La vista `v_ClientesEnRiesgo` consolida línea de crédito por persona
- Los campos `LineaCredito_Persona` y `Dias_Credito` aparecen en varias vistas de reportes

### 5.7 Actividad Fiscal

- Se valida contra SUNAT (Perú) o Hacienda (Costa Rica)
- `CodigoActividadPrincipal` + `DescripcionActividadPrincipal`
- `ActividadValidada`, `FechaValidacionActividad`, `FuenteValidacionActividad`

---

## 6. Reportes Crystal que dependen de Clientes

| Reporte .rpt | Propósito |
|--------------|-----------|
| `CRreporte_persona.rpt` | Datos de persona |
| `CRAlmacen_EnvasesXcliente.rpt` | Inventario de envases por cliente |
| `CRDeudasxCobrar.rpt` | Cuentas por cobrar por cliente |
| `CRDeudasxCobrarBACK.rpt` | Deudas por cobrar (backup) |
| `CRAlmacen_EnvasesVencen4a8cliente.rpt` | Envases por vencer (4-8 años) por cliente |
| `CRAlmacen_EnvasesVencen9amascliente.rpt` | Envases vencidos (+9 años) por cliente |
| `CRAlmacen_DevolucionesAtiempoXcliente.rpt` | Devoluciones a tiempo por cliente |
| `CRFacturacion.rpt` | Facturación |
| `CRFacturacion1.rpt` | Facturación (alternativo) |
| `CREstadoCtaAdm.rpt` | Estado de cuenta administrativo |
| `CRLetras.rpt` | Letras de cambio |
| `vTICKETFACcliente.rpt` | Ticket de factura por cliente |

---

## 7. Dependencias del Módulo

### 7.1 ¿Qué necesita el módulo clientes para funcionar?

| Dependencia | Tipo | Tabla/Recurso |
|-------------|------|---------------|
| Catálogo de formas de pago | Tabla | `Formas_pago` |
| Catálogo de geografía | Tablas | Departamentos, Provincias, Distritos, Localidades |
| Catálogo de zonas | Tabla | `ZONA` |
| Catálogo de rutas | Tabla | `Ruta`, `Ruta_PuntoEntrega` |
| Catálogo de almacenes | Tabla | `Almacen` |
| Catálogo de claves de operación | Tabla | `EClaves_operacion` (solo España) |
| Catálogo de bancos | Catálogo | Bancos (hardcoded o tabla) |
| Configuración regional | Tabla | `ConfiguracionRegional` |
| Google Maps API | Externo | Geocodificación inversa |

### 7.2 ¿Qué módulos dependen de Clientes?

| Módulo | Dependencia | ¿Qué pasa si clientes falla? |
|--------|-------------|------------------------------|
| **Facturación** | Todo movimiento de factura requiere un cliente | **No se puede facturar** |
| **Logística/Reparto** | Toda ruta y agenda requiere cliente destino | **No se puede planificar ni despachar** |
| **Cilindros** | Ecil_duenio, EGarantia, CONTRATOS | **No se puede rastrear propiedad** |
| **Ventas (OC)** | Toda orden de compra requiere cliente | **No se pueden registrar pedidos** |
| **Compras** | Orden de compra a proveedor requiere proveedor | **No se pueden comprar insumos** |
| **Finanzas/Cobranza** | Toda cancelación requiere cliente | **No se puede cobrar** |
| **Reportes** | ~30 reportes filtran por cliente | **Reportes incompletos** |
| **Caja** | Movimientos de caja registran cliente | **Caja inconsistente** |

---

## 8. Diagrama de Flujo de Datos

```
                    ┌─────────────────────┐
                    │  FrmCatClientes     │
                    │  FrmRegClientePRO   │  ← Forms de mantenimiento
                    │  FrmRegClientePLUS  │
                    └────────┬────────────┘
                             │ INSERT / UPDATE
                             ▼
                    ┌─────────────────────┐
                    │    Persona_Nuevo     │  ← Tabla central
                    │   (+Direccion,       │
                    │    +Vehiculo_        │
                    │     cliente_nuevo)   │
                    └────────┬────────────┘
                             │
              ┌──────────────┼──────────────────┐
              │              │                  │
              ▼              ▼                  ▼
     ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐
     │ Facturación  │ │  Logística   │ │   Finanzas        │
     │ (Comprobante,│ │ (Movimiento, │ │ (Cancelaciones,   │
     │  Movimiento) │ │  Agenda,     │ │  Creditos,        │
     │              │ │  Ruta)       │ │  EstadoCuenta)    │
     └──────────────┘ └──────────────┘ └──────────────────┘
              │              │                  │
              ▼              ▼                  ▼
     ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐
     │   Cilindros  │ │   Ventas     │ │   Reportes        │
     │ (Ecil_duenio,│ │ (ECabecera_  │ │ (~30 Crystal)    │
     │  EGarantia,  │ │  pedido,     │ │                   │
     │  CONTRATOS)  │ │  Tarifa_)    │ │                   │
     └──────────────┘ └──────────────┘ └──────────────────┘
```

---

## 9. Resumen de Riesgos

| Riesgo | Descripción | Impacto |
|--------|-------------|---------|
| **R1** | `Persona_Nuevo` es tabla universal (mezcla clientes, proveedores, empleados, repartidores). Un cambio en estructura afecta a todos. | Alto |
| **R2** | ~30 formularios tienen queries inline con `Persona_Nuevo` (no pasan por SP). Migrar requiere encontrar y actualizar cada uno. | Alto |
| **R3** | `CContab.vb` hace UPDATE directo a `Persona_Nuevo` sin pasar por `Modificar_Persona_Nuevo` (bypasea validaciones). | Medio |
| **R4** | Campos Spain-only (`id_clave_Operacion`, `clave_op_intracomunitaria`) están en la misma tabla que clientes Perú/CR. | Bajo |
| **R5** | `FrmReporteEntregas.vb` tiene ~30 consultas inline con JOIN a Persona_Nuevo — difícil de mantener. | Alto |
| **R6** | `Pass_Persona` usa MD5 (inseguro). | Medio |
| **R7** | No hay documentación de jobs, triggers o schedules que afecten datos de clientes. | Medio |

---

## 10. Para el nuevo diseño

### Separar en tablas específicas:
- `clientes` (solo datos de cliente)
- `proveedores` (solo datos de proveedor)
- `empleados` / `usuarios` (solo personal interno)
- `repartidores` (con datos específicos de reparto)

### Catálogos obligatorios:
- `tipos_documento_identidad` (RUC, DNI, NIF, Cédula, etc.)
- `tipos_persona` (cliente, proveedor, empleado, repartidor)
- `formas_pago`
- `zonas`, `rutas`, `almacenes`

### Endpoints necesarios:
- CRUD de clientes con validación fiscal por país
- CRUD de puntos de entrega (anidado a cliente)
- CRUD de direcciones con geocodificación
- Geografía departamental jerárquica
- Búsqueda de clientes por múltiples criterios
