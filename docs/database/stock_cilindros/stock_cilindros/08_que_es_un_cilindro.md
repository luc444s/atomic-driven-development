# ¿Qué producto representa un cilindro en legacy?

## Modelo Conceptual Actual

En SYSTUTOR legacy, un cilindro NO es un solo producto. Son **dos entidades separadas**:

```
Producto (Cod_Producto = 1234)
├── Desc_Producto = "BOMBONA 15KG"
├── Condicion = "CILPRO" (cilindro propio de la empresa)
├── stock = 50 (unidades de este tipo de envase)
├── Cod_Grupo = 5678 (apunta al producto de GAS)
├── unidad = "UND"
└── Nro_Producto = "BOM-001" (serie individual del cilindro físico)

Producto (Cod_Producto = 5678)  ← al que apunta Cod_Grupo
├── Desc_Producto = "GAS LICUADO 15KG"
├── Condicion = "PRODUCTO"
├── stock = 5000 (KG de gas)
├── unidad = "KG"
└── Nro_Producto = null (no tiene serie individual)
```

## Relación Envase ↔ Gas

| Aspecto | Envase (Cilindro) | Gas |
|---|---|---|
| **Tabla** | Producto | Producto (registro separado) |
| **Condicion** | CILPRO, CILCLI, CILPROV, CILGAR | PRODUCTO |
| **Unidad** | UND | KG |
| **Stock** | Unidades físicas de envase | Peso/KG de gas |
| **Serie** | Cada cilindro tiene serie única | No tiene serie |
| **Control individual** | ECilindroEstadoActual (estado logístico) | No aplica |
| **Código de barras** | Serie del cilindro | Código genérico del producto |
| **FK entre ellos** | `Producto.Cod_Grupo` → `Producto.Cod_Producto` del gas | Inversa: el gas es "grupo" del envase |
| **Movimiento stock** | Raro (solo si se compra/vende envase como activo) | Cada vez que se llena/vende |

## ¿Cuándo se mueve uno y cuándo el otro?

| Evento | Envase (UND) | Gas (KG) |
|---|---|---|
| Creación bombona vacía | stock = 0 (recién creada) | No afecta |
| Llenado de proveedor | No afecta (sigue siendo 1 und) | +15 KG via Agregastock_Click |
| Venta a cliente | No afecta (envase se retorna) | -15 KG via DetalleMovimiento |
| Venta de envase nuevo | -1 UND | No afecta (no tiene gas) |
| Pérdida/Robo/Baja | -1 UND via ajuste | No afecta |
| Traslado entre almacenes | Se mueve la UND física | No afecta (el gas viaja dentro) |

## 37 vistas de cilindros: síntoma de diseño incompleto

La existencia de **37 vistas** relacionadas con cilindros/envases/bombonas indica que el diseño original no capturó bien el modelo, y las vistas fueron el parche para consultar la información correcta.

## Conclusión

Un cilindro en legacy es:
- **Físicamente**: un activo (envase) con serie única, condición de propiedad, estado logístico
- **Comercialmente**: un vehículo para contener y transportar gas
- **En stock**: una unidad (UND) en Producto, con seguimiento individual en ECilindroEstadoActual
- **En movimientos**: el gas se mueve en KG, el envase en UND — rara vez se mueve el envase como activo

El `Cod_Grupo` del envase apunta al Cod_Producto del gas. Esta es la clave que relaciona ambos mundos, pero el stock de cada uno se calcula independientemente desde DetalleMovimiento.
