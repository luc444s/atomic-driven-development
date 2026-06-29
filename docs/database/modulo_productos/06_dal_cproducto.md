# 06 — DAL Classes — Módulo Productos/Catálogos

## CProducto.vb (2,607 líneas)

### NOTA
Los métodos de **stock** ya están documentados en `docs/legacy/database/modulo_stock/06_dal_cproducto.md`.
Aquí se documentan solo los métodos de **catálogo**.

### Métodos de Catálogo (no stock)

#### InsertarProducto (38 parámetros)
```vb
Public Function InsertarProducto(
    ByRef Cod_Producto As Integer,
    ByVal Desc_Producto As String,
    ByVal Nro_Producto As String,
    ByVal StockMin_Producto As Double,
    ByVal Cod_Linea As Integer,
    ByVal Cod_TipoInsumo As Integer,
    ByVal Cod_Unidad As Integer,
    ByVal Precio_Producto As Double,
    ByVal Costo_Producto As Double,
    ByVal peso_producto As Double,
    ByVal Marca_Producto As Integer,
    ByVal Estado_Producto As Integer,
    ByVal PrecioCja_Producto As Double,
    ByVal Cod_UnidadCja As Integer,
    ByVal cigv As Integer,
    ByVal Costo_rep As Double,
    ByVal UtilidadxUnid As Double,
    ByVal Utilidadxcja As Double,
    ByVal Precio_Interm As Double,
    ByVal Cant As Double,
    ByVal Utilidadxint As Double,
    ByVal UtilidadEstxunid As Double,
    ByVal UtilidadEstxInterm As Double,
    ByVal UtilidadEstxCja As Double,
    ByVal MargAct As Integer,
    ByVal MargEst As Integer,
    ByVal DifPrecios As Integer,
    ByVal costo_Ant As Double,
    ByVal Nro_cja As String,
    ByVal percepcion As Integer,
    ByVal porc_ce As Double,
    ByVal cod_subcategoria As Integer,
    ByVal tiempoi As String,
    ByVal servicio As Integer,
    ByVal barcode1 As String,
    ByVal barcode2 As String,
    ByVal estadoPromo As Integer,
    ByVal condicion As String
) As Integer
```
- **SP**: `Producto_Insertar`
- **Transacción**: Sí, IsolationLevel.Serializable
- **Output**: `Cod_Producto` (identity)
- **Riesgo**: ALTO — 38 parámetros, mapeo manual

#### ModificarProducto (38 parámetros)
- **SP**: `Producto_Modificar`
- **Transacción**: Sí
- **Riesgo**: ALTO — mismos 38 parámetros que Insertar

#### BuscarProducto
- **SP**: `Producto_Buscar`
- **Descripción**: Busca por Cod_Producto (PK)

#### BuscarProductoxDesc
- **SP**: `Producto_BuscarxNom`
- **Descripción**: Búsqueda por nombre

#### BuscarProdxTipo (y variantes)
- **SPs**: `Producto_BuscarxTipo`, `Producto_BuscarxTipo1`, `Producto_BuscarxTipo12`, etc.
- **Riesgo**: Duplicación masiva de SPs de búsqueda

#### BuscarProdxTipoMultiple / BuscarProdxTipoMultipleGAS
- **SPs**: `Producto_BuscarxTipoMiltiple`, `Producto_BuscarxTipoMiltiple_GAS`, `Producto_BuscarxTipoMiltipleGAS`
- **Riesgo**: 3 SPs casi idénticos

#### BuscarProductoxCODEBARR / BuscarProductoxCODEBARRproberton
- **SP**: `Producto_BuscarxNomxCODEBARR`, `Producto_BuscarxNomxCODEBARRproberton`
- **Descripción**: Búsqueda por código de barras

#### BuscarProductoxns / BuscarProductoxnsCilindro
- **SP**: `Producto_BuscarxNroSerie`, `Producto_BuscarxNroSerieCilindros`
- **Descripción**: Búsqueda por número de serie

#### ActualizarUtilidad
- **SP**: `Producto_ActualizarUtilidad`
- **Parámetros**: Cod_Producto, UtilidadxUnid, Utilidadxcja, Utilidadxint

#### ActualizarCosto
- **SP**: `Producto_ActualizaCosto`
- **Parámetros**: Cod_Producto, Costo_Producto, Costo_Rep, costo_Ant

#### ActualizarPrecio
- **SP**: `Producto_ModificarPrecio`
- **Parámetros**: Cod_Producto, Precio_Producto, precio_interm, PrecioCja_Producto

#### ActualizarPreciosEst
- **SP**: `Producto_ActualizarPreciosEst`
- **Parámetros**: Cod_Producto, peso_producto, Precio_Producto, Costo_Producto

#### Actualizar_precios (completo)
- **SP**: `Producto_ActualizarPrecios`
- **Parámetros**: 10 parámetros (precios + utilidades + costo_total)

#### Cambiarestadoproducto
- **SP**: `Producto_cambiarestado`
- **Descripción**: Cambia Estado_Producto

