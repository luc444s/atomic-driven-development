# 12 — Clases VB Adicionales — Módulo Productos/Catálogos

## CConversion.vb

### Propósito
Gestión de conversiones de unidades de medida.

### Métodos
| Método | SP | Descripción |
|--------|-----|-------------|
| `BuscarConversionxNombre(descripcion)` | `BuscarConversionxNombre` | Busca conversión por nombre |
| `CBConversionxNombre(unidad)` | `CBConversionxNombre` | Carga ComboBox de conversiones |
| `InsertarConversion(codigo, unidad, descripcion, valor)` | `InsertarConversion` | Inserta nueva conversión |
| `ModificarConversion(codigo, unidad, descripcion, valor)` | `ModificarConversion` | Modifica conversión existente |

### Riesgo
- `valor` es Double — sin validación de tipo

## CConstante.vb

### Propósito
Gestión de constantes del sistema agrupadas.

### Métodos
| Método | SP | Descripción |
|--------|-----|-------------|
| `mostrar_Constantes(idGrupo)` | `mostrar_Constantes` | Retorna DataTable con constantes de un grupo |

### Riesgo
- Solo tiene un método. Podría ser reemplazado por tabla de parámetros.

## CtipoCambio.vb

### Propósito
Gestión de tipo de cambio (relacionado a precios multi-moneda).

### Métodos (basado en CProducto)
| Método | SP | Descripción |
|--------|-----|-------------|
| `InsertarTC(v, fecha, TCventasunat, TCVentaComercial)` | `insertar_tc` | Inserta tipo de cambio del día |
| `TcBuscarPorDia(dia, mes, año)` | `tc_buscarxdia` | Busca TC por fecha |

### Uso en Productos
- El tipo de cambio se muestra en FrmCatProductos para convertir precios a dólares
- Se lee desde `MDIMenu.sbrBarra.Panels(36).Text` (TC del día desde la barra de estado)

## CDistrito.vb, CProvincia.vb, CDepartamento.vb

### Propósito
Catálogos de ubicación geográfica.

### Relación con Productos
- No tienen relación directa con productos
- Se usan en direcciones de clientes/sucursales
- Mencionados aquí porque la clase `CUbicacion` se usa en FrmCatBombonas para ubicación física de cilindros

## CtIPOdOC.vb

### Propósito
Catálogo de tipos de documento.

### Uso en Productos
- Se usa en FrmCatProductos para cargar `ComboBox1` (tipos de documento contable)
- Método: `BuscarTipoDocxNombreCB("Nota Pedido")` para obtener el tipo de documento de inventario

## Cgas.vb

### Propósito
Gestión de gases y bombonas. Clase crítica para bombonas.

### Métodos relacionados con productos
| Método | SP | Descripción |
|--------|-----|-------------|
| `InsertarRetimbrado(...)` | `Retimbrado_Insertar` | Inserta retimbrado de bombona |
| `actualizar_retimbrado(...)` | `actualizar_retimbrado` | Actualiza retimbrado |
| `Retimbrado_BuscarUltimoPorCodProducto(codigo)` | `Retimbrado_Buscar` | Busca último retimbrado |
| `BuscarPorCodSublinea(codSublinea)` | `BuscarPorCodSublinea` | Busca productos por sublínea |

### Bug ADR
Confirmado en FrmCatBombonas: `InsertarRetimbrado` recibe cadenas vacías para todos los campos ADR.

## CFamilia.vb (Promociones)

### Propósito
A pesar del nombre, maneja **familias de producto Y promociones**.

### Métodos de promociones
| Método | SP | Descripción |
|--------|-----|-------------|
| `InsertarPromocion(...)` | `Promocion_Insertar` | Inserta promoción |
| `Modificarpromocion(...)` | `Promocion_Modificar` | Modifica promoción |
| `BuscarPromoxProducto(desc)` | `Promocion_BuscarxProd` | Busca promociones por producto |
| `mostrar_promociones(desc)` | `Promocion_mostrar` | Lista promociones |
| `mostrarpromoactiva(grupo)` | `Promocion_mostrarActiva` | Promociones activas |
| `ActualizarEstPromProducto(cod)` | `Actualizar_EstPromProducto` | Actualiza estado de promoción en producto |
| `InsertarTicketDescuento(...)` | `TicketDescuento_*` | Inserta ticket de descuento |

### Riesgo
- La clase debería llamarse `CPromocion`, no `CFamilia`
- Mezcla dos responsabilidades distintas

## Cbarcode.vb

### Propósito
Generación de códigos de barras.

### Uso en Productos
- Usado en FrmCatProductos para generar imágenes de código de barras
- Integración con librería `OnBarcode.Barcode`

## CReportesPDF (clase externa)

### Propósito
Generación de reportes en PDF (alternativa moderna a Crystal Reports).

### Uso en Productos
- Usado en FrmCatBombonas para etiquetas de cilindros
- Integración con `QRCoder` y `ZXing` para generación de QR y códigos de barras
