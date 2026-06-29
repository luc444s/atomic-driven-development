# 00 — Extracción de Base de Datos — Productos/Catálogos

## Conexión
- Servidor: ACONCAGUA
- BD: Sys_GMS_ES
- Motor: SQL Server (2008+)

## Hallazgos generales

### Sin Foreign Keys en Producto
La tabla `Producto` **no tiene ninguna FK** definida a nivel de base de datos. Las relaciones con `Linea`, `TipoInsumo`, `Unidad`, `Marca`, `EstadoProducto`, `SubCategoria`, `Grupo` existen solo a nivel de aplicación (VB.NET). Esto significa:
- No hay integridad referencial en BD.
- Se pueden insertar productos con IDs de línea, marca, etc. que no existen.
- Las limpiezas de catálogos pueden dejar huérfanos.

### Sin Triggers en Producto
No se encontraron triggers en la tabla `Producto`.

### Sin CHECK Constraints
No hay CHECK constraints en ninguna de las tablas del módulo.

### Índices

| Tabla | Índice | Tipo | Único | PK |
|-------|--------|------|-------|----|
| Producto | PK_Producto_1 | CLUSTERED | Sí | Sí |
| Producto | IX_TarifaCliente_CodProducto | NONCLUSTERED | No | No |
| Producto | IX_Producto_NroProducto | NONCLUSTERED | No | No |
| Producto | IX_Producto_codprod | NONCLUSTERED | No | No |
| Linea | PK_Linea | CLUSTERED | Sí | Sí |
| SubLinea | PK_Sublinea | CLUSTERED | Sí | Sí |
| Marca | PK_Marca | CLUSTERED | Sí | Sí |
| TipoInsumo | PK_TipoInsumo | CLUSTERED | Sí | Sí |
| Unidad | PK_Unidad | CLUSTERED | Sí | Sí |
| SubCategoria | PK_SubCategoria_1 | CLUSTERED | Sí | Sí |
| Grupo | PK_Grupo | CLUSTERED | Sí | Sí |
| EstadoProducto | PK_EstadoProducto | CLUSTERED | Sí | Sí |
| Promocion | PK_Promocion | CLUSTERED | Sí | Sí |

### Defaults en Producto

| Columna | Default |
|---------|---------|
| Costo_Rep | ((0)) |
| crapido | ((0)) |
| costo_Ant | ((0)) |
| percepcion | ((0)) |
| cod_grupo | ((1)) |
| cgi | ((0)) |
| costo_total | ((0)) |
| servicio | ((0)) |
| stock | ((0)) |
| lista2 | ((0)) |
| lista3 | ((0)) |
| lista4 | ((0)) |

### Vistas relacionadas con productos
Se identificaron las siguientes vistas en SPs y código:
- `vw_EdetPB_Vigente` — datos ADR vigentes de bombonas
- `vCilindroEstadoLogDet` — histórico de estados de cilindros
- `vPlan_PedidosCILPRO` — pedidos CILPRO para planificación

## Tablas del módulo Productos/Catálogos

| Tabla | Propósito | Filas estimadas |
|-------|-----------|-----------------|
| Producto | Maestro principal de productos | Grande |
| Linea | Líneas de producto | Pequeño |
| SubLinea | Sublíneas de producto | Pequeño |
| Marca | Marcas de producto | Pequeño |
| Rubro | Rubros (subcategorías generales) | Pequeño |
| TipoInsumo | Tipos de insumo | Pequeño |
| Unidad | Unidades de medida | Pequeño |
| SubCategoria | Subcategorías (GAS, BOMBONAS, etc.) | Pequeño |
| Grupo | Grupos de producto | Pequeño |
| EstadoProducto | Estados de producto | Pequeño |
| Promocion | Promociones por producto | Medio |
| Descuento | Descuentos | Medio |

### Tablas auxiliares relacionadas
- `Edetalle_retimbrado` — histórico de retimbrado de bombonas
- `Edetalle_Producto_Bombona` — datos ADR por bombona con vigencias
- `Eph` — pruebas hidráulicas de bombonas
- `ECilindroEstadoLog` / `ECilindroEstadoActual` — trazabilidad de estado de cilindros
- `ECilindroEtiquetaHistorial` — log de impresión de etiquetas
- `CFG_Parametros` — parámetros de configuración

## Tablas que NO existen en BD (buscadas)
- `Bombonas` — No existe como tabla separada. Bombonas/Envases son productos normales en `Producto` con `cod_subcategoria` apuntando a "BOMBONAS"
