# 04 — Forms del Módulo Productos/Catálogos

## FrmCatProductos.vb (5,773 líneas)

### Descripción General
Formulario principal de CRUD de productos. Es el más complejo del módulo con ~5,773 líneas. Permite crear, modificar, buscar productos, gestionar precios, códigos de barras, imágenes, stock, y más.

### Declaraciones de objetos DAL
```vb
Dim WithEvents objTar As New CAtencion.CProducto   'Principal
Dim WithEvents obj As New CAtencion.CProducto       'Principal (dup)
Dim WithEvents obji As New CAtencion.CProducto      'Secundario
Dim WithEvents objM As New CAtencion.CMovimiento    'Movimientos/Stock
Dim WithEvents objl As New CAtencion.CLinea         'Líneas
Dim WithEvents objsl As New CAtencion.CsubLinea     'Sublíneas
Dim WithEvents objmarca As New CAtencion.CMarca     'Marcas
Dim WithEvents obje As New CAtencion.CEstadoProducto 'Estados
Dim WithEvents obju As New CAtencion.Cunidad        'Unidades
Dim WithEvents objt As New CAtencion.CTipoInsumo    'Tipos de insumo
Dim WithEvents objSc As New CAtencion.CSubcategoria 'Subcategorías
Dim WithEvents objgr As New CAtencion.CGrupo        'Grupos
Dim WithEvents objgas As New CAtencion.Cgas         'Gas/bombonas
Dim WithEvents objfa As New CAtencion.CFamilia      'Familia/Promociones
```

### Eventos Principales

#### Form_Load (línea 607)
- Carga catálogos: subcategorías (excluye "BOMBONAS"), líneas, unidades (filtro equivalencia=1), marcas, tipos de insumo, sucursales, estados
- Configura numeración automática de documento de inventario
- Inicializa diccionario CABYS (Costa Rica, 13 productos de gas)
- Llama a `cmdnuevo_Click`

#### cmdnuevo_Click (línea 701)
- Habilita controles para nuevo producto
- Si subcategoría = "BOMBONAS" y hay orden activa, pregunta si agregar más cilindros a la misma orden
- Limpia formulario

#### cmdBuscar_Click (línea 742)
- Abre `FrmBuscarProducto` (ShowDialog)
- Al regresar, carga:
  - Fórmula/receta del producto (ListView4)
  - Ubicaciones en almacenes (ListView7)
  - Stock por almacén (ListView3)
  - Tipo de cambio (MDIMenu barra)
  - Grupo del producto

#### cmdgrabar_Click (línea 977)
**El método más complejo del formulario**. Case 1 = Insertar, Case 2 = Modificar.

**Case 1 (InsertarProducto)**:
1. Lee flags de UI: CheckBox1 (Exonerado IGV), CheckBox8 (pack), CheckBox7Pack, CheckBox4 (servicio), RadioButton1/2 (percepción)
2. Valida código de barras obligatorio
3. Valida código CABYS si no es GAS
4. Verifica duplicado de código de barras `Producto_BuscarxNomxCODEBARR`
5. Construye `TXTDESC_CORTA` (descripción corta con metadata)
6. Llama a `obj.InsertarProducto(0, ...)` con **valores inconsistentes** vs parámetros formales
7. Si es GAS: asigna `Stockcant=1`, `NUDCosto=1`, `TxtGrupo=9`, llama `Agregastock_Click`
8. Si es PRODUCTO+BOMBONAS: actualiza grupo
9. Llama a: `Codrapido`, `Actcont`, `grabar_imagen`, `Registrar_nuevoscostos`, `Modificar_listaprecios`

**Case 2 (ModificarProducto)**:
1. Valida que el usuario sea Administrador
2. Llama a `obj.ModificarProducto(CInt(TxtCodigo.Text), ...)`
3. Llama a `Actualiza_ProductoCodGrupo`, `Codrapido`, `Actcont`, `grabar_imagen`, `Modificar_listaprecios`, `Registrar_nuevoscostos`

#### cmdmodificar_Click (línea 958)
- Habilita controles para edición
- Si es GAS, configura UI para cilindros

### Mapeo de Controles a Columnas de Producto

