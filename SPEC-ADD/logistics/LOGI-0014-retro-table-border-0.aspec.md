# A.SPEC LOGI-0014 — Retro: grosor de borde de tabla en 0

> Cambio IMPLEMENTADO. En el tema `retro`, las tablas usaban borde de 1px
> (`tableBorder: "bordered"` -> `apply-tokens.ts` emite `th, td { border: 1px
> solid hsl(var(--border)) }`). El usuario pide grosor 0, así que se desactiva
> el borde de tabla en retro (`tableBorder: "none"`).

## WHY

El usuario pregunta el grosor de borde de columnas en retro (1px) y pide
ponerlo en 0. Equivale a quitar el borde de tabla en retro, alineándolo con
los demás temas (catppuccin/nord ya usan `tableBorder: "none"`).

## WHAT

- `apps/web/src/features/theme/tokens/retro.ts`:
  - `tableBorder` de `"bordered"` → `"none"`.
  - `tableZebra: "surface-alt"` y `tableBorderCollapse: "collapse"` se
    conservan (el zebra sigue dando diferenciación por tono, sin líneas).

## SCOPE

- `apps/web/src/features/theme/tokens/retro.ts`

## OUT OF SCOPE

- No se cambia `apply-tokens.ts` (la regla de borde solo se emite si
  `tableBorder === "bordered"`; con `"none"` no emite nada).
- No se cambian los demás temas.
- Sin dependencias nuevas.

## CONTRACT

- Precondición: retro emite `th, td { border: 1px solid hsl(var(--border)) }`.
- Postcondición: retro NO emite regla de borde de tabla (grosor 0 implícito);
  las celdas se diferencian por zebra `surface-alt`.

## INVARIANTS

```yaml
invariants:
  - Los demás temas MUST quedar sin cambios.
  - apply-tokens.ts MUST seguir sin cambios de API.
  - Sin dependencias nuevas.
```

## VERIFICATION

- `apps/web` `tsc --noEmit`: sin errores nuevos.
- Grep: `grep -n "tableBorder" apps/web/src/features/theme/tokens/retro.ts` ->
  `tableBorder: "none"`.
- Runtime: `document.getElementById('systutor-theme-tokens').textContent` no
  contiene `th, .retro td { border:` con 1px para retro; tablas retro sin
  bordes, con zebra.

## ROLLBACK

Reversible: `git restore` del único path. Sin migraciones ni datos.

## Change Surface

```yaml
change_surface:
  allowed:
    - apps/web/src/features/theme/tokens/retro.ts
  prohibited:
    - apps/web/src/features/theme/apply-tokens.ts
    - apps/web/src/features/theme/store.ts
    - plugins/**
    - vendor/**
```

## Blast Radius

```yaml
blast_radius:
  direct:
    - web.theme.retro.table.border
  indirect:
    - web.theme.retro (vista de tablas)
  must_not_affect:
    - otros temas
    - theme switching API
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
  preferred_new_logic_locations: []
```

## Traceability

- Requirement: borde de tabla de retro en grosor 0
- Commit: pendiente (asignar al integrar)
- Deployment: n/a
- Pendiente: `catpuccin_mocha` (LOGI-0008) aún sin A.SPEC propio -> sugerir
  LOGI-0015 para trazabilidad completa.

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
