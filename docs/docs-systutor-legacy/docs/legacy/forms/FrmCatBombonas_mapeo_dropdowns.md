# FrmCatBombonas — Mapeo completo de ComboBox (Dropdowns)

## 1. Introducción

Este documento detalla **todos los ComboBox** del formulario `FrmCatBombonas` (creación y mantenimiento de cilindros/envases), indicando:

- Tipo de carga (BD vs hardcoded)
- Stored Procedure y tabla de origen
- Columnas que proveen Display/Value
- Evento que dispara la carga
- Handler y línea de código
- Dónde se usa su valor seleccionado (.Text / SelectedValue)
- Relación con otros módulos

---

## 2. Dropdowns con carga desde base de datos

### 2.1 cbsc — Subcategoría

| Propiedad | Valor |
|-----------|-------|
| **Tipo** | ComboBox |
| **Carga** | Desde BD |
| **SP** | `SubCategoria_BuscarxNom` |
| **Clase DAL** | `CSubcategoria` → método `BuscarSubCategoriaxNombre` |
| **Tabla origen** | `SubCategoria` |
| **Columna Display** | `DESCRIPCION` |
| **Filtro** | Se pasa `"BOMBONAS"` como parámetro de búsqueda |
| **Evento carga** | `limpiar()` → llamado desde `cmdnuevo_Click` y `cmdmodificar_Click` |
| **Líneas** | 312-324 (población), 170 (clean) |
| **Handler propio** | `cbsc_SelectedIndexChanged` (línea 3629) |
| **Efecto al cambiar** | Recarga `CBlinea` vía `Linea_BuscarxNomXRubro` |
| **Usado en** | 172 (limpiar), 1106 (cargar producto existente), 3629-3677 (SelectedIndexChanged) |

**Código de carga (línea 312-324):**
```vb
cbsc.Items.Clear()
Dr = objSc.BuscarSubCategoriaxNombre("BOMBONAS")
While Dr.Read()
    cbsc.Items.Add(Dr("DESCRIPCION"))
End While
```

---

### 2.2 CBlinea — Línea de producto

| Propiedad | Valor |
|-----------|-------|
| **Tipo** | ComboBox |
| **Carga** | Desde BD |
| **SP** | `Linea_BuscarxNom` (carga inicial) → `Linea_BuscarxNomXRubro` (recarga por subcategoría) |
| **Clase DAL** | `CLinea` → método `BuscarLineaxNombre` / `BuscarLineaxNombrexRubro` |
| **Tabla origen** | `CLinea` |
| **Columna Display** | `Desc_Linea` |
| **Evento carga inicial** | `limpiar()` (línea 327-335) |
| **Evento recarga** | `cbsc_SelectedIndexChanged` (línea 3659-3667) |
| **Handler propio** | `CBlinea_SelectedIndexChanged` (línea 1660) |
| **Efecto al cambiar** | Recarga `cbsublinea` vía `SubLinea_BuscarxNomXLineaxcod` |
| **Usado en** | 173 (limpiar), 1685, 1969, 6634, 7215 |

**Código de recarga (línea 3659-3667):**
```vb
CBlinea.Items.Clear()
Dr = objSc.BuscarLineaxNombrexRubro(cbsc.Text)
While Dr.Read()
    CBlinea.Items.Add(Dr("Desc_Linea"))
End While
```

---

### 2.3 cbsublinea — Sublínea de producto

| Propiedad | Valor |
|-----------|-------|
| **Tipo** | ComboBox |
| **Carga** | Desde BD |
| **SP** | `SubLinea_BuscarxNomXLineaxcod` |
| **Clase DAL** | `CsubLinea` → método `BuscarSubLineaxNombrexcodLinea` |
| **Tabla origen** | `CsubLinea` |
| **Columna Display** | `desc_SubLinea` |
| **Evento carga** | `CBlinea_SelectedIndexChanged` (línea 1693-1702) |
| **Handler propio** | `cbsublinea_SelectedIndexChanged` (línea 1933) |
| **Efecto al cambiar** | Recarga `CBcontenidoGrupo` vía `BuscarProductoPorCondicionYCadena` y `BuscarPorCodSublinea` |
| **Usado en** | 1702, 1933-1990, 1969, 6634, 7215 |

