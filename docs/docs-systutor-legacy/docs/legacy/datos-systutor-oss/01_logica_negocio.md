# 01 — Lógica de Negocio Legacy (SysTutor GLP / SOLYGASES)

## 1. Dominio: Cilindros / Envases / Bombonas de GLP

### 1.1 Ciclo de Vida del Cilindro (Estado Físico)

El cilindro se identifica por su serie (Nro_Producto en Producto). Su estado físico se rastrea en ECilindroEstadoLog y su estado actual está en ECilindroEstadoActual.

Estados de la máquina (ECilindroEstadoCatalogo):
- CREADO — cilindro nuevo registrado
- VACIO — disponible, vacío en almacén
- LLENO — lleno (salió de planta), listo para despacho
- ASIGNADO — asignado a un pedido/movimiento
- EN_CLIENTE — en posesión del cliente
- EN_TRASLADO — en ruta hacia cliente/almacén
- EN_MANTENIMIENTO — en taller/servicio
- EN_RETIMBRADO — en proceso de retimbrado (prueba hidráulica)
- OBSOLETO — fuera de servicio
- BAJA — dado de baja permanentemente

Transiciones permitidas (ECilindroEstadoTransicion):
CREADO → VACIO
VACIO → LLENO (planta de llenado)
LLENO → ASIGNADO (asignación a pedido)
ASIGNADO → EN_TRASLADO (sale de almacén)
EN_TRASLADO → EN_CLIENTE (recibido por cliente)
EN_CLIENTE → VACIO (devolución a almacén)
EN_CLIENTE → EN_MANTENIMIENTO
EN_MANTENIMIENTO → VACIO
VACIO → EN_RETIMBRADO
EN_RETIMBRADO → VACIO
VACIO → OBSOLETO
OBSOLETO → BAJA

Validaciones en cada transición:
- VACIO→LLENO: requiere ADR vigente (ufn_Valida_ADR) y PH vigente (ufn_Valida_PH)
- LLENO→ASIGNADO: verificar stock disponible en almacén
- EN_CLIENTE→VACIO: registrar devolución con peso y condición

### 1.2 Concepto de Grupo (Producto)

El modelo de producto es jerárquico:
- Producto.cod_grupo → apunta a otro Producto (el "gas padre")
- Un cilindro (ej. "Cilindro 10kg Vacío") tiene cod_grupo = "GLP 10kg" (el gas)
- El gas padre contiene datos ADR, peso neto, etc.
- Edetalle_Producto_Bombona contiene la configuración ADR vigente para cada producto gas (con fechas de vigencia)

### 1.3 Prueba Hidráulica (PH / Retimbrado)

Cada cilindro tiene un historial de pruebas hidráulicas (Eph):
- Eph.Id_Cilindro → Producto.cod_producto
- Eph.Fecha_PH → última fecha de prueba
- Eph.Estado → estado de la prueba
- Próxima PH se calcula: Fecha_PH + 5 años (regla de negocio GLP)

Edetalle_retimbrado registra los datos técnicos completos:
- Peso_origen, Peso_actual, Presion_servicio, Presion_prueba
- Nro_aprobacion, Clase_peligro, Nro_ONU
- Marcado1, Marcado2, Formato_Bulto, Etiqueta, Tuneles

### 1.4 Garantías sobre Envases (EGarantia)

- Tipo: Cambio, Reparación, Devolución
- Flujo: cliente entrega envase → se registra garantía → se procesa → se devuelve
- Estados: Ingreso, Procesando, Devuelto, Cerrado
- SPs: Egarantia_Insertar, EGarantia_Modificar, buscar_garantia_envase

### 1.5 Cambios de Dueño / Custodia (Ecil_duenio, Ecambios)

Registra cada cambio de custodia del cilindro:
- Ecil_duenio: persona, producto, detalle_movimiento, fecha, estado_condicion
- Ecambios: cliente, documento, producto, reemplazado_por

### 1.6 Pedidos de Envases (ECabecera_pedido + EDetalle_cpedido)

Sistema de pedidos específico para envases/cilindros:
- ECabecera_pedido: cabecera con cliente, tipo_movimiento, almacén, fechas compromiso, ventanas horarias
- EDetalle_cpedido: detalle por producto, con motivo, condición, cantidad, precio, ubicación ("ALMACEN", "CLIENTE")
- Los pedidos se vinculan a Movimiento a través de Movimiento.Id_Cpedido

### 1.7 Servicios de Cilindros (SOLYGAS)

Para cilindros en servicio técnico/mantenimiento:
- ECilindros_Servicios: pedido, detalle, movimiento, producto, servicio
- Estados: PENDIENTE, REALIZADO, CANCELADO
- Servicios típicos: LIMPIEZA, PINTURA, CAMBIO_VALVULA, PRUEBA_HIDROSTATICA