| Control VB.NET | Columna SQL | Notas |
|----------------|-------------|-------|
| TxtCodigo | cod_producto | Solo lectura |
| txtCodbarra | Nro_Producto | Código de barras primario |
| TxtDescripcion | Desc_Producto | Descripción |
| TXTDESC_CORTA | Nro_cja | Descripción corta con metadata |
| NUDstockmin | StockMin_Producto | Stock mínimo |
| CBlinea -> Txtlinea | Cod_Linea | ID de línea (resuelto por nombre) |
| Cbtinsumo -> txtinsumo | Cod_TipoInsumo | ID de tipo insumo |
| CBUnidad -> txtunidad | Cod_Unidad | ID de unidad |
| CBUnidad1 -> txtunidad (caja) | Cod_UnidadCja | Unidad de caja |
| NUDPrecio | Precio_Producto | Precio unitario |
| NumericUpDown1 | PrecioCja_Producto | Precio caja |
| NUDCosto | Costo_Producto | Costo |
| NUDContenido | peso_producto | Peso/contenido |
| CBMarca -> txtcodmarca | Marca_Producto | ID marca |
| CBestado -> TxtEstado | Estado_Producto | ID estado |
| CheckBox1 | cIGV | 0=exonerado, 1=gravado |
| NUDCosto_Rep | Costo_Rep | Costo reposición |
| RadioButton1/2 | percepcion | 0=no, 1=sí |
| NumericUpDown19 | porc_ce | % comisión externa |
| cbsc -> txtcodsubcat | cod_SubCategoria | ID subcategoría |
| CheckBox4 | servicio | Flag servicio |
| txtcodsap1 | barcode1 | Código CABYS |
| txtcodsap3 | barcode2 | Código matrícula |
| txtPromProducto | estadoPromo | Estado promoción (mal mapeado) |
| CBcondicion | condicion | PRODUCTO, GAS, CILPRO, etc. |
| NUDUU | UtilidadxUnid | Utilidad por unidad (%) |
| NUDUC | UtilidadxCja | Utilidad por caja (%) |
| NumericUpDown3 | precio_interm | Precio intermedio |
| NumericUpDown19 | utilidadxint | Utilidad intermedia |
| NumericUpDown7 | MargAct | Margen actual (%) |
| NumericUpDown15 | MargEst | Margen estándar (%) |
| NumericUpDown13 | UtilidadEstxunid | Utilidad estándar unidad |
| NumericUpDown18 | UtilidadEstxInterm | Utilidad estándar interm |
| NumericUpDown14 | UtilidadEstxCja | Utilidad estándar caja |
| NumericUpDown8 | lista3 | Lista de precios 3 |
| NumericUpDown16 | lista2 | Lista de precios 2 |
| NumericUpDown14 | lista4 | Lista de precios 4 |
| Label72 | costo_Ant | Costo anterior |
| txtti | tiempoi | Tiempo de instalación |

### Lógica de Precios

```vb
' calcular_margen() (línea 591):
NumericUpDown7.Text = ((NUDPrecio - NUDCosto) / NUDCosto) * 100    ' MargAct
NumericUpDown15.Text = ((NumericUpDown16 - NUDCosto) / NUDCosto) * 100  ' MargEst
NumericUpDown13.Text = ((NumericUpDown8 - NUDCosto) / NUDCosto) * 100   ' UtilidadEstxunid
NumericUpDown18.Text = ((NumericUpDown14 - NUDCosto) / NUDCosto) * 100  ' UtilidadEstxInterm

' calcular_lista() (línea 600):
NUDPrecio = NUDCosto * (1 + (NumericUpDown7 / 100))           ' Precio_Producto
NumericUpDown16 = NUDCosto * (1 + (NumericUpDown15 / 100))     ' lista2
NumericUpDown8 = NUDCosto * (1 + (NumericUpDown13 / 100))      ' lista3
NumericUpDown14 = NUDCosto * (1 + (NumericUpDown18 / 100))     ' lista4
```

### Lógica de Impuestos
- **CheckBox1 (cIGV)**: True = Exonerado (0), False = Gravado (1) — ¡inverso lógico!
- **RadioButton1/2 (percepcion)**: RadioButton1 = 0 (sin percepción), RadioButton2 = 1 (con percepción)
- **CheckBox4 (servicio)**: Marca el producto como servicio

### Códigos de Barras
- `txtCodbarra` → `Nro_Producto` (NVARCHAR(20)) — código principal
- `txtcodsap1` → `barcode1` (NVARCHAR(150)) — CABYS Costa Rica / Hacienda
- `txtcodsap3` → `barcode2` (NVARCHAR(50)) — matrícula
- Diccionario CABYS hardcodeado en Form_Load para 13 gases

### Bugs Identificados en FrmCatProductos

1. **P0 — Parámetros incorrectos en InsertarProducto vs ModificarProducto**: La llamada real en cmdgrabar (línea 1082) NO coincide con los parámetros formales de la función. Se envían valores como "1.00" para Cant (debería ser Cant/NumericUpDown2) y se omiten parámetros críticos como costo_Ant.

2. **P1 — Lógica inversa de CheckBox1**: `CheckBox1.Checked = True` → `est = 1` pero luego `cigv = est` donde 1 = exonerado según UI pero 1 = gravado según nombre de columna. La columna se llama `cIGV` donde 1 probablemente significa "tiene IGV" (gravado), pero la UI dice "Exonerado".

3. **P1 — Validación duplicado de código de barras solo en inserción**: No se valida al modificar.

4. **P2 — ModificarProducto usa NumericUpDown3 como Precio_Interm pero InsertarProducto usa NumericUpDown7**: Inconsistencia en qué campo es precio intermedio.

