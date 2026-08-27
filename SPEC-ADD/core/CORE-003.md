# A.SPEC CORE-003 — Risk-tiering: ceremonia proporcional al riesgo del cambio

## WHY

Hoy todo A.SPEC paga el mismo overhead de ceremonia. Un typo de 1 línea en un
README paga la misma exigencia que una migración destructiva que toca stock o
dinero. Resultado: fricción innecesaria en cambios triviales y — peor — riesgo
no concentrado donde importa. El trigger contract de SPEC-REVIEWER ya matiza
"no siempre", pero la proporcionalidad no está sistematizada: no hay nivel de
riesgo declarado, no hay señal que escale la ceremonia, ni puerta humana para
cambios irreversibles o de blast radius amplio.

## WHAT

Una propiedad estructural nueva del canon: **el nivel de riesgo declarado del
cambio determina la ceremonia mínima obligatoria del ciclo** (proporcionalidad
ADD). Niveles:

- `risk: low` — cambio reversible, sin tocar dinero, stock, auth/seguridad ni
  migraciones destructivas; blast radius acotado a la feature. Ceremonia
  estándar (SPECCER → GENERATOR → VERIFIER → TRACE). SPEC-REVIEWER opcional.
- `risk: normal` (default) — el comportamiento actual del canon. SPEC-REVIEWER
  regido por su Trigger contract (condicional).
- `risk: high` — irreversibilidad (§9), dinero, stock físico, auth/seguridad,
  migración destructiva o blast radius amplio (`must_not_affect` con superficies
  críticas). Ceremonia reforzada: SPEC-REVIEWER SIEMPRE obligatorio, aprobación
  humana explícita (`approver`), VERIFIER y TRACE obligatorios; para
  irreversibles, ROLLBACK con compensación/contención/no-repetición (§9).

Derivación del nivel: señales leídas del A.SPEC (no inferencia externa):

- ROLLBACK con reversión física imposible → `high`.
- Scope o invariantes tocan `stock`, `finanzas`, `auth`, `tenancy`,
  `seguridad`, `lg_*` → `high`.
- Migración con `drop`/destructiva o reescritura de datos existentes → `high`.
- Blast radius `must_not_affect` amplio o con superficies críticas → `high`.
- Fuera de eso → `normal`; trivias internas reversibles sin señales → `low`.

1. `ADD/SPECIFICATION.md` §4.1 — norma de risk-tiering con los 3 niveles,
   señales de derivación y ceremonia mínima por nivel; matiza el Trigger
   contract de SPEC-REVIEWER (high ⇒ siempre, no condicional).
2. `ADD/ASPEC-TEMPLATE.md` — campo `risk: low|normal|high` con hint en el
   encabezado.
3. `ADD/task-tools/SPEC-REVIEWER.md` — nueva dimensión `risk`: el reviewer
   valida que el `risk` declarado sea honesto frente a las señales del A.SPEC;
   `low` declarado con señales de `high` → `REVISE`. El Trigger contract queda
   condicional para `low/normal`, incondicional para `high`.
4. `AGENTS.md` del repositorio — regla de enforcement: `high` exige
   SPEC-REVIEWER siempre, `approver` humano documentado en el A.SPEC, y no se
   integra sin esa aprobación.

## SCOPE

- `ADD/SPECIFICATION.md` — §4.1 risk-tiering.
- `ADD/ASPEC-TEMPLATE.md` — campo `risk` + hint.
- `ADD/task-tools/SPEC-REVIEWER.md` — dimensión `risk` + matiz Trigger contract.
- `AGENTS.md` — enforcement high/approver.
- `SPEC-ADD/core/CORE-003.md` — esta A.SPEC.

## OUT OF SCOPE

- Ownership/approver completo como rol permanente (mejora nº6; aquí solo se usa
  el campo `approver` como puerta del nivel high).
- Reversibilidad probada por tests de downgrade (mejora nº4).
- Composición/release gate (mejora nº5).
- Cambios en VERIFIER, TRACE, GENERATOR, SPECCER, ATOMIZER.
- Cualquier cambio de código de producto.

## CONTRACT

Precondiciones:

- Task tool SPEC-REVIEWER existente con Trigger contract (§4 y trigger).
- Plantilla con Blast Radius y ROLLBACK (§9) existentes.

Postcondiciones:

- `risk` es campo declarado y honesto: low/normal/high con señales de
  derivación objetivas.
- `high` dispara SPEC-REVIEWER SIEMPRE (override del trigger condicional).
- `high` con ROLLBACK irreversible exige compensación/contención (§9) y
  `approver` humano documentado.
- `low/normal` mantienen el trigger condicional actual.
- SPEC-REVIEWER emite `REVISE` si el `risk` declarado contradice señales del
  A.SPEC: todo nivel declarado **menor** al sugerido por las señales
  (`low` o `normal` con señales de `high`) se subvalora → `REVISE`. Un nivel
  declarado mayor (conservador) NO llama a `REVISE`.

## INVARIANTS