## 2. Dominio: Movimiento (Transacciones de Almacén)

### 2.1 Estructura del Movimiento

Movimiento es la tabla central de transacciones:
- Cod_Movimiento (PK)
- TipoMovimiento → define qué tipo de transacción (venta, compra, traslado, etc.)
- TipoDocumento + Serie + NroDocumento → documento fiscal/asociado
- Persona → cliente/proveedor
- Almacén → almacén origen
- Total, SubTotal, IGV, Descuento → montos
- Estado, EstadoPago, EstadoTraslado → estados múltiples
- Id_Cpedido → vínculo a pedido de envases
- Fecha, FechaVenc, fecha_emision → fechas clave
- EstadoTraslado → PENDIENTE, EN_RUTA, ENTREGADO, COMPLETADO, CANCELADO
- Transportista, Placa, LugarDestino, DirDestino → datos logísticos

### 2.2 DetalleMovimiento

Líneas del movimiento:
- Ids (PK), CodMovimiento, CodProducto
- StkIngreso, StkEgreso, CANT → cantidades
- PVenta, Pcompra, Total_items, descuento → precios
- Estadoitem → estado de la línea ('R' = registrado, etc.)
- Serie → número de serie (para productos con control de series)
- CantPlanificada → cantidad planificada para despacho
- Glosa, Obs → observaciones

### 2.3 Tipos de Documento (TipoDoc)

La tabla TipoDoc controla el comportamiento de cada tipo de transacción:
- TipoOperacion: VENTA, COMPRA, TRASLADO, DEVOLUCION, etc.
- Categoria: INGRESO, EGRESO, TRASLADO
- EsIngreso: true si suma stock
- MueveEnvases: true si afecta estado de envases
- OrigenEnvase / DestinoEnvase: a qué estado va el envase (VACIO, LLENO, etc.)
- TablaDestino: qué tabla afecta (Movimiento, ECabecera_pedido, etc.)

### 2.4 Historial de Estados del Movimiento

Dos tablas complementarias:
- HistorialMovimientoEstado: cambios de TipoAtencion (estado de atención al cliente)
- HistorialEstadosTraslados: cambios de EstadoTraslado (logístico)
  - Columnas: EstadoAnterior, EstadoNuevo, FechaCambio, Responsable, Comentarios
  - SPs: InsertarHistorialEstadoTraslado, ActualizarEstadoMovimiento, usp_HistorialTraslado_Registrar

### 2.5 Stock_Actual

Tabla de stock consolidado:
- Cod_Grupo (producto gas), IdAlmacen, Stock, FechaActualizacion
- Se actualiza mediante triggers o procesos batch
- Es un snapshot de inventario por producto/almacén

## 3. Dominio: Planificación y Logística

### 3.1 Flujo de Reparto

1. **Registro de pedido** → ECabecera_pedido + EDetalle_cpedido
2. **Asignación a Movimiento** → Movimiento.Id_Cpedido vincula a pedido
3. **Creación en agenda** → AGENDA_REPARTIDOR (con fecha, repartidor, cliente)
4. **Preparación de carga** → AGENDA_PREPARACION_CARGA + PLAN_PREPARACION_CARGA
5. **Carga del vehículo** → se asignan cilindros específicos (por serie)
6. **Despacho** → se actualiza estado a EN_RUTA
7. **Entrega** → se escanea cilindro (usp_Scan_Procesar / usp_Scan_RegistrarVenta)
8. **Retorno** → se actualiza a ENTREGADO / COMPLETADO
9. **Cierre** → se actualizan estados de envases y stock

### 3.2 Tablas de Logística

- AGENDA_REPARTIDOR: tareas diarias de reparto
- AGENDA_PREPARACION_CARGA: cilindros preparados por día/repartidor
- Ruta, Ruta_DiaSemana, Ruta_PuntoEntrega: definición de rutas
- Camion, Camion_Ruta_Restriccion: vehículos con capacidades ADR
- Parametros_Repartidor: configuración por repartidor
- Vehiculo_cliente_nuevo: establecimientos/direcciones de entrega por cliente

### 3.3 ADR (Acuerdo de Transporte de Mercancías Peligrosas)

- ADR_Incompatibilidades: clases incompatibles entre sí
- ADR_Referencia: catálogo UN de mercancías peligrosas
- Producto.ADR_*: campos ADR en cada producto
- Camion.ADR_*: capacidades ADR del vehículo
- usp_ADR_SeleccionarCamion: selecciona vehículo compatible
- vw_EdetPB_Vigente: vista de configuración ADR vigente por producto gas

