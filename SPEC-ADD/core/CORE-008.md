# A.SPEC CORE-008 — Presupuesto mínimo de lectura en jueces autocontenidos

> `risk: low` — reversibles, docs puros, sin señales §4.1.

## WHY

Los task-tools se declaran *self-contained system prompts* (README), pero
TRACE, COMPOSER y ATOMIZER ordenaban releer `MANIFESTO.md` + `SPECIFICATION.md`
(~6.200 tokens) cuyas normas operativas ya viven completas e inline en su
propio cuerpo — TRACE incluso duplica §13.5. Esto viola el principio del propio
MANIFESTO (contexto mínimo suficiente) y encarece/alucinabiliza cada corrida.
Detectado por el owner en sesión; alcance mínimo decidido (solo los 3 tools;
REVIEWER/VERIFIER/SPECCER/GENERATOR conservan su lectura porque citan cláusulas
finas o necesitan el template).

## WHAT

Una verdad estructural nueva: los tres jueces autocontenidos leen SOLO su
input de juicio (y su fuente), no el canon general. Sus operating procedures
pasan a declararlo explícitamente. Es un cambio observable: una nueva corrida
de estos jueces consume menos contexto y no dependen del canon para juzgar.

## SCOPE

- `ADD/task-tools/TRACE.md` — procedure paso 1: lectura self-contained.
- `ADD/task-tools/COMPOSER.md` — idem.
- `ADD/task-tools/ATOMIZER.md` — idem.
- `SPEC-ADD/core/CORE-008.md` — esta spec.

## OUT OF SCOPE

- Otros task-tools (SPECCER/SPEC-REVIEWER/GENERATOR/VERIFIER) — auditoría
  completa futura (alcance B).
- Split del canon / reorganización de SPECIFICATION.md.
- Cualquier cambio semántico de checks, veredictos o contratos.

## CONTRACT

Precondiciones:

- Los checks/reglas de los 3 tools están completos inline (verificado).

Postcondiciones:

- Los 3 operating procedures ordenan leer solo input+fuente propia.
- Cero cambios semánticos en checks/veredictos (diff muestra solo cláusulas
  de lectura).
- Cada tool declara su autosuficiencia en texto.

## INVARIANTS

```yaml
invariants:
  - "Semántica de veredictos PASS/FAIL/GAP y checks no cambian en ningún tool."
  - "SPECCER/SPEC-REVIEWER/GENERATOR/VERIFIER byte-idénticos."
  - "MANIFESTO.md/SPECIFICATION.md/ASPEC-TEMPLATE.md byte-idénticos."
  - "Proveniencia documental (menciones '(SPECIFICATION §n)') se conserva."
```

Correspondencia must_not_affect → INVARIANTS (§7.1): ver Blast Radius.

## VERIFICATION

- `git -C ADD diff --stat` → exactamente 3 files (TRACE/COMPOSER/ATOMIZER),
  sin ninguna línea de checks ni verdicts modificada (inspección del dif:
  solo la cláusula Read cambia y las líneas añadidas son declaraciones de
  autosuficiencia).
- `rg -n "fresh" ADD/task-tools/{TRACE,COMPOSER,ATOMIZER}.md` → nuevos pasos
  presentes; `rg -l "ADD/MANIFESTO.md" ADD/task-tools/` → solo en los 4 tools
  intactos.
- Menciones de proveniencia conservadas: `rg -c "SPECIFICATION §"
  ADD/task-tools/{TRACE,COMPOSER,ATOMIZER}.md` → ≥1 cada uno.
- Ahorro medible: ~(1100+5100) ≈ 6.200 tokens/juez/corrida (wc de diffs).

## ROLLBACK

Reversible: revert del commit submodule + bump. Sin migraciones, sin estado.

## Change Surface

```yaml
change_surface:
  allowed:
    - ADD/task-tools/TRACE.md
    - ADD/task-tools/COMPOSER.md
    - ADD/task-tools/ATOMIZER.md
    - SPEC-ADD/core/CORE-008.md   # self-inclusion F1/§5
  prohibited:
    - ADD/task-tools/SPECCER.md
    - ADD/task-tools/SPEC-REVIEWER.md
    - ADD/task-tools/GENERATOR.md
    - ADD/task-tools/VERIFIER.md
    - ADD/SPECIFICATION.md
    - ADD/MANIFESTO.md
    - ADD/ASPEC-TEMPLATE.md
    - plugins/**
    - apps/**
    - vendor/**
```

## Blast Radius

```yaml
blast_radius:
  direct:
    - add.tasktools.reading_budget (TRACE/COMPOSER/ATOMIZER)
  indirect:
    - consumo de contexto de corridas vía Task
  must_not_affect:
    - semántica de checks/veredictos → invariante "semántica no cambia"
    - otros cuatro task-tools → invariante "byte-idénticos"
    - canon (SPECIFICATION/MANIFESTO/TEMPLATE) → invariante idem
    - runtime/producto → invariante "sin cambios de producto" (scope solo .md canon)
```

## Composition

```yaml
composition:
  requires_aspecs:
    - CORE-007 # F1 self-inclusion (surface incluye este doc); F8 espejo TRACE↔§13.5 coherente
  must_compose_with:
    - futura auditoría completa de presupuesto de lectura (alcance B)
  systemic_invariants:
    - "Cada juez lee el mínimo suficiente para su contrato."
  composition_checks:
    - "Corrida de prueba de cualquiera de los 3 jueces consumiendo SOLO su
      input/self-body — juzga igual que antes (verificado por inspección de
      autosuficiencia inline; ejecución real diferida a próxima sesión que
      lance tasks, decisión del approver)."
```

## Structural Constraints

```yaml
structural_constraints:
  primary_rule: cláusula de lectura mínima, cero cambios semánticos
  entrypoints_must_stay_thin: true
  review_threshold_lines: 400
  extraction_threshold_lines: 600
  preferred_new_logic_locations:
    - ADD/task-tools/*.md
```

## Traceability

- Requirement: decisión owner en sesión 2026-08-27 tras cierre CORE-007
  ("trace no necesita leer specification"; alcance mínimo; sin ejecutar task
  tools en esta pasada).
- Desviación documentada: DEFINE/IMPLEMENT resueltos en hilo principal SIN
  subagents-jueces, por instrucción explícita del approver. El VERIFIER real
  será sustituible por esta verificación grep mecánica + revisión visual del
  diff; si al reactivarse las corridas algún juez resulta necesitar una
  cláusula del canon, es señal de autosuficiencia falsa → revert/re-spec.
- owner: Owner del canon ADD (rol)
- approver: Approver del repo padre Systutor-oss (rol, presente en sesión)
- Commit: al ejecutar (submodule + bump padre).
- Deployment: canon ADD vía submodule+bump.

## Definition of Done

- [ ] Objective satisfied
- [ ] Scope respected
- [ ] Contract satisfied
- [ ] Independent falsable truth exists now
- [ ] Invariants preserved
- [ ] Verification passed
- [ ] Rollback / compensation is honest
- [ ] Composition checks passed when applicable
- [ ] No unrelated changes
- [ ] Structural constraints respected
- [ ] Traceability established
