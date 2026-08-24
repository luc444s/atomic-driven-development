# A.SPEC LOGI-0016 — Combobox: tope de resultados renderizados (maxResults)

> Cambio IMPLEMENTADO. El componente `Combobox` (shell) filtra sobre el array
> completo de `options` sin límite y renderiza TODOS los coincidentes en el
> dropdown (solo hay scroll `max-h-60`). Con catálogos grandes (productos/gases)
> el buscador muestra cientos de resultados ("demasiados resultados"). Se
> agrega un tope `maxResults` (default 50) y un aviso cuando se recorta.

## WHY

El usuario ve "demasiados resultados" en el buscador de productos del combobox.
Causa raíz: `filteredOptions` (`combobox.tsx`) no tiene tope; con query vacío
devuelve `options` completo y, al escribir, devuelve todos los coincidentes.
Los combobox de producto reciben el catálogo entero como `options` y filtran en
cliente, así que el dropdown lista cientos de ítems.

## WHAT

- `vendor/systutor-shell/src/ui/combobox.tsx`:
  - Nuevo prop `maxResults?: number` (default `50`) en `ComboboxProps`.
  - Nuevo memo `visibleOptions = filteredOptions.slice(0, maxResults)`.
  - Render, navegación por teclado y `highlightedIndex` usan `visibleOptions`
    (no `filteredOptions`).
  - Si `filteredOptions.length > maxResults`, se muestra un pie:
    `Mostrando {visibleOptions.length} de {filteredOptions.length}`.

## SCOPE

- `vendor/systutor-shell/src/ui/combobox.tsx` (único archivo)

## OUT OF SCOPE

- No se cambia ningún llamador (los combobox de producto siguen pasando el
  catálogo; ahora se recorta en UI).
- No se cambia la búsqueda en backend (`searchProducts` ya tiene `limit`).
- Sin dependencias nuevas.

## CONTRACT

- Precondición: dropdown renderiza todos los `filteredOptions`.
- Postcondición: dropdown renderiza a lo sumo `maxResults` (50) opciones; si hay
  más, muestra aviso de recorte. Listas pequeñas (<50) no cambian.

## INVARIANTS

```yaml
invariants:
  - La opción seleccionada actual (value) MUST seguir seleccionable/visible si está en el top 50.
  - Listas con <=50 opciones MUST renderizar idéntico a antes.
  - Sin cambios de API del componente para llamadores existentes (prop opcional).
  - Sin dependencias nuevas.
```

## VERIFICATION

- `vendor/systutor-shell` `tsc --noEmit` (o apps/web `tsc --noEmit`): sin errores.
- Grep: `grep -n "maxResults\|visibleOptions" vendor/systutor-shell/src/ui/combobox.tsx` ->定义 y usos presentes.
- Runtime: abrir combobox de producto con catálogo grande -> dropdown corta en
  50 y muestra "Mostrando 50 de N".

## ROLLBACK

Reversible: `git restore` del único path. Sin migraciones ni datos.

## Change Surface

```yaml
change_surface:
  allowed:
    - vendor/systutor-shell/src/ui/combobox.tsx
  prohibited:
    - plugins/**
    - apps/web/src/features/**
    - vendor/systutor-shell/src/ui/** (otros)
```

## Blast Radius

```yaml
blast_radius:
  direct:
    - shell.ui.combobox.rendered_results
  indirect:
    - todos los Combobox del ecosistema (producto, cliente, almacén, etc.)
  must_not_affect:
    - lógica de negocio de los llamadores
    - backend
```

## Composition

```yaml
composition:
  requires_aspecs: []
  must_compose_with: []
  systemic_invariants: []
  composition_checks: []
```

## Structural Constraints

```yaml
structural_constraints:
  primary_rule: one coherent responsibility and one main reason to change
  entrypoints_must_stay_thin: true
  review_threshold_lines: 400
  extraction_threshold_lines: 600
  preferred_new_logic_locations:
    - vendor/systutor-shell/src/ui/combobox.tsx (único punto de cambio)
```

## Traceability

- Requirement: limitar resultados visibles del combobox (tope 50 + aviso)
- Commit: pendiente (asignar al integrar)
- Deployment: n/a

## Definition of Done

- [x] Objective satisfied
- [x] Scope respected
- [x] Contract satisfied
- [x] Independent falsable truth exists now
- [x] Invariants preserved
- [x] Verification passed
- [x] Rollback / compensation is honest
- [x] Composition checks passed when applicable
- [x] No unrelated changes
- [x] Structural constraints respected
- [x] Traceability established (commit pendiente de integración)
