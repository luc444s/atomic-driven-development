# 08 — Reglas de Negocio — Módulo Productos/Catálogos

## 1. Precios: 4 Niveles

### Nivel 1: Precio Unitario (`Precio_Producto`)
- Precio de venta por unidad individual
- Calculado como: `Costo * (1 + MargAct/100)`
- Control en UI: `NUDPrecio`

### Nivel 2: Precio Intermedio (`precio_interm`)
- Precio de venta intermedio
- Calculado como: `Costo * (1 + MargEst/100)`
- Control en UI: `NumericUpDown3` (pero inconsistente entre Insertar y Modificar)

### Nivel 3: Precio por Caja (`PrecioCja_Producto`)
- Precio de venta por caja
- Calculado como: `Costo * (1 + UtilidadEstxunid/100)`
- Control en UI: `NumericUpDown1`

### Nivel 4: Listas de Precios Adicionales (`lista2`, `lista3`, `lista4`)
- Tres niveles de precio adicionales
- Se actualizan con `Modificar_listaprecios`
- `lista2` = `NumericUpDown16`, `lista3` = `NumericUpDown8`, `lista4` = `NumericUpDown14`

## 2. Utilidades: 4 Dimensiones

### Utilidad por Unidad (`UtilidadxUnid`)
- Control en UI: `NUDUU`
- Fórmula: `((Precio_Producto - Costo) / Costo) * 100`

### Utilidad por Caja (`UtilidadxCja`)
- Control en UI: `NUDUC`
- Fórmula: `((PrecioCja - Costo) / Costo) * 100`

### Utilidad Intermedia (`utilidadxint`)
- Control en UI: `NumericUpDown19`
- Fórmula: `((precio_interm - Costo) / Costo) * 100`

### Utilidades Estándar
- `UtilidadEstxunid`, `UtilidadEstxInterm`, `UtilidadEstxCja`
- Se almacenan pero su uso no está claro en el flujo principal

## 3. Márgenes

### Margen Actual (`MargAct`)
- `NumericUpDown7` en UI
- Fórmula: `((Precio_Producto - Costo) / Costo) * 100`

### Margen Estándar (`MargEst`)
- `NumericUpDown15` en UI
- Fórmula: `((precio_interm - Costo) / Costo) * 100`

### Diferencia de Precios (`DifPrecios`)
- Propósito no documentado. Se almacena como entero.

## 4. Impuestos

### IGV (`cIGV`)
- 0 = Exonerado (marcado CheckBox1)
- 1 = Gravado (no marcado)
- **BUG**: La lógica en UI es inversa. CheckBox1.Checked=True → est=1 → cIGV=1, pero el label dice "Exonerado"

### Percepción (`percepcion`)
- 0 = Sin percepción (RadioButton1)
- 1 = Con percepción (RadioButton2)
- Se usa en facturación para aplicar percepción de IGV

### Porcentaje Comisión Externa (`porc_ce`)
- Porcentaje de comisión (posiblemente para vendedores externos)
- Valor numérico capturado en `NumericUpDown19` (compartido con utilidadxint)

## 5. Códigos de Barras

### Código Principal (`Nro_Producto`)
- Código de barras único del producto (validado solo al insertar)
- NVARCHAR(20) — limitado a 20 caracteres
- Control en UI: `txtCodbarra`

### Código CABYS/Hacienda (`barcode1`)
- Código tributario de Costa Rica (CABYS) o España (Hacienda)
- NVARCHAR(150)
- Control en UI: `txtcodsap1`
- Diccionario hardcodeado en Form_Load para 13 gases
- **Obligatorio** para no-gases (validación en cmdgrabar)

### Matrícula (`barcode2`)
- Número de matrícula (para bombonas/cilindros)
- NVARCHAR(50)
- Control en UI: `txtcodsap3`

## 6. Multi-Unidad

### Unidad Principal (`Cod_Unidad`)
- Control en UI: `CBUnidad`
- Filtro: solo unidades con `equivalencia = 1`

### Unidad de Caja (`Cod_UnidadCja`)
- Control en UI: `CBUnidad1`
- Sin filtro — muestra todas las unidades

### Cantidad por Caja (`cant`)
- Número de unidades por caja
- Control en UI: `NumericUpDown2`

## 7. Promociones

### Estado de Promoción (`estadoPromo`)
- Almacenado en `Producto.estadopromo`
- Se actualiza con `Actualizar_EstPromProducto`
- Control en UI: `txtPromProducto` (TextBox usado como campo oculto)

### Condición de Promoción (`condicion`)
- Cadena descriptiva
- Almacenada en `Producto.condicion`
- Control en UI: `CBcondicion`

## 8. Multi-País

### Columna `PaisCodigo` (char(2))
- PE = Perú, CR = Costa Rica, ES = España
- **No se usa activamente** en la lógica de precios actual
- El diccionario CABYS hardcodeado sugiere que Costa Rica tiene lógica especial
- No hay SPs ni código VB que diferencien precios por país

### Diccionario CABYS (Costa Rica)
```vb
CabysDiccionario.Add("GAS ACETILENO", "3411001020300")
CabysDiccionario.Add("GAS AIRE COMPRIMIDO", "3425004020000")
' ... 13 gases en total
```

## 9. Condiciones de Producto

### Valores de `condicion`
| Valor | Significado | Ámbito |
|-------|-------------|--------|
| PRODUCTO | Producto normal | General |
| GAS | Gas (contenido de cilindro) | Gases |
| CILPRO | Cilindro propio de empresa | Bombonas |
| CILCLI | Cilindro del cliente | Bombonas |
| CILPROV | Cilindro del proveedor | Bombonas |
| CILGAR | Cilindro en garantía | Bombonas |
| SERVICIO | Producto tipo servicio | General |

Estos valores están hardcodeados en la UI (ComboBox) y se usan en todo el sistema.

## 10. Bombonas — Retimbrado ADR

### Presión de Servicio vs Prueba
- Presión de servicio: 150, 200, 300 bar
- Presión de prueba: servicio × 1.5 (autocalculado)
- Hardcodeados en ComboBox

### Datos ADR (NO guardados — BUG)
Los siguientes campos existen en UI (Panel11) pero NO se guardan:
- Nro_aprobacion, Clase_peligro, Marcado1, Marcado2, Formato_Bulto
- Transporte, Etiqueta, Tuneles, Nro_ONU, Regist_Alimentario

## 11. Costos

### Costo Actual (`Costo_Producto`)
- Costo del producto

### Costo de Reposición (`Costo_Rep`)
- Default: 0
- Si es 0.00 al guardar, se iguala a `Costo_Producto`

### Costo Anterior (`costo_Ant`)
- Almacena el costo previo a la última actualización

### Costo de Gestión Integral (`cgi`)
- Default: 0

### Costo Total (`costo_total`)
- Default: 0
- Suma de costos (no hay lógica visible de cálculo)

## 12. Stock Mínimo (`StockMin_Producto`)
- Se almacena pero **no se valida automáticamente** en el módulo productos
- Su validación depende de otros módulos (stock, ventas)

## 13. Generación de Código de Barras
- `MOSTRAR_ULTIMO_CODIGO_GEN` genera el siguiente código basado en línea
- El código generado se asigna a `txtCodbarra` automáticamente
- Se valida unicidad solo al insertar
