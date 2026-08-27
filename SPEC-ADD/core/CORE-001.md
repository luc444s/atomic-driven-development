# A.SPEC CORE-001 — Verificación adversaria: completitud de invariantes

## WHY

El VERIFIER mapea cláusula→proof solo sobre lo que el autor **declaró** en
`INVARIANTS`. Si una superficie queda sin proteger (ej. `stock`) pero el autor
la declara en `blast_radius.must_not_affect`, la A.SPEC pasa igual. El juicio
es autocomplaciente: valida lo declarado, nunca la **completitud** del contrato.
Superficies sin invariante explícito escapan de toda garantía verificable.

## WHAT

Una propiedad estructural nueva del canon ADD: **toda superficie declarada en
`blast_radius.must_not_affect` debe tener un invariante explícito, evaluable y
con proof explícita.** (La superficie `indirect` se informa como nota, no como
puerta de verificación.)

1. `ADD/SPECIFICATION.md` §7: norma normativa — cada entrada `must_not_affect`
   exige invariante explícito y evaluable; superficie sin invariante = `FAIL`
   (A.SPEC incompleta), no `PASS`.
2. `ADD/ASPEC-TEMPLATE.md`: hint en secciones INVARIANTS y Blast Radius —
   derivar invariantes desde `must_not_affect`.
3. `ADD/task-tools/VERIFIER.md`: nuevo paso de completitud — map
   `blast_radius.must_not_affect → invariant → proof`; superficie sin
   invariante → `GAP` con lista `Uncovered surfaces`.
4. `ADD/task-tools/SPEC-REVIEWER.md`: dimensión de review extiende "invariant
   strength" con cobertura `must_not_affect × invariants`; hallazgo `REVISE`
   si hay superficie sin invariante.

## SCOPE

- `ADD/SPECIFICATION.md` — §7 nueva norma de completitud.
- `ADD/ASPEC-TEMPLATE.md` — hints en INVARIANTS y Blast Radius.
- `ADD/task-tools/VERIFIER.md` — modo `verify-run`: procedimiento + output.
- `ADD/task-tools/SPEC-REVIEWER.md` — review dimension extendida.

## OUT OF SCOPE

- Verificación de composición entre A.SPECs (dimension 5 / mejora nº5 del
  plan de madurez; requerirá A.SPEC propia).
- Risk-tiering del ciclo (mejora nº3; A.SPEC futura).
- Traceability chequeada por hechos del repo (mejora nº2; A.SPEC futura).
- Cambios en GENERATOR, ATOMIZER, SPECCER.
- Ningún cambio de código de producto.

## CONTRACT

Precondiciones:

- Canon ADD vigente (task-tools como fuente única de verdad de los jueces).
- La A.SPEC candidata del usuario declara `blast_radius` (template lo exige).

Postcondiciones:

- VERIFIER, ante A.SPEC con `must_not_affect` sin invariante correlativo,
  devuelve `GAP` (nunca `PASS`).
- SPEC-REVIEWER lista la superficie sin cubrir como hallazgo `REVISE`.
- SPECIFICATION.md contiene la norma escrita de completitud.
- Aplicabilidad: la norma rige para A.SPECs nuevas o re-abiertas. Las A.SPECs
  ya integradas quedan **grandfathered** (COMPRAS-001…011 incluidas): su
  review de completitud puede reportarse como `GAP` informativo al re-abrirlas,
  sin invalidar su integración previa.

## INVARIANTS

```yaml
invariants:
  - "Toda must_not_affect declarada tiene invariant correlativo evaluable."
  - "El VERIFIER nunca devuelve PASS con superficies must_not_affect sin cubrir."
  - "SPEC-REVIEWER verdict routing (REVISE/SPLIT/REJECT) queda intacto: la
    cobertura solo agrega un caso más de REVISE; no cambia semántica de veredicto."
  - "El protocolo clean-context de los jueces (task-tools) se preserva: el
    completeness_map solo lee el A.SPEC, no el repo."
  - "La estructura task-tools (fuente única de verdad de los jueces) no se
    reorganiza ni se renombra en esta A.SPEC."
  - "Sin cambios de código de producto fuera del canon ADD."
  - "Toda A.SPEC de compras ya integrada (COMPRAS-001…011) no se reescribe;
    la norma de completitud rige solo para A.SPECs nuevas o re-abiertas."
```

