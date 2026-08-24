# A.SPEC LOGI-0008 — Add Nord theme (atomic per-file token, based on Catppuccin Mocha template)

> Cambio IMPLEMENTADO. Nuevo tema `nord` siguiendo la plantilla de
> `catpuccin_mocha.ts`: mismo esqueleto `ThemeTokens` (paleta HSL + overrides
> estructurales), distinta paleta (Nord). Se registra en `ThemeName`,
> `themes`, `THEME_NAMES` y el selector.

## WHY

El usuario quiere un tema Nord (paleta fría: azul hielo, gris azulado) en la
misma base estructural que Catppuccin Mocha: oscuro, sin líneas en tablas,
diferencias por tono, radio mínimo (2px), sin sombras. Reutilizar la plantilla
garantiza consistencia con `catpuccin_mocha` y cero lógica nueva en
`apply-tokens.ts`.

## WHAT

- Nuevo `apps/web/src/features/theme/tokens/nord.ts`:
  - `export const nord: ThemeTokens` con paleta Nord convertida a HSL
    (`background 220 16% 22%`, `foreground 219 3% 88%`, `primary 193 16% 67%`,
    `destructive 354 23% 56%`, `surface 222 16% 28%`, `surfaceAlt 220 17% 32%`,
    etc.).
  - Mismos overrides que `catpuccin_mocha`: `radius:"2px"`,
    `cardShadow:"0 0 0 0 transparent"`, `enforceRadius:"none"`,
    `enforceShadow:"none"`, `tableBorder:"none"`, `tableZebra:"surface-alt"`,
    `tableBorderCollapse:"separate"`, `tableHeaderBg:"none"`,
    `headerStyle:"primary"`, `sidebarActiveStyle:"primary"`.
  - `...NO_OVERRIDE` para el resto (tipografía/switchers por default).
- `apps/web/src/features/theme/tokens/types.ts`: `ThemeName` añade `"nord"`.
- `apps/web/src/features/theme/tokens/index.ts`: importa `nord`, lo agrega a
  `themes` y a `THEME_NAMES` (al final del ciclo).
- `apps/web/src/shared/layout/theme-toggle.tsx`: label `nord: "Nord"`.

## SCOPE

- `apps/web/src/features/theme/tokens/nord.ts` (nuevo)
- `apps/web/src/features/theme/tokens/types.ts` (añade union member)
- `apps/web/src/features/theme/tokens/index.ts` (import + registro)
- `apps/web/src/shared/layout/theme-toggle.tsx` (label)

## OUT OF SCOPE

- No se toca `apply-tokens.ts` (ya itera `themes` dinámicamente).
- No se toca `store.ts` (usa `THEME_NAMES` dinámico desde LOGI previas).
- Sin cambios de valores en los temas existentes.
- Sin dependencias nuevas.

## CONTRACT

- Precondición: estructura de tokens por archivo (LOGI-0006) y selector
  dinámico ya existen; `catpuccin_mocha` ya es tema válido de referencia.
- Postcondición: `nord` aparece en el `<select>` de tema, aplica clase
  `html.nord`, e `injectThemeTokens()` emite bloque `.nord{...}` con las 26
  vars + overrides estructurales. Conmuta igual que los otros.

## INVARIANTS

```yaml
invariants:
  - nord MUST exportar ThemeTokens completo (mismas claves que los otros).
  - CSS inyectado de nord MUST usar selector `.nord` y no romper light/dark/retro/catpuccin_mocha.
  - apply-tokens.ts y store.ts MUST seguir funcionando sin cambios de API.
  - Sin dependencias nuevas en package.json.
  - El override usa !important y va prefijado por `.nord` (nunca global sin prefijo).
```

## VERIFICATION

- `apps/web` `tsc --noEmit`: sin errores nuevos.
- `THEME_NAMES` incluye `nord`; `themes.nord` definido.
- Runtime: `document.getElementById('systutor-theme-tokens').textContent`
  contiene `.nord {` con las 26 vars + reglas de override (border-radius 0,
  box-shadow none, th sin borde, tbody zebra surface-alt).
- Toggle en navegador: Nord renderiza oscuro, sin líneas de tabla, radio 2px.

## ROLLBACK

Reversible: `git restore` de los 4 paths (borra `nord.ts`, revierte union/
registro/label). Sin migraciones ni datos.

## Change Surface

```yaml
change_surface:
  allowed:
    - apps/web/src/features/theme/tokens/nord.ts
    - apps/web/src/features/theme/tokens/types.ts
    - apps/web/src/features/theme/tokens/index.ts
    - apps/web/src/shared/layout/theme-toggle.tsx
  prohibited:
    - apps/web/src/features/theme/apply-tokens.ts
    - apps/web/src/features/theme/store.ts
    - plugins/**
    - vendor/**
    - backend
```

## Blast Radius

```yaml
blast_radius:
  direct:
    - web.theme.tokens.source
    - web.theme.nord
  indirect:
    - web.theme.selector (nuevo option)
    - web.components (consumen vars + Tailwind bajo html.nord)
  must_not_affect:
    - light/dark/retro/catpuccin_mocha rendering
    - theme switching API
    - backend
```

## Composition

```yaml
composition:
  requires_aspecs:
    - LOGI-0006  # un archivo por tema
  must_compose_with:
    - catpuccin_mocha (misma plantilla, creado sin A.SPEC propio -> sugerir LOGI-0009 para trazabilidad)
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
    - apps/web/src/features/theme/tokens/nord.ts (única fuente del tema Nord)
```

## Traceability

- Requirement: tema Nord oscuro, sin líneas, mismo esqueleto que Catppuccin Mocha
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
