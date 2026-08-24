# A.SPEC UI-THEMES-001 — Sistema de temas: un archivo .ts por tema con tokens atómicos

> Estado vigente del sistema de theming. Consolida y extiende LOGI-0005 /
> LOGI-0006 (que quedaron en el namespace logistics) al namespace UI, y
> documenta la forma actual: 6 temas en archivos independientes, 28 variables
> de paleta (incluye `success` y `warning`) inyectadas como CSS vars.

## WHY

La separación física de temas por archivo quedó documentada como LOGI-0005 /
LOGI-0006 en `SPEC-ADD/logistics/`, pero es una decisión puramente de UI, no de
logística. Desde entonces el sistema creció (temas `nord`, `nord_dark`,
`catpuccin_mocha`; tokens semánticos `success` / `warning` para badges de
estado) sin spec que describa el contrato actual. Quien agregue un tema o un
token nuevo hoy no tiene fuente normativa en UI sobre dónde tocar ni qué
archivos deben permanecer sincronizados.

## WHAT

Verdad estructural falsable ahora:

1. **Un archivo por tema** en `apps/web/src/features/theme/tokens/`:
   `light.ts`, `dark.ts`, `retro.ts`, `catpuccin_mocha.ts`, `nord.ts`,
   `nord_dark.ts`. Cada uno exporta un único objeto `ThemeTokens` completo e
   independiente — editar un tema no toca los otros.
2. **Contrato tipado** en `tokens/types.ts`: `ThemeName = "light" | "dark" |
   "retro" | "catpuccin_mocha" | "nord" | "nord_dark"` y `ThemeTokens` con:
   - Paleta de **28 vars HSL**: las 26 originales + `success` + `warning`.
   - Tipografía (`fontFamily`, `fontSmoothing`, `baseFontSize`,
     `moduleTitle*`), sidebar, espaciados (`""` = no override), radios/sombras
     (`enforceRadius` / `enforceShadow`), tablas, header, botones.
3. **Registro** en `tokens/index.ts`: `themes: Record<ThemeName, ThemeTokens>`
   + `THEME_NAMES`. Agregar un tema = crear su `.ts` + registrarlo acá + sumarlo
   a `ThemeName`. Nada más.
4. **Inyección runtime**: `apply-tokens.ts` mapea `PALETTE_KEYS` → CSS custom
   properties `--<kebab-case>` bajo `:root` (light) o `.<tema>` (resto), y emite
   reglas de override estructurales según los flags del tema. `store.ts`
   aplica/quita la clase en `documentElement`.
5. **Consumo Tailwind**: `apps/web/tailwind.config.ts` mapea los colores
   semánticos (`primary`, `secondary`, `destructive`, `success`, `warning`,
   etc.) a `hsl(var(--...))` — prohibido hardcodear paletas de Tailwind
   (`emerald-500`, `amber-100`, ...) en componentes; los estados usan tokens
   semánticos que cada tema define.

## SCOPE

- `apps/web/src/features/theme/tokens/*.ts` (6 temas + `types.ts` + `index.ts`)
- `apps/web/src/features/theme/apply-tokens.ts`
- `apps/web/src/features/theme/store.ts`
- `apps/web/tailwind.config.ts` (mapeo colores → CSS vars)

## OUT OF SCOPE

- Valores específicos de cada paleta (ver specs individuales: LOGI-0008 nord,
  LOGI-0015 catppuccin, etc.).
- Componentes UI que consumen los tokens.
- Modo de alto contraste, detección `prefers-color-scheme`.

## CONTRACT

Precondiciones:

- Todo color usado por un componente proviene de un token semántico Tailwind
  respaldado por una CSS var del tema.

Postcondiciones:

- Cambiar cualquier valor de un tema requiere tocar exactamente un archivo.
- Agregar un token nuevo a la paleta exige, en el mismo cambio: `types.ts`,
  `PALETTE_KEYS` en `apply-tokens.ts`, valor en los **6** archivos de tema, y
  mapeo en `tailwind.config.ts` si se expone como clase de color.
- Un tema incompleto (falta un key de `PALETTE_KEYS`) rompe la inyección — el
  sistema debe fallar visible, no silenciosamente.

## INVARIANTS

```yaml
invariants:
  - Ningún componente importa valores de paleta directamente; solo clases
    semánticas Tailwind.
  - Los temas no comparten estado entre archivos (atomicidad física por tema).
  - index.css NO contiene paleta; es solo base + comentario apuntando a tokens.
  - El selector de tema aplica/quita UNA clase en documentElement.
```

## VERIFICATION

- `ls apps/web/src/features/theme/tokens/` → 8 archivos (6 temas + types +
  index); no existe `tokens.ts` monolítico.
- `grep -L success apps/web/src/features/theme/tokens/{light,dark,retro,catpuccin_mocha,nord,nord_dark}.ts`
  → vacío (los 6 definen `success`).
- `cd apps/web && npx tsc --noEmit` sin errores de tipos faltantes en themes.
- Runtime: alternar temas desde el ThemeToggle cambia la paleta sin recargar;
  badges de estado ("Jornada sana", "Borrador", "Vigente") legibles en todos
  los temas.

## ROLLBACK

Reversible por git: revertir commits del directorio `tokens/`, `apply-tokens.ts`
y `tailwind.config.ts`. Sin efectos irreversibles (solo código frontend).

## Change Surface

```yaml
change_surface:
  allowed:
    - apps/web/src/features/theme/**
    - apps/web/tailwind.config.ts
  prohibited:
    - vendor/systutor-shell/** # consume tokens, no los define
    - plugins/*/frontend/**
    - apps/web/src/index.css # sin paleta
```

## Blast Radius

```yaml
blast_radius:
  direct:
    - theme.tokens
    - theme.apply-tokens
    - tailwind.colors
  indirect:
    - todos los componentes que usan clases semánticas de color
  must_not_affect:
    - lógica de negocio (backend)
    - routing / estado de app
```

## Composition

```yaml
composition:
  requires_aspecs:
    - LOGI-0005 # origen: tokens TS atómicos por tema
    - LOGI-0006 # origen: split físico un archivo por tema
  must_compose_with:
    - LOGI-0032 # badges de jornada consumen success/warning/destructive/muted
  systemic_invariants:
    - Un token nuevo existe en los 6 temas o no se mergea.
  composition_checks:
    - Toggle por cada uno de los 6 temas: app usable y badges legibles en todos.
```

## Structural Constraints

```yaml
structural_constraints:
  primary_rule: un archivo por tema; types/index compartidos mínimos
  entrypoints_must_stay_thin: true
  review_threshold_lines: 400
  extraction_threshold_lines: 600
  preferred_new_logic_locations:
    - apps/web/src/features/theme/tokens/<tema>.ts
```

## Traceability

- Requirement: solicitud del usuario — "en ui no existe la separación de temas
  en archivos .ts como spec".
- Origen histórico: LOGI-0005, LOGI-0006 (SPEC-ADD/logistics).
- Extensión de esta sesión: tokens `success` / `warning` en los 6 temas +
  tailwind.config (badges semánticos).
- Commit: `6d2284b`

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
- [x] Traceability established (commit `6d2284b`)
