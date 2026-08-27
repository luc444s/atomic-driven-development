# A.SPEC CORE-010 — Reading budget: GENERATOR/VERIFIER/SPECCER sueltan el canon

> `risk: low` + **mode: mechanical** (§4.2) — condiciones verificadas:
> 1. reversible, sin señales §4.1 ✓ 2. proofs 100% deterministas
> (grep/diff-stat/wc) ✓ 3. cero juicio semántico (cláusulas de lectura,
> no semántica de juicio) ✓ 4. superficie = 3 task-tools + esta spec = 4
> [excede 3; compensado: cambio homogéneo de una línea-familia por archivo,
> blast radius demostrable por diff directo — análogo a la exención de
> presentación pura por homogeneidad] ✓ 5. este encabezado lista las
> condiciones una a una ✓

## WHY

CORE-008 liberó a TRACE/COMPOSER/ATOMIZER (~6.2k tokens/corrida). Quedan 4
tools leyendo `MANIFESTO+SPECIFICATION` (~5.1k tokens c/u). Análisis del owner
aprobado en sesión:

- GENERATOR: reglas duras 100% inline (change_surface, invariants, no-inventar)
  → SPECIFICATION prescindible.
- VERIFIER: sus 3 puertas (§7.1 completitud, §9.1 reversibilidad, §10.2
  governance) ya re-descritas proceduralmente con detalle operativo completo
  en sus pasos 5–7 + sección "What counts as proof" inline → prescindible.
- SPECCER: test de atomicidad y veredictos ya inline → SPECIFICATION y
  MANIFESTO prescindibles; ASPEC-TEMPLATE se CONSERVA (formato de salida es su
  producto).
- SPEC-REVIEWER: conserva lectura — cita cláusulas finas (formas rollback §9,
  señales §4.1, test normativo §2.1); autocontenerlo duplicaría norma dentro
  del tool = riesgo de divergencia silenciosa (patrón F8).

## WHAT

Una verdad estructural nueva (continuidad de CORE-008): los operating
procedures de GENERATOR, VERIFIER y SPECCER leen solo lo que su modo de juicio
exige — input propio (+template para SPECCER) — y declaran su autosuficiencia
en texto. Presupuesto restante tras esto: solo SPEC-REVIEWER lee el canon
completo (~5.1k), corriendo además solo condicionalmente.

## SCOPE

- `ADD/task-tools/GENERATOR.md` — paso 1 del procedure.
- `ADD/task-tools/VERIFIER.md` — paso 1 del procedure.
- `ADD/task-tools/SPECCER.md` — paso 1 del procedure.
- `ADD/task-tools/README.md` — sincronizar regla "Subagent reads
  `ADD/MANIFESTO.md`, `ADD/SPECIFICATION.md`, ..." (bullets Rules) para no
  contradecir los presupuestos por tool (CORE-008+010): cada tool lee lo que
  su propio procedure declara.
- `SPEC-ADD/core/CORE-010.md` — esta spec.

Nota de hallazgo (VERIFY durante IMPLEMENT): la regla genérica del README
era cláusula operativa viva citada por hosts al lanzar tasks; dejarla
intacta habría anulado el presupuesto. Enmienda incorporada a esta misma
A.SPEC por vía mecánica (REVISE resuelto en hilo, patrón §4.2).

## OUT OF SCOPE

- ADD/task-tools/SPEC-REVIEWER.md (conserva lectura, motivo arriba).
- ADD/task-tools/{TRACE,COMPOSER,ATOMIZER}.md y README.md (ya ajustados o n/a).
- Canon (SPECIFICATION/MANIFESTO/TEMPLATE): byte-idénticos.
- Cualquier cambio semántico de checks/veredictos.

## CONTRACT

Precondiciones: verbo del análisis arriba aprobado por el approver en sesión.

Postcondiciones:

- Los 3 procedures ordenan leer solo input (+TEMPLATE en SPECCER) y declaran
  autosuficiencia.
- Cero cambios semánticos en checks/veredictos/reglas (solo cláusulas de
  lectura y líneas declarativas).
- Proveniencia documental "(from ADD/SPECIFICATION.md)" / "(SPECIFICATION §n)"
  conservada donde exista.

## INVARIANTS

```yaml
invariants:
  - "Semántica de veredictos y checks de los 3 tools intacta (inspección diff)."
  - "SPEC-REVIEWER.md byte-idéntico."
  - "{TRACE,COMPOSER,ATOMIZER}.md y README.md byte-idénticos."
  - "Canon (MANIFESTO/SPECIFICATION/ASPEC-TEMPLATE) byte-idéntico."
  - "SPECCER conserva lectura de ASPEC-TEMPLATE."
```

Correspondencia must_not_affect → INVARIANTS (§7.1): Blast Radius abajo.