## VERIFICATION

- La frase normativa exacta que se agregue en §7 (pinneada al redactarla,
  p.ej. "superficie must_not_affect sin invariante correlativo ⇒ FAIL")
  presente en `ADD/SPECIFICATION.md`. El término genérico `must_not_affect`
  ya existía y NO es prueba válida.
- VERIFIER transformado incluye paso `completeness_map` en su operating
  procedure (inspección del archivo).
- SPEC-REVIEWER incluye dimensión de cobertura en su checklist.
- Ejecución de prueba, dos casos, ambos con VERIFIER **y** SPEC-REVIEWER:
  - Control negativo → A.SPEC ficticia con `must_not_affect: [stock]` y sin
    invariante de stock → VERIFIER `GAP`; SPEC-REVIEWER `REVISE`
    (prueba: sin falso-verde).
  - Control positivo → la misma A.SPEC con invariante de stock declarado y
    proof explícita → VERIFIER `PASS`; SPEC-REVIEWER `PASS`
    (prueba: sin sobre-bloqueo / falso-GAP).
  - La A.SPEC ficticia se materializa en un archivo temporal bajo
    `/data/data/com.termux/files/usr/tmp/opencode/spec-review-fixture.md`
    y se elimina tras el run.

## ROLLBACK

Reversible: revertir commit del submódulo; el canon queda en el estado previo
(cualquiera de las 4 rutas de reversión de gitflow). Sin migraciones.

## Change Surface

```yaml
change_surface:
  allowed:
    - ADD/SPECIFICATION.md
    - ADD/ASPEC-TEMPLATE.md
    - ADD/task-tools/VERIFIER.md
    - ADD/task-tools/SPEC-REVIEWER.md
    - SPEC-ADD/core/CORE-001.md
  prohibited:
    - plugins/**
    - apps/**
    - vendor/**
    - ADD/task-tools/GENERATOR.md
    - ADD/task-tools/ATOMIZER.md
    - ADD/task-tools/SPECCER.md
```

## Blast Radius

```yaml
blast_radius:
  direct:
    - add.verifier.completeness
    - add.spec_reviewer.coverage
  indirect:
    - agente definiendo A.SPECs futuras (exigencia de invariantes completas)
  must_not_affect:
    - VERIFIER clean-context protocol
    - SPEC-REVIEWER verdict routing (REVISE/SPLIT/REJECT)
    - estructura de task-tools (fuente única de verdad)
    - A.SPECs existentes de compras
    - ningún comportamiento de runtime/producto
```

## Composition

```yaml
composition:
  requires_aspecs: []
  must_compose_with:
    - CORE-002 # traceability ejeccionada (mejora nº2; futura)
    - CORE-003 # risk-tiering (mejora nº3; futura)
  systemic_invariants:
    - "Todo juez ADD juzga completitud, no solo lo declarado."
  composition_checks:
    - Un A.SPEC con superficie stock sin invariante stock → GAP en VERIFIER
      y REVISE en SPEC-REVIEWER, de forma consistente.
```

## Structural Constraints

```yaml
structural_constraints:
  primary_rule: cambio del canon; docs cortos y cohesivos por archivo
  entrypoints_must_stay_thin: true
  review_threshold_lines: 400
  extraction_threshold_lines: 600
  preferred_new_logic_locations:
    - ADD/task-tools/VERIFIER.md
    - ADD/task-tools/SPEC-REVIEWER.md
```

## Traceability

- Requirement: plan de madurez ADD — mejora nº1 (verificabilidad adversaria),
  acordado en sesión 2026-08-26 y documentado en este A.SPEC (fuente de verdad
  del requirement). "Mejora nº1" se define aquí mismo: el VERIFIER/SPEC-REVIEWER
  juzgan completitud de invariantes, no solo cláusulas declaradas. Punto de
  partida y evaluación del resto de mejoras: pendiente (al ejecutar) en
  sesiones futuras.
- Commit: 1 commit en submódulo ADD + 1 bump en repo padre (al ejecutar).
- Deployment: canon en submódulo atomic-driven-development vía commit + bump.

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