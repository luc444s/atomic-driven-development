# Datos Sensibles — Módulo Stock/Inventario

---

## Clasificación de datos

| Dato | Tabla/Columna | Clasificación | Riesgo |
|------|---------------|---------------|--------|
| Stock actual por grupo | Stock_Actual.Stock | **Crítico** | Base para planificación logística y ventas |
| Stock por producto | Producto.stock | **Crítico** | Base para decisiones de compra y venta |
| Stock mínimo | Producto.StockMin_Producto | **Alto** | Define punto de reorden |
| Costo de producto | Producto.Costo_Producto | **Alto** | Información financiera confidencial |
| Precio de producto | Producto.Precio_Producto | **Alto** | Información comercial confidencial |
| Precio de compra | DetalleMovimiento.Pcompra | **Alto** | Costo real de adquisición |
| Costos de importación | Movimiento (flete, seguro, etc.) | **Alto** | Desglose de costos |
| Histórico de kardex | kardex (saldo, costo) | **Medio** | Historial valorizado |
| Estado de cilindros | ECilindroEstadoActual.EstadoActual | **Medio** | Disponibilidad logística |
| Fecha de actualización | Stock_Actual.FechaActualizacion | **Bajo** | Metadato |

---

## Exposición actual

### Por capa de presentación (Forms)
- **FrmMostrarSotckGeneral** muestra costo unitario en pantalla y Excel
- **FrmMostrarSotckxMarca** muestra costo unitario
- **FrmMostrarSotckxpROV** muestra costo unitario y total = costo * stock
- **FrmMostrarSotckRaz** muestra costo unitario
- **FrmInventario** permite modificar costo y precio

### Por exportación a Excel
Todos los forms de "MostrarSotck*" tienen botón "Exportar a Excel" que envía datos sin ningún filtro de seguridad.

### Por reportes Crystal
Los reportes Crystal pueden ser visualizados por cualquier usuario con acceso al form.

---

## Controles de acceso

**No se detectaron controles de acceso específicos** para los datos de stock en la capa de aplicación. Cualquier usuario con acceso a los forms puede ver y modificar datos de stock.

Los permisos están probablemente manejados a nivel de menú en el MDI principal (`MDIMenu.sbrBarra.Panels`), no a nivel de datos.

---

## Recomendaciones

1. Restringir visualización de costos por perfil de usuario
2. Auditar cambios en `Stock_Actual` y `Producto.stock`
3. No exportar costos a Excel sin autorización
4. Proteger contraseña de BD en configuración
