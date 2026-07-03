# Casos de Ingreso/Egreso de Cilindros

## Matriz de Afectación

| Caso | ¿Afecta Stock? (cantidad) | ¿Afecta Estado? (ECilindroEstadoActual) | ¿Afecta ambos? |
|---|---|---|---|
| **Creación bombona** (FrmCatBombonas) | Sí (si llena: Agregastock crea DetalleMovimiento) | Sí (LogEstadoCilindro) | Ambos |
| **Venta** (FrmMovFacturacion) | Sí (DetalleMovimiento.StkEgreso) | No directo (debería cambiar a VACIO o EN_CLIENTE) | Solo stock |
| **Compra** (FrmMovCompras) | Sí (DetalleMovimiento.StkIngreso) | No directo | Solo stock |
| **Traslado** (FrmMovTrasladoAlmacen) | Sí (via BTNgrabarSalida) | Parcial (via REPORTEDETENVASE, no ECilindroEstadoActual) | Ambos (parcial) |
| **Canje** | No identificado | No identificado | ? |
| **Devolución** | Sí (StkIngreso inverso) | Depende del flujo | Parcial |
| **Mantenimiento/PH** | No (solo cambio de estado) | Sí (cambio a EN_TALLER) | Solo estado |
| **Baja** | Sí (egreso manual) | Sí (marca como DADO_DE_BAJA) | Ambos |
| **Pérdida** | Sí (ajuste de inventario) | No automático | Solo stock |
| **Garantía** (FrmGarantia) | No identificado | Sí (via EGarantia) | Solo estado |

## Análisis por caso

### 1. Venta (el caso más crítico)

Cuando se vende una bombona de gas:
- `DetalleMovimiento.StkEgreso` = contenido de gas (KG)
- El envase debería cambiar su estado a `VACIO_EN_ALMACEN` (si se retorna) o `EN_CLIENTE` (si se deja)
- **EN LEGACY: no se actualiza ECilindroEstadoActual automáticamente desde la venta**
- Gap: la venta descuenta stock del gas, pero el estado del cilindro queda desactualizado

### 2. Compra

Cuando se compra gas para llenar cilindros:
- `DetalleMovimiento.StkIngreso` = gas comprado
- El envase se llena y debería cambiar a `LLENO_EN_ALMACEN`
- **Solo cambia si el usuario lo hace manualmente**

### 3. Traslado

El flujo actual (FrmMovTrasladoAlmacen):
- Separa llenos y vacíos en pedidos distintos
- Crea `ECabeceraPedido` + `EDetallePedido` con motivo Lleno/Vacio
- **NO llama a `usp_Cilindro_CambiarEstado`** para actualizar almacén
- Usa `REPORTEDETENVASE` como tabla de tracking propia (no estándar)

### 4. Mantenimiento / PH (Prueba Hidrostática)

- Cambia estado del cilindro (via `usp_Cilindro_CambiarEstado`)
- No afecta stock cuantitativo
- Las vistas `v_CilindrosLlenos_Almacen_UltimoPH` y `v_UltimoPH_porCilindro` cruzan PH con estado

### 5. Garantía

- Tabla `EGarantia` gestiona garantías de envases
- No parece integrarse con stock ni con ECilindroEstadoActual
- Sistema paralelo dentro del submódulo de alquiler de envases

## Resumen de gaps

| Gap | Impacto |
|---|---|
| Venta no actualiza estado de cilindro | El cilindro aparece como LLENO cuando ya está VACIO |
| Traslado no actualiza ECilindroEstadoActual | La ubicación del cilindro queda desactualizada |
| Compra no marca cilindros como LLENOS | Stock de gas aumenta pero cilindros no reflejan llenado |
| No hay trazabilidad unificada | Los 37 vistas de cilindros intentan compensar la falta de integración |