---

### 2.4 Cbtinsumo — Tipo de insumo

| Propiedad | Valor |
|-----------|-------|
| **Tipo** | ComboBox |
| **Carga** | Desde BD |
| **SP** | `Tipoatencion_BuscarDesc` |
| **Clase DAL** | `CTipoInsumo` → método `BuscarTipoInsumoxDesc` |
| **Tabla origen** | `CTipoInsumo` |
| **Columna Display** | `Desc_tipoinsumo` |
| **Evento carga** | `limpiar()` (línea 387-394) |
| **Usado en** | 1747 (lectura de .Text) |

---

### 2.5 CBUnidad — Unidad de medida (filtrada)

| Propiedad | Valor |
|-----------|-------|
| **Tipo** | ComboBox |
| **Carga** | Desde BD |
| **SP** | `Unidad_BuscarxNom` |
| **Clase DAL** | `Cunidad` → método `BuscarLineaxNombre` |
| **Tabla origen** | `Cunidad` |
| **Columna Display** | `Desc_unidad` |
| **Filtro** | `equivalencia = 1` (filtro en capa VB, no en SP) |
| **Evento carga** | `limpiar()` (línea 340-351) |
| **Usado en** | 1730 (asignación a txtunidad.Text) |

---

### 2.6 CBUnidad1 — Unidad de medida (sin filtro)

| Propiedad | Valor |
|-----------|-------|
| **Tipo** | ComboBox |
| **Carga** | Desde BD |
| **SP** | `Unidad_BuscarxNom` |
| **Clase DAL** | `Cunidad` |
| **Tabla origen** | `Cunidad` |
| **Columna Display** | `Desc_unidad` |
| **Filtro** | Ninguno — muestra todas las unidades |
| **Default** | Selecciona `"UND."` por defecto |
| **Evento carga** | `limpiar()` (línea 356-366) |
| **Usado en** | Se pasa como `txtunidad` a `InsertarProducto` / `ModificarProducto` |

---

### 2.7 CBMarca — Marca del producto

| Propiedad | Valor |
|-----------|-------|
| **Tipo** | ComboBox |
| **Carga** | Desde BD |
| **SP** | `marca_BuscarxNom` |
| **Clase DAL** | `CMarca` → método `BuscarmarcaxNombre` |
| **Tabla origen** | `CMarca` |
| **Columna Display** | `Desc_Marca` |
| **Evento carga** | `limpiar()` (línea 371-377) |
| **Usado en** | 174, 1920, 5015 |

---

### 2.8 CBestado — Estado del producto

| Propiedad | Valor |
|-----------|-------|
| **Tipo** | ComboBox |
| **Carga** | Desde BD |
| **SP** | `EstadoProducto_BuscarxNom` |
| **Clase DAL** | `CEstadoProducto` → método `BuscarEstadoProductoxNombre` |
| **Tabla origen** | `CEstadoProducto` |
| **Columna Display** | `Desc_EstadoProd` |
| **Evento carga** | `limpiar()` (línea 410-417) |
| **Usado en** | 175, 2000 |

---

### 2.9 cbsucursal — Almacén/Sucursal

| Propiedad | Valor |
|-----------|-------|
| **Tipo** | ComboBox |
| **Carga** | Desde BD |
| **SP** | `[Almacen_MOSTRAR_ANEXOS]` |
| **Clase DAL** | `CSucursal` → método `MOSTRAR_ANEXOS` |
| **Tabla origen** | `CSucursal` / `Almacen` |
| **Columna Display** | Índice 1 del DataReader (nombre del almacén) |
| **Evento carga** | `limpiar()` (línea 398-406) |
| **Usado en** | 246 (limpiar), 1234 (insertar producto), 2253 (consulta stock) |

