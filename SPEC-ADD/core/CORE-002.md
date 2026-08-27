# A.SPEC CORE-002 — Trazabilidad verificada por hechos del repo (hash SHA)

## WHY

El template exige Traceability (Requirement → A.SPEC → code → migration → test
→ commit → deployment), pero hoy es **prosa**: el campo `Commit:` queda
"pendiente" o se rellena a mano y nadie lo valida contra el repo. Un commit que
no referencia la A.SPEC, un archivo modificado fuera de `change_surface.allowed`,
un test nombrado en VERIFICATION que no existe o una migración sin `downgrade()`
pasan igual. La cadena is prometida, nunca chequeada — se vuelve un checkbox.

## WHAT

Una propiedad operacional nueva del canon: **la cadena de trazabilidad se vuelve
verificable por hechos del repo, anclada en el SHA del commit (hash real de
git), no por prosa.**

1. `Traceability.Commit` del template se llena en INTEGRATE con el **SHA literal**
   del commit (o SHA inicial de la secuencia). Si no hay SHA → `GAP`.
2. Nuevo task tool `ADD/task-tools/TRACE.md` (juez, contexto limpio) con input
   contract explícito:
   - `spec_path` (A.SPEC), `sha` (commit ancla, pasado como input; TRACE NO
     re-parsea campos prosaicos del A.SPEC buscando el SHA), `repo_root`
     (root del repo donde se evalúan `change_surface`; para A.SPECs de
     dominio = repo padre; para A.SPECs del canon = submódulo ADD).
   - Checks contra el repo, relativos a `repo_root`:
     - A.SPEC→commit: `git log -1 --format=%H <sha>` existe; el mensaje del
       commit menciona el ID de la A.SPEC.
     - commit→code: `git show --stat <sha>` → paths modificados solo bajo
       `change_surface.allowed`, ningún path bajo `prohibited`.
     - Gitlink de submódulos: si el commit padre modifica un gitlink `G` (p.ej.
       `ADD`) y paths de `allowed` viven bajo `G/`, se acepta el gitlink y TRACE
       valida el diff de ese submódulo contra el mismo SHA en `repo_root=G`.
       El gitlink por sí solo no cuenta como violation.
     - commit→test (regla de discovery): los `.py` que VERIFICATION nombra con
       nombre /`test_\w+\.py`/ DEBEN existir en el tree del SHA; si VERIFICATION
       no nombra paths, se buscan en SCOPE bajo `**/tests/**` con prefijo
       `test_`.
     - commit→migración (regla de discovery): cada path del SCOPE que matchee
       `migrations/*\.py` DEBE existir en el tree y contener `def downgrade(`
       o `def down(`.
     - deployment: si el entorno expone runtime del plugin se verifica la
       migración aplicada; si no, se marca `GAP` informativo de deployment.
3. `ADD/SPECIFICATION.md` §13.5: norma — la trazabilidad es verificable por
   hechos del repo; sin SHA ancla consistente, la integración de la A.SPEC
   queda `GAP` (no `PASS`).
4. `ADD/ASPEC-TEMPLATE.md`: hint en Traceability — `Commit:` se llena con el
   SHA literal al integrar; el resto lo verifica TRACE.

## SCOPE

- `ADD/task-tools/TRACE.md` — task tool nuevo (operating procedure, inputs,
  output shape, verdicts, anti-noise).
- `ADD/SPECIFICATION.md` — §13.5 norma de trazabilidad verificable.
- `ADD/ASPEC-TEMPLATE.md` — hint en sección Traceability.
- `ADD/task-tools/README.md` y `ADD/README.md` — registro de TRACE en índice.
- `SPEC-ADD/core/CORE-002.md` — esta A.SPEC.

## OUT OF SCOPE

- Fingerprint de contenido del spec (hash de WHAT/ID/surface) — descartado por
  decisión de sesión; el SHA del commit es el ancla.
- Integración de TRACE con CI (requiere A.SPEC de CI/binding).
- Risk-tiering (mejora nº3) — A.SPEC futura.
- Verificar veracidad de los tests (eso es VERIFIER, no TRACE).
- Deployment real a servidor; solo chequeo de migración presente/aplicada.

## CONTRACT

Precondiciones:

- El commit de integración existe (INTEGRATE ya ejecutado) con SHA conocido.
- `change_surface.allowed/prohibited` declarados (template lo exige).

Postcondiciones:

- TRACE, con SHA inválido o ausente → `GAP`.
- TRACE, con SHA válido pero mensaje del commit que no menciona el ID de la
  A.SPEC → `GAP` (el hecho de existencia del commit no alcanza para la cadena).
- TRACE detecta path fuera de `allowed` o en `prohibited` → `FAIL` (hecho
  contradictorio del repo).
- Test nombrado inexistente o migración sin `downgrade()` → `GAP`.
- Con todos los hechos consistentes → `PASS`.
- Norma §13.5 presente en SPECIFICATION.

