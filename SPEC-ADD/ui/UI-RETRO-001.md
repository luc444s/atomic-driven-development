# A.SPEC UI-RETRO-001 — Tema retro estilo SAP GUI clásico (seleccionable)

## WHY

El usuario quiere que la UI se sienta "vieja, antigua y retro" tipo SAP GUI
clásico (ECC "Enjoy"): barra de título azul, fondo gris, esquinas cuadradas,
tablas grid densas, fuente pequeña tipo Tahoma. No es S/4HANA Fiori (moderno).
Debe ser un tema **seleccionable** (light / dark / retro) sin romper los temas
actuales ni los componentes.

## WHAT

Se agrega una variante de tema `retro` al sistema de temas existente, basada
en override de tokens CSS (HSL) en `apps/web/src/index.css`, más overrides
acotados bajo la clase `.retro` para vender el look (barra de título azul,
tablas grid). La clase `retro` se aplica en `document.documentElement`, igual
que `.dark`. El `ThemeToggle` pasa a ser un selector de 3 estados.

Verdad nueva falsable ahora: con `data`/clase `retro` activa, la app renderiza
con paleta gris/Azul-SAP, `--radius: 0` (botones y tarjetas cuadrados), fuente
Tahoma 12px y la cabecera superior en azul con texto blanco; los temas light y
dark siguen idénticos.

## SCOPE

- `apps/web/src/index.css`: bloque `.retro` con tokens + reglas acotadas.
- `apps/web/src/features/theme/store.ts`: `Theme` incluye `"retro"`; `applyTheme`
  agrega/quita clase `retro`.
- `apps/web/src/shared/layout/theme-toggle.tsx`: control de 3 estados.

## OUT OF SCOPE

- Reescribir componentes de `@systutor/shell/ui`.
- Cambiar el tema por defecto (sigue `dark`).
- Tema oscuro retro.
- Migrar forms/dialogs a nuevos patrones.

## CONTRACT

Precondiciones:
- Sistema de temas light/dark funciona con clase `.dark` en `<html>`.

Postcondiciones:
- `useThemeStore` acepta `"retro"`; `applyTheme("retro")` pone clase `retro`
  y quita `dark`.
- En `retro`: `--radius == 0`, `--background` gris claro, `--primary` azul SAP,
  fuente base Tahoma ~12px, `--card-shadow` transparente.
- Cabecera `<header>` de `AppLayout` se ve azul con texto blanco en `retro`.
- light y dark inalterados (sin regresión visual).

## INVARIANTS

```yaml
invariants:
  - temas light y dark idénticos a antes (mismos tokens)
  - componentes de @systutor/shell/ui sin modificaciones
  - toggle reversible: volver a light/dark restaura look exacto
  - accesibilidad: contraste texto/botones sigue legible
```

## VERIFICATION

```bash
# build/dev del web y comprobar clases; check objetivo:
grep -n "retro" apps/web/src/index.css apps/web/src/features/theme/store.ts apps/web/src/shared/layout/theme-toggle.tsx
# chequeo de tokens retro
grep -n "\-\-radius: 0\|\-\-primary: 209\|Tahoma" apps/web/src/index.css
```

Además: revisar manualmente (o test de snapshot) que en `retro` el header es
azul y los botones cuadrados.

## ROLLBACK

Reversible: borrar bloque `.retro` de index.css, revertir store y toggle al
estado light/dark. Sin datos en juego.

## Change Surface

```yaml
change_surface:
  allowed:
    - apps/web/src/index.css
    - apps/web/src/features/theme/store.ts
    - apps/web/src/shared/layout/theme-toggle.tsx
  prohibited:
    - packages/systutor-shell/**     # ui components
    - apps/web/src/shared/ui/**
    - vendor/**
```

## Blast Radius

```yaml
blast_radius:
  direct:
    - apariencia global de la app en tema retro
  indirect:
    - ThemeToggle (ahora 3 estados)
  must_not_affect:
    - temas light/dark
    - componentes del shell
    - lógica de negocio
```

## Composition

```yaml
composition:
  requires_aspecs: []
  must_compose_with: []
  systemic_invariants:
    - el sistema de temas sigue basado en clases en <html> (dark/retro)
  composition_checks:
    - light y dark siguen aplicándose sin el bloque retro
```

## Structural Constraints

```yaml
structural_constraints:
  primary_rule: one coherent responsibility and one main reason to change
  entrypoints_must_stay_thin: true
  review_threshold_lines: 400
  extraction_threshold_lines: 600
  preferred_new_logic_locations:
    - apps/web/src/index.css (tokens)
```

## Traceability

- Requirement: "UI retro estilo SAP GUI clásico, seleccionable"
- Commit: UI-RETRO-001 (index.css .retro + store + toggle 3 estados)
- Deployment: main (tema disponible en el toggle)

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
