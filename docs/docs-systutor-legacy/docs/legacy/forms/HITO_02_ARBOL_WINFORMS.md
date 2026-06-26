# HITO 2 — Árbol de WinForms del ERP-SYSTUTOR

**Total forms:** 218 archivos `.Designer.vb`
**Forms activos referenciados desde MDIMenu:** ~110

---

## Arquitectura General

```
MDIMenu.vb (MDI Principal)
├── TreeView dinámico (desde BD: CMenu.ListarMenuPrincipal)
│   └── trv_DoubleClick → apertura de forms según texto del nodo
├── ToolStripMenuItems fijos
├── Paneles laterales (PanelEnvases, PanelCaja, Panellogistica)
└── Botones de acceso rápido (Button1..Button44)
```

El menú se carga desde la BD (tabla de menús → submenús → opciones). Cada nodo del árbol tiene un texto que se compara en `trv_DoubleClick` para abrir el form correspondiente.

---

## Categorías de Forms

### 1. Catálogos Maestros (18 forms)

| Form | Propósito |
|---|---|
| `FrmCatClientes` | Registro de clientes |
| `FrmCatProveedores` | Registro de proveedores |
| `FrmCatProductos` | Registro de productos |
| `FrmCatBombonas` | Registro de bombonas/cilindros |
| `FrmCatLineas` | Líneas de productos |
| `FrmCatSubLineas` | Sub-líneas |
| `FrmCatMarca` | Marcas |
| `FrmCatRubro` | Rubros |
| `FrmUnidad` | Unidades / presentaciones |
| `FrmRazonSocial` | Empresas / Razones sociales |
| `FrmRegSUCURSAL` | Sucursales |
| `FRegUbic` | Áreas / ubicaciones de almacén |
| `FRegSerie` | Series de documentos |
| `FRegSerTer` | Packs de producto |
| `FRegTipAte` | Tipos de atención |
| `FrmConfgrupo` | Grupos de producto |
| `FrmPromProducto` | Promociones de producto |
| `FRegEquipos` | Equipos por sucursal |

### 2. Facturación / Ventas (16 forms)

| Form | Propósito |
|---|---|
| `FrmRegVentasPRO` | Facturación corporativa (PRO) |
| `FrmRegVentasgOC` | Orden de compra cliente |
| `FrmRegVentasgOCcotiz` | Recojo botellas / cotización |
| `FrmRegVentasgPagosAcuentadeOC` | Fact. con pagos a cuenta de OC |
| `FrmMovFacturacion` | Facturación electrónica |
| `FrmMovFacturacionDirecta` | Registro interno de ventas |
| `FrmFacturacionProgramada` | Facturación programada |
| `FrmMovPresupuestoCliente` | Presupuestos |
| `RegVentasgDIRECTAS` | Venta directa |
| `RegVentasgDIRECTASBasic` | Venta directa básica |
| `RegVentasgDIRECTASmultiSeries` | Venta multi-serie |
| `RegVentasgDIRECTASSereiemultiStock` | Venta rápida contado |
| `FrmRepLventas` | Envío notificaciones correo |
| `FrmRepLventasPRO` | Reenvío fact. electrónica |
| `FrmDEVOLUCIONES` | Devoluciones |
| `FrmGarantia` | Garantías |

### 3. Compras / Proveedores (8 forms)

| Form | Propósito |
|---|---|
| `FrmMovCompras` | Registro de compras |
| `FrmRegCompras` | Compras (alternativo) |
| `FrmRegOCproveedor` | Orden de compra a proveedor |
| `FrmMovIngresoProveedor` | Recepción bombonas proveedor |
| `FrmMovSalidaProveedor` | Envío bombonas proveedor |
| `FrmREGENVIOPROV` | Envío a proveedor |
| `FrmREGENVIOPROVadmin` | Envío a proveedor (admin) |
| `FrmReporteComprasP` | Reporte compras por pagar |

### 4. Cilindros / Bombonas / Envases (14 forms)

