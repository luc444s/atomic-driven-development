# SPEC 0017 — SearchDialog Generico Compartido

## Estado

Propuesta

## Contexto

El frontend actual tiene al menos dos dialogos de busqueda reutilizables con la misma estructura base:

- `apps/web/src/components/ProductSearchDialog.tsx`;
- `plugins/crm/frontend/components/CustomerSearchDialog.tsx`.

Ambos implementan el mismo patron visual y operativo:

- `Dialog` para abrir/cerrar;
- `Input` para busqueda por texto;
- `DataTable` para listar resultados;
- seleccion de una fila con `onSelect`;
- estados de loading, vacio y error.

El problema no es solo la duplicacion.

Tambien existe una inconsistencia de ownership:

- `ProductSearchDialog` vive en `apps/web/src/components/` pero es consumido por plugins;
- `CustomerSearchDialog` vive en `plugins/crm/` pero funciona como pieza reusable para otros plugins.

ADR 0017 corrige esta situacion definiendo un `SearchDialog<T>` generico en `apps/web/src/shared/ui/search-dialog.tsx` como compromiso temporal, reutilizando los primitivos ya compartidos del shell frontend.

Esta spec operacionaliza esa decision.

## Objetivo

Crear un componente generico `SearchDialog<T>` para estandarizar la UX de seleccion por busqueda en plugins y frontend shell, reducir duplicacion y eliminar componentes concretos duplicados cuando ya no aporten comportamiento propio.

## No objetivos

- crear `packages/ui/` en esta tarea;
- mover todo `shared/ui/` fuera de `apps/web/`;
- rediseñar `DataTable`;
- introducir un sistema de filtros avanzados generico;
- convertir todos los dialogos existentes a autocomplete inline;
- reescribir las APIs de `productos` o `crm`.

## Alcance

### Incluye

1. crear `apps/web/src/shared/ui/search-dialog.tsx`;
2. definir un contrato generico basado en `ColumnDef<T>`;
3. encapsular debounce, carga inicial, estados vacio/error y seleccion;
4. migrar `ProductSearchDialog` para que use `SearchDialog` o eliminarlo si deja de aportar valor;
5. migrar `CustomerSearchDialog` para que use `SearchDialog` o eliminarlo si deja de aportar valor;
6. actualizar imports en plugins que consuman estos buscadores;
7. actualizar tests frontend afectados;
8. documentar la relacion con specs previas.

### No incluye

1. soporte de filtros compuestos por multiples campos;
2. busqueda server-side con paginacion infinita;
3. cache global compartido de busquedas;
4. soporte offline;
5. cambios backend de semantica en endpoints de busqueda.

## Relacion con documentos previos

Esta spec complementa y corrige parcialmente estas specs previas:

- `SPEC 0013 — CRM Plugin (Clientes)`;
- `SPEC 0015 — Productos Plugin`;
- `SPEC 0016 — Stock Plugin`.

Regla de compatibilidad documental:

- donde esas specs hablen de `ProductSearchDialog` o `CustomerSearchDialog` como piezas reutilizables base, debe entenderse que la pieza reutilizable base ahora es `SearchDialog<T>`;
- `ProductSearchDialog` y `CustomerSearchDialog` pueden sobrevivir solo como wrappers delgados si siguen aportando defaults de dominio.

## Arquitectura objetivo

### Ubicacion

El componente vive en:

`apps/web/src/shared/ui/search-dialog.tsx`

Motivo:

- ya existen en ese espacio `Input`, `Dialog`, `Alert` y `DataTable`;
- evita crear una tercera variante reusable en otro lugar;
- mantiene el cambio pequeno y consistente con el estado actual del repo.

Esto no reemplaza el objetivo futuro de mover `shared/ui/` a `packages/ui/`.

### Ownership

- `SearchDialog<T>` es dueño de la experiencia generica de busqueda y seleccion;
- cada plugin sigue siendo dueño de:
  - sus tipos de dominio;
  - su `fetchFn`;
  - sus columnas;
  - su logica posterior a `onSelect`.

### Regla de diseno

`SearchDialog<T>` no debe conocer conceptos de dominio como cliente, producto, ruta, cilindro o almacén.

Toda diferencia de dominio entra por props.

## Contrato funcional

### Props base

```typescript
interface SearchDialogProps<T> {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  placeholder?: string;
  columns: ColumnDef<T>[];
  fetchFn: (query: string) => Promise<T[]>;
  onSelect: (item: T) => void;
  getRowId?: (item: T) => string;
  emptyMessage?: string;
}
```

### Comportamiento requerido

