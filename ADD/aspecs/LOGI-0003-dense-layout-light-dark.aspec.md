# A.SPEC LOGI-0003 — Apply dense layout to light and dark themes

> Cambio ya implementado y verificado. El layout denso (espaciado comprimido,
> sidebar y tablas ALV) que antes vivía solo en `.retro` ahora se aplica también
> a `light` (`:root`) y `dark` (`.dark`). El tema `retro` conserva su
> identidad de color/fuente/forma SAP; light/dark conservan sus colores y la
> tipografía moderna.

## WHY

El modo `retro` (estilo SAP GUI) tenía un layout denso que el usuario quiere
también en `light` y `dark`, pero sin forzar el azul SAP, la fuente PT Sans ni
las esquinas cuadradas en los temas modernos.

## WHAT

En `apps/web/src/index.css` se separó la densidad de la identidad retro:

- **Bloque global (light/dark/retro)**: `html { font-size: 14px }`, sidebar
  densa (nav 11px, jerarquía indentada, gaps 0.5px), tablas ALV
  (`border-collapse`, `th`/`td` borde+padding 2px/5px, zebra con
  `--surface-alt`), `.card { padding: 6px }`, y compresión de `space-y`/`space-x`
  a 2px y `p-6`/`p-5`/`p-4` a 3px.
- **Bloque solo `.retro`**: vars de color SAP, fuente PT Sans sin antialiasing,
  `border-radius:0`/`box-shadow:none`, header azul, `th` azul, activo de nav
  azul, `[class*="rounded"]` padding 6px.

## SCOPE

- `apps/web/src/index.css` (sección de temas dentro de `@layer base`)

## OUT OF SCOPE

- No se cambian los colores de `:root` (light) ni `.dark`.
- No se cambia la fuente moderna en light/dark (sigue Geist/JetBrains).
- No se fuerza `border-radius:0` ni `box-shadow:none` en light/dark.
- El tema `retro` conserva su aspecto completo.

## CONTRACT

- Precondición: las variables `--sidebar`, `--surface-alt`, `--primary`,
  `--primary-foreground`, `--border` existen en los tres temas.
- Postcondición: con tema light o dark, sidebar, tablas y tarjetas se renderizan
  compactos (igual métrica que retro). El color de fondo/primario y la fuente
  siguen siendo los del tema moderno.

## INVARIANTS

```yaml
invariants:
  - light y dark MUST conservar sus colores primario/fondo definidos.
  - light y dark MUST conservar tipografía moderna (no PT Sans, no font-smoothing:none).
  - light y dark MUST conservar esquinas redondadas y sombras (sin border-radius:0 / box-shadow:none).
  - retro MUST seguir idéntico a antes (azul SAP, PT Sans, cuadrado).
```

## VERIFICATION

- Inspección del CSS: el bloque global ya no está prefijado por `.retro`; el
  bloque `.retro` conserva color/fuente/forma.
- Grep: `grep -n "retro" apps/web/src/index.css` -> solo en el bloque de
  identidad retro y en `html.retro`.
- Recarga en navegador (Vite HMR) con tema light y dark: sidebar/tablas/cards
  se ven densos; colores y fuentes modernas intactas.

## ROLLBACK

Reversible con `git restore apps/web/src/index.css`. Sin migraciones ni datos.

## Change Surface

```yaml
change_surface:
  allowed:
    - apps/web/src/index.css
  prohibited:
    - apps/web/src/features/theme/**
    - plugins/**
    - vendor/**
```

## Blast Radius

```yaml
blast_radius:
  direct:
    - web.theme.light.density
    - web.theme.dark.density
  indirect:
    - web.sidebar
    - web.tables
    - web.cards
  must_not_affect:
    - web.theme.light.colors
    - web.theme.dark.colors
    - web.theme.retro
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

- Requirement: layout denso también en light y dark (sin heredar color/fuente SAP de retro)
- Commit: pendiente
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
- [ ] Traceability established (commit pendiente)