---

### 2.10 C (letra simple) — Ubicación en almacén

| Propiedad | Valor |
|-----------|-------|
| **Tipo** | ComboBox |
| **Carga** | Desde BD |
| **SP** | `mostrar_ubicacion_almacen` |
| **Clase DAL** | `CUbicacion` → método `mostrar_ubicacion_almacen` |
| **Tabla origen** | `CUbicacion` |
| **Columna Display** | `Desc_Ubic` |
| **Evento carga** | `Button5_Click` (línea 2283-2292) |
| **Handler propio** | `C_SelectedIndexChanged` (línea 3685) |
| **Usado en** | 3685 (SelectedIndexChanged) |

**Nota:** Este ComboBox tiene nombre de variable de un solo carácter `C`, lo que es mala práctica. Su propósito es seleccionar ubicación física del cilindro en el almacén.

---

### 2.11 ComboBox1 — Tipo de documento contable

| Propiedad | Valor |
|-----------|-------|
| **Tipo** | ComboBox |
| **Carga** | Desde BD |
| **SP** | `mostrar_cbdocumentos` |
| **Clase DAL** | `CComprobante` → método `cbmostrardoc` |
| **Tabla origen** | `CComprobante` (tabla de tipos de documento) |
| **Columna Display** | `cbempresa` |
| **Evento carga** | `limpiar()` (línea 441-447) y `Button11_Click` (línea 3325-3329) |
| **Usado en** | Solo lectura en pantalla; su `.Text` se concatena en `TXTDESC_CORTA` |

---

### 2.12 CBcontenidoGrupo — Producto/contenido del grupo

| Propiedad | Valor |
|-----------|-------|
| **Tipo** | ComboBox |
| **Carga** | Desde BD |
| **SP 1** | `BuscarProductoPorCondicionYCadena` (clase `CProducto`) |
| **SP 2** | `BuscarPorCodSublinea` (clase `Cgas`) |
| **Tabla origen** | `Producto` |
| **Columna Display** | `Desc_Producto` (SP1) / `desc_producto` (SP2) |
| **Evento carga** | `cbsublinea_SelectedIndexChanged` (línea 1944-1953, 1988-1990) |
| **Nota** | Se carga dos veces en el mismo evento (duplicado/comentado) |
| **Usado en** | 6192, 6210 |

---

## 3. Dropdowns con valores hardcoded (quemados en el Designer)

### 3.1 CBcondicion — Condición/Dueño del cilindro

| Propiedad | Valor |
|-----------|-------|
| **Items** | `"CILPRO"`, `"CILCLI"`, `"CILPROV"`, `"CILGAR"` |
| **Tipo** | String fijo |
| **Significado** | CILPRO = cilindro propio de la empresa, CILCLI = cilindro del cliente, CILPROV = cilindro del proveedor, CILGAR = cilindro en garantía |
| **Línea Designer** | `Items.AddRange(New Object() {"CILPRO", "CILCLI", "CILPROV", "CILGAR"})` |
| **Referencias en código** | ~54 ocurrencias |
| **Crítico para** | `InsertarProducto`, `InsertardetallePedido`, lógica de condición de cilindro en despachos |
| **Uso típico** | Determina quién es el dueño del cilindro. Afecta `Ecil_duenio` en otros módulos |
| **Relación con otros módulos** | Los mismos valores aparecen en `FrmMovIntercambioCliente`, `FrmMovFacturacionDirecta`, `FrmMovPreparacionCarga`. Es un **vocabulario compartido en toda la solución** |

---

### 3.2 CBPresion_servicio — Presión de servicio