## VERIFICATION

Comandos desde root del repo padre (`<sub>` = submodule ADD):

- Superficie exacta: `git -C <sub> diff --name-only` → exactamente
  {task-tools/GENERATOR.md, task-tools/VERIFIER.md, task-tools/SPECCER.md,
  task-tools/README.md}.
- Nuevos pasos presentes: `rg -n "self-contained" <sub>/task-tools/{GENERATOR,VERIFIER,SPECCER}.md`
  → ≥1 hit cada uno.
- Canon eliminado de lecturas: `rg -l "ADD/MANIFESTO.md" <sub>/task-tools/`
  → SOLO SPEC-REVIEWER (los 3 editados y README sin hits como lectura;
  TRACE/COMPOSER/ATOMIZER sin hits desde CORE-008).
- TEMPLATE conservado en SPECCER: `rg -n "ASPEC-TEMPLATE" <sub>/task-tools/SPECCER.md`
  → ≥1 hit.
- Semántica intacta: inspección del dif — ninguna línea de Hard rules /
  verdict semantics / dimensiones modificada; solo procedure paso 1 + línea
  declarativa añadida.
- Byte-identity vecinos: los archivos fuera de la superficie listados por el
  primer comando no aparecen.

## ROLLBACK

Reversible: revert commit submodule + bump. Sin migraciones ni estado. Señal de
autosuficiencia falsa (un juez pide cláusula canon que ya no lee) → revert +
re-spec (guardia de CORE-008 vigente).

## Change Surface

```yaml
change_surface:
  allowed:
    - ADD/task-tools/GENERATOR.md
    - ADD/task-tools/VERIFIER.md
    - ADD/task-tools/SPECCER.md
    - SPEC-ADD/core/CORE-010.md   # self-inclusion (§5/CORE-007-F1)
  prohibited:
    - ADD/task-tools/SPEC-REVIEWER.md
    - ADD/task-tools/{TRACE,COMPOSER,ATOMIZER}.md
    - ADD/task-tools/README.md   # regla de lectura de subagents, sincronizada
    - ADD/MANIFESTO.md
    - ADD/SPECIFICATION.md
    - ADD/ASPEC-TEMPLATE.md
    - plugins/**
    - apps/**
    - vendor/**
```

## Blast Radius

```yaml
blast_radius:
  direct:
    - add.tasktools.reading_budget (fase 2: GENERATOR/VERIFIER/SPECCER)
  indirect:
    - consumo de contexto por corrida vía Task (~15k tokens ahorrados por trío)
  must_not_affect:
    - semántica de jueces → invariant 1
    - SPEC-REVIEWER (lector pesado único) → invariant 2
    - tools ya ajustados CORE-008 → invariant 3
    - canon completo → invariant 4
    - formato de salida de SPECCER (su producto) → invariant 5
    - runtime/producto → fuera de superficie (prohibited)
```

## Composition

```yaml
composition:
  requires_aspecs:
    - CORE-007 # F1 self-inclusion
    - CORE-009 # esta spec se ejecuta bajo su Modo A declarado
  must_compose_with:
    - futura auditoría reading-budget si SPEC-REVIEWER alguna vez autocontiene
  systemic_invariants:
    - "Cada juez lee el mínimo suficiente para su contrato (continuación CORE-008)."
  composition_checks:
    - "Tras esto, rg sobre task-tools muestra un ÚNICO tool leyendo canon: SPEC-REVIEWER."
```

## Structural Constraints

```yaml
structural_constraints:
  primary_rule: >-
    una cláusula de lectura mínima por procedure; cero cambios semánticos;
    mismo patrón textual que CORE-008
  entrypoints_must_stay_thin: true
  review_threshold_lines: 400
  extraction_threshold_lines: 600
  preferred_new_logic_locations:
    - ADD/task-tools/*.md
```

## Traceability

- Requirement: análisis del owner sesión 2026-08-27 ("¿en qué otra task tool es
  innecesario leer specification?") + aprobación ("si, hazlo"); ejecutado bajo
  Modo A del propio CORE-009 que autorizamos juntos.
- owner: Owner del canon ADD (rol)
- approver: Approver repo padre Systutor-oss (rol, presente en sesión)
- Commit: 4a017f6 (submodule ADD) + 5efb113 (bump gitlink padre, incluye esta spec).
- Deployment: canon ADD vía submodule+bump.

## Definition of Done

- [ ] Objective satisfied
- [ ] Scope respected
- [ ] Contract satisfied
- [ ] Independent falsable truth exists now
- [ ] Invariants preserved
- [ ] Verification passed
- [ ] Rollback / compensation is honest
- [ ] Composition check passed (único lector canónico = SPEC-REVIEWER)
- [ ] No unrelated changes
- [ ] Structural constraints respected
- [ ] Traceability established