5. **P2 — Sin transacción**: cmdgrabar llama múltiples SPs sin una transacción común. Si falla el segundo SP, el producto queda a medio insertar.

6. **P2 — TXTDESC_CORTA mal construido**: En línea 1075, concatena literal "cbsc.Text" en lugar del valor de la variable.

7. **P3 — grabar_imagen usa SQL injection**: Línea 1246, `"Update producto Set foto=@foto WHERE cod_producto = '" & id & "'"` — aunque no recibe input del usuario directamente, usa concatenación.

---

## FrmCatBombonas.vb (6,886 líneas)

### Descripción General
Formulario para gestión de cilindros/envases (bombonas). Incluye datos técnicos, retimbrado ADR, equivalencias, tarifas.

### Hallazgos Críticos
- **BUG ADR CONFIRMADO**: Los 10 campos del Panel11 (ADR) NO se guardan en BD.
  - InsertarRetimbrado recibe `"", "", "", "", "", 0, "", "", "", ""` en lugar de los valores reales.
  - El código comentado (línea ~1537) SÍ pasaba los valores correctos.
  - Referencia: `docs/legacy/forms/FrmCatBombonas_combobox.md` sección 6.1
- **Panel11** (Visible = False) contiene todos los controles ADR: Clase_peligro, Marcado1, Formato_Bulto, Transporte, Etiqueta, Tuneles, Nro_ONU, ComboBox3, Nro_aprobacion, Marcado2, Regist_Alimentario
- **ComboBoxes hardcodeados**: CBcondicion (CILPRO/CILCLI/CILPROV/CILGAR), presiones (150/200/300)

### Eventos Principales
- **limpiar()**: Carga todos los ComboBox desde BD (subcategoría filtrada "BOMBONAS", líneas, unidades, marcas, etc.)
- **cbsc_SelectedIndexChanged**: Recarga líneas por subcategoría
- **CBlinea_SelectedIndexChanged**: Recarga sublíneas y calcula códigos SAP
- **cmdgrabar_Click**: Inserta/actualiza producto + retimbrado

### Bug ADR Detallado
```vb
' Llamada ACTUAL (NO guarda ADR) - línea ~1311:
idr = objgas.InsertarRetimbrado(0, Cod_producto, Codigo_fabricacion,
      Anio_fabricacion, txtcodsap3.Text, TxtPeso_origen.Text, TxtPeso_actual.Text,
      CBPresion_servicio.Text, CBPresion_prueba.Text,
      "", "", "", "", "", 0, "", "", "", "")  ← CAMPOS ADR VACÍOS

' Llamada COMENTADA (SÍ guardaba ADR) - línea ~1537:
'id = objgas.InsertarRetimbrado(0, Cod_producto, Codigo_fabricacion,
'      Anio_fabricacion, txtcodsap3.Text, TxtPeso_origen.Text, TxtPeso_actual.Text,
'      CBPresion_servicio.Text, CBPresion_prueba.Text,
'      TxtNro_aprobacion.Text, TxtClase_peligro.Text, CBMarcado1.Text,
'      TxtMarcado.Text, CBFormato_Bulto.Text, CBtransporte.Text,
'      CBEtiqueta.Text, CBtuneles.Text, CBNro_ONU.Text, TxtRegist_Alimentario.Text)
```

---

## FrmCatLineas.vb (106 líneas)

CRUD simple de líneas. SPs: Linea_BuscarxNom, Linea_Insertar, Linea_Modificar. Sin novedades.

## FrmCatSubLineas.vb (139 líneas)

CRUD simple de sublíneas. SPs: SubLinea_BuscarxNom, SubLinea_Insertar, SubLinea_Modificar. Sin novedades.

## FrmCatMarca.vb (100 líneas)

CRUD simple de marcas. SPs: Marca_BuscarxNom, Marca_Insertar, Marca_Modificar. Sin novedades.

## FrmCatRubro.vb (91 líneas)

CRUD simple de rubros. SPs: Rubro_BuscarxNom, Rubro_Insertar, Rubro_Modificar. Sin novedades.

## FrmPromProducto.vb

Gestión de promociones por producto. SPs: Promocion_Insertar, Promocion_Modificar, Promocion_BuscarxProd.

**Hallazgo**: La clase `CFamilia` maneja promociones (no existe clase `CPromocion`). Esto es un error de naming y arquitectura.

## FrmRegPrecios.vb

Registro de listas de precios. Permite actualizar precio unitario, precio caja, precio intermedio.
SPs: Producto_listadoprecios, Producto_ActualizarPrecios.

## FrmRegDesc.vb

Registro de descuentos. SPs: sp_Descuento_Insertar, sp_Descuento_Buscarxproducto.

## FrmConfGrupo.vb

Configuración de grupos de producto. SPs: Grupo_BuscarxNom, actualizar_Producto_CodGrupo.

## FrmCONFTC.vb

Tipo de cambio (relacionado a precios multi-moneda). SPs: insertar_tc, tc_buscarxdia.
