# 10 — Riesgos de Migración — Módulo Productos/Catálogos

## Priorización

### P0 — Crítico (debe resolverse antes de migrar)

| # | Riesgo | Descripción | Impacto |
|---|--------|-------------|---------|
| 1 | **Bug ADR en FrmCatBombonas** | 10 campos ADR (Panel11) NO se guardan en InsertarRetimbrado. Código comentado que SÍ guardaba fue reemplazado por cadenas vacías. | Datos ADR perdidos. Incumplimiento normativo de transporte de mercancías peligrosas. |
| 2 | **38 parámetros en InsertarProducto/ModificarProducto** | Mapeo manual de 38 parámetros sin validación de tipos ni obligatoriedad. La llamada real en cmdgrabar NO coincide con la firma formal. | Bugs de inconsistencia de datos. Dificultad extrema para migrar. |
| 3 | **Sin Foreign Keys en Producto** | La tabla Producto no tiene FK a Linea, Marca, Unidad, etc. La integridad referencial solo existe en código VB. | Datos huérfanos. Migración requiere limpieza masiva. |
| 4 | **Lógica inversa de CheckBox1 (cIGV/exonerado)** | `CheckBox1.Checked=True` → `cigv=1`, pero el label dice "Exonerado". Confusión entre exonerado y gravado. | Errores en facturación electrónica. Multas fiscales. |
| 5 | **Parámetros inconsistentes entre Insertar y Modificar** | InsertarProducto usa NumericUpDown7 como Precio_Interm, ModificarProducto usa NumericUpDown3. Cant hardcodeado a "1.00" en Insertar pero usa NumericUpDown2 en Modificar. | Inconsistencia de datos entre alta y modificación. |

### P1 — Alto

| # | Riesgo | Descripción | Impacto |
|---|--------|-------------|---------|
| 6 | **Complejidad de FrmCatProductos (5,773 líneas)** | Un solo form con toda la lógica de producto, precios, stock, imágenes, promociones, búsquedas. Sin separación de responsabilidades. | Mantenibilidad extremadamente baja. Refactor obligatorio. |
| 7 | **Complejidad de FrmCatBombonas (6,886 líneas)** | Similar al anterior. Incluye lógica de retimbrado ADR, etiquetas, PH, escaneo. | Dificultad de migración. Código espagueti. |
| 8 | **Lógica de precios duplicada** | Los cálculos de margen/utilidad existen en: VB.NET form (calcular_margen, calcular_lista), DAL (ActualizarUtilidad, ActualizarPrecio), y SPs (Producto_ActualizarUtilidad, Producto_ActualizarPrecios). | Riesgo de inconsistencia. ¿Dónde está la fuente de verdad? |
| 9 | **Duplicación de SPs de búsqueda** | ~40 SPs de búsqueda de producto, muchos casi idénticos (Producto_BuscarxTipo, xTipo1, xTipo2, xTipo3, xTipo4, etc.) | Código redundante. Dificulta migración a ORM. |
| 10 | **Sin transacción en cmdgrabar** | Multiple SPs llamados secuencialmente sin transacción compartida. Si falla el SP 3, el producto queda medio insertado. | Inconsistencia de datos. Productos huérfanos. |
| 11 | **Validación de código de barras solo al insertar** | No se valida unicidad al modificar. | Duplicados de código de barras. |

### P2 — Medio

| # | Riesgo | Descripción | Impacto |
|---|--------|-------------|---------|
| 12 | **Sin CHECK constraints ni defaults útiles** | Defaults solo para valores 0. Sin validación de rangos de precios. | Datos inválidos pueden entrar al sistema. |
| 13 | **Multi-país mal implementado** | `PaisCodigo` existe pero no se usa en lógica de precios. CABYS hardcodeado para Costa Rica. | La migración a multi-país requiere reescribir toda la lógica de precios. |
| 14 | **Valores hardcodeados en combos** | CBcondicion (CILPRO/CILCLI/CILPROV/CILGAR), presiones (150/200/300), ADR Categories. | No flexibles para configuración por país. |
| 15 | **Dos métodos Actualiza_ProductoCodGrupo vs actualizar_Producto_CodGrupo** | Dos métodos DAL con nombres casi idénticos. Posible dead code. | Confusión. Riesgo de usar el incorrecto. |
| 16 | **CFamilia maneja promociones** | La clase CFamilia contiene métodos de promociones. Error de naming y arquitectura. | Confusión en mantenimiento. Dificulta migración. |
| 17 | **Stock desnormalizado en Producto** | La columna `stock` en Producto se actualiza manualmente. Puede desincronizarse con el stock real. | Reportes de stock incorrectos. |
| 18 | **grabar_imagen con SQL injection potencial** | Usa concatenación de cadenas aunque con parámetros. | Bajo riesgo por uso interno, pero mala práctica. |

### P3 — Bajo

| # | Riesgo | Descripción | Impacto |
|---|--------|-------------|---------|
| 19 | **CBequivalencia huérfano en FrmCatBombonas** | ComboBox declarado, sin items, sin referencias. | Dead code. |
| 20 | **ComboBox5/6/7 obsoletos** | Sucursal, Estante, Columna — se limpian pero nunca se usan. | Dead code. |
| 21 | **Variable `C`** | ComboBox de ubicación con nombre de un solo carácter. | Mala práctica de naming. |
| 22 | **Numeración manual de documento inventario** | Código de 14 líneas para formatear número de 6 dígitos. | Código redundante. |
| 23 | **Sin vista previa** | Muchas operaciones sin confirmación visual antes de grabar. | Error humano. |

## Dependencias con otros módulos

| Módulo | Dependencia | Dirección |
|--------|-------------|-----------|
| **Stock** | Consume CProducto para listar productos, verificar stock, kardex | Stock → Productos |
| **Logística** | CProducto usado en movimientos, preparación de carga, despachos | Logística → Productos |
| **Ventas** | Precios de producto usados en facturación | Ventas → Productos |
| **Compras** | Costos de producto usados en órdenes de compra | Compras → Productos |
| **Contabilidad** | cIGV, percepcion usados en asientos contables | Contab → Productos |
| **Planificación** | Stock, precios, grupos usados en planificación de producción | Planif → Productos |
| **Escaneo/Scan** | CProducto usado para validar ADR, PH, estado de cilindros | Scan → Productos |

**Importante**: Productos NO depende de ningún otro módulo. Es un catálogo base del sistema.

## Recomendaciones para migración

1. **Reemplazar 40+ SPs de búsqueda** por un solo SP parametrizado o consulta ORM
2. **Normalizar foreign keys** en tabla Producto
3. **Separar FrmCatProductos** en múltiples componentes: producto, precios, stock, imágenes
4. **Crear tabla de condiciones de cilindro** (CILPRO, CILCLI, etc.) en BD
5. **Implementar auditoría** de cambios de precios y costos
6. **Corregir bug ADR** antes de migrar
7. **Estandarizar lógica de precios** a una sola capa
8. **Implementar multi-país** correctamente usando PaisCodigo
