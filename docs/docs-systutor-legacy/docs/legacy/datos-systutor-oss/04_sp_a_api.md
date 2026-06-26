# 04 — Traducción de Stored Procedures a Endpoints REST

## 1. Patrón General de Traducción

| Tipo SP Legacy | Equivalente OSS |
|---|---|
| SELECT con filtros (Buscar_, Mos_, Mostrar_) | GET /api/v1/{recurso} con query params |
| SELECT de un registro (consultar_) | GET /api/v1/{recurso}/{id} |
| INSERT simple (Insertar_, sp_Insertar) | POST /api/v1/{recurso} |
| UPDATE simple (Actualizar_, Modificar_) | PUT o PATCH /api/v1/{recurso}/{id} |
| DELETE (Eliminar_) | DELETE /api/v1/{recurso}/{id} |
| SP complejo multi-tabla (usp_Procesar, usp_Registrar) | Service layer con UnitOfWork |
| SP de catálogo (Listar_, Mostrar_ combo) | GET /api/v1/catalogos/{nombre} |
| Función escalar (fn_) | Método de servicio o helper |

## 2. Traducción Detallada por Módulo

### 2.1 Módulo: Cilindros / Envases

#### SPs de Consulta de Envases

| SP Legacy | Endpoint OSS | Notas |
|---|---|---|
| consultar_envase(@nro_producto) | GET /api/v1/cilindros/{serie} | Datos completos del cilindro + estado + cliente actual |
| consultar_envaseAct(@cod_producto) | GET /api/v1/cilindros/{id} | Versión por ID |
| consultar_envase_venta(...) | GET /api/v1/cilindros/disponibles?almacen=&estado= | Filtros dinámicos |
| mostrar_envases_disponibles(@Almacen) | GET /api/v1/cilindros/disponibles?almacen_id=X | Envases disponibles (con SP Buscar_mostrardocumentodisponible) |
| mostrar_envases_disponiblesTraslado(@almacen) | GET /api/v1/traslados/envases-disponibles | Para traslados entre almacenes |
| mostrar_envases_VACIO(@Almacen) | GET /api/v1/cilindros/vacios?almacen_id=X | Solo vacíos |
| Buscar_mostrardocumentodisponible(@Almacen) | GET /api/v1/pedidos-envases/pendientes?almacen_id=X | Pedidos pendientes de atención |
| consultar_detalle_envase(@cod_envase) | GET /api/v1/cilindros/{id}/detalle | Detalle técnico |
| mostrar_DETALLEnrodocEnvase(@nrodoc) | GET /api/v1/movimientos/{nro}/envases | Envases en un movimiento/documento |
| mostrar_DETALLEnrodocEnvaseSalida(@nrodoc) | GET /api/v1/movimientos/{nro}/envases-salida | Envases de salida |
| mostrar_DETALLEnrodocEnvaseTrasl(@nrodoc) | GET /api/v1/movimientos/{nro}/envases-traslado | Envases de traslado |
| mostrar_ingresos_pendientes(@Almacen) | GET /api/v1/movimientos/pendientes-ingreso?almacen_id=X | Ingresos pendientes |
| mostrar_nrodoc(@serie, @cod_producto) | GET /api/v1/cilindros/{serie}/documentos | Documentos asociados a un cilindro |

#### SPs de Cambio de Estado de Cilindro

| SP Legacy | Endpoint OSS | Notas |
|---|---|---|
| actualizar_estado(...) | PUT /api/v1/cilindros/{serie}/estado | Versión legacy simple |
| usp_Cilindro_CambiarEstado(...) | POST /api/v1/cilindros/cambiar-estado | Versión nueva con validación de transición |
| usp_Cilindro_InsertarEstado(...) | POST /api/v1/cilindros/estado-log | Insertar log directo (uso administrativo) |
| usp_Cilindro_Estado_Log(...) | POST /api/v1/cilindros/estado-log | Insertar log simple |
| usp_Cilindro_Estado_LogBulk(...) | POST /api/v1/cilindros/estado-log/bulk | Batch: series + estado |
| usp_Cilindro_Estado_LogSingle(...) | POST /api/v1/cilindros/{serie}/estado-log | Para un solo cilindro |
| usp_Cilindro_RegistrarCreacion(...) | POST /api/v1/cilindros/registrar-creacion | Creación de cilindro nuevo |
| actualizar_AlmacenTransfEnv(...) | PUT /api/v1/cilindros/transferir-almacen | Transferencia entre almacenes |