#### Actualiza_ProductoCodGrupo / Actualizar_ProductoCodGrupo
- **SPs**: `ActualizaProducto_CodGrupo`, `actualizar_Producto_CodGrupo`
- **Riesgo**: Dos métodos DAL con nombres casi idénticos para funcionalidad duplicada

#### Registrar_nuevoscostos
- **SP**: `Producto_nuevocosto`
- **Parámetros**: Cod_Producto, cgi, costo_total, costo_Producto, costo_rep

#### Modificar_listaprecios
- **SP**: `Producto_listadoprecios`
- **Parámetros**: Cod_Producto, lista2, lista3, lista4

#### MOSTRAR_ULTIMO_CODIGO_GEN
- **SP**: `MOSTRAR_ULTIMO_CODIGO_GEN`
- **Descripción**: Genera el siguiente código de barras basado en línea

### Patrón de conexión inconsistente
Algunos métodos usan `Conectar()`/`DesConnectar()` con `CommandBehavior.CloseConnection`, otros manejan la conexión manualmente. Esto puede causar fugas de conexión.

---

## CLinea.vb
- `BuscarLineaxNombre` → `Linea_BuscarxNom`
- `CBLineaxNombre` → `Linea_BuscarxNomCB`
- `CBLineaxNombrexrubro` → `Linea_BuscarxNomCBxrubro`
- `InsertarLinea` → `Linea_Insertar`
- `ModificarLinea` → `Linea_Modificar`

## CsubLinea.vb
- `BuscarSubLineaxNombre` → `SubLinea_BuscarxNom`
- `BuscarSubLineaxNombrexcodLinea` → `SubLinea_BuscarxNomXLineaxcod`
- `BuscarSubLineaxNombrexLinea` → `SubLinea_BuscarxNomXLinea`
- `BuscarSubLineaxNombrexLineaxrubro` → `SubLinea_BuscarxNomXLineaxrubro`
- `CBSubLineaxNombre` → `SubLinea_BuscarxNomCB`
- `InsertarSubLinea` → `SubLinea_Insertar`
- `ModificarSubLinea` → `SubLinea_Modificar`

## CMarca.vb
- `BuscarmarcaxNombre` → `Marca_BuscarxNom`
- `CBmarcaxNombre` → `Marca_BuscarxNomCB`
- `Insertarmarca` → `Marca_Insertar`
- `Modificarmarca` → `Marca_Modificar`

## CRubro.vb
- `BuscarRubroxNombre` → `Rubro_BuscarxNom`
- `CBRubroxNombre` → `Rubro_BuscarxNomCB`
- `InsertarRubro` → `Rubro_Insertar`
- `ModificarRubro` → `Rubro_Modificar`

## CTipoInsumo.vb
- `BuscarTipoInsumoxDesc` → `TipoInsumo_BuscarDescCB`
- `CBTipoInsumoxDesc` → `TipoInsumo_BuscarDescCB`
- `InsertarTipoInsumo` → `TipoInsumo_Insertar`
- `ModificarTipoInsumo` → `TipoInsumo_Modificar`

## CUnidad.vb
- `BuscarLineaxNombre` → `Unidad_BuscarxNom`
- `CBBuscarUnidadxNombre` → `Unidad_BuscarxNomCB`
- `InsertarUnidad` → `Unidad_Insertar`
- `ModificarUnidad` → `Unidad_Modificar`

## CSubcategoria.vb
- `BuscarSubCategoriaxNombre` → `SubCategoria_BuscarxNomCB`
- `CBSubCategoriaxNombre` → `SubCategoria_BuscarxNomCB`
- `InsertarSubcategoria` → (no se encontró SP de inserción)
- `ModificarSubCategoria` → `SubCategoria_Modificar`

## CGrupo.vb
- `BuscarDescGrupo` → `Grupo_BuscarxNom`
- `BuscarGrupo` → `buscar_Grupo`
- `BuscarGrupoxNombre` → `Grupo_BuscarxNom`
- `ListarGrupo` → (SP no identificado)

## CEstadoProducto.vb
- `BuscarEstadoProductoxNombre` → `EstadoProducto_BuscarxNom`
- `CBEstadoProductoxNombre` → `EstadoProducto_BuscarxNomCB`
- `InsertarEstadoProducto` → `EstadoProducto_Insertar`
- `ModificarEstadoProducto` → `EstadoProducto_Modificar`

## CFamilia.vb (contiene lógica de promociones)
**NOTA**: A pesar de llamarse CFamilia, maneja promociones. Esto es un error de arquitectura.

- `InsertarPromocion` → `Promocion_Insertar`
- `Modificarpromocion` → `Promocion_Modificar`
- `BuscarPromoxProducto` → `Promocion_BuscarxProd`
- `mostrar_promociones` → `Promocion_mostrar`
- `mostrarpromoactiva` → `Promocion_mostrarActiva`
- `ActualizarEstPromProducto` → `Actualizar_EstPromProducto`
- `ActualizarPromo` → actualización directa de promoción

## CConversion.vb
- `BuscarConversionxNombre` → búsqueda de conversiones
- `InsertarConversion` → inserción de conversión
- `ModificarConversion` → modificación de conversión

## CConstante.vb
- `mostrar_Constantes` → muestra constantes por grupo