| Form | Propósito |
|---|---|
| `FrmMovLlenadoBombonas` | Planta de llenado |
| `FrmMovIntercambioCliente` | Módulo de reparto (intercambio) |
| `FrmMovTrasladoAlmacen` | Traslado de cilindros |
| `FrmOrdenSalida` | Orden de salida |
| `FrmOrdenSalidaADMIN` | Orden de salida admin (cilindros llenos) |
| `FrmOrdenSalidaTransf` | Orden salida transferencia |
| `FrmOrdenIngresoC` | Recepción envases clientes |
| `FrmOrdenIngresoPllenado` | Ingreso a planta de llenado |
| `FrmMovPreparacionCarga` | Preparación de carga |
| `FrmMovRetornoVehiculo` | Descarga de vehículo |
| `FrmActuPH` | Actualizar PH (prueba hidráulica) |
| `FrmHistorialCilindro` | Historial de cilindro |
| `FrmReportedETeNVASE` | Consulta de envases |
| `FrmVistaEtiqueta` | Vista de etiqueta de cilindro |

### 5. Planificación / Logística / Reparto (11 forms)

| Form | Propósito |
|---|---|
| `FrmMovPlanificacionOperaciones` | Planificar pedido (nuevo) |
| `FrmMovPlanificacionOperacionesAntiguo` | Planificar pedido (antiguo) |
| `FrmMovPlanificacionADR` | Planificar pedido/ADR |
| `FrmAgendaRepartidor` | Tareas programadas / agenda |
| `FrmHistorialAgendaCliente` | Agenda por cliente |
| `FrmCargaRepartidor` | Carga del repartidor |
| `FrmParametrosRepartidor` | Parámetros del repartidor |
| `FrmDespacho` | Atender pedido |
| `FrmRecepcion` | Recepción de descarga |
| `FrmIncidenciasRepartidor` | Incidencias del repartidor |
| `FrmDiagnosticoTaller` | Diagnóstico de taller |

### 6. Caja / Finanzas (12 forms)

| Form | Propósito |
|---|---|
| `Frmcierrecaja` | Apertura y cierre de caja |
| `FrmRegcaja` | Movimiento de caja |
| `FrmRegcajaA` | Movimiento entre bancos |
| `FrmCajaAdministrativa` | Reporte bancos x moneda |
| `FrmCajaAdministrativaRep` | Reporte de bancos |
| `FrmAmortizaciones` | Cancelación de cliente |
| `FrmAmortizaciones01` | Cancelaciones (alternativo) |
| `FrmAmortizaProv2` | Cancelación a proveedor |
| `FrmRegCVmoneda` | Compra/venta moneda extranjera |
| `FrmCONFTC` | Configurar tipo de cambio |
| `Frmcomision` | Registrar comisiones |
| `FrmRegistraramortizacion` | Registrar amortización |

### 7. Reportes (22 forms)

| Form | Propósito |
|---|---|
| `FrmReportes` | Visor de Crystal Reports |
| `FrmReporteVentas` | Reporte de ventas |
| `FrmReporteVentas01` | Ventas x medio de pago |
| `FrmReporteVentas02` | Reporte de compras |
| `FrmReportedxc` | Ventas por cobrar |
| `FrmReporteCompras` | Reporte de compras |
| `FrmReporteEntregas` | Centro de reporte operativo |
| `FrmRepAlmacenes` | Reporte de almacén |
| `FrmRepCajaTienda` | Cierre caja tienda (nuevo) |
| `FrmRepLventas` | Envío notificaciones |
| `FrmRepLventasPRO` | Reenvío facturación |
| `FrmRepmovimientos` | Reporte movimientos (nuevo) |
| `FrmRepentregasTranfsuc` | Entregas/traslados |
| `FrmRepentregasMed01` | Productos c/s stock |
| `FRMvalorizado` | Stock valorizado |
| `FrmDETALLE1` a `FrmDETALLE5` | Reportes detallados varios |
| `FrmEstadoCuenta` | Estado de cuenta |
| `FRMMASVENDIDOS` | Más vendidos |
| `FrmuTILIDADES` / `FrmuTILIDADES1` / `FrmuTILIDADES2` | Utilidades |
| `FrmRepEstadoOperativo` | Estado operativo |

