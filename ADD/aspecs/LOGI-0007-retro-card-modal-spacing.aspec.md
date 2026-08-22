# A.SPEC LOGI-0007 — Retro: +15px de margen en cards principales y modales

> Cambio ya implementado y verificado. En el tema `retro` se aumenta el
> espaciado de las cards principales y los modales para que no se sientan
> tan juntos. Solo afecta `retro`; light/dark quedan igual.

## WHY

El usuario indicó que en modo `retro` las cards principales y los modales se
sientan "muy juntos" (muy comprimidos). El retro usa `cardPadding: 6px` y
`sectionPadding: 3px` (muy denso). Se pidió +15px, pero resultó excesivo; se
ajusta a **+5px**, solo para retro.

## WHAT

En `apps/web/src/features/theme/tokens/retro.ts`:
- `cardPadding`: `"6px"` → `"11px"` (+5px a las cards `.card`).
- `sectionPadding`: `"3px"` → `"8px"` (+5px a `p-4`/`p-5`/`p-6`, incluye el
  contenido y footer de los modales `Dialog` que usan `p-5`).

Nota: `cardPadding`/`sectionPadding` NO afectan el sidebar (`aside` usa
`aside nav`, no `.card` ni `p-*`). El sidebar de retro queda igual.

## SCOPE

- `apps/web/src/features/theme/tokens/retro.ts` (2 valores)

## OUT OF SCOPE

- light y dark: sin cambios (siguen en `""`/default Tailwind).
- No se toca `light.ts`/`dark.ts`/`types.ts`/`index.ts`/`apply-tokens.ts`.
- No se cambia otro aspecto de retro (fuente, radios, tablas, header).

## CONTRACT

- Postcondición: en `retro`, `.card` tiene 21px de padding y los modales
  (`p-5`) tienen 18px. En light/dark el render es idéntico al previo.

## INVARIANTS

```yaml
invariants:
  - light y dark MUST quedar idénticos al estado de LOGI-0006.
  - Solo retro MUST cambiar (atomicidad de tema).
  - El generador/inyeccion MUST seguir igual.
```

## VERIFICATION

- tsc: sin errores nuevos.
- `buildThemeStylesheet()` para retro incluye `.retro .card { padding: 11px !important; }`
  y `.retro [class*="p-5"] { padding: 8px !important; }`.
- light/dark: sin `!important` en cards/modales (sin cambio).
- Sidebar de retro: sin cambio (no usa `.card` ni `p-*`).

## ROLLBACK

Reversible con `git restore apps/web/src/features/theme/tokens/retro.ts`. Sin
migraciones ni datos.

## Change Surface

```yaml
change_surface:
  allowed:
    - apps/web/src/features/theme/tokens/retro.ts
  prohibited:
    - apps/web/src/features/theme/tokens/light.ts
    - apps/web/src/features/theme/tokens/dark.ts
    - apps/web/src/features/theme/tokens/types.ts
    - apps/web/src/features/theme/apply-tokens.ts
```

## Blast Radius

```yaml
blast_radius:
  direct:
    - web.theme.retro.card_spacing
    - web.theme.retro.modal_spacing
  indirect: []
  must_not_affect:
    - web.theme.light
    - web.theme.dark
    - web.theme.retro.other_aspects
```

## Composition

```yaml
composition:
  requires_aspecs:
    - LOGI-0005
    - LOGI-0006
  must_compose_with: []
  systemic_invariants: []
  composition_checks: []
```

## Structural Constraints

```yaml
structural_constraints:
  primary_rule: one coherent responsibility and one main reason to change
  entrypoints_must_stay_thin_after: true
  review_threshold_lines: 400
  extraction_threshold_lines: 600
  preferred_new_logic_locations:
    - apps/web/src/features/theme/tokens/retro.ts
```

## Traceability

- Requirement: +15px margen en cards y modales, solo retro
- Commit: 25c2253 — "LOGI-0007: retro +15px margin on cards and modales"
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
- [x] Traceability established (commit pendiente)
