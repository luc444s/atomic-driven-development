# A.SPEC LOGI-0004 — Dark theme to neutral near-black gray (no blue)

> Cambio ya implementado y verificado. El tema `dark` (`.dark`) dejó de usar
> tonos azules (hue ~222) y pasa a gris neutro casi negro (hue 0), conservando
> el primario turquesa como acento.

## WHY

El usuario pidió que el modo oscuro sea "gris muy oscuro, casi negro, no azul".
El bloque `.dark` original usaba hue 222/214/217/215 (azulado) en fondo,
tarjetas, sidebar, bordes y superficies, dando un tono azulado en lugar de
gris neutro.

## WHAT

En `apps/web/src/index.css`, bloque `.dark`: se cambiaron todas las variables
neutras de hue azulado a `0 0%` (gris puro) con luminancias cercanas a negro:

- `--background` / `--sidebar` / `--surface` / `--card` / `--popover`:
  gris muy oscuro (4%-7%).
- `--foreground` / `--card-foreground` / etc.: gris claro (90%).
- `--secondary` / `--muted` / `--accent` / `--surface-alt`: grises medios
  (12%-14%).
- `--border` / `--input`: grises (16%-22%).
- `--muted-foreground` / `--sidebar-muted`: gris (55%).

Se mantuvo `--primary` turquesa `187 85% 53%` (y `--ring`) como acento de marca,
y `--primary-foreground` en casi negro para contraste sobre el primario.

## SCOPE

- `apps/web/src/index.css` (solo bloque `.dark`)

## OUT OF SCOPE

- `:root` (light) sin cambios.
- `.retro` sin cambios.
- Variables de primario/marca: se conserva turquesa.

## CONTRACT

- Postcondición: con tema `dark`, el fondo y superficies son gris neutro casi
  negro (sin tinte azul). El acento primario sigue siendo turquesa.

## INVARIANTS

```yaml
invariants:
  - light (:root) MUST quedar igual.
  - retro MUST quedar igual (azul SAP).
  - El primario turquesa (187 85% 53%) MUST seguir disponible como acento.
  - Contraste de texto sobre primario MUST seguir legible (foreground casi negro).
```

## VERIFICATION

- Grep: `grep -n "222\|214\|217\|215" apps/web/src/index.css` en bloque `.dark`
  -> sin coincidencias de hue azulado.
- Inspección: todas las variables neutras de `.dark` usan `0 0%`.
- Recarga en navegador con tema dark: fondo gris casi negro, sin azul.

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
    - web.theme.dark.colors
  indirect:
    - web.dark.background
    - web.dark.sidebar
  must_not_affect:
    - web.theme.light
    - web.theme.retro
    - primario/marca
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

- Requirement: modo oscuro gris casi negro, no azul
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