| Propiedad | Valor |
|-----------|-------|
| **Items** | `"150"`, `"200"`, `"300"` (bar) |
| **Tipo** | String numérico (se parsea a Decimal) |
| **Línea Designer** | Items.AddRange |
| **Referencias** | 1292, 1507, 5040 (conversión a Decimal), 7497 (autocalcular) |
| **Autocalculador** | Línea 7497: al presionar tecla, `CBPresion_prueba.Text = CStr(CDbl(CBPresion_servicio.Text) * 1.5)` |
| **Guardado en BD** | Se pasa a `InsertarRetimbrado` / `actualizar_retimbrado` como `Presion_servicio` (decimal) |

---

### 3.3 CBPresion_prueba — Presión de prueba hidráulica

| Propiedad | Valor |
|-----------|-------|
| **Items** | `"150"`, `"200"`, `"300"` (bar) |
| **Tipo** | String numérico |
| **Línea Designer** | Items.AddRange |
| **Referencias** | 1293, 1508, 5041 |
| **Autocalculado** | Se calcula como servicio × 1.5, pero también se puede seleccionar manualmente |
| **Guardado en BD** | Se pasa a `InsertarRetimbrado` / `actualizar_retimbrado` como `Presion_prueba` (decimal) |

---

### 3.4 CBFormato_Bulto — Formato del bulto (ADR)

| Propiedad | Valor |
|-----------|-------|
| **Items** | `"BOTELLA"`, `"BLOQUE  BOTELLAS"`, `"RECIPIENTE CRIOGENICO"` |
| **Panel contenedor** | `Panel11` (Visible = False) |
| **Estado actual** | **No se guarda en BD** — solo aparece en código comentado (línea 1537, 5110) |
| **Propósito** | Clasificación ADR del formato de transporte |

---

### 3.5 CBtransporte — Categoría de transporte (ADR)

| Propiedad | Valor |
|-----------|-------|
| **Items** | `"1"`, `"2"`, `"3"` |
| **Panel contenedor** | `Panel11` (Visible = False) |
| **Estado actual** | **No se guarda en BD** |
| **Propósito** | Categoría de transporte para mercancías peligrosas |

---

### 3.6 CBEtiqueta — Tipo de etiqueta (ADR)

| Propiedad | Valor |
|-----------|-------|
| **Items** | `"ε"`, `"π"` (caracteres griegos — posiblemente corruptos/codificados) |
| **Panel contenedor** | `Panel11` (Visible = False) |
| **Estado actual** | **No se guarda en BD** |

---

### 3.7 CBtuneles — Restricción de túneles (ADR)

| Propiedad | Valor |
|-----------|-------|
| **Items** | `"ε"`, `"π"` |
| **Panel contenedor** | `Panel11` (Visible = False) |
| **Estado actual** | **No se guarda en BD** |

---

### 3.8 CBNro_ONU — Número ONU (ADR)

| Propiedad | Valor |
|-----------|-------|
| **Items** | `"ε"`, `"π"` |
| **Panel contenedor** | `Panel11` (Visible = False) |
| **Estado actual** | **No se guarda en BD** |

---

### 3.9 CBMarcado1 — Marcado 1 (ADR)

| Propiedad | Valor |
|-----------|-------|
| **Items** | `"e"`, `"p"` |
| **Panel contenedor** | `Panel11` (Visible = False) |
| **Estado actual** | **No se guarda en BD** |

---

### 3.10 TxtClase_peligro — Clase de peligro (ADR)

| Propiedad | Valor |
|-----------|-------|
| **Items** | `"1"`, `"2"`, `"3"` |
| **Panel contenedor** | `Panel11` (Visible = False) |
| **Estado actual** | **No se guarda en BD** |
| **Nota** | Aunque se llame `Txt...`, es un ComboBox |

---

### 3.11 ComboBox3 — Tipo de gas

| Propiedad | Valor |
|-----------|-------|
| **Items** | `"Industrial"`, `"Alimenticio"`, `"Médico"` |
| **Usado en** | Solo 1 referencia comentada (línea 1523) |
| **Estado actual** | **Inactivo** — código comentado |

---

### 3.12 ComboBox2 — Documento de referencia

