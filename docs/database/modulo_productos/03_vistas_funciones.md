# 03 — Vistas y Funciones — Módulo Productos/Catálogos

## Vistas

### vw_EdetPB_Vigente
**Propósito**: Obtener la fila vigente de datos ADR para una bombona
**Tablas origen**: `Edetalle_Producto_Bombona`
**Uso**: SP `usp_EdetPB_ObtenerVigente`
**WHERE**: `VigenteHasta IS NULL` (fila actual vigente)

### vCilindroEstadoLogDet
**Propósito**: Detalle del log de estados de cilindros con joins a personas
**Tablas origen**: `ECilindroEstadoLog`, `Producto`, `Persona_Nuevo`
**Uso**: SP `usp_Rpt_Cilindros_Historico`

### ECilindroEstadoActual
**Propósito**: Obtener el último estado de cada cilindro (vista, no tabla física)
**Tablas origen**: `ECilindroEstadoLog` con `ROW_NUMBER() OVER (PARTITION BY Serie)`
**Uso**: SPs de consulta de estado actual de cilindros

### vPlan_PedidosCILPRO
**Propósito**: Pedidos CILPRO con datos de planificación
**Uso**: SP `usp_Plan_ListarPedidosCILPRO`

## Funciones

### fn_StockDisponible
**Propósito**: Stock disponible de un producto
**Tipo**: Función escalar
**Documentada en**: módulo stock

### fn_StockFisico_Planificador
**Propósito**: Stock físico para planificador
**Tipo**: Función escalar
**Documentada en**: módulo stock

### fn_StockFisico_Planificador_Grupo
**Propósito**: Stock físico por grupo para planificador
**Tipo**: Función escalar
**Uso en productos**: SP `usp_Plan_ListarPendientes` llama a esta función

### fn_StockReal
**Propósito**: Stock real de productos
**Tipo**: Función escalar

### fn_ContenidoCilindro(@CodProducto)
**Propósito**: Obtener el contenido de un cilindro
**Tipo**: Función escalar

### fn_TaraCilindro(@CodProducto)
**Propósito**: Obtener la tara de un cilindro
**Tipo**: Función escalar

### fn_TTE_Categoria(@CodProducto)
**Propósito**: Categoría de transporte
**Tipo**: Función escalar

### fnMOSTRARDIASDEVOLVER(@fecha, @producto)
**Propósito**: Días para devolución de producto
**Tipo**: Función escalar

### ufn_Valida_ADR(@Producto)
**Propósito**: Validar si un producto tiene ADR vigente
**Tipo**: Función escalar
**Uso**: SP `usp_Scan_Procesar` la utiliza para validar antes de escanear

### ufn_Valida_PH(@ProductoId)
**Propósito**: Validar si un cilindro tiene PH vigente
**Tipo**: Función escalar
**Uso**: SP `usp_Scan_Procesar`