```yaml
invariants:
  - "Los 3 niveles se derivan de señales del A.SPEC (inferencia externa
    queda prohibida)."
  - "El Trigger contract de SPEC-REVIEWER: condicional para low/normal,
    incondicional para high. Semántica de veredicto REVISE/SPLIT/REJECT intacta."
  - "Veredictos de VERIFIER y TRACE no cambian con el tiering."
  - "El protocolo clean-context de los jueces se preserva."
  - "La estructura task-tools no se reorganiza; solo se agrega la dimensión
    risk en SPEC-REVIEWER (texto)."
  - "Sin cambios de código de producto."
  - "A.SPECs integradas existentes siguen grandfathered (norma aplica a nuevas
    o re-abiertas)."
```

Correspondencia `must_not_affect` → INVARIANTS (§7.1 del canon):

- verdict routing VERIFIER/TRACE → invariante "Veredictos de VERIFIER y TRACE no cambian".
- clean-context → invariante "protocolo clean-context se preserva".
- estructura task-tools → invariante "estructura task-tools no se reorganiza".
- A.SPECs integradas → invariante "grandfathered".
- runtime/producto → invariante "sin cambios de código de producto".
- derivación por señales → invariante "Los 3 niveles se derivan de señales".

## VERIFICATION

- `grep -F "risk:" ADD/ASPEC-TEMPLATE.md` → campo presente en plantilla.
- `grep -F "ceremonia proporcional" ADD/SPECIFICATION.md` → §4.1 presente
  (frase a pin near al redactar).
- `grep -F "SPEC-REVIEWER SIEMPRE" AGENTS.md` → enforcement high presente.
- `grep -F "approver:" ADD/ASPEC-TEMPLATE.md` → campo approver en plantilla.
- SPEC-REVIEWER incluye dimensión `risk` (inspección del archivo).
- Ejecución de prueba (fixtures inline, sin archivos en el repo):
  - Caso `high` deshonesto: A.SPEC ficticia con `risk: high` y ROLLBACK
    irreversible sin compensación → SPEC-REVIEWER hallazgo ROLLBACK (§9) → REVISE.
  - Caso `high` honesto (control positivo): A.SPEC ficticia con `risk: high`,
    señales de alto (stock) y ROLLBACK con compensación (§9) → sin hallazgos de
    risk/rollback → sin REVISE (prueba sin falso-positivo).
  - Caso `risk-mismatch`: A.SPEC ficticia con `must_not_affect: [stock]` pero
    `risk: low` → SPEC-REVIEWER marca `REVISE` por riesgo subvalorado.
  - Caso `low`: A.SPEC ficticia sin señales, `risk: low` → sin hallazgo de risk
    (no se eleva por capricho).

## ROLLBACK

Reversible: revertir commit del submódulo; §4.1, campo `risk` y dimensión
`risk` se revientan con el revert. Sin migraciones.

## Change Surface

```yaml
change_surface:
  allowed:
    - ADD/SPECIFICATION.md
    - ADD/ASPEC-TEMPLATE.md
    - ADD/task-tools/SPEC-REVIEWER.md
    - AGENTS.md
    - SPEC-ADD/core/CORE-003.md
  prohibited:
    - plugins/**
    - apps/**
    - vendor/**
    - ADD/task-tools/VERIFIER.md
    - ADD/task-tools/TRACE.md
    - ADD/task-tools/GENERATOR.md
    - ADD/task-tools/SPECCER.md
    - ADD/task-tools/ATOMIZER.md
```

## Blast Radius

```yaml
blast_radius:
  direct:
    - add.spec_reviewer.risk_dimension
    - add.specification.risk_tiering
  indirect:
    - agentes que clasifican A.SPECs futuras (ceremonia por nivel)
    - fluencia de integración high (approver humano)
  must_not_affect:
    - verdict routing de VERIFIER/TRACE
    - clean-context protocol de jueces
    - estructura task-tools
    - A.SPECs integradas existentes
    - runtime/producto del sistema
```

## Composition

```yaml
composition:
  requires_aspecs: []
  must_compose_with:
    - CORE-001 # invariantes §7.1: risk también se valida por completitud
    - CORE-004 # reversibilidad probada (futura; high exigirá downgrade-test)
    - CORE-006 # ownership/approver como rol permanente (futura)
  systemic_invariants:
    - "La ceremonia de un A.SPEC es proporcional a su riesgo declarado y honesto."
  composition_checks:
    - "high SIEMPRE tiene spec-review + approver. low nunca exige approver."
```

## Structural Constraints

```yaml
structural_constraints:
  primary_rule: normas cortas en SPECIFICATION + campo en template + dimensión
    en SPEC-REVIEWER
  entrypoints_must_stay_thin: true
  review_threshold_lines: 400
  extraction_threshold_lines: 600
  preferred_new_logic_locations:
    - ADD/SPECIFICATION.md
    - ADD/task-tools/SPEC-REVIEWER.md
```

## Traceability

- Requirement: plan de madurez ADD — mejora nº3 (risk-tiering), acordado en
  sesión 2026-08-26. Definida aquí: ceremonia proporcional al riesgo declarado.
- Commit: al ejecutar (1 en submódulo + 1 bump en repo padre; AGENTS.md en
  repo padre).
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