# Módulo Clientes — Riesgos de Migración

## Evaluación por Elemento

| Elemento | Estado | Acción Requerida |
|----------|--------|-----------------|
| `Persona_Nuevo` (tabla universal) | **[TRANSFORMAR]** | Separar en customers, suppliers, employees, drivers |
| `Direccion` | **[OK]** | Mapeo 1:1 al nuevo diseño |
| `Vehiculo_cliente_nuevo` (Puntos de Entrega) | **[OK]** | Renombrar a `puntos_entrega` |
| `Cliente_Sucursal` | **[VALIDAR]** | FK apunta a Vehiculo_cliente_nuevo, no a Persona_Nuevo |
| `Formas_pago` | **[OK]** | Catálogo 1:1 |
| `EClaves_operacion` | **[OK]** | Solo España/EU |
| `Telefonos`, `Correos` | **[OK]** | Tablas hijas 1:1 |
| `Creditos` | **[OK]** | Mapeo 1:1, renombrar columna Cod_VehiculoCliente |
| `Tarifa_cliente` | **[OK]** | Precios especiales por cliente+producto |
| `Direcciones_NoClientes` | **[OK]** | Tabla separada |

### Stored Procedures

| Categoría | Estado | Acción |
|-----------|--------|--------|
| Insertar_Persona_Nuevo | **[TRANSFORMAR]** | Separar por tipo de persona |
| Modificar_Persona_Nuevo | **[TRANSFORMAR]** | Separar por tipo de persona |
| PERSONA_Buscar* (7 SPs) | **[TRANSFORMAR]** | Unificar en búsqueda parametrizada |
| Persona_BuscarXfiltro | **[OK]** | WHERE dinámico, reutilizable |
| MOSTRAR_PERSONA | **[VALIDAR]** | Ver JOINs exactos |
| sp_Persona_ActividadFiscal_Guardar | **[VALIDAR]** | No verificado si llama API externa |
| Insertar_ClienteProveedor | **[TRANSFORMAR]** | Separar cliente vs proveedor |
| Personal_Insertar | **[TRANSFORMAR]** | Mover a módulo RRHH |
| BuscarClientesAnotificar | **[VALIDAR]** | No se conoce condición "notificable" |
| SP_PERSONA_MOSTRARMOZO | **[OBSOLETO]** | Módulo mozo legacy |
| crear_personalm / eliminar_personalm | **[OBSOLETO]** | Legacy no migrar |
| Insertar_Establecimiento | **[VALIDAR]** | TRUNCADO en documentación |
| sp_Despacho_ListarPuntosEntrega | **[NO ENCONTRADO]** | Buscar en BD |
| Vehiculo_cliente_nuevo_SetPrincipal | **[OK]** | Lógica clara, renombrar |
| Direccion_CapturaEnSitio | **[OK]** | Lógica con Google Maps |
| InsertarClienteSucursal | **[VALIDAR]** | FK a Vehiculo_cliente_nuevo |
| DatosBancarios_CambiarCuentaCliente | **[OK]** | Mantiene histórico |
| SucursalGeo_GetDefaults | **[OK]** | Defaults geográficos |

### Vistas y Funciones

| Elemento | Estado | Acción |
|----------|--------|--------|
| 144 vistas (ninguna con CREATE VIEW) | **[PENDIENTE]** | Extraer definiciones de BD |
| v_ClientesEnRiesgo | **[PENDIENTE]** | Sin definición, reconstruir desde lógica |
| Vreporte_persona | **[PENDIENTE]** | Usada por CRreporte_persona |
| 22 funciones (ninguna toca módulo clientes) | **[OK]** | No migrar |

### Forms VB

| Formulario | Estado | Acción |
|-----------|--------|--------|
| FrmCatClientes (818KB) | **[TRANSFORMAR]** | Dividir en componentes por pestaña |
| FrmRegClientePRO (545KB) | **[TRANSFORMAR]** | Unificar con FrmCatClientes |
| FrmRegClientePLUS (199KB) | **[OBSOLETO]** | Reemplazar por versión completa |
| FrmRegCliente (65KB, antiguo) | **[OBSOLETO]** | No migrar |
| FBusPacPRO / PLUS / PROcr / Prov | **[TRANSFORMAR]** | Unificar en un buscador parametrizado |

### Reportes Crystal

| Reporte | Estado | Acción |
|---------|--------|--------|
| CRreporte_persona | **[TRANSFORMAR]**| Migrar a nuevo reporteador |
| CRAlmacen_EnvasesXcliente | **[VALIDAR]** | Ver lógica de filtro `ubicacion = 'CLIENTE'` |
| CRDeudasxCobrar | **[OK]** | Migrar |
| CREstadoCtaAdm | **[OK]** | Migrar |
| vTICKETFAC* (4 reportes) | **[TRANSFORMAR]**| Migrar a nuevo formato de ticket |
| CRLetras, CRFacturacion, CRDeudasxCobrarBACK | **[OBSOLETO]** | Código muerto, no migrar |

### DAL (CPaciente.vb)

| Elemento | Estado | Acción |
|----------|--------|--------|
| 109 métodos | **[TRANSFORMAR]**| Refactorizar por entidad (customer, supplier, employee) |
| InsertarPersonaNuevo / ModificarPersonaNuevo | **[OK]**| Renombrar y separar |
| 2 métodos SQL inline | **[CORREGIR]**| Migrar a SPs o consultas parametrizadas |
| 10 métodos con Rollback comentado | **[CORREGIR]**| Corregir manejo de transacciones |
| Métodos duplicados (DesConnectar/DesConectar) | **[CORREGIR]**| Eliminar duplicados |

---

## Riesgos Priorizados

| # | Riesgo | Impacto | Prioridad |
|---|--------|---------|-----------|
| R1 | `Persona_Nuevo` es tabla universal — cambiar afecta a clientes, proveedores, empleados, repartidores | Alto | **CRÍTICO** |
| R2 | Validación fiscal SOLO en forms VB (ninguna en BD ni DAL) | Alto | **ALTA** |
| R3 | `Pass_Persona` usa MD5 (inseguro) | Alto | **ALTA** |
| R4 | No hay definiciones de vistas (144 vistas sin CREATE VIEW) | Alto | **ALTA** |
| R5 | 30+ formularios consultan Persona_Nuevo directamente (queries inline) | Alto | **ALTA** |
| R6 | FK Cliente_Sucursal apunta a Vehiculo_cliente_nuevo (no a Persona_Nuevo) | Medio | **MEDIA** |
| R7 | SPs Insertar_Establecimiento y Buscar_ClientexnomFiscal TRUNCADOS en docs | Medio | **MEDIA** |
| R8 | 10+ métodos DAL con Rollback comentado | Medio | **MEDIA** |
| R9 | Reportes Crystal con conexión hardcodeada (sa/password) | Medio | **MEDIA** |
| R10 | Código muerto: CRDeudasxCobrarBACK, CRLetras, CRFacturacion, FrmRegCliente | Bajo | **BAJA** |
| R11 | FBusPacPLUS.KeyPress apunta a FrmRegClientePRO (BUG) | Bajo | **BAJA** |
| R12 | No hay triggers, jobs ni schedules documentados | Medio | **MEDIA** |
