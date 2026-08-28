# A.SPEC CORE-012 — Integrar extreme-poverty como modo formal del canon (§4.2)

> `risk: low` — reversibles, docs puros del submódulo ADD, sin señales §4.1.
> `mode: extreme-poverty`, `toolcalls: 0` (cambios de docs en main thread).

## WHY

CORE-011 dejó una contradicción: la plantilla enumeraba tres modos
(`mechanical|judges-lite|full`) pero usaba un cuarto (`extreme-poverty`), y el
QUICKSTART/AGENTS.md afirmaban que extreme-poverty aplica SIEMPRE (incluso
señales hard §4.1) mientras §4.2 decía que las señales hard obligan siempre al
ciclo completo. Como el propio QUICKSTART declara que ante contradicción gana
SPECIFICATION, extreme-poverty era una excepción ilegal al canon, no un modo.

La distinción que resuelve el conflicto: **ceremonia ≠ subagent calls**. Las
garantías de un risk (approver humano, proofs ejecutadas, gates) no exigen
lanzar 5 subagentes. Un modo puede conservar todas las garantías con
presupuesto mínimo de agents.

## WHAT

Una verdad estructural: extreme-poverty entra al canon como **Modo D** de §4.2
con semántica explícita, y la contra-guardia pasa de "señal hard → ciclo
completo" a "señal hard → **garantías completas obligatorias**" (el modo puede
ser `full` o `extreme-poverty`; ninguna proof/gate exigida se omite). La
plantilla enumera los 4 modos; README documenta la tabla de 4 modos.

## SCOPE

- `ADD/SPECIFICATION.md` §4.2 — Modo D (extreme-poverty) + contra-guardias
  reescritas (garantías completas obligatorias; ceremonia ≠ subagent calls).
- `ADD/ASPEC-TEMPLATE.md` — encabezado enumera `mechanical|judges-lite|
  extreme-poverty|full`.
- `ADD/README.md` — tabla de modos (4) + regla de señales hard actualizada.
- `ADD/QUICKSTART.md` — título (modo formal §4.2) + regla clave de señales
  hard.
- `ADD/skills/extreme-poverty-add/Extreme-Poverty-ADD.md` — sección riesgo
  alto alineada (garantías completas).
- `AGENTS.md` — distinción ceremonia ≠ subagent calls en el modo por defecto.
- `SPEC-ADD/core/CORE-012.md` — esta spec.

## OUT OF SCOPE

- Cambios de riesgo/ceremonia en §4.1.
- Cambios de veredictos o contratos de los task-tools.
- El split del canon.

## CONTRACT

Precondiciones: CORE-011 integrado (mode en plantilla, §11 heurístico, tools
autocontenidos, COMPOSER skill).

Postcondiciones:

- §4.2 declara `mode: extreme-poverty` como Modo D formal, con presupuesto
  0–1 Task (solo GENERATOR), absorción de SPECCER/VERIFIER/TRACE/ATOMIZER,
  SPEC-REVIEWER nunca como subagente, COMPOSER como acción de primer plano, y
  mantenimiento de TODAS las checks/proofs (high exige approver humano).
- La contra-guardia no dice "señal hard → ciclo completo": dice "señal hard →
  garantías completas obligatorias; modo full o extreme-poverty; ninguna
  proof/gate omitible".
- La plantilla enumera los 4 modos (incluido extreme-poverty).
- README/QUICKSTART/AGENTS.md no contradicen el canon.

## INVARIANTS

```yaml
invariants:
  - "§4.1 (derivación de riesgo) no cambia: las señales siguen derivando low/normal/high."
  - "Ninguna proof o gate exigido por un risk se omite en ningún modo."
  - "`high` siempre exige approver humano y no se integra sin esa aprobación."
  - "La DoD es idéntica en los 4 modos."
  - "Ningún task tool gana o pierde checks/veredictos."
```

## VERIFICATION

- `rg -c "Modo D — Pobreza extrema" ADD/SPECIFICATION.md` → 1.
- `rg -c "garantías completas obligatorias" ADD/SPECIFICATION.md` → 1.
- `rg -c "prevalece SIEMPRE" ADD/SPECIFICATION.md` → 0 (contra-guardia vieja
  removida).
- `rg -c "extreme-poverty" ADD/ASPEC-TEMPLATE.md` → ≥1 (4º modo enumerado).
- `rg -c "extreme-poverty" ADD/README.md` → ≥1 (tabla de 4 modos).

## ROLLBACK

Reversible: revert del commit del submódulo ADD (docs puros).

## Change Surface

```yaml
change_surface:
  allowed:
    - ADD/SPECIFICATION.md
    - ADD/ASPEC-TEMPLATE.md
    - ADD/README.md
    - ADD/QUICKSTART.md
    - ADD/skills/extreme-poverty-add/Extreme-Poverty-ADD.md
    - AGENTS.md
    - SPEC-ADD/core/CORE-012.md
  prohibited:
    - ADD/SPECIFICATION.md §4.1   # señales de riesgo intactas
    - ADD/task-tools/**            # veredictos/contratos intactos
    - ADD/skills/composer-gate-add/**
```

## Blast Radius

```yaml
blast_radius:
  direct:
    - canon.modos (§4.2)
    - canon.contra-guardias
  indirect: []
  must_not_affect:
    - señales de riesgo (§4.1) → invariant 1
    - proofs/gates de cada modo → invariant 2-3
    - veredictos de jueces → invariant 5
```

## Composition

```yaml
composition:
  requires_aspecs: [CORE-011]
  must_compose_with: []
  systemic_invariants: []
  composition_checks: []
```

## Structural Constraints

```yaml
structural_constraints:
  primary_rule: enmienda mínima coherente; una razón de cambio (extreme-poverty como modo formal)
  entrypoints_must_stay_thin: true
  review_threshold_lines: 400
  extraction_threshold_lines: 600
  preferred_new_logic_locations: []
```

## Traceability

- Requirement: hallazgo del approver post-CORE-011 (contradicción
  extreme-poverty vs señales hard; resolución: ceremonia ≠ subagent calls).
- owner: Approver Systutor-oss (rol)
- approver: Approver Systutor-oss (rol)
- Commit: se ancla al integrar el submódulo ADD.
- Deployment: submódulo ADD (repo padre bumpa el gitlink al integrar).

## Definition of Done

- [ ] Objetivo satisfecho (extreme-poverty es modo formal; señales hard →
  garantías completas)
- [ ] Scope respetado
- [ ] Contract satisfecho
- [ ] Verdad independiente y falsable ahora
- [ ] Invariantes preservadas
- [ ] Verificación pasada (greps de la sección VERIFICATION)
- [ ] Rollback honesto (revert de docs)
- [ ] Sin cambios no relacionados
- [ ] Restricciones estructurales respetadas
- [ ] Trazabilidad establecida