### 8. Administración / Configuración (12 forms)

| Form | Propósito |
|---|---|
| `MDIMenu` | Menú principal MDI |
| `MDIMenuNuevo` | Menú nuevo (alternativo) |
| `Frmusuario` | Login de usuario |
| `FrmRegPersonal` | Registrar usuario/personal |
| `FrmRegEmpleado` | Registrar empleado |
| `FrmPermiso` | Registrar permisos |
| `FormCofParametro` | Configurar parámetros |
| `FrmBackup` | Backup de base de datos |
| `FrmRestaurarbd` | Restaurar base de datos |
| `FrmConfOpcionesbanco` | Configurar opciones de banco |
| `FrmRegVisorSucesos` | Visor de sucesos |
| `FrmRegDesc` | Registrar descuentos |

### 9. Forms de Búsqueda (FBus*) — ~20 forms

Forms modales de búsqueda y selección:

| Form | Propósito |
|---|---|
| `FBusEmpleado` | Buscar empleado |
| `FBusEmpresa` | Buscar empresa |
| `FBusLab` | Buscar laboratorio |
| `FBusPacPLUS` / `FBusPacPRO` / `FBusPacPROcr` | Buscar paciente/cliente |
| `FBusPacProv` | Buscar proveedor |
| `FBusPersonal` | Buscar personal |
| `FBusRea` / `FBusRea1` | Buscar... |
| `FBusSerie` | Buscar serie de documento |
| `FBusServTerc` | Buscar servicio tercero |
| `FBusTChequeo` | Buscar tipo de chequeo |
| `FBusTipoAte` | Buscar tipo de atención |
| `FBusUbic` | Buscar ubicación |
| `FBusUnidad` | Buscar unidad |

### 10. Forms Auxiliares (10 forms)

| Form | Propósito |
|---|---|
| `FrmExplorer` | Explorador de archivos |
| `FrmExplorerContratoPDF` | Visor de contratos PDF |
| `FrmExplorerFotoCliente` | Visor de fotos de cliente |
| `Frmenviarmail` | Envío de correos |
| `FormImg` | Visor de imágenes |
| `FrmRichtextbox` | Editor de texto |
| `CustomMessageBox` | MessageBox personalizado |
| `Dialog1` | Diálogo de confirmación |
| `FrmAcercad` | Acerca de... |
| `FrmConfVacaciones` | Configurar vacaciones |

### 11. Forms de Módulos Específicos

| Form | Propósito |
|---|---|
| `FrmRegOrden` | Registrar orden |
| `FrmRegPrepedido` | Pre-pedido |
| `FrmRegProforma` | Proforma |
| `FrmRegTransf` | Transferencias |
| `FrmRegTransfProdInterna` | Traslado productos interno |
| `FrmRegVentasgEntregasSUCunaSerie` | Fact. venta gases/productos |
| `FrmRegVentasgEntregasSUCunaSeriePROBFac` | Fact. Sucursal PRO |
| `FrmOrdenPlus` / `FrmOrdenPlusRECOGIDA` | Orden plus recogida |
| `Frmasivo` / `FrmasivoNotificaciones` | Procesos masivos / notificaciones |

---

## Patrón de creación de forms

```vb.net
' Desde MDIMenu:
Dim f As New FrmXXX
f.MdiParent = Me
f.Show()
f.BringToFront()
```

La mayoría de forms siguen este patrón:
1. Cargar datos en `Load` (llenar combos, grids)
2. Botón Nuevo → limpia campos
3. Botón Buscar → abre `FBus*` o llama a SP `Buscar_*`
4. Botón Guardar → ejecuta SP `sp_*_Insertar` o `sp_*_Actualizar`
5. Botón Eliminar → ejecuta SP `sp_*_Eliminar`
6. Botón Reporte → abre `FrmReportes` con Crystal Report

---

## Archivos generados

| Archivo | Contenido |
|---|---|
| `menu_forms_referencias.txt` | Lista de todas las referencias a forms desde MDIMenu |
| `todos_forms.txt` (en sp_info) | Los 218 forms del proyecto |
