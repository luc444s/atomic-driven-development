# SPEC 0019 — Envases de logistica con catalogos remotos de productos

## Estado

En implementacion

## Contexto

El formulario de envases y retimbrado de `logistics` aun usa una mezcla de hardcodes y textos simples para datos que en el legacy eran catalogos reales.

El analisis del legacy confirma que:

- gas, marca, linea y sublinea son catalogos de productos;
- `ADR_Mercancia` es una denominacion textual, no un catalogo;
- no hace falta una validacion critica de esos catalogos dentro de `logistics`.

`productos` ya expone endpoints de lectura para esos catalogos, por lo que esta spec define una integracion de solo lectura via REST.

La primera implementacion de esta spec consume los catalogos remotos desde el frontend de `logistics` y resuelve los IDs locales existentes para no romper las FKs del modelo actual.

En el alta de envase no se captura ADR manualmente. La configuracion ADR es propiedad de `productos` y, si el flujo necesita mostrarla, debe leerse como referencia o snapshot de solo lectura, no como entrada editable del formulario de envase.

## Objetivo

Reemplazar hardcodes y textos simples del flujo de envases por seleccion de catalogos remotos de `productos`, manteniendo `ADR_Mercancia` como texto libre.

## No objetivos

- crear una sincronizacion de catlogos entre plugins;
- mover la logica de negocio a `productos`;
- agregar validaciones criticas cruzadas entre plugins;
- cambiar el modelo de datos persistido de `lg_cylinders`.

## Alcance

### Incluye

1. consumir por REST los catalogos necesarios desde `productos`;
2. reemplazar la lista hardcodeada de gas por un catalogo remoto;
3. reemplazar los textos simples de marca y sublinea por seleccion remota;
4. mantener `ADR_Mercancia` como campo de texto libre;
5. reutilizar componentes compartidos de busqueda o seleccion para no duplicar UI.

### No incluye

1. introducir nuevas tablas en `logistics` para replicar esos catalogos;
2. convertir `ADR_Mercancia` en un catalogo;
3. agregar validacion transaccional entre plugins al guardar envases;
4. modificar precios o costos maestros desde `logistics`.

## Contrato funcional minimo

### Gas

- debe seleccionarse desde el catalogo de `productos`;
- no debe existir lista hardcodeada local;
- la UI puede usar busqueda o select remoto, segun cardinalidad.

### Marca

- debe seleccionarse desde `prod_brands`;
- no debe capturarse como texto libre en el formulario principal.

### Linea y sublinea

- deben provenir de `prod_lines` y `prod_subline`;
- si la UI necesita dependencia entre ambos, la sublinea debe filtrarse por la linea seleccionada.

### ADR_Mercancia

- permanece como texto libre;
- no requiere lookup remoto;
- no requiere catalogo nuevo.

### ADR en alta de envase

- no debe pedirse manualmente en el formulario de crear envase;
- no debe mantenerse como fuente maestra en `logistics`;
- cualquier dato ADR visible en el flujo debe venir de `productos` como lectura.

## Criterios de aceptacion

1. el formulario de envases deja de usar hardcodes para gas;
2. marca y sublinea se seleccionan desde catalogos de `productos`;
3. `ADR_Mercancia` sigue siendo texto libre;
4. el alta de envase no solicita ADR manualmente;
5. no se agrega validacion critica entre `logistics` y `productos`;
6. la UI reutiliza componentes compartidos de busqueda/seleccion.

## Riesgos

| Riesgo | Impacto | Mitigacion |
|---|---|---|
| La UI de envases crece por integrar varios catalogos remotos | medio | usar wrappers delgados y componentes compartidos |
| Un campo que parecia catalogo termine siendo texto libre en el legacy | medio | validar cada campo contra el legacy antes de endurecerlo |
| La dependencia REST introduzca latencia en los formularios | bajo | cargar catalogos de forma controlada y cacheada en frontend |

## Dependencias

- ADR 0019 — Catalogos de envases via REST desde productos;
- SPEC 0012 — Logistics: Envase completo + trazabilidad field;
- ADR 0015 — Productos plugin;
- `plugins/productos/backend/router.py`;
- `plugins/productos/frontend/api.ts`;
- `apps/web/src/shared/ui/search-dialog.tsx`.
