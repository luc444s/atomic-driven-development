# A.SPEC CORE-011 — Synchronize execution-mode and reading semantics

> `risk: low` — reversibles, docs puros del submódulo ADD, sin señales §4.1.
> `mode: extreme-poverty`, `toolcalls: 0` (cambios de docs en main thread).

## WHY

Tres problemas visibles en el canon y la plantilla:

1. **`mode:` faltante en la plantilla** — §4.2 exige declarar el modo en el
   encabezado de cada A.SPEC antes de IMPLEMENT, pero `ASPEC-TEMPLATE.md` solo
   declara `risk:`. El modo queda implícito o se omite.
2. **Límite duro de 600 líneas contradictorio en §11** — el canon decía que
   SPECIFICATION.md se mantiene monolito "mientras respete el presupuesto de
   <=600 líneas", pero §12.2 declara esos umbrales heurísticos (no fallan una
   A.SPEC por sí solos). El límite duro contradice la heurística.
3. **Encabezados de task-tools que declaran lectura de docs que CORE-008/010
   eliminaron** — CORE-008/010 retiraron la lectura de canon de los jueces
   autocontenidos, pero los encabezados siguen diciendo "reads ADD docs
   itself" (o "and the A.SPEC"). Inconsistencia entre el presupuesto de
   lectura real y lo declarado.

## WHAT

Una verdad estructural: el ciclo ADD queda sincronizado en su semántica de
modos y lectura. (a) la plantilla declara `mode:` junto a `risk:`; (b) el
monolito se rige por responsabilidad normativa coherente, no por un límite de
líneas; (c) los task-tools autocontenidos declaran una frase única de
autocontención (leen solo lo que su Operating Procedure declara; no leen el
canon salvo mención explícita), con SPEC-REVIEWER como única excepción
(QUICKSTART como ley; canon completo solo si `risk: high` o duda de norma).

## SCOPE

- `ADD/ASPEC-TEMPLATE.md` — añadir línea `mode:` al encabezado.
- `ADD/SPECIFICATION.md` — §11: quitar el límite duro <=600, dejarlo como
  heurística alineada con §12.2.
- `ADD/task-tools/SPECCER.md`, `GENERATOR.md`, `VERIFIER.md`, `TRACE.md`,
  `ATOMIZER.md` — encabezado común de autocontención.
- `ADD/task-tools/SPEC-REVIEWER.md` — encabezado como única excepción.
- `SPEC-ADD/core/CORE-011.md` — esta spec.

## OUT OF SCOPE

- CANON-MIRRORS.md, CI wrapper, registry ni más estructura (decisión del
  approver: no meter).
- Cambio semántico de checks, veredictos o contratos de los task-tools.
- El split del canon en artículos.

## CONTRACT

Precondiciones: estado actual del submódulo ADD (QUICKSTART + skills
extreme-poverty/composer-gate ya presentes).

Postcondiciones:

- `ASPEC-TEMPLATE.md` declara `risk:` y `mode:` en el encabezado.
- §11 no menciona un límite duro de líneas; la regla del monolito es la
  responsabilidad normativa coherente (heurística §12.2).
- Los 5 task-tools autocontenidos comparten la frase única de autocontención;
  SPEC-REVIEWER declara ser la única excepción que lee canon.

## INVARIANTS

```yaml
invariants:
  - "El canon completo (MANIFESTO + SPECIFICATION) sigue siendo la autoridad normativa de fondo; el QUICKSTART es canon de cabecera subordinado."
  - "SPEC-REVIEWER conserva su lectura del QUICKSTART (ley por defecto) y del canon completo bajo risk: high o duda de norma."
  - "Los demás task-tools no ganan lecturas de canon nuevas."
  - "La DoD de los modos de §4.2 no cambia."
```

## VERIFICATION

- `grep -c "mode: mechanical|judges-lite|full" ADD/ASPEC-TEMPLATE.md` → 1
  (línea añadida).
- `grep -c "<= 600" ADD/SPECIFICATION.md` → 0 (límite duro removido).
- `grep -c "This task tool is self-contained" ADD/task-tools/*.md` → 5
  (SPECCER, GENERATOR, VERIFIER, TRACE, ATOMIZER).
- `grep -c "ONLY canon reader" ADD/task-tools/SPEC-REVIEWER.md` → 1.
- `grep -c "reads ADD docs itself" ADD/task-tools/*.md` → 0 (sin vestigios).

## ROLLBACK

Reversible: revert del commit del submódulo ADD (docs puros, sin migraciones,
sin estado).

## Change Surface

```yaml
change_surface:
  allowed:
    - ADD/ASPEC-TEMPLATE.md
    - ADD/SPECIFICATION.md
    - ADD/task-tools/SPECCER.md
    - ADD/task-tools/GENERATOR.md
    - ADD/task-tools/VERIFIER.md
    - ADD/task-tools/TRACE.md
    - ADD/task-tools/ATOMIZER.md
    - ADD/task-tools/SPEC-REVIEWER.md
    - SPEC-ADD/core/CORE-011.md
  prohibited:
    - SPECIFICATION.md §4.1/§4.2  # modos y ceremonia intactos
    - skills/**                    # extreme-poverty y composer-gate intactos
```

## Blast Radius

```yaml
blast_radius:
  direct:
    - canon.template (encabezado A.SPEC)
    - canon.monolito (§11)
    - task-tools.presupuesto_lectura
  indirect: []
  must_not_affect:
    - modos de ciclo (§4.2) → invariant DoD intacta
    - reglas de riesgo (§4.1) → invariant canon autoridad
    - veredictos de los jueces → invariant sin cambios semánticos
```

## Composition

```yaml
composition:
  requires_aspecs: [CORE-008, CORE-010]   # base del presupuesto de lectura
  must_compose_with: []                   # docs del submódulo, sin set mayor
  systemic_invariants: []
  composition_checks: []
```

## Structural Constraints

```yaml
structural_constraints:
  primary_rule: enmiendas mínimas a docs del submódulo; una razón de cambio (sincronizar semántica de modo y lectura)
  entrypoints_must_stay_thin: true
  review_threshold_lines: 400
  extraction_threshold_lines: 600
  preferred_new_logic_locations: []
```

## Traceability

- Requirement: hallazgos del approver en sesión (mode faltante, límite 600
  contradictorio, encabezados de lectura obsoletos) + QUICKSTART como canon de
  cabecera (presupuesto de lectura).
- owner: Approver Systutor-oss (rol)
- approver: Approver Systutor-oss (rol)
- Commit: se ancla al integrar el submódulo ADD.
- Deployment: submódulo ADD (repo padre bumpa el gitlink al integrar).

## Definition of Done

- [ ] Objetivo satisfecho (semántica de modo y lectura sincronizada)
- [ ] Scope respetado (solo docs del submódulo + esta spec)
- [ ] Contract satisfecho (postcondiciones cumplidas)
- [ ] Verdad independiente y falsable ahora
- [ ] Invariantes preservadas
- [ ] Verificación pasada (greps de la sección VERIFICATION)
- [ ] Rollback honesto (revert de docs)
- [ ] Sin cambios no relacionados
- [ ] Restricciones estructurales respetadas
- [ ] Trazabilidad establecida
