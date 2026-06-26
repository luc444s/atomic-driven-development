# Stored Procedures — Sys_GMS_ESCR

**Total:** 944 procedimientos almacenados

---

## Prefijos por cantidad

| Prefijo | Cantidad | Propósito |
|---|---|---|
| `sp_` | 177 | CRUD estándar y operaciones de negocio modernas |
| `Mos` / `Mostrar_` | 103 | Consultas SELECT para grids, combos, reportes |
| `Bus` / `Buscar_` | 82 | Búsquedas por nombre, código, RUC, serie |
| `Pro` / `Producto_` | 76 | CRUD y lógica de productos, cilindros, envases |
| `usp_` | 56 | CRUD alternativo (mismo patrón que `sp_`) |
| `Mod` / `Modificar_` | 33 | Actualizaciones específicas |
| `CON_` / `Config_` | 32 | Configuraciones del sistema (TC, precios, etc.) |
| `Act` / `Actualizar_` | 32 | Actualizaciones de estado |
| `ins` / `Insertar_` | 25 | Inserciones específicas |
| `CP_` | 22 | Códigos postales y geolocalización |
| `Eli` / `Eliminar_` | 13 | Eliminaciones (físicas o lógicas) |
| `Pac_` / `Per_` / `Cli_` | ~30 | Personas (clientes, proveedores, personal) |
| Otros | ~280 | Funciones auxiliares, reportes, utilidades |

---

## Nomenclatura

| Patrón | Ejemplo |
|---|---|
| `PrefijoEntidad_Acción` | `sp_AgendaRepartidor_Insertar` |
| `Acción_Entidad` | `Buscar_ClientexnomFiscal` |
| `Entidad_Acción` | `Producto_ActualizarPrecios` |
| `Prefijo_Acción_Entidad` | `usp_Insertar_Cliente` |

---

## Clasificación funcional

### CRUD estándar (`sp_`, `usp_`, `ins_`, `Eli_`, `Act_`)
Siguen el patrón:
- `_Insertar` → INSERT + SCOPE_IDENTITY()
- `_Actualizar` → UPDATE por ID
- `_Eliminar` → DELETE o UPDATE de estado
- `_Listar` → SELECT con filtros
- `_Buscar` → SELECT con LIKE

### Catálogos
- **Almacenes** → `mostrar_almacen`, `Alm_*`
- **Productos** → `Producto_*`, `Buscar_*Producto*`
- **Clientes** → `Buscar_Clientex*`, `Per_*`, `Cli_*`
- **Proveedores** → `COM_Proveedor*`, `Buscar_*Prov*`
- **Líneas / Sublíneas / Marcas** → `mostrar_linea`, `Lin_*`, `Mar_*`
- **Ubicaciones geográficas** → `CP_*`, `Ubi_*`

### Movimientos / Transacciones
- `Mov_Ingreso_*`, `Mov_Salida_*` — movimientos de almacén
- `Mov_Compras_*`, `Mov_Ventas_*` — compras y ventas
- `Mov_Traslado_*` — traslados entre almacenes
- `Mov_Llenado*` — llenado de bombonas/cilindros
- `FrmMov*` — los que llaman los formularios directamente

### Operaciones de negocio críticas
- **Agenda de repartidor** → `sp_AgendaRepartidor_*` (~20 SPs)
- **Carga de repartidor** → `sp_CargaRepartidor_*`
- **Planificación** → `sp_Planificacion_*`, `FrmMovPlanificacion*`
- **Intercambio de cilindros** → `sp_IntercambioCliente_*`
- **Retorno de vehículo** → `sp_RetornoVehiculo_*`

### Reportes (`Mos`, `REP_`, `CR_`)
- `Mostrar_*` — consultas que alimentan formularios de reportes
- `CR_*` — llamados desde Crystal Reports
- `REP_*` — reportes específicos

### Facturación electrónica (SUNAT / Nubefact)
- `sp_Facturacion_*`, `Fact_*` — generación de comprobantes
- `sp_EnviarSunat*` — envío a SUNAT
- `sp_AnularComprobante*` — bajas / notas de crédito

---

## Archivos generados en esta carpeta

| Archivo | Contenido |
|---|---|
| `lista_completa_sp.txt` | Los 944 SPs en orden alfabético |
| `sps_por_fecha.txt` | SPs ordenados por fecha de creación |
| `ejemplo_sp_crud.txt` | Código de `sp_AgendaRepartidor_Insertar` (típico CRUD) |
| `ejemplo_sp_busqueda.txt` | Código de `Producto_BuscarxNroSerie` (búsqueda típica) |
| `prefijos_sp.txt` | Conteo de SPs agrupados por prefijo |