## INVARIANTS

```yaml
invariants:
  - "TRACE es juez de hechos: solo lee git y archivos; nunca inventa commands ni
    pruebas; no emite PASS sin evidencia del repo."
  - "El protocolo clean-context de los jueces se preserva (TRACE corre vía
    Task con contexto limpio)."
  - "Veredicto de VERIFIER y SPEC-REVIEWER no cambia: TRACE agrega dimensión de
    integración, no re-juzga contract/invariants."
  - "La estructura task-tools (fuente única de verdad) no se reorganiza; solo se
    agrega TRACE.md."
  - "Sin cambios de código de producto; solo canon ADD + esta A.SPEC."
  - "A.SPECs integradas existentes se mantienen válidas (grandfathered); la
    norma aplica a nuevas o re-abiertas."
  - "El ID humano de A.SPEC no se reemplaza por hash; sigue siendo legible en
    títulos y mensajes de commit."
```

## VERIFICATION

- `grep -F "trazabilidad verificable por hechos del repo" ADD/SPECIFICATION.md`
  → norma §13.5 presente (frase pinneada; el término vago "trazabilidad" ya
  existía y no vale).
- `ls ADD/task-tools/TRACE.md` → existe.
- TRACE incluye paso `sha_anchor` en su operating procedure (inspección del
  archivo).
- Ejecución de prueba:
  - Caso `PASS`: lanzar TRACE contra un commit real del canon con surface
    declarada — el `git log` de esta A.SPEC tras integrar, o cualquier commit real
    respetando `allowed` — verificando los 5 checks salvo deployment → `PASS`
    (o `GAP` informativo solo si runtime no expone).
  - Caso `GAP`: correr TRACE con SHA inexistente (`0000000000000000`) →
    veredicto `GAP`, sin emitir `FAIL`.
- Exam care: el fixture del caso `GAP` se ejecuta inline (input del task), sin
  escribir archivos falsos en el repo.

## ROLLBACK

Reversible: revertir commit del submódulo. TRACE.md se elimina; §13.5 y hint se
revientan con el revert. Sin migraciones.

## Change Surface

```yaml
change_surface:
  allowed:
    - ADD/task-tools/TRACE.md
    - ADD/SPECIFICATION.md
    - ADD/ASPEC-TEMPLATE.md
    - ADD/task-tools/README.md
    - ADD/README.md
    - SPEC-ADD/core/CORE-002.md
  prohibited:
    - plugins/**
    - apps/**
    - vendor/**
    - ADD/task-tools/VERIFIER.md
    - ADD/task-tools/SPEC-REVIEWER.md
    - ADD/task-tools/GENERATOR.md
    - ADD/task-tools/SPECCER.md
```

## Blast Radius

```yaml
blast_radius:
  direct:
    - add.trace.task_tool
    - add.specification.traceability_norm
  indirect:
    - integración de A.SPECs futuras (exige SHA en Traceability.Commit)
  must_not_affect:
    - verdict routing de VERIFIER/SPEC-REVIEWER
    - clean-context protocol de jueces (TRACE incluido)
    - estructura task-tools (fuente única de verdad)
    - A.SPECs integradas existentes (grandfathered)
    - runtime/producto del sistema
```

Correspondencia `must_not_affect` → INVARIANTS (cobertura 4b de CORE-001, §7.1):

- verdict routing → invariante "Veredicto de VERIFIER y SPEC-REVIEWER no cambia".
- clean-context → invariante "protocolo clean-context se preserva".
- estructura task-tools → invariante "estructura task-tools no se reorganiza".
- A.SPECs integradas → invariante "grandfathered".
- runtime/producto → invariante "sin cambios de código de producto".

## Composition

```yaml
composition:
  requires_aspecs: []
  must_compose_with:
    - CORE-001 # invariantes adversarias; TRACE usa change_surface declarado
    - CORE-003 # risk-tiering (futura)
  systemic_invariants:
    - "Ninguna A.SPEC se cierra con trazabilidad no verificable sin GAP explícito."
  composition_checks:
    - A.SPEC integrada con SHA válido + surface respetada → TRACE PASS.
    - A.SPEC con SHA ausente → TRACE GAP (nunca PASS).
```

## Structural Constraints

```yaml
structural_constraints:
  primary_rule: TRACE es juez delgado (leer git + archivos, emitir veredicto)
  entrypoints_must_stay_thin: true
  review_threshold_lines: 400
  extraction_threshold_lines: 600
  preferred_new_logic_locations:
    - ADD/task-tools/TRACE.md
```

## Traceability

- Requirement: plan de madurez ADD — mejora nº2 (trazabilidad por hechos),
  acordado en sesión 2026-08-26. Definida aquí: traza anclada en SHA del
  commit verificable por TRACE; fingerprint de contenido descartado.
- Commit: al ejecutar (1 en submódulo + 1 bump en repo padre).
- Deployment: canon ADD vía commit + bump del submódulo.

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