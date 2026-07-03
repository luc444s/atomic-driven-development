# La Pregunta Más Importante

## "Hay 50 bombonas 15KG" — ¿Qué significa exactamente?

En el legacy SYSTUTOR, la frase "hay 50 bombonas 15KG" puede significar **4 cosas distintas** según quién la dice y dónde la consulta:

### 1. ¿50 cilindros físicos de ese tipo?
- **`sp_StockCilindros_PorProducto`** contando todos los motivos = 50
- **`SELECT COUNT(*) FROM ECilindroEstadoActual WHERE ProductoId=X`** = 50 (si todos están registrados)
- **Significado**: Existen 50 envases físicos de ese modelo en el sistema

### 2. ¿50 cargas de gas?
- **`fn_StockReal(prod_gas, almacen)`** = 750 KG / 15 KG por carga = 50 cargas
- **Significado**: Hay gas suficiente para llenar 50 bombonas
- **NOTA**: El stock de gas y el stock de envases son independientes. Podría haber 50 cargas de gas pero solo 30 envases, o viceversa.

### 3. ¿50 unidades disponibles para vender?
- **`fn_StockFisico_Planificador(prod_envase, almacen)`** = 50 unds
- **Significado**: Stock disponible según criterios logísticos (movimientos activos, inventariables, reales)
- **No distingue**: llenos vs vacíos — asume que la unidad está disponible

### 4. ¿50 cilindros en cierto estado?
- **`sp_StockCilindros_PorProducto`** desglosado:
  - Stock_Lleno = 20
  - Stock_Vacio = 25
  - Stock_EnTransito = 5
- **Significado**: Distribución por estado operativo de los 50 cilindros

## Tabla de Correspondencia

| Contexto | Sistema | Valor | Dimensión |
|---|---|---|---|
| "Hay 50 bombonas" (almacén) | fn_StockFisico_Planificador | 50 UND | Unidades de envase |
| "Hay 50 bombonas" (logística) | sp_StockCilindros_PorProducto | 20L + 25V + 5T = 50 | Estados de cilindros |
| "Hay 50 cargas" (ventas) | fn_StockReal(gas) | 750 KG / 15 = 50 | Equivalencia en gas |
| "Hay 50 registradas" (control) | ECilindroEstadoActual | 50 series | Cilindros individuales |

## ¿Pueden diferir?

**Sí, y de hecho es probable que difieran:**

| Escenario | Stock dice | Estado dice | Explicación |
|---|---|---|---|
| Cilindro creado sin log | 50 unds | 48 registros | 2 cilindros sin ECilindroEstadoActual |
| Gas comprado sin envases | 50 cargas de gas | 40 envases | Hay gas pero faltan envases |
| Envases vacíos en almacén | 50 unds disponibles | 50 vacíos | Stock dice "disponible" pero todos están vacíos |
| Envases llenos en cliente | 40 unds (egresaron) | 50 llenos | No se actualizó estado al vender |

## Conclusión para OSS

**En OSS, "hay 50 bombonas 15KG" debe responder:**

```sql
Producto:        Bombona 15KG (Cod_Producto = 1234)
Almacen:         ALM-001

Stock físico:    50 unds       (de Producto)
Stock gas:       750 KG        (equivalente a 50 cargas de 15KG)

Estado actual:
  Llenas:        20            (listas para despachar)
  Vacías:        25            (disponibles para llenar)
  En tránsito:   5             (en ruta)
  Total:         50            (debe coincidir con stock físico)

Diferencia stock vs estados:  0  (siempre debe ser 0)
```

Para lograr esto, OSS necesita:
1. **Trigger/SP**: Cada movimiento de stock que afecte un envase debe actualizar `ECilindroEstadoActual`
2. **Sincronización**: Al crear/eliminar un cilindro, debe crearse/eliminarse su registro en ambas tablas
3. **Reporte de conciliación**: Para detectar diferencias entre stock cuantitativo y estados individuales
4. **Una vista única** que responda la pregunta completa en una sola consulta
