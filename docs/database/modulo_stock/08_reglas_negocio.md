# Reglas de Negocio — Módulo Stock/Inventario

---

## 1. Cálculo de Stock Disponible

### Fórmula general
```
StockDisponible = SUM(DetalleMovimiento.StkIngreso - DetalleMovimiento.StkEgreso)
```

Implementada en `fn_StockDisponible()` SIN filtros de estado.

### Fórmula para planificación logística
```
StockDisponible = SUM(StkIngreso - StkEgreso) 
  WHERE Movimiento.Estado = 1 
    AND Movimiento.inventario = 1 
    AND Movimiento.TipoAtencion = 1
```

Implementada en `fn_StockFisico_Planificador()`. Es la función oficial usada por el planificador logístico.

### Fórmula para stock real
```
StockReal = SUM(StkIngreso - StkEgreso)
  WHERE Movimiento.Estado = 1
```

Implementada en `fn_StockReal()`.

### Conclusión crítica
**Ninguna función consulta la tabla `Stock_Actual`.** El stock se calcula SIEMPRE desde `DetalleMovimiento`.

---

## 2. Stock Mínimo vs Stock Actual

- `Producto.StockMin_Producto` (float, nullable) — stock mínimo de seguridad
- `Producto.stock` (int, default 0) — stock actual (cache)
- `Stock_Actual.Stock` (decimal, default 0) — stock por grupo y almacén

**No hay un SP que valide stock mínimo vs stock actual.** La columna `StockMin_Producto` existe pero no se usa en alertas automáticas ni en validaciones de movimiento.

**Regla faltante:** No hay alerta de reposición cuando `stock < StockMin_Producto`.

---

## 3. Validaciones de Stock en Planificación Logística

Las siguientes reglas están en el módulo logística (`docs/legacy/database/modulo_logistica/08_reglas_negocio.md`):

| Regla | Aplicación |
|-------|-----------|
| `CantPlanificada <= CantPendiente` | Planificación de carga |
| `StockDisponible = StockActual - StockComprometido - StockPlanificado` | Cálculo en planificador |
| Estados visuales: OK (verde), PARCIAL (amarillo), SIN STOCK (rojo) | UI planificación |
| `chkPermitirSinStock` permite sobreplanificar | Bypass de validación |

**Dependencia crítica:** La planificación logística usa `fn_StockFisico_Planificador()` para validar stock. Cualquier cambio en esa función afecta directamente la planificación.

---

## 4. Diferencia de Inventario

### Proceso de ajuste (FrmInventario)

1. Usuario ingresa stock físico (conteo manual)
2. Sistema calcula: `Diferencia = StockSistema - StockFisico`
3. Si `Diferencia != 0`:
   - Si `StockFisico < StockSistema` → **EGRESO** (sobrante en sistema, falta físico)
   - Si `StockFisico > StockSistema` → **INGRESO** (falta en sistema, sobrante físico)
4. Se crea un movimiento de inventario (TipoMovimiento=6 para egreso, 1 para ingreso)
5. Se crea comprobante y detalle de movimiento
6. Se llama a `PRODUCTO_INVENTARIO_Cerrar` para actualizar stock

### Bug crítico en el proceso
**BUG (FrmInventario.vb líneas 492-493):** La decisión de ingreso/egreso se toma basándose SOLO en el primer producto del listado. El resto de productos se procesan con la misma dirección.

---

## 5. Traslado entre Almacenes

### Reglas identificadas

1. **Origen y destino no pueden ser el mismo** (validación en FrmMovTrasladoAlmacen)
2. **Cilindros llenos y vacíos se procesan por separado** — no se mezclan en un mismo detalle
3. **Estados de traslado:**
   - `EN_ALMACEN` — creado, pendiente de carga
   - `EN_RUTA` — en camino
   - `DESCARGADO_POR_RECEPCIONAR` — llegó a destino
   - `RECEPCIONADO` — recepcionado formalmente
4. **Diferencia en recepción:** Si hay diferencia, se crea registro como "FALTANTE NO TRANSFERIDO"

### Dependencia con logística
El trigger `trg_Movimiento_LogEstadoTraslado` (en logística) registra automáticamente el historial de estados del traslado en `HistorialEstadosTraslados`.

---

## 6. Kardex (Valorizado)

### Reglas

1. Se inserta desde `sp_kardex_Insertar` usando transacción Serializable
2. Campos: fecha, proveedor, costo, ingreso, salida, saldo, lote, fechav
3. **El kardex es temporal** — `sp_kardex_Eliminar` elimina **TODO** sin filtro
4. No hay relación FK con `Producto.Cod_Producto` — usa nombres textuales
5. No hay almacén en kardex — no soporta multi-almacén

### Riesgo
La eliminación total del kardex puede ocurrir accidentalmente desde cualquier form que llame a `Eliminarkardex()`.

---

## 7. Inventario Físico vs Lógico

### Proceso de inventario

1. **Preparación:** Usuario selecciona almacén, línea, sublínea
2. **Carga de datos del sistema:** `PRODUCTO_MOSTRARinventario` obtiene stock del sistema
3. **Conteo físico:** Usuario ingresa stock físico (NumericUpDown22)
4. **Cálculo de diferencia:** `Diferencia = StockSistema - StockFisico`
5. **Aplicación de ajuste:** `Button9_Click` procesa las diferencias
6. **Cierre:** `PRODUCTO_INVENTARIO_Cerrar` actualiza stock final

### Validaciones faltantes
- No se valida que el stock físico sea un número positivo
- No se valida que el usuario no haya omitido productos
- No hay registro de quién realizó el conteo
- No hay bloqueo de movimientos durante el inventario