| Propiedad | Valor |
|-----------|-------|
| **Items** | `"Garantía Nro.:"`, `"Doc. compra:"`, `""`, `""`, `""` |
| **Usado en** | Concatenación en `TXTDESC_CORTA.Text` (descripción corta del producto) y en `docafec` |

---

### 3.13 ComboBox4 — Tipo AIRE

| Propiedad | Valor |
|-----------|-------|
| **Items** | `"AIRE"` (1 solo item) |
| **Estado** | **Nunca referenciado** en el código `.vb` |

---

### 3.14 ComboBox5 — Sucursal (código)

| Propiedad | Valor |
|-----------|-------|
| **Items** | `"SUC1"`, `"SUC2"`, `"SUC3"`, `"SUC4"` |
| **Estado** | Solo se limpia su `.Text` (línea 484). **Nunca usado en lógica** |

---

### 3.15 ComboBox6 — Estante (código)

| Propiedad | Valor |
|-----------|-------|
| **Items** | `"E01"`, `"E02"`, `"E03"`, `"E04"`, `"E05"`, `"E06"`, `"E07"`, `"E08"`, `"E09"`, `"E10"`, `"E11"`, `"E12"`, `"E13"`, `"E14"`, `"E15"`, `"E16"`, `"E17"`, `"E18"` |
| **Estado** | Solo se limpia su `.Text` (línea 484). **Nunca usado en lógica** |

---

### 3.16 ComboBox7 — Columna (código)

| Propiedad | Valor |
|-----------|-------|
| **Items** | `"01"` a `"09"` |
| **Estado** | Solo se limpia su `.Text` (línea 484). **Nunca usado en lógica** |

---

### 3.17 cbmoneda — Moneda

| Propiedad | Valor |
|-----------|-------|
| **Items** | `"Soles"`, `"Euros"` |
| **Default** | Desde `ClsContextoRegional` (línea 777) |
| **Usado en** | 3974, 6290 — contexto regional de precios |

---

### 3.18 TxtProveedor — Proveedor (ComboBox disfrazado)

| Propiedad | Valor |
|-----------|-------|
| **Items** | `"ACTIVACION DE CILINDRO"` (1 solo item) |
| **Visible** | `False` — siempre oculto |
| **Usado en** | 4471, 4568, 4624, 4690, 5363, 5810 |

---

### 3.19 CBequivalencia — Equivalencia de unidad

| Propiedad | Valor |
|-----------|-------|
| **Items** | *(ninguno — ComboBox vacío)* |
| **Items en Designer** | Sin Items.AddRange |
| **Estado** | **Huérfano** — declarado pero nunca referenciado en el código `.vb` |
| **Conclusión** | Resto de funcionalidad no implementada o eliminada |

---

## 4. Mapa visual de paneles

```
┌─────────────────────────────────────────────────────┐
│  PANELDATOSTECNICOS (visible en "Datos Técnicos")   │
│                                                     │
│  [txtcodsap1]  Código fabricación    (TextBox)      │
│  [txtcodsap2]  (intermedio)          (TextBox)      │
│  [txtcodsap3]  Nro_Bombona / Serie   (TextBox)      │
│  [AnioFabricacion]  Año fabricación  (TextBox)      │
│  [TxtPeso_origen]   Peso origen      (NumericUpDown) │
│  [TxtPeso_actual]   Peso actual      (NumericUpDown) │
│  [CBPresion_servicio ▼]  150,200,300 (ComboBox)     │
│  [CBPresion_prueba ▼]    150,200,300 (ComboBox)     │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│  PANEL11 (Visible = False — ADR oculto)             │
│                                                     │
│  [TxtClase_peligro ▼]    1,2,3        (ComboBox)    │
│  [CBMarcado1 ▼]          e,p          (ComboBox)    │
│  [CBFormato_Bulto ▼]     BOTELLA,...  (ComboBox)    │
│  [CBtransporte ▼]        1,2,3        (ComboBox)    │
│  [CBEtiqueta ▼]          ε,π          (ComboBox)    │
│  [CBtuneles ▼]           ε,π          (ComboBox)    │
│  [CBNro_ONU ▼]           ε,π          (ComboBox)    │
│  [TxtNro_aprobacion]     (TextBox)                  │
│  [TxtMarcado]            (TextBox)                  │
│  [TxtRegist_Alimentario] (TextBox)                  │
│  [ComboBox3 ▼]   Industrial,Alimenticio,Médico      │
└─────────────────────────────────────────────────────┘
```

