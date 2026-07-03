# ADR 0019 — Catálogos de envases via REST desde productos

## Estado

Propuesto

## Contexto

El formulario de control de envases y retimbrado en `logistics` hoy mezcla tres tipos de datos:

- valores hardcodeados para algunas opciones;
- textos libres que en el legacy eran catálogos;
- referencias de negocio que realmente pertenecen al master data de `productos`.

El legacy muestra que:

- `Marca_Producto` apunta a un catalogo de marcas;
- `Cod_Linea` y `Cod_Sublinea` apuntan a catalogos de clasificacion;
- `cod_grupo` se usa como referencia a un gas padre;
- `ADR_Mercancia` es una denominacion textual, no un catalogo validado.

La plataforma ya tiene el plugin `productos` con endpoints de lectura para esos catalogos, por lo que no hace falta duplicar listas ni agregar validacion critica en `logistics`.

## Decision

Los formularios de envases en `logistics` deben consumir por REST los catalogos de `productos` para reemplazar hardcodes y textos simples donde exista catalogo real.

### Origen de datos

- gas -> `productos` (`prod_products`, filtrado por condicion GAS);
- marca -> `productos` (`prod_brands`);
- linea -> `productos` (`prod_lines`);
- sublinea -> `productos` (`prod_subline`);
- `ADR_Mercancia` -> texto libre.

## Consecuencias

**Positivas:**
- elimina duplicacion de catalogos en `logistics`;
- alinea envases con el master data real de `productos`;
- reduce hardcodes en UI;
- no requiere sincronizacion ni validacion cruzada critica.

**Negativas:**
- la UI depende de endpoints de lectura de otro plugin;
- los formularios necesitan loaders o buscadores remotos.

## Riesgos

- Si `productos` cambia nombres o estructura de sus catálogos, la UI de envases debe ajustarse.
- Si algun campo del legacy era realmente texto libre y no catalogo, el cambio podria endurecerlo mas de lo necesario. Mitigacion: confirmar cada campo contra el legacy antes de convertirlo.

## Referencias

- `docs/specs/core/0012-logistics-envase-completo.md`
- `docs/database/modulo_productos/01_ddl_tablas.md`
- `docs/database/modulo_productos/04_forms.md`
- `docs/database/modulo_productos/11_vistas_sql_completas.md`
- `docs/database/modulo_productos/12_clases_vb_adicionales.md`
- `docs/adr/0015-productos-plugin.md`
- `plugins/productos/backend/router.py`