### 3.4 Agenda del Repartidor

Tipos de tarea (AGENDA_TIPO_TAREA):
- ENTREGA: llevar cilindros llenos
- RECOJO: recoger cilindros vacíos
- SERVICIO: mantenimiento en sitio
- VISITA: visita programada
- COBRO: cobranza

Estados de tarea: PROGRAMADO, ENRUTA, REALIZADO, CANCELADO, RECHAZADO

La agenda soporta:
- Historial de cambios (AGENDA_REPARTIDOR_HISTORIAL)
- Log de acciones (AGENDA_REPARTIDOR_LOG)
- Coordenadas GPS (Registro_Coordenadas)
- Firma digital (Evidencia_URL)

## 4. Dominio: Facturación

### 4.1 Comprobante

Cabecera de factura/boleta/N C/N D:
- CodComprobante, NroSerie, NroDoc
- Cliente, Fecha, TipoComprobante
- Venta_Bruta, Descuento, IGV_Total, Total
- Estado, Estado_SUNAT (para FE Perú)
- ESTADO_SUNAT: 0=pendiente, 1=enviado, 2=aceptado, 3=rechazado, 4=baja

### 4.2 Facturación Electrónica

Dos proveedores según país:
- **Perú**: Nubefact/SUNAT → api.nubefact.com.pe
- **Costa Rica**: Hacienda CR → api.fe.go.cr

El flujo es:
1. Generar comprobante en BD
2. Enviar a proveedor FE (ClsFacturacionElectronica.EnviarFactura)
3. Recibir respuesta y actualizar Estado_SUNAT
4. Almacenar CDR (Constancia de Recepción)

### 4.3 Tarifas

- Tarifa_cliente: precios específicos por cliente/producto
- Puede tener precio fijo o usar lista de precios del producto

## 5. Dominio: Caja / Finanzas

### 5.1 Cancelaciones (Amortizaciones)

- Cancelaciones: pagos de clientes
- CAJA_ADM: movimientos de caja administrativa
- cierrecaja: apertura/cierre de caja diario
- Formas_pago: efectivo, tarjeta, cheque, transferencia

### 5.2 Tipo de Cambio

- TipoCambioDiario: TC compra/venta diario por moneda
- Monedas: catálogo de monedas
- TC = tipo de cambio al momento de la transacción

## 6. Dominio: Reportes (Crystal Reports → Datos)

### 6.1 Reportes Existentes (~50 rpt)

Categorías principales (identificadas por vistas auxiliares):
- Reportes de ventas: Vlistarventas, VdetVentas, VMASVEND
- Reportes de envases: Vreporte_Documentoenvase, VDETALLE_ENVASE
- Reportes de inventario: VExistencias, vStockProductos, kardex
- Reportes logísticos: vPreparacionCarga, vCartaPorte
- Estado de cuenta: VESTADO_CUENTA_ADM, VoucherPagos

### 6.2 Estrategia de Reemplazo

Cada reporte Crystal se mapeará a un endpoint REST que devuelva JSON, consumible desde:
- Frontend web (tabla dinámica)
- Descarga CSV/Excel
- Integración con Power BI / Metabase

## 7. Dominio: Configuración Regional Multi-País

### 7.1 ConfiguracionRegional

Permite operar en múltiples países con reglas fiscales diferentes:
- Perú: RUC, DNI, SUNAT, factura electrónica, IGV 18%
- Costa Rica: cédula física/jurídica, Hacienda CR, IVA 13%
- España: NIF/NIE, IVA 21%

Campos clave:
- PaisCodigo, PaisNombre
- NombreDocumentoFiscal, LongitudDocumento, SoloNumerico
- NombreMoneda, SimboloMoneda, CodigoMonedaISO
- NombreImpuesto, TasaImpuesto
- UsaClaveElectronica, UsaConsecutivoElectronico
- Terminos regionalizados (Unidad, Repartidor, Almacén, Planta, Traslado)

### 7.2 Validación de Documentos

ClsValidaciones soporta:
- DNI Perú (8 dígitos + dígito verificar opcional)
- RUC Perú (11 dígitos con algoritmo de módulo 11)
- DNI España / NIF / NIE
- RUT Chile
- Cédulas Costa Rica (física/jurídica)
- DIMEX / NITE

## 8. Roles de Usuario Legacy (hardcoded en Permiso)

Los roles del sistema legacy son fijos y se asignan por usuario:
- Administrador: acceso total
- Contabilidad: módulos financieros, reportes
- Ventas: clientes, facturación, cobranza
- Sistemas: configuraciones técnicas
- Almacén: inventario, cilindros, logística

Cada opción del menú se autoriza contra una combinación de rol + permiso específico en tabla Permiso.