**Datos de dominio: estados y transiciones de cilindros**

ECilindroEstadoCatalogo (18 estados):

| Estado | Tipo |
|---|---|
| BLOQUEADO | final |
| CARGA_EN_VEHICULO | intermedio |
| CREADO_VACIO | intermedio |
| DE_BAJA | final |
| DESCARGADO_POR_RECEPCIONAR | intermedio |
| EN_ALMACEN_VACIO | intermedio |
| EN_CLIENTE_LLENO | intermedio |
| EN_CLIENTE_VACIO | intermedio |
| EN_LLENADO | intermedio |
| EN_MANTENIMIENTO | intermedio |
| EN_RUTA | intermedio |
| LLENADO_OK | intermedio |
| OBSERVADO | intermedio |
| PARA_REPARACION | intermedio |
| PARA_TRASLADO | intermedio |
| PERDIDO | final |
| RECEPCIONADO | intermedio |
| VACIO_EN_ALMACEN | intermedio |

Transiciones permitidas (ECilindroEstadoTransicion):

| Desde | Hacia |
|---|---|
| CARGA_EN_VEHICULO | EN_RUTA |
| CREADO_VACIO | EN_ALMACEN_VACIO |
| DESCARGADO_POR_RECEPCIONAR | RECEPCIONADO |
| EN_ALMACEN_VACIO | DE_BAJA, EN_MANTENIMIENTO, LLENADO_OK, PERDIDO |
| EN_CLIENTE_LLENO | EN_CLIENTE_VACIO, VACIO_EN_ALMACEN |
| EN_CLIENTE_VACIO | EN_RUTA, PERDIDO |
| EN_MANTENIMIENTO | EN_ALMACEN_VACIO |
| EN_RUTA | DESCARGADO_POR_RECEPCIONAR, EN_CLIENTE_LLENO |
| LLENADO_OK | CARGA_EN_VEHICULO, EN_CLIENTE_LLENO |
| RECEPCIONADO | EN_ALMACEN_VACIO |

**Datos de entrada/salida esperados para el endpoint cambiar-estado**:

Input esperado:
- serie (string): identificador del cilindro
- estado_nuevo (string): valor del catálogo ECilindroEstadoCatalogo
- origen (string opcional): "PLANTA", "DESPACHO", "CLIENTE", "TALLER"
- motivo_codigo (string opcional): código del motivo del cambio
- observacion (string opcional): texto libre
- almacen_id (int opcional): almacén donde ocurre el cambio

Output esperado:
- serie, estado_anterior, estado_nuevo, fecha_hora, resultado

Validaciones que debe implementar:
1. El cilindro debe existir
2. El estado actual no debe ser final (BLOQUEADO, DE_BAJA, PERDIDO, OBSERVADO)
3. La transición debe existir en ECilindroEstadoTransicion
4. Si destino = EN_CLIENTE_LLENO: validar PH vigente + ADR vigente

#### SPs de Pedidos de Envases (ECabecera_pedido + EDetalle_cpedido)

| SP Legacy | Endpoint OSS | Notas |
|---|---|---|
| InsertarECabeceraPedido (27 params) | POST /api/v1/pedidos-envases | Crear pedido con detalle |
| InsertardetallePedido | POST /api/v1/pedidos-envases/{id}/detalle | Agregar línea al pedido |
| usp_Edetalle_Cpedido_Insertar | POST /api/v1/pedidos-envases/detalle | Insertar detalle (con validaciones) |
| actualizar_edetalle_pedido | PATCH /api/v1/pedidos-envases/detalle/{id} | Actualizar línea de detalle |
| cambiar_envases | PATCH /api/v1/pedidos-envases/detalle/{id}/cambiar-producto | Cambiar producto en línea |
| mostrar_edetalle | GET /api/v1/pedidos-envases/{id}/detalle | Líneas de un pedido |
| ModificarDocAfect | PATCH /api/v1/pedidos-envases/{id}/documento-asociado | Vincular documento |

**Datos mínimos para crear pedido de envase**:

