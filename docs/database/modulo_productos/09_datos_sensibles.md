# 09 — Datos Sensibles — Módulo Productos/Catálogos

## Clasificación de datos en tabla Producto

| Columna | Nivel de sensibilidad | Justificación |
|---------|----------------------|---------------|
| `Precio_Producto` | ALTO | Precio de venta — información comercial crítica |
| `PrecioCja_Producto` | ALTO | Precio de venta por caja |
| `Costo_Producto` | ALTO | Costo del producto — información financiera sensible |
| `Costo_Rep` | ALTO | Costo de reposición |
| `costo_Ant` | ALTO | Historial de costos |
| `UtilidadxUnid` | ALTO | Margen de utilidad — secreto comercial |
| `UtilidadxCja` | ALTO | Margen de utilidad por caja |
| `MargAct` | ALTO | Margen actual — información estratégica |
| `MargEst` | ALTO | Margen estándar |
| `cgi` | ALTO | Costo de gestión integral |
| `costo_total` | ALTO | Costo total |
| `lista2`, `lista3`, `lista4` | ALTO | Listas de precios alternativas |
| `pRECIO_INV` | ALTO | Precio de inventario |
| `COSTO_INV` | ALTO | Costo de inventario |
| `cIGV` | MEDIO | Condición tributaria (exonerado/gravado) |
| `percepcion` | MEDIO | Régimen de percepción |
| `porc_ce` | MEDIO | Porcentaje de comisión externa |
| `Nro_Producto` | BAJO | Código de barras (identificador) |
| `barcode1` | BAJO | Código CABYS/Hacienda |
| `barcode2` | BAJO | Matrícula |
| `Desc_Producto` | BAJO | Descripción |
| `foto` | BAJO | Imagen del producto |
| `barcode` | BAJO | Imagen de código de barras |
| `StockMin_Producto` | BAJO | Stock mínimo |
| `stock` | BAJO | Stock actual (desnormalizado) |
| `condicion` | BAJO | Condición del producto |

## Riesgos identificados

1. **Costos y precios visibles**: Cualquier usuario del sistema puede ver costos y precios de productos
2. **Sin auditoría**: No hay log de cambios en precios y costos
3. **Sin roles**: No hay diferenciación de roles para ver datos sensibles
4. **Campos imagen (barcode, foto)**: Almacenados como IMAGE en SQL Server — no hay control de tamaño
5. **PaisCodigo**: No se usa activamente pero podría exponer estrategia multi-país
