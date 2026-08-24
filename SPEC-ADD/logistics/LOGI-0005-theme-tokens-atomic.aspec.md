# A.SPEC LOGI-0005 — TS theme tokens: every visual aspect is a per-theme atomic source

> Cambio propuesto (aún NO implementado). Refactor estructural de theming:
> mover TODO lo relativo a la apariencia de los temas (paleta, tipografía,
> espaciado/separaciones, radios, sombras, botones, tablas, header) de
> `index.css` a un módulo TS de tokens donde cada tema (light/dark/retro) es un
> objeto completo e independiente. Un generador emite las variables CSS y las
> reglas de override por tema en runtime. Una sola fuente editable por tema;
> cambiar un tema no afecta a los otros (atomicidad entre temas).

## WHY

Hoy los temas viven como bloques `:root` / `.dark` / `.retro` en
`apps/web/src/index.css` (paleta) más reglas estructurales de `.retro`
(fuente PT Sans, `border-radius:0`, `box-shadow:none`, header azul, `th` azul,
tablas ALV, sidebar denso). Cada ajuste implica editar CSS crudo y a menudo
commits de rollback (LOGI-0003). No hay fuente única ni garantía de que los
temas definan lo mismo. El usuario quiere poder modificar tablas, botones,
separaciones, márgenes y letras por tema, sin tocar CSS.

## WHAT

- Nuevo `apps/web/src/features/theme/tokens.ts`:
  - `type ThemeTokens`: UNA forma con TODOS los aspectos:
    - Paleta (26 vars): `colorScheme`, `background`, `foreground`, `card`,
      `cardForeground`, `popover`, `popoverForeground`, `primary`,
      `primaryForeground`, `secondary`, `secondaryForeground`, `muted`,
      `mutedForeground`, `accent`, `accentForeground`, `destructive`,
      `destructiveForeground`, `border`, `input`, `ring`, `sidebar`,
      `sidebarForeground`, `sidebarMuted`, `surface`, `surfaceAlt`, `radius`,
      `cardShadow`.
    - Tipografía: `fontFamily`, `fontSmoothing`
      (`"antialiased" | "none" | "inherit"`), `baseFontSize`,
      `moduleTitleTransform` (`"uppercase" | "none"`), `moduleTitleSize`,
      `moduleTitleWeight`.
    - Espaciado/separaciones (override de utilidades Tailwind; `""` = no
      override, usa default): `spaceY`, `spaceX`, `cardPadding`,
      `sectionPadding`, `sidebarItemPadding`, `sidebarIndent`.
    - Radios/sombras: `enforceRadius` (`"full" | "none"`), `enforceShadow`
      (`"full" | "none"`).
    - Botones: `buttonRadius`, `buttonPadding` (`""` = no override).
    - Tablas: `tableFontSize`, `tableCellPadding`, `tableBorder`
      (`"bordered" | "none"`), `tableBorderCollapse` (`"collapse" | "separate"`),
      `tableHeaderBg` (`"primary" | "themed" | "none"`), `tableZebra`
      (`"surface-alt" | "none"`).
    - Header: `headerStyle` (`"primary" | "themed"`).
    - Sidebar activo: `sidebarActiveStyle` (`"primary" | "themed"`).
  Nota: reglas de override SOLO se emiten cuando el campo difiere del default
  de Tailwind (p.ej. `tableBorderCollapse:"separate"` no emite regla; light/dark
  quedan sin `!important` y sin reglas de tabla). `aside { background: var(--sidebar) }`
  se emite para los tres (usa la variable de paleta, mismo valor que Tailwind).
  - `themes: Record<ThemeName, ThemeTokens>` con `light`, `dark`, `retro`
    COMPLETOS e independientes. light/dark usan `""` / `"inherit"` / `"themed"`
    / `"full"` en los campos estructurales (NO emiten override; conservan
    defaults de Tailwind). `retro` usa los valores SAP (PT Sans, radios 0,
    sombras none, header primario, th primario, tablas ALV densas).
  - `THEME_NAMES` para orden de ciclo.