---

## 5. Flujo de carga completo

```
Form_Load (línea 682)
  │
  ├── cmdnuevo_Click (línea 782)
  │     └── limpiar() (línea 170)
  │           ├── cbsc        ← SubCategoria_BuscarxNom("BOMBONAS")
  │           ├── CBlinea     ← Linea_BuscarxNom()
  │           ├── CBUnidad    ← Unidad_BuscarxNom() [filtro equivalencia=1]
  │           ├── CBUnidad1   ← Unidad_BuscarxNom() [sin filtro]
  │           ├── CBMarca     ← marca_BuscarxNom()
  │           ├── Cbtinsumo   ← Tipoatencion_BuscarDesc()
  │           ├── cbsucursal  ← [Almacen_MOSTRAR_ANEXOS]()
  │           ├── CBestado    ← EstadoProducto_BuscarxNom()
  │           └── ComboBox1   ← mostrar_cbdocumentos()
  │
  ├── cbsc_SelectedIndexChanged (línea 3629)
  │     └── CBlinea ← Linea_BuscarxNomXRubro(cbsc.Text)
  │
  ├── CBlinea_SelectedIndexChanged (línea 1660)
  │     └── cbsublinea ← SubLinea_BuscarxNomXLineaxcod(CBlinea.Text)
  │
  └── cbsublinea_SelectedIndexChanged (línea 1933)
        └── CBcontenidoGrupo ← BuscarProductoPorCondicionYCadena()
        └── CBcontenidoGrupo ← BuscarPorCodSublinea()
```

---

## 6. Bugs y observaciones críticas

### 6.1 Panel11 oculto + datos ADR

Los 8 ComboBox de ADR (Clase_peligro, Marcado1, Formato_Bulto, Transporte, Etiqueta, Tuneles, Nro_ONU, ComboBox3) y 3 TextBox (Nro_aprobacion, Marcado2, Regist_Alimentario) están contenidos en `Panel11` con `Visible = False`. Es intencional: el panel ADR se muestra solo cuando el certificado corresponde a **ES (España)** o **CR (Costa Rica)** — variantes regionales de normativa ADR. No es un bug.

A nivel de guardado, la llamada real a `InsertarRetimbrado` (línea 1311) y `actualizar_retimbrado` (línea 1546) pasa **cadenas vacías** para todos estos campos ADR en la ruta estándar:

```vb
' Llamada actual (NO guarda ADR):
idr = objgas.InsertarRetimbrado(0, Cod_producto, Codigo_fabricacion, Anio_fabricacion,
      txtcodsap3.Text, TxtPeso_origen.Text, TxtPeso_actual.Text,
      CBPresion_servicio.Text, CBPresion_prueba.Text,
      "", "", "", "", "", 0, "", "", "", "")  ← TODOS VACÍOS

' Llamada COMENTADA que SÍ guardaba ADR (línea 1537):
'id = objgas.InsertarRetimbrado(0, Cod_producto, Codigo_fabricacion, Anio_fabricacion,
'      txtcodsap3.Text, TxtPeso_origen.Text, TxtPeso_actual.Text,
'      CBPresion_servicio.Text, CBPresion_prueba.Text,
'      TxtNro_aprobacion.Text, TxtClase_peligro.Text, CBMarcado1.Text,
'      TxtMarcado.Text, CBFormato_Bulto.Text, CBtransporte.Text,
'      CBEtiqueta.Text, CBtuneles.Text, CBNro_ONU.Text, TxtRegist_Alimentario.Text)
```

