# Consulta de Disponibilidad para Logística

## ¿Qué usa logística para decidir disponibilidad?

Logística usa **mezcla de ambos** sistemas, pero separados según la decisión:

### 1. Stock genérico por producto

```sql
fn_StockFisico_Planificador(@CodProducto, @IdAlmacen)
```

La función oficial del planificador. Calcula stock desde `DetalleMovimiento` con filtros:
- `Estado = 1` (movimientos activos)
- `inventario = 1` (afecta inventario)
- `TipoAtencion = 1` (movimientos reales, no planificados)

**Devuelve**: "Hay 50 unidades de Bombona 15KG disponibles para planificar"

**NO distingue**: llenos vs vacíos. Es un número genérico de "unidades disponibles".

### 2. Estado por cilindro (individual)

```sql
sp_StockCilindros_PorProducto(@CodProducto, @CodAlmacen)
```

Usa la vista `Valmacen_Envases` que agrupa cilindros por su motivo (estado operativo):
- Stock_Lleno
- Stock_Vacio
- Stock_Cargado
- Stock_EnTransito
- Stock_Recepcionado

**Devuelve**: "20 llenos, 25 vacíos, 5 en tránsito"

### 3. Consultas específicas de cilindros disponibles

Vistas disponibles (37 vistas relacionadas):

| Vista | Propósito |
|---|---|
| `v_CilindrosLlenosPorProductoAlmacen` | Cilindros llenos agrupados |
| `v_Cilindros_VaciosEnAlmacen` | Cilindros vacíos en almacén |
| `v_CilindrosDisponibles` | Cilindros disponibles (probablemente llenos) |
| `v_BombonasDisponibles` | Similar, para UI de logística |
| `vw_BombonasEstadoActual` | Estado actual de bombonas |
| `v_Cilindro_UltimoEstado` | Último estado de cada cilindro |
| `v_CilindroEstadoOperativoActual` | Estado operativo actual |
| `vECilindro_UbicacionActual` | Ubicación actual del cilindro |

## Contrato actual entre stock y envases

```
Logística pregunta:
  1. "¿Cuántas unds de Bombona 15KG hay?"  → fn_StockFisico_Planificador
  2. "¿De esas, cuántas están llenas?"      → sp_StockCilindros_PorProducto
  3. "¿La serie BOM-001 está disponible?"    → ECilindroEstadoActual

NO hay una sola consulta que responda:
  "De las 50 unds de stock, 20 están llenas en almacén A"
```

## Contrato OSS propuesto

Para OSS, la disponibilidad debería responder:

```sql
-- Unificada
SELECT 
    producto, almacen,
    total_unds,        -- fn_StockFisico_Planificador
    llenos,            -- sp_StockCilindros_PorProducto
    vacios,
    en_transito
FROM vw_DisponibilidadUnificada
WHERE producto = @Prod AND almacen = @Almacen
```

Esto requiere sincronizar `ECilindroEstadoActual` con los movimientos de stock (hoy no existe).