Input:
- cliente_id, tipo_movimiento, almacen_id
- serie_documento (opcional), forma_movimiento, motivo
- fecha_compromiso, ventana_desde, ventana_hasta (opcionales)
- observaciones (opcional)
- lineas: [{producto_id, cantidad, condicion, motivo, ubicacion, descripcion}]

Output: pedido creado con su ID y estado inicial

#### SPs de Garantías

| SP Legacy | Endpoint OSS |
|---|---|
| Egarantia_Insertar | POST /api/v1/garantias |
| EGarantia_Modificar | PUT /api/v1/garantias/{id} |
| buscar_garantia_envase(@cliente) | GET /api/v1/garantias?cliente_id=X |
| MOSTRAR_CATEGORIA | GET /api/v1/garantias/categorias-disponibles |

#### SPs de Retimbrado

| SP Legacy | Endpoint OSS |
|---|---|
| Retimbrado_insertar (18 campos) | POST /api/v1/retimbrados |
| Retimbrado_modificar (18 campos) | PUT /api/v1/retimbrados/{id} |
| Retimbrado_BuscarUltimoPorCodProducto | GET /api/v1/cilindros/{id}/ultimo-retimbrado |
| modificarfecha_ph | PATCH /api/v1/cilindros/{id}/ph |
| usp_EdetPB_ObtenerVigente | GET /api/v1/productos/{id}/configuracion-adr-vigente |
| usp_EdetPB_ReemplazarVigencia | PUT /api/v1/productos/{id}/configuracion-adr |

### 2.2 Módulo: SOLYGAS — Servicios, Flota, Carga Peligrosa

#### SPs de Servicios de Cilindros

| SP Legacy | Endpoint OSS |
|---|---|
| InsertarECilindrosServicios | POST /api/v1/servicios-cilindros |
| ActualizarECilindrosServicios | PUT /api/v1/servicios-cilindros/{id} |
| EliminarECilindrosServicios | DELETE /api/v1/servicios-cilindros/{id} |
| MostrarServiciosPendientes | GET /api/v1/servicios-cilindros/pendientes |
| ObtenerTodosServicios | GET /api/v1/servicios-cilindros |
| mostrar_ObtenerEnvasesPorServicio | GET /api/v1/servicios-cilindros/{id}/cilindros |
| Mostrar_ServiciosXproducto | GET /api/v1/servicios-cilindros?producto_id=X |
| usp_CilindroServicio_CerrarDesdePlus | POST /api/v1/servicios-cilindros/{id}/cerrar |

#### SPs de Flota (Choferes + Equipos)

| SP Legacy | Endpoint OSS |
|---|---|
| InsertarChoferPorMovimiento | POST /api/v1/movimientos/{id}/choferes |
| ModificarChoferPorMovimiento | PUT /api/v1/movimientos/{id}/choferes/{chofer_id} |
| EliminarChoferPorMovimiento | DELETE /api/v1/movimientos/{id}/choferes/{chofer_id} |
| InsertarEquipoTransporte | POST /api/v1/flota/equipos |
| ActualizarEquipoTransporte | PUT /api/v1/flota/equipos/{id} |
| EliminarEquipoTransporte | DELETE /api/v1/flota/equipos/{id} |
| ConsultarEquipoTransporte | GET /api/v1/flota/equipos/{id} |
| mostrar_equiposTransp_por_tipo | GET /api/v1/flota/equipos?tipo=X |
| InsertarEquipoPorMovimiento | POST /api/v1/movimientos/{id}/equipos |
| ActualizarEquipoPorMovimiento | PUT /api/v1/movimientos/{id}/equipos/{equipo_id} |
| EliminarEquipoPorMovimiento | DELETE /api/v1/movimientos/{id}/equipos/{equipo_id} |
| ConsultarEquiposPorMovimiento | GET /api/v1/movimientos/{id}/equipos |

#### SPs de Carga Peligrosa

| SP Legacy | Endpoint OSS |
|---|---|
| Insertar_Reporte_Carga_Peligrosa | POST /api/v1/movimientos/{id}/reporte-carga-peligrosa |
| MostrarReporteCargaPeligrosa | GET /api/v1/movimientos/{id}/reporte-carga-peligrosa |
| ActualizarReporteCargaPeligrosa | PUT /api/v1/movimientos/{id}/reporte-carga-peligrosa |