1. al abrir el dialogo, ejecuta `fetchFn("")`;
2. al cambiar el texto, espera `300ms` antes de volver a consultar;
3. si el usuario sigue escribiendo antes del debounce, cancela la consulta anterior a nivel de estado UI;
4. muestra estado de carga mientras la consulta en curso no termina;
5. muestra `emptyMessage` cuando la consulta retorna `[]`;
6. muestra `Alert` cuando `fetchFn` falla;
7. al seleccionar una fila, llama `onSelect(item)` y luego cierra el dialogo;
8. debe cerrar con Escape y con click fuera, reutilizando el comportamiento del `Dialog` base.

### Comportamiento no requerido

No es obligatorio en esta spec:

- autofocus del input;
- seleccion automatica por match exacto;
- navegacion completa por teclado entre filas;
- resaltado de coincidencias dentro del texto;
- paginacion de resultados.

## Estados visuales minimos

El componente debe contemplar estos estados:

1. cerrado;
2. abierto + loading inicial;
3. abierto + resultados;
4. abierto + sin resultados;
5. abierto + error.

No debe introducir colores hardcodeados; debe usar las variables semanticas ya existentes del sistema visual.

## Integracion con implementaciones existentes

### Productos

`ProductSearchDialog` puede quedar en uno de estos estados:

1. eliminado y reemplazado por uso directo de `SearchDialog<ProductSearchItem>`; o
2. reducido a wrapper delgado que solo define:
   - `title`;
   - `placeholder`;
   - `columns`;
   - `fetchFn`.

La decision recomendada es mantener wrapper solo si mejora claridad de uso en 3 o mas sitios.

### CRM

`CustomerSearchDialog` sigue la misma regla:

1. uso directo del generico; o
2. wrapper delgado de dominio.

No debe seguir existiendo una implementacion duplicada de la misma UI.

## Plan de migracion

1. crear `search-dialog.tsx` en `shared/ui`;
2. migrar `apps/web/src/components/ProductSearchDialog.tsx` para usar el generico;
3. migrar consumidores en `stock` y `productos`;
4. migrar `plugins/crm/frontend/components/CustomerSearchDialog.tsx` para usar el generico;
5. migrar consumidores en `logistics`;
6. eliminar implementaciones muertas si ya no aportan defaults utiles;
7. actualizar specs referenciales si queda algun cambio de ownership explicito.

## Criterios de aceptacion

### Funcionales

1. un usuario puede abrir el buscador de productos desde stock y seleccionar un producto valido;
2. un usuario puede abrir el buscador de clientes desde logistics y seleccionar un cliente valido;
3. escribir texto dispara busqueda con debounce de `300ms`;
4. si no hay resultados, se muestra mensaje vacio claro;
5. si la consulta falla, se muestra error visible sin romper la pagina;
6. seleccionar una fila devuelve el item correcto al componente padre y cierra el dialogo.

### Arquitectonicos

1. no se agrega una tercera implementacion concreta independiente de buscador;
2. el comportamiento generico vive en `shared/ui/search-dialog.tsx`;
3. los wrappers de dominio, si sobreviven, no duplican logica de tabla + estado + debounce;
4. el cambio no introduce colores hardcodeados ni componentes visuales paralelos.

### Calidad

1. `tsc --noEmit` pasa;
2. `vitest` pasa en los tests afectados;
3. si se tocan tests Python o backend, no aplica por defecto en esta spec;
4. el componente queda suficientemente tipado para no requerir `any` en su API publica.

## Riesgos

| Riesgo | Impacto | Mitigacion |
|---|---|---|
| El generico intenta cubrir demasiados casos | API confusa y dificil de mantener | Mantener alcance minimo: query simple + tabla + seleccion |
| Quedan wrappers que siguen duplicando logica interna | Beneficio parcial | Limitar wrappers a defaults de dominio |
| Plugins siguen importando de `apps/web/src/shared/ui/` | Deuda estructural persistente | Resolver en ADR/spec futura para `packages/ui` |
| Diferencias entre columnas de productos y clientes fuerzan excepciones | Complejidad extra | Reutilizar `ColumnDef<T>` y evitar props especiales de dominio |

## Dependencias

- ADR 0002 — Arquitectura monorepo;
- ADR 0004 — Runtime de plugins;
- ADR 0017 — SearchDialog generico en shared/ui;
- `DataTable`, `Dialog`, `Input`, `Alert` existentes en `apps/web/src/shared/ui/`.

## Referencias

- `docs/specs/core/0013-crm-plugin.md`
- `docs/specs/core/0015-productos-plugin/index.md`
- `docs/specs/core/0016-stock-plugin/index.md`
- `apps/web/src/components/ProductSearchDialog.tsx`
- `plugins/crm/frontend/components/CustomerSearchDialog.tsx`
