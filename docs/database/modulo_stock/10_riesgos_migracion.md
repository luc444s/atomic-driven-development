# Riesgos de Migración — Módulo Stock/Inventario

---

## Priorización

| ID | Riesgo | Severidad | Impacto | Prioridad |
|----|--------|-----------|---------|-----------|
| R01 | **Stock_Actual sin FK, sin triggers, sin CHECK** | CRÍTICO | Integridad de datos | P0 |
| R02 | **Ninguna función fn_Stock* usa Stock_Actual** | CRÍTICO | Cálculo de stock inconsistente | P0 |
| R03 | **sp_kardex_Eliminar borra todo sin filtro** | CRÍTICO | Pérdida total de histórico | P0 |
| R04 | **Bug en ajuste de inventario (solo primer producto)** | ALTO | Ajuste incorrecto de stock | P1 |
| R05 | **Rollback comentado en ModificarComprasSerie** | ALTO | Transacciones huérfanas | P1 |
| R06 | **FrmMovTrasladoAlmacen con lógica mezclada** | ALTO | Migración extremadamente compleja | P1 |
| R07 | **Conexiones directas a BD en FrmMovTrasladoAlmacen** | ALTO | Bypass de capa DAL | P1 |
| R08 | **Credenciales SA en app.config en texto plano** | ALTO | Seguridad | P1 |
| R09 | **Patrón N+1 queries en forms de consulta** | MEDIO | Performance | P2 |
| R10 | **Código muerto comentado en FrmInventario** | MEDIO | Mantenibilidad | P2 |
| R11 | **Variables no inicializadas en ajuste inventario** | MEDIO | Resultados incorrectos | P2 |
| R12 | **Hardcoding de conceptos "Egreso x cuadre stock"** | MEDIO | Rotura si cambia catálogo | P2 |
| R13 | **Sin validación de stock negativo al insertar** | MEDIO | Stock puede quedar negativo | P2 |
| R14 | **Sin alerta de stock mínimo** | MEDIO | Desabastecimiento | P2 |
| R15 | **Sin índices no clusterizados en Stock_Actual** | BAJO | Performance en consultas | P3 |
| R16 | **Sin control de acceso a costos** | BAJO | Exposición de datos financieros | P3 |

---

## Detalle de riesgos

### R01 — Stock_Actual sin integridad referencial (CRÍTICO)

**Problema:** `Stock_Actual` no tiene:
- FK a `Producto(Cod_Grupo)`
- FK a `Almacen(IdAlmacen)`
- Triggers de auditoría
- CHECK constraints para stock >= 0

**Impacto:** Se pueden insertar registros huérfanos. No hay garantía de integridad.

### R02 — Stock_Actual no usado por funciones (CRÍTICO)

**Problema:** Las 4 funciones `fn_Stock*` calculan stock desde `DetalleMovimiento` ignorando `Stock_Actual`. La tabla `Stock_Actual` parece ser un cache que podría estar desactualizado.

**Pregunta para migración:** ¿`Stock_Actual` se usa realmente? ¿O es un residuo de versión anterior?

### R03 — sp_kardex_Eliminar destructivo (CRÍTICO)

**Problema:** Este SP elimina TODOS los registros de kardex sin filtro. Puede llamarse accidentalmente.

**Migración:** Implementar eliminación lógica (bit de borrado) o filtro por fecha/producto.

### R04 — Bug ajuste de inventario (ALTO)

**Problema:** En `FrmInventario.Button9_Click`, las variables `StockAnterior` y `StockNuevo` se leen antes del loop con `i=0`, determinando ingreso/egreso solo para el primer producto.

**Solución:** Mover la lectura de stock dentro del loop, para cada producto individual.

### R06 — FrmMovTrasladoAlmacen monolítico (ALTO)

**Problema:** ~4300 líneas con funcionalidades mezcladas:
- Traslados
- Guías de remisión (electrónicas)
- Recepción
- Preparación de carga
- Gestión de cilindros

**Migración:** Separar en módulos: Traslados, Guías, Recepción, Preparación de carga.

### R08 — Credenciales SA expuestas (ALTO)

**Problema:** Todos los reportes Crystal usan:
```xml
appSettings:
  servername, database, userid="sa", password="..."
```

**Migración:** Usar Integrated Security o credenciales con permisos mínimos.

---

## Dependencias críticas con otros módulos

### Con Logística (ALTA)

| Dependencia | Dirección | Riesgo |
|-------------|-----------|--------|
| `fn_StockFisico_Planificador` usada por planificación | Stock → Logística | Si cambia cálculo, logística se ve afectada |
| `ECilindroEstadoActual` en stock de cilindros | Logística → Stock | Stock de cilindros depende de estado logístico |
| `sp_StockCilindros_PorProducto` | Stock → Logística | Consulta stock de cilindros para planificación |
| Traslados afectan stock | Logística → Stock | Recepción de traslados modifica stock |
| `trg_Movimiento_LogEstadoTraslado` | Logística → Stock | Trigger logístico sobre Movimiento |

### Con Ventas (ALTA)

| Dependencia | Dirección | Riesgo |
|-------------|-----------|--------|
| `SHOW_ValidarStockProductoMovimiento` | Stock → Ventas | Ventas valida stock antes de despachar |
| DetalleMovimiento usado para stock | Ventas → Stock | Cada venta genera movimiento que afecta stock |
| `Producto.stock` usado por ventas | Stock → Ventas | Stock disponible para cotización/venta |

### Con Compras (MEDIA)

| Dependencia | Dirección | Riesgo |
|-------------|-----------|--------|
| `SHOW_ValidarStockProductoMovimientoCOMPRA` | Stock → Compras | Compras valida stock antes de recepcionar |
| `Producto.StockMin_Producto` | Stock → Compras | Stock mínimo para suggested reorder |
| DetalleMovimiento de compras | Compras → Stock | Compras generan ingresos a stock |

### Con Productos (ALTA)

| Dependencia | Dirección | Riesgo |
|-------------|-----------|--------|
| `Producto.Cod_Grupo` → `Stock_Actual.Cod_Grupo` | Productos → Stock | Grupo de producto determina agrupación de stock |
| `Producto.StockMin_Producto` | Productos → Stock | Stock mínimo definido en producto |
| `Producto.stock` (cache) | Productos → Stock | Stock redundante en producto |

---

## Bugs activos confirmados

1. **BUG1 - Decisión incorrecta ingreso/egreso:** FrmInventario, solo evalúa primer producto
2. **BUG2 - Variable no inicializada `precio`:** FrmInventario línea 546
3. **BUG3 - Rollback comentado:** CProducto.ModificarComprasSerie_Insertar línea 2213
4. **BUG4 - Sin validación stock negativo:** Stock_Actual puede tener stock negativo
5. **BUG5 - Hardcoding de personas:** FrmInventario busca por nombre fijo

---

## Bypasses identificados

1. **Bypass1 — Stock_Actual sin FK:** Se puede insertar cualquier valor
2. **Bypass2 — Conexión directa en FrmMovTrasladoAlmacen:** Tiene `Conectar()` local que bypassea CProducto
3. **Bypass3 — Reportes Crystal con conexión directa:** Credenciales SA en app.config
4. **Bypass4 — Exportación Excel sin control:** Todos los forms pueden exportar stock a Excel
5. **Bypass5 — kardex sin FK:** Se pueden insertar registros para productos inexistentes
