# A.SPEC LOGI-0006 — One file per theme (split tokens.ts into atomic theme modules)

> Cambio propuesto (aún NO implementado). Refactor estructural sobre
> `LOGI-0005`: dividir `apps/web/src/features/theme/tokens.ts` (que hoy contiene
> los tres temas en un solo objeto `themes`) en un módulo por tema, de modo que
> cada tema sea un archivo físico independiente y editarlo no toque los otros.

## WHY

`LOGI-0005` logró que todo el tema viva en TS, pero los tres temas conviven en
un único `tokens.ts`. El usuario quiere **atomicidad física**: un archivo por
tema, para que la fuente de `dark` esté aislada de `light` y `retro` (edición,
review y rollback por tema, sin cruzar archivos).

## WHAT

- Nuevo dir `apps/web/src/features/theme/tokens/`.
- `tokens/types.ts`:
  - `export type ThemeName`
  - `export type ThemeTokens` (la forma completa de `LOGI-0005`, incluye
    `sidebarActiveStyle`).
- `tokens/light.ts`: `export const light: ThemeTokens = { ... }` (valores
  actuales de light, sin overrides estructurales).
- `tokens/dark.ts`: `export const dark: ThemeTokens = { ... }` (gris casi negro
  por LOGI-0004, sin overrides estructurales).
- `tokens/retro.ts`: `export const retro: ThemeTokens = { ... }` (SAP completo:
  PT Sans, radios 0, sombras none, header/tablas primarios, sidebar denso).
- `tokens/index.ts`:
  - `import { light } from "./light";` etc.
  - `export const themes: Record<ThemeName, ThemeTokens> = { light, dark, retro };`
  - `export const THEME_NAMES: ThemeName[] = ["dark", "light", "retro"];`
- Borrar `apps/web/src/features/theme/tokens.ts` (reemplazado por el dir).
- `apps/web/src/features/theme/apply-tokens.ts`: el import cambia de
  `./tokens` (archivo) a `./tokens` (directorio → `tokens/index.ts`). La ruta de
  import `./tokens` sigue resolviendo al index, así que `apply-tokens.ts` y
  `store.ts` NO requieren cambio de import más allá de que el módulo ahora es
  un directorio.

## SCOPE

- `apps/web/src/features/theme/tokens/` (nuevo directorio, 5 archivos)
- Borrado de `apps/web/src/features/theme/tokens.ts`

## OUT OF SCOPE

- No se cambia ningún valor de tema (se migran tal cual desde `LOGI-0005`).
- No se toca `apply-tokens.ts` (lógica de generación/injección igual).
- No se toca `store.ts` (sigue importando `injectThemeTokens` de `./apply-tokens`).
- No se toca `index.css`.

## CONTRACT

- Precondición: `LOGI-0005` ya centraliza el tema en `tokens.ts` con
  `themes: Record<ThemeName, ThemeTokens>`.
- Postcondición: cada tema vive en su propio archivo; `themes` se recompone en
  `tokens/index.ts` manteniendo la misma forma y valores. El runtime (CSS
  inyectado) es idéntico al de `LOGI-0005`.

## INVARIANTS

```yaml
invariants:
  - Cada archivo de tema MUST exportar un ThemeTokens completo (mismas claves).
  - El CSS inyectado en runtime MUST ser byte-a-byte idéntico al de LOGI-0005 (mismos valores).
  - apply-tokens.ts y store.ts MUST seguir funcionando sin cambios de API.
  - Sin dependencias nuevas.
```

## VERIFICATION

- `apps/web` `tsc --noEmit`: sin errores nuevos.
- `grep -rn "from \"./tokens\"" apps/web/src/features/theme` resuelve al dir
  `tokens/index.ts`.
- Runtime: `buildThemeStylesheet()` produce idéntico CSS que en `LOGI-0005`
  (mismos selectores y valores). Toggle light/dark/retro idéntico.
- `ls apps/web/src/features/theme/tokens/` -> `types.ts`, `light.ts`,
  `dark.ts`, `retro.ts`, `index.ts`; `tokens.ts` ya no existe.

## ROLLBACK

Reversible: `git restore` de los paths (recrear `tokens.ts`, borrar dir). Sin
migraciones ni datos.

## Change Surface

```yaml
change_surface:
  allowed:
    - apps/web/src/features/theme/tokens/
    - apps/web/src/features/theme/tokens.ts (borrado)
  prohibited:
    - apps/web/src/features/theme/apply-tokens.ts
    - apps/web/src/features/theme/store.ts
    - apps/web/src/index.css
    - plugins/**
    - vendor/**
```

## Blast Radius

```yaml
blast_radius:
  direct:
    - web.theme.tokens.module_layout
  indirect:
    - web.theme.tokens.source
  must_not_affect:
    - web.theme.injection
    - web.theme.runtime_css
    - theme switching API
```

## Composition

```yaml
composition:
  requires_aspecs:
    - LOGI-0005
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
    - apps/web/src/features/theme/tokens/<theme>.ts (fuente unica de cada tema)
```

## Traceability

- Requirement: un archivo fisico por tema (atomicidad de edicion/review/rollback)
- Commit: 889786a — "LOGI-0006: split theme tokens into one file per theme"
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
- [x] Traceability established
