# A.SPEC LOGI-0009 — Nord Dark theme + lighten secondary text in Nord variants

> Cambio IMPLEMENTADO. (1) Nuevo tema `nord_dark`: variante más oscura de Nord
> (background/sidebar bajan a 17% L) sobre la misma plantilla. (2) En `nord` y
> `nord_dark` se aclara el texto secundario (`mutedForeground`, `sidebarMuted`)
> porque a 36%/73% de luminosidad se fusionaba con el fondo.

## WHY

- El usuario quiere un Nord aún más oscuro (`nord_dark`) para entornos de bajo
  brillo.
- En `nord`, `mutedForeground`/`sidebarMuted` estaban en `220 16% 36%`: sobre
  fondo `220 16% 22%` la diferencia de luminosidad (~14 puntos) fusionaba las
  letras secundarias con el fondo. Pedido explícito: secundarias más claras en
  ambos Nord.

## WHAT

- Nuevo `apps/web/src/features/theme/tokens/nord_dark.ts`:
  - `export const nord_dark: ThemeTokens` = Nord con superficies más hundidas:
    `background 219 19% 17%`, `sidebar 219 19% 17%`, `card/muted/surface
    220 16% 22%`, `surfaceAlt/secondary 222 16% 28%`, `accent/border/input
    220 17% 32%`, `foreground 218 2% 92%` (más brillante), `primary 193 16% 67%`,
    `destructive 354 23% 56%`.
  - Texto secundario ya claro: `mutedForeground 218 8% 73%`,
    `sidebarMuted 218 8% 73%` (contraste alto sobre fondo 17%).
  - Mismos overrides estructurales que `nord`: `radius:"2px"`,
    `enforceRadius/enforceShadow:"none"`, `tableBorder:"none"`,
    `tableZebra:"surface-alt"`, `tableBorderCollapse:"separate"`,
    `tableHeaderBg:"none"`, `headerStyle/sidebarActiveStyle:"primary"`.
- `apps/web/src/features/theme/tokens/nord.ts`: `mutedForeground` y
  `sidebarMuted` de `220 16% 36%` → `218 7% 67%` (secundarias legibles).
- `types.ts`: `ThemeName` añade `"nord_dark"`.
- `index.ts`: importa `nord_dark`, lo agrega a `themes` y `THEME_NAMES`.
- `theme-toggle.tsx`: label `nord_dark: "Nord Dark"`.

## SCOPE

- `apps/web/src/features/theme/tokens/nord_dark.ts` (nuevo)
- `apps/web/src/features/theme/tokens/nord.ts` (aclara secundarias)
- `apps/web/src/features/theme/tokens/types.ts`
- `apps/web/src/features/theme/tokens/index.ts`
- `apps/web/src/shared/layout/theme-toggle.tsx`

## OUT OF SCOPE

- No se toca `apply-tokens.ts` (itera `themes` dinámico).
- No se toca `store.ts`.
- `light`/`dark`/`retro`/`catpuccin_mocha` NO cambian (catpuccin ya tiene
  secundarias claras en 72% L, fuera de alcance).
- Sin dependencias nuevas.

## CONTRACT

- Precondición: plantilla por archivo (LOGI-0006) + `nord` ya existe (LOGI-0008).
- Postcondición: `nord_dark` disponible en el selector, aplica `html.nord_dark`,
  emite `.nord_dark{...}` con 26 vars + overrides. En `nord`, el texto
  secundario es claramente legible sobre el fondo.

## INVARIANTS

```yaml
invariants:
  - nord_dark MUST exportar ThemeTokens completo (mismas claves).
  - nord MUST seguir cumpliendo ThemeTokens tras aclarar secundarias.
  - CSS de light/dark/retro/catpuccin_mocha MUST quedar idéntico (no tocados).
  - apply-tokens.ts y store.ts MUST seguir sin cambios de API.
  - Sin dependencias nuevas.
```

## VERIFICATION

- `apps/web` `tsc --noEmit`: sin errores nuevos.
- `THEME_NAMES` incluye `nord_dark`; `themes.nord_dark` definido.
- `nord.ts`: `mutedForeground`/`sidebarMuted` == `218 7% 67%`.
- Runtime: `document.getElementById('systutor-theme-tokens').textContent`
  contiene `.nord_dark {` y `.nord {` con secundarias claras.
- Toggle: Nord Dark más oscuro; texto secundario de Nord legible (no fusionado).

## ROLLBACK

Reversible: `git restore` de los 5 paths. Sin migraciones ni datos.

## Change Surface

```yaml
change_surface:
  allowed:
    - apps/web/src/features/theme/tokens/nord_dark.ts
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
    - web.theme.nord_dark
    - web.theme.nord (solo secundarias)
  indirect:
    - web.theme.selector (nuevo option)
    - web.components (bajo html.nord / html.nord_dark)
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
    - LOGI-0008  # tema nord base
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
    - apps/web/src/features/theme/tokens/nord_dark.ts
```

## Traceability

- Requirement: Nord Dark (más oscuro) + secundarias legibles en Nord
- Commit: pendiente (asignar al integrar)
- Deployment: n/a
- Pendiente: `catpuccin_mocha` (LOGI-0008) aún sin A.SPEC propio -> sugerir
  LOGI-0010 para trazabilidad completa.

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
