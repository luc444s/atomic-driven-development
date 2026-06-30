# ADR 0017 — SearchDialog generico en shared/ui

## Estado

Propuesto

## Contexto

Actualmente existen dos componentes de dialogo de busqueda:

| Componente | Ubicacion | Uso |
|---|---|---|
| `ProductSearchDialog` | `apps/web/src/components/` | Importado por plugins `stock`, `productos` |
| `CustomerSearchDialog` | `plugins/crm/frontend/components/` | Importado por `logistics` |

El primero viola la arquitectura del monorepo porque un plugin importa desde `apps/web/` (dependencia inversa app → plugin). El segundo esta en el lugar correcto pero es especifico de CRM.

Ambos componentes comparten la misma estructura: `Input` + `DataTable` dentro de un `Dialog`, con variaciones menores en funcion de busqueda, columnas y comportamiento de seleccion.

La arquitectura definida en ADR 0002 y ADR 0004 establece que:

- `packages/` contiene librerias compartidas sin dependencias de plugins.
- `plugins/` contiene modulos de negocio que pueden depender entre si.
- `apps/` nunca debe ser importado por plugins.

Los plugins ya importan de `apps/web/src/shared/ui/` para usar primitivos como `Input`, `DataTable`, `Dialog`, `Alert`. La dependencia inversa ya existe a nivel de primitivos. Este ADR la consolida y reduce duplicacion en lugar de empeorarla.

## Decision

Se crea un componente generico `SearchDialog<T>` en `apps/web/src/shared/ui/search-dialog.tsx`, junto a los primitivos que ya usa. Se reutiliza `ColumnDef` de `@tanstack/react-table` (mismo tipo que usa `DataTable`) y el componente maneja debounce internamente.

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

### Comportamiento

- Al abrir el dialogo, llama a `fetchFn("")` para cargar items iniciales.
- En cada cambio del input, llama a `fetchFn(query)` con debounce de 300ms.
- Muestra los resultados en `DataTable` con las `columns` provistas.
- Al hacer clic en una fila, ejecuta `onSelect` y cierra el dialogo.
- Muestra `Alert` en caso de error y `emptyMessage` si no hay resultados.
- El input tiene icono de lupa y placeholder configurable.

### Migracion

1. Crear `apps/web/src/shared/ui/search-dialog.tsx`.
2. Migrar `ProductSearchDialog` (stock, productos) para usar `SearchDialog`.
3. Eliminar `apps/web/src/components/ProductSearchDialog.tsx`.
4. Migrar `CustomerSearchDialog` (logistics) para usar `SearchDialog`.
5. Eliminar `plugins/crm/frontend/components/CustomerSearchDialog.tsx`.

### Dependencias

- `@tanstack/react-table` (ya existe via `DataTable`).
- `Input`, `DataTable`, `Dialog`, `Alert` de `shared/ui/` (ya existen).

### Futuro

Cuando `packages/ui/` exista como paquete publicable, todo `shared/ui/` se mueve alli incluyendo `SearchDialog`. Ese es un ADR separado.

## Consecuencias

**Positivas:**
- Unifica el patron de busqueda en todos los plugins.
- Reduce duplicacion de codigo (2 implementaciones → 1).
- Facilita crear nuevos buscadores en plugins nuevos.
- Consolida la dependencia inversa existente en un solo lugar claro.

**Negativas:**
- Cambio en todos los lugares que usan `ProductSearchDialog` y `CustomerSearchDialog`.
- `SearchDialog` queda en `apps/web/` en lugar de `packages/ui/`, lo cual es un compromiso temporal.

**Riesgos:**
- Si `SearchDialog` se vuelve demasiado complejo por querer cubrir todos los casos, pierde su valor generico. Mitigacion: mantenerlo minimalista y extender solo cuando haya 3+ casos de uso.
- La dependencia inversa plugins → `apps/web/src/shared/ui/` persiste. Mitigacion: resolver con `packages/ui/` en un ADR futuro.

## Referencias

- ADR 0002: Arquitectura monorepo
- ADR 0004: Runtime plugins
- `apps/web/src/components/ProductSearchDialog.tsx`
- `plugins/crm/frontend/components/CustomerSearchDialog.tsx`