## 3. Traducción de SPs de Movimiento

### SPs de Historial de Estados

| SP Legacy | Endpoint OSS |
|---|---|
| ActualizarEstadoMovimiento | PUT /api/v1/movimientos/{id}/estado-traslado |
| InsertarHistorialEstadoTraslado | POST /api/v1/movimientos/{id}/historial-estados |
| usp_HistorialTraslado_Registrar | POST /api/v1/movimientos/{id}/historial-estados |
| MostrarHistorialEstadosTraslados | GET /api/v1/movimientos/{id}/historial-estados |
| ListarHistorialEstados | GET /api/v1/historial-estados?movimiento_id=X |
| EliminarHistorialEstadoTraslado | DELETE /api/v1/historial-estados/{id} |
| EliminarHistorialDeMovimiento | DELETE /api/v1/movimientos/{id}/historial-estados |

**Validaciones para el cambio de estado de movimiento**:

1. Obtener estado anterior desde Movimiento.EstadoTraslado
2. Validar que el cambio sea lógico (PENDIENTE → EN_RUTA → ENTREGADO → COMPLETADO, etc.)
3. Actualizar Movimiento.EstadoTraslado
4. Insertar en HistorialEstadosTraslados (EstadoAnterior, EstadoNuevo, FechaCambio, Responsable, Comentarios)
5. Opcional: si nuevo estado es EN_RUTA o ENTREGADO, cambiar estado de cilindros asociados al movimiento

### SPs de Planificación y Carga

| SP Legacy | Endpoint OSS |
|---|---|
| usp_Pedido_PrepararCarga | POST /api/v1/planificacion/preparar-carga |
| usp_Plan_GenerarPreCarga | POST /api/v1/planificacion/generar-pre-carga |
| usp_Plan_GuardarCantidad | PATCH /api/v1/planificacion/detalle/{id}/cantidad |
| usp_Plan_GuardarCantidadCILPRO | PATCH /api/v1/planificacion/cilpro/cantidad |
| usp_Plan_GuardarLinea | POST /api/v1/planificacion/lineas |
| usp_Plan_InsertarDetallePreCarga | POST /api/v1/planificacion/pre-carga/{id}/detalle |
| usp_Plan_InsertarServiciosEnAgenda | POST /api/v1/planificacion/generar-agenda |
| usp_Plan_ListarPedidosCILPRO | GET /api/v1/planificacion/pedidos-cilpro |
| usp_Plan_ListarPendientes | GET /api/v1/planificacion/pendientes |
| usp_Plan_PreparacionCarga | GET /api/v1/planificacion/preparacion-carga |
| usp_Plan_ListarPreCargaDetalle | GET /api/v1/planificacion/pre-carga/{id}/detalle |
| usp_Plan_ListarPreCargaPendiente | GET /api/v1/planificacion/pre-cargas-pendientes |
| usp_Llenado_ListarPendientes | GET /api/v1/llenado/pendientes |
| usp_Llenado_RegistrarLote | POST /api/v1/llenado/registrar-lote |
| usp_Llenos_ListarActuales | GET /api/v1/llenado/cilindros-llenos |

## 4. SPs de Escaneo y Despacho

| SP Legacy | Endpoint OSS |
|---|---|
| usp_Scan_Procesar | POST /api/v1/despacho/escanear |
| usp_Scan_EntregarCilindro | POST /api/v1/despacho/entregar-cilindro |
| usp_Scan_RegistrarVenta | POST /api/v1/despacho/registrar-venta |
| usp_Traslado_ListarParaCarga | GET /api/v1/traslados/{id}/carga |

**Pasos que debe ejecutar el escaneo de despacho**:

1. Validar que el producto existe
2. Opcional: validar ADR vigente (ufn_Valida_ADR → ver vw_EdetPB_Vigente)
3. Opcional: validar PH vigente (ufn_Valida_PH → ver tabla Eph)
4. Cambiar estado del cilindro según tipo de servicio usando la máquina ECilindroEstadoTransicion
5. Registrar en DetalleMovimiento (serie, cantidad, precio)
6. Mapeo servicio → estado destino:

| Servicio | Estado Destino |
|----------|---------------|
| VENTA | EN_CLIENTE_LLENO |
| CANJE_ENTREGA | EN_CLIENTE_LLENO |
| CANJE_RECOJO | EN_ALMACEN_VACIO |
| ALQUILER | EN_CLIENTE_LLENO |
| DEVOLUCION | EN_ALMACEN_VACIO |
| RECHAZO | EN_ALMACEN_VACIO |
| SPOT | EN_CLIENTE_LLENO |

## 5. SPs de Agenda del Repartidor

| SP Legacy | Endpoint OSS |
|---|---|
| usp_Agenda_InsertFromPlus | POST /api/v1/agenda |
| usp_Agenda_InsertServicioDesdePlus | POST /api/v1/agenda/servicio |
| usp_Agenda_CerrarDesdePlus | PUT /api/v1/agenda/{id}/cerrar |
| sp_Listar tareas por fecha | GET /api/v1/agenda?fecha=&repartidor_id= |

## 6. Funciones Escalares (fn_ → helpers)

| Función Legacy | Equivalente OSS |
|---|---|
| fn_ADR_Points(@CodProducto, @Cantidad) | adr_service.calcular_puntos(producto_id, cantidad) |
| fn_ContenidoCilindro(@CodProducto) | producto_service.obtener_contenido_kg(producto_id) |
| ufn_Valida_ADR(@ProductoGasId) | adr_service.validar_adr(producto_gas_id) |
| ufn_Valida_PH(@CilindroId) | cilindro_service.validar_ph(producto_id) |

## 7. SPs de ADR

| SP Legacy | Endpoint OSS |
|---|---|
| usp_ADR_CalcularPuntosDocumento | GET /api/v1/adr/puntos?movimiento_id=X |
| usp_ADR_EvaluarPedido | GET /api/v1/adr/evaluar?producto_id=&cantidad= |
| usp_ADR_SeleccionarCamion | POST /api/v1/adr/seleccionar-camion |

## 8. SPs de Reportes

| SP Legacy | Endpoint OSS |
|---|---|
| usp_Rpt_Cilindros_EstadoActual | GET /api/v1/reportes/cilindros/estado-actual |
| usp_Rpt_Cilindros_EstadoActual_SinRango | GET /api/v1/reportes/cilindros/estado-actual-sin-rango |
| usp_Rpt_Cilindros_Historico | GET /api/v1/reportes/cilindros/historico |
| usp_CilindroEstadoLog_Reporte | GET /api/v1/reportes/cilindros/log |
| usp_Producto_StockPlanificado | GET /api/v1/reportes/productos/stock-planificado |

## 9. SPs de Carta Porte

| SP Legacy | Endpoint OSS |
|---|---|
| usp_CartaPorte_Cabecera | GET /api/v1/movimientos/{id}/carta-porte/cabecera |
| usp_CartaPorte_Detalle | GET /api/v1/movimientos/{id}/carta-porte/detalle |
| usp_CartaPorte_Resumen | GET /api/v1/movimientos/{id}/carta-porte/resumen |
| usp_CartaPorte_ResumenFromSeries | POST /api/v1/carta-porte/resumen-desde-series |
| usp_CartaPorte_ResumenPorMovimiento | GET /api/v1/movimientos/{id}/carta-porte |

## 10. SPs de Tipo Documento con Movimiento de Envases

TipoDoc con MueveEnvases = 1:

| # | Tipo Documento | Origen | Destino | Endpoint OSS |
|---|---|---|---|---|
| 5 | Albarán Entrega a cliente (SC) | ALMACEN | CLIENTE | POST /api/v1/movimientos/entrega-cliente |
| 13 | Albarán Recepción cliente (IC) | CLIENTE | ALMACEN | POST /api/v1/movimientos/recepcion-cliente |
| 14 | Albarán Recepción proveedor (IP) | PROVEEDOR | ALMACEN | POST /api/v1/movimientos/recepcion-proveedor |
| 41 | Albarán Entrega a proveedor (SP) | ALMACEN | PROVEEDOR | POST /api/v1/movimientos/entrega-proveedor |

Cada uno de estos movimientos debe ejecutar, en el service layer, la validación de transición de estado de cilindros y el registro de log correspondiente, según la tabla ECilindroEstadoTransicion documentada en la sección 2.1.
