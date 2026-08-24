# A.SPEC LOGI-0015 — Add Catppuccin Mocha theme (atomic per-file token)

> Cambio IMPLEMENTADO (retroactivo). Nuevo tema `catpuccin_mocha` basado en la
> paleta Catppuccin Mocha (oscuro), siguiendo la plantilla de tokens por
> archivo. Se registra en `ThemeName`, `themes`, `THEME_NAMES` y el selector.
> Se crea este A.SPEC para dar trazabilidad al código ya añadido en sesión.

## WHY

El usuario quiere un tema Catppuccin Mocha (oscuro, sin líneas en tablas,
diferencias por tono, radio mínimo 2px, sin sombras). Se creó el archivo de
tokens y su registro; este A.SPEC documenta y traza ese cambio.

## WHAT

- Nuevo `apps/web/src/features/theme/tokens/catpuccin_mocha.ts`:
  - `export const catpuccin_mocha: ThemeTokens` con paleta Catppuccin Mocha en
    HSL (`background 240 21% 15%`, `foreground 226 8% 88%`,
    `primary 267 19% 81%`, `destructive 343 26% 75%`, `surface 237 16% 23%`,
    `surfaceAlt 234 20% 20%`, etc.).
  - Overrides estructurales: `radius:"2px"`, `cardShadow:"0 0 0 0 transparent"`,
    `enforceRadius:"none"`, `enforceShadow:"none"`, `tableBorder:"none"`,
    `tableZebra:"surface-alt"`, `tableBorderCollapse:"separate"`,
    `tableHeaderBg:"none"`, `headerStyle:"primary"`,
    `sidebarActiveStyle:"primary"`.
  - `...NO_OVERRIDE` para el resto.
- `apps/web/src/features/theme/tokens/types.ts`: `ThemeName` añade
  `"catpuccin_mocha"`.
- `apps/web/src/features/theme/tokens/index.ts`: importa `catpuccin_mocha`,
  lo agrega a `themes` y `THEME_NAMES`.
- `apps/web/src/shared/layout/theme-toggle.tsx`: label
  `catpuccin_mocha: "Catppuccin Mocha"`.
- `apps/web/src/features/theme/store.ts`: selector dinámico ya iteraba
  `THEME_NAMES` (cambio previo de la misma sesión).

## SCOPE

- `apps/web/src/features/theme/tokens/catpuccin_mocha.ts` (nuevo)
- `apps/web/src/features/theme/tokens/types.ts`
- `apps/web/src/features/theme/tokens/index.ts`
- `apps/web/src/shared/layout/theme-toggle.tsx`

## OUT OF SCOPE

- No se toca `apply-tokens.ts`.
- No se cambian los demás temas.
- Sin dependencias nuevas.

## CONTRACT

- Precondición: plantilla por archivo (LOGI-0006) existe.
- Postcondición: `catpuccin_mocha` disponible en el selector, aplica
  `html.catpuccin_mocha`, emite `.catpuccin_mocha{...}` con 26 vars + overrides.

## INVARIANTS

```yaml
invariants:
  - catpuccin_mocha MUST exportar ThemeTokens completo.
  - CSS de light/dark/retro/nord/nord_dark MUST quedar idéntico.
  - apply-tokens.ts y store.ts MUST seguir sin cambios de API.
  - Sin dependencias nuevas.
```

## VERIFICATION

- `apps/web` `tsc --noEmit`: sin errores nuevos.
- `THEME_NAMES` incluye `catpuccin_mocha`; `themes.catpuccin_mocha` definido.
- Runtime: `document.getElementById('systutor-theme-tokens').textContent`
  contiene `.catpuccin_mocha {` con las 26 vars + overrides.

## ROLLBACK

Reversible: `git restore` de los paths. Sin migraciones ni datos.

## Change Surface

```yaml
change_surface:
  allowed:
    - apps/web/src/features/theme/tokens/catpuccin_mocha.ts
    - apps/web/src/features/theme/tokens/types.ts
    - apps/web/src/features/theme/tokens/index.ts
    - apps/web/src/shared/layout/theme-toggle.tsx
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
    - web.theme.tokens.source
    - web.theme.catpuccin_mocha
  indirect:
    - web.theme.selector (nuevo option)
  must_not_affect:
    - otros temas
    - theme switching API
    - backend
```

## Composition

```yaml
composition:
  requires_aspecs:
    - LOGI-0006  # un archivo por tema
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
    - apps/web/src/features/theme/tokens/catpuccin_mocha.ts
```

## Traceability

- Requirement: tema Catppuccin Mocha oscuro, sin líneas, radio 2px
- Commit: pendiente (asignar al integrar, junto a LOGI-0008/0009/0014)
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