- Nuevo `apps/web/src/features/theme/apply-tokens.ts`:
  - `buildThemeStylesheet()`: por cada tema emite:
    1. bloque `:root{...}` (light) / `.dark{...}` / `.retro{...}` con las 26
       variables de paleta.
    2. reglas de override SOLO para los campos no-default, todas con
       `!important` y prefijadas por el selector del tema, p.ej.:
       - `fontFamily` → `.retro * { font-family: ... !important }`
       - `fontSmoothing==="none"` → `-webkit-font-smoothing: none !important`
       - `baseFontSize` → `html.retro { font-size: ... }`
       - `spaceY` → `.retro [class*="space-y"] > :not([hidden]) ~ :not([hidden]) { margin-top: X !important }`
       - `enforceRadius==="none"` → `.retro * { border-radius: 0 !important }`
       - `enforceShadow==="none"` → `.retro * { box-shadow: none !important }`
       - `buttonRadius`/`buttonPadding` → `.retro button { ... !important }`
       - `table*` → `.retro table/th/td/tbody tr:nth-child(even) { ... }`
       - `headerStyle==="primary"` → `.retro header { background: var(--primary); color: var(--primary-foreground) }`
  - `injectThemeTokens()`: crea/actualiza `<style id="systutor-theme-tokens">`
    en `document.head`.
- `apps/web/src/features/theme/store.ts`: al init, llama `injectThemeTokens()`.
- `apps/web/src/index.css`: se **eliminan** los bloques de variables
  `:root`/`.dark`/`.retro` y TODAS las reglas estructurales de `.retro`
  (fuente, radios, sombras, header, nav, tablas, cards, padding). Solo queda
  lo común base (`body`, `#root`, `* { box-border }`, fuentes base). Tema =
  TS puro.

## SCOPE

- `apps/web/src/features/theme/tokens.ts` (nuevo)
- `apps/web/src/features/theme/apply-tokens.ts` (nuevo)
- `apps/web/src/features/theme/store.ts` (usa inject en init)
- `apps/web/src/index.css` (borrar bloques de variables y reglas `.retro` estructurales)

## OUT OF SCOPE

- No se cambia ningún valor actual: se migran tal cual (light azul claro,
  dark gris casi negro por LOGI arc, retro azul SAP con su densidad).
- No se toca el switcher de tema ni `ThemeName`.
- No se cambia la API del store ni componentes consumidores.
- Sin Lua, sin dependencias nuevas (TS + DOM API).

## CONTRACT

- Precondición: el app consume variables CSS y utilidades Tailwind; `<html>`
  recibe clases `dark`/`retro`.
- Postcondición: TODA la apariencia de tema se define en `tokens.ts` y se
  inyecta en runtime. light/dark renderizan idénticos al estado actual
  (sin overrides emitidos). `retro` renderiza idéntico al actual (mismos
  overrides emitidos desde tokens). Cambiar `themes.dark` no altera los otros.

## INVARIANTS

```yaml
invariants:
  - Los tres temas MUST definir EXACTAMENTE las mismas claves (Record<ThemeName, ThemeTokens> lo fuerza en tsc).
  - Render final MUST ser idéntico al estado previo al refactor (mismos valores migrados).
  - light/dark/retro MUST conmutar via clases en <html> (API de store sin cambios).
  - Sin dependencias nuevas en package.json.
  - El override usa !important y va prefijado por el selector del tema (nunca global sin prefijo).
```

## VERIFICATION

- `apps/web` `tsc --noEmit`: sin errores (los tres temas cumplen `ThemeTokens`).
- Runtime: `document.getElementById('systutor-theme-tokens').textContent`
  contiene `:root{...}`, `.dark{...}`, `.retro{...}` con las 26 vars + reglas
  de override solo para `retro`.
- Grep: `grep -n "\-\-background:\|\.retro \*\|retro header\|retro table" apps/web/src/index.css` -> sin coincidencias.
- Toggle en navegador: light/dark/retro idénticos al estado previo.

## ROLLBACK

Reversible: `git restore` de los 4 paths (tokens/apply-tokens se borran, store
vuelve a no inyectar, index.css recupera bloques). Sin migraciones ni datos.

## Change Surface

```yaml
change_surface:
  allowed:
    - apps/web/src/features/theme/tokens.ts
    - apps/web/src/features/theme/apply-tokens.ts
    - apps/web/src/features/theme/store.ts
    - apps/web/src/index.css
  prohibited:
    - apps/web/src/features/theme/theme-toggle.tsx
    - plugins/**
    - vendor/**
    - backend
```

## Blast Radius

```yaml
blast_radius:
  direct:
    - web.theme.tokens.source
    - web.theme.injection
  indirect:
    - web.theme.light
    - web.theme.dark
    - web.theme.retro
    - web.components (consumen vars + Tailwind)
  must_not_affect:
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
  preferred_new_logic_locations:
    - apps/web/src/features/theme/tokens.ts (única fuente de tema)
    - apps/web/src/features/theme/apply-tokens.ts (solo genera CSS desde tokens)
```

## Traceability

- Requirement: todo el tema (color, tipografia, espaciado, botones, tablas, radios, sombras) configurable por tema en TS, sin editar CSS
- Commit: 08b2040 — "LOGI-0005: move all theme aspects to atomic TS tokens (no CSS editing)"
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