### 6.2 CBequivalencia — ComboBox huérfano

Declarado en el Designer, sin items, sin referencias en el código. Probablemente un resto de funcionalidad eliminada.

### 6.3 ComboBox5/6/7 — Restos de interfaz de ubicación física

Estos 3 ComboBox (Sucursal, Estante, Columna) se limpian pero nunca se usan. Posiblemente eran parte de un selector de ubicación física que fue reemplazado por el ComboBox `C`.

### 6.4 Nombre de variable `C`

El ComboBox de ubicación se llama `C` (una sola letra). Viola cualquier convención de nomenclatura. En el nuevo diseño debe renombrarse a `cmbUbicacion` o similar.

---

## 7. Resumen de arquitectura de datos

```
                    ┌───────────────────┐
                    │   FrmCatBombonas  │
                    │ (autocontenido)   │
                    └────────┬──────────┘
                             │
               ┌─────────────┼─────────────┐
               │             │             │
               ▼             ▼             ▼
         ┌──────────┐ ┌──────────┐ ┌──────────────┐
         │ Producto │ │Edetalle_ │ │   Otras      │
         │ (INSERT/ │ │retimbrado│ │ tablas (SP)  │
         │  UPDATE) │ │ (INSERT/ │ │ (solo lectura)│
         └──────────┘ │  UPDATE) │ └──────────────┘
                      └──────────┘
```

**Relaciones con otros módulos:** Ninguna directa. Los valores `CBcondicion` (CILPRO, CILCLI, CILPROV, CILGAR) son estándar en toda la solución y aparecen en FrmMovIntercambioCliente, FrmMovFacturacionDirecta, FrmMovPreparacionCarga, etc., pero no referencian a FrmCatBombonas.

---

## 8. Especificación para el nuevo diseño Python

### 8.1 Tablas necesarias (catálogos)

| Tabla PostgreSQL | Equivalente legacy | Propósito |
|-----------------|-------------------|-----------|
| `categorias` | SubCategoria | Subcategorías de producto (filtro "BOMBONAS") |
| `lineas` | CLinea | Líneas de producto |
| `sublineas` | CsubLinea | Sublíneas de producto |
| `tipos_insumo` | CTipoInsumo | Tipos de insumo |
| `unidades_medida` | Cunidad | Unidades de medida |
| `marcas` | CMarca | Marcas de producto |
| `estados_producto` | CEstadoProducto | Estados de producto |
| `almacenes` | CSucursal/Almacen | Sucursales/almacenes |
| `ubicaciones` | CUbicacion | Ubicaciones físicas |
| `condiciones_cilindro` | (hardcoded) | CILPRO, CILCLI, CILPROV, CILGAR |
| `presiones_cilindro` | (hardcoded) | 150, 200, 300 bar |
| `clases_peligro` | (hardcoded) | 1, 2, 3 |
| `formatos_bulto` | (hardcoded) | BOTELLA, BLOQUE BOTELLAS, RECIPIENTE CRIOGENICO |

### 8.2 Tablas transaccionales

| Tabla PostgreSQL | Equivalente legacy | Propósito |
|-----------------|-------------------|-----------|
| `productos` | Producto | Maestro de productos (cilindros) |
| `cilindros_retimbrado` | Edetalle_retimbrado | Historial de retimbrado |

### 8.3 Reglas de negocio a implementar

1. **Presión prueba** = Presión servicio × 1.5 (autocalcular)
2. **Condición de cilindro** (CILPRO/CILCLI/CILPROV/CILGAR) debe ser un catálogo en BD, no hardcoded
3. **Datos ADR** deben guardarse correctamente en cilindros_retimbrado (todos los campos actualmente ignorados)
4. **Panel ADR** debe ser visible y editable cuando el cilindro requiera certificación ADR
5. **Ubicación física** debe usar un selector único (no 3 ComboBox obsoletos)
