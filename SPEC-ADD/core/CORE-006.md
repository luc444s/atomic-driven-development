# A.SPEC CORE-006 — Governance: owner/approver estructural y escalación

> `risk: normal` — canon, sin señales de high (§4.1)

## WHY

Hoy la gobernanza está fragmentada y no es estructural. CORE-005 introdujo
`owner` pero solo como *presence check* de la A.SPEC de integración; CORE-003
introdujo `approver` pero solo para conjuntos `risk: high` (aprobación humana
antes de integrar). Ningún campo obliga una A.SPEC *ordinaria* a declarar quién
responde por ella ni quién la libera, y el camino de escalación de
REVISE/SPLIT/REJECT no nombra a nadie: "se devuelve al usuario" queda difuso
cuando hay múltiples propietarios, equipos o agentes. Resultado: cambios sin
responsable verificable y desescaladas ad hoc.

## WHAT

Una propiedad estructural nueva del canon: **toda A.SPEC declara `owner` y
`approver` en Traceability; el approver es el punto de escalación de los
veredictos REVISE/SPLIT/REJECT y de la liberación (integración) del cambio.**

1. `ADD/ASPEC-TEMPLATE.md` — Traceability gana campos `owner:` y `approver:`
   con hint. `owner` = responsable del cambio; `approver` = quien libera la
   integración. Campos obligatorios.
2. `ADD/SPECIFICATION.md` §10.2 — norma de governance (hospedada junto al owner
   de integración de §10.1, cohesión estructural §12.1):
- Toda A.SPEC declara `owner` y `approver` (persona o rol).
   - El `approver` es el destino de escalación de `REVISE` (si no es
     mecánico), `SPLIT` y `REJECT` — reemplaza el vago "se devuelve al
     usuario".
   - La integración (commit/release) requiere approver; en conjuntos de nivel
     `high` (CORE-003), el approver debe ser humano documentado y aprobar
     explícitamente.
   - owner/approver se verifican por **presence-check** (presencia, no veracidad
     humana del rol).
   - El agente no puede auto-asignarse como owner ni approver.
   - Aplica a A.SPECs nuevas o re-abiertas; las integradas quedan
     grandfathered.
   - Campos (disambiguación): `composition.owner` (nivel set, leído por
     COMPOSER) y Traceability `owner`/`approver` (nivel spec, leídos por
     VERIFIER/SPEC-REVIEWER) son **dos campos distintos** con el mismo espíritu;
     COMPOSER no lee Traceability, y VERIFIER no lee composition.owner.
3. `ADD/task-tools/SPEC-REVIEWER.md` — dimensión `governance`: verifica que
   `owner`/`approver` estén presentes en Traceability; ausencia → `REVISE`.
   En veredictos `SPLIT`/`REJECT`, nombra como destino al approver declarado.
4. `ADD/task-tools/VERIFIER.md` — `verify-run` agrega check de governance:
   owner/approver presentes (presence, no veracidad humana). Ausencia → `GAP`.
5. `ADD/task-tools/COMPOSER.md` — ya usa `composition.owner` para integraciones
   (nivel set, campo distinto de Traceability.owner); sin cambio de regla.
6. `AGENTS.md` — enforcement de escalación: reemplazar "`SPLIT`/`REJECT` se
   devuelven al usuario" por "se devuelven al `approver` de la A.SPEC"
   (destino concreto, no vago). Sin cambios en el bloqueo REVISE/claves.

## SCOPE

- `ADD/ASPEC-TEMPLATE.md` — campos `owner`/`approver` + hint en Traceability.
- `ADD/SPECIFICATION.md` — §10.2 governance.
- `ADD/task-tools/SPEC-REVIEWER.md` — dimensión governance.
- `ADD/task-tools/VERIFIER.md` — check governance en verify-run.
- `AGENTS.md` — enforcement: escalación de SPLIT/REJECT al approver.
- `SPEC-ADD/core/CORE-006.md` — esta A.SPEC.

## OUT OF SCOPE

- CI que ejecute aprobaciones (requiere A.SPEC de CI/binding futura).
- Sistema de roles/permisos del producto (auth) — no aplica al canon.
- Cambiar el presence-check de `composition.owner` en COMPOSER: COMPOSER.md
  no recibe diff en esta A.SPEC (está en change_surface.prohibited); su
  lectura de `composition.owner` sigue intacta.
- Cambios en TRACE, GENERATOR, SPECCER, ATOMIZER.
- Cualquier cambio de código de producto.

## CONTRACT

Precondiciones:

- Template con Traceability (§template).
- SPEC-REVIEWER y VERIFIER activos.

Postcondiciones:

- `owner` y `approver` son obligatorios en toda A.SPEC (nueva o re-abierta).
- SPEC-REVIEWER flaggea ausencia → `REVISE`; veredictos `SPLIT`/`REJECT`
  escalan al approver declarado.
- VERIFIER: ausencia de owner/approver → `GAP` (nunca `PASS`).
- En conjuntos `high`, el approver humano ya exigido por CORE-003 se documenta
  en el mismo campo.
- §10.2 no contradice §10.1 (owner de integración) ni §4.1 (approver high).

## INVARIANTS

```yaml
invariants:
  - "owner/approver son presence-check: el verifier/reviewer no juzga la
    veracidad humana del rol (eso queda en la autoría y en CORE-003 para high)."
  - "La semántica de veredictos REVISE/SPLIT/REJECT no cambia; solo su destino
    de escalación (approver)."
  - "El agente nunca se auto-asigna owner ni approver."
  - "Veredictos de TRACE y COMPOSER no cambian por esta norma (solo alineación
    del campo owner en COMPOSER, sin cambio de regla)."
  - "El protocolo clean-context de los jueces se preserva."
  - "La estructura task-tools no se reorganiza."
  - "Sin cambios de código de producto."
  - "A.SPECs integradas existentes quedan grandfathered."
```

Correspondencia `must_not_affect` → INVARIANTS (§7.1):

- verdict routing → invariante "semántica REVISE/SPLIT/REJECT no cambia".
- clean-context → invariante "protocolo clean-context se preserva".
- estructura task-tools → invariante "estructura task-tools no se reorganiza".
- A.SPECs integradas → invariante "grandfathered".
- runtime/producto → invariante "sin cambios de código de producto".
- TRACE/COMPOSER → invariante "veredictos de TRACE y COMPOSER no cambian".
- ausencia veracidad humana → invariante "presence-check, no veracidad".

## VERIFICATION

- `grep -F "owner:" ADD/ASPEC-TEMPLATE.md` → campo obligatorio en template.
- `grep -F "approver:" ADD/ASPEC-TEMPLATE.md` → idem.
- `grep -F "destino de escalación" ADD/SPECIFICATION.md` → §10.2 presente
  (frase pinneada; el término vago "gobernanza" no vale).
- SPEC-REVIEWER incluye dimensión governance (inspección).
- VERIFIER incluye check governance (inspección).
- Enforced-by-change-surface (proof de invariantes estructurales):
  `git diff --name-only <base> <head>` → todos los paths bajo
  `change_surface.allowed`, ninguno bajo `prohibited` (cubre estructura
  task-tools + verdict routing + sin cambios de producto). Para clean-context:
  inspección del diff de VERIFIER/SPEC-REVIEWER confirmando que sus secciones
  "Clean-context note" no cambian (no basta el file-set).
  `grep -cF "governance" ADD/SPECIFICATION.md` → frase "governance" presente en
  §10.2 (grandfathered de governance: `grep -F "Aplica a A.SPECs nuevas o
  re-abiertas" ADD/SPECIFICATION.md`, frase del propio §10.2).
- Proof de invariantes governance:
  `grep -F "presence-check" ADD/SPECIFICATION.md` → presence-not-veracity en
  canon. `grep -F "no puede auto-asignarse" ADD/SPECIFICATION.md` → no-self-assign
  en canon.
- Ejecución de prueba (fixtures inline, sin archivos en el repo):
  - Caso `REVISE` (governance): A.SPEC ficticia sin owner/approver →
    SPEC-REVIEWER `REVISE` por dimensión governance.
  - Caso `GAP` (governance): la misma A.SPEC → VERIFIER `GAP` por owner/approver
    ausentes, sin `FAIL`.
  - Caso `PASS` (governance): A.SPEC con owner/approver → sin hallazgo de
    governance (PASS si el resto está limpio).

## ROLLBACK

Reversible: revertir commit del submódulo; §10.2, campos y dimensiones se
revientan. Sin migraciones.

## Change Surface

```yaml
change_surface:
  allowed:
    - ADD/ASPEC-TEMPLATE.md
    - ADD/SPECIFICATION.md
    - ADD/task-tools/SPEC-REVIEWER.md
    - ADD/task-tools/VERIFIER.md
    - AGENTS.md
    - SPEC-ADD/core/CORE-006.md
  prohibited:
    - plugins/**
    - apps/**
    - vendor/**
    - ADD/task-tools/TRACE.md
    - ADD/task-tools/COMPOSER.md
    - ADD/task-tools/GENERATOR.md
    - ADD/task-tools/SPECCER.md
    - ADD/task-tools/ATOMIZER.md
```

## Blast Radius

```yaml
blast_radius:
  direct:
    - add.governance.fields
    - add.spec_reviewer.governance_dimension
  indirect:
    - flujo de escalación de veredictos (REVISE/SPLIT/REJECT al approver)
  must_not_affect:
    - verdict routing REVISE/SPLIT/REJECT
    - verdicts de TRACE y COMPOSER
    - clean-context protocol de jueces
    - estructura task-tools
    - A.SPECs integradas existentes
    - runtime/producto del sistema
```

## Composition

```yaml
composition:
  requires_aspecs:
    - CORE-003 # approver humano en high (el campo se documenta aquí)
    - CORE-005 # owner de integración (mismo campo, ahora estructural)
  must_compose_with: []
  systemic_invariants:
    - "Todo A.SPEC tiene un responsable (owner) y un liberador (approver) verificables."
  composition_checks:
    - "A.SPEC sin owner/approver -> REVISE (SPEC-REVIEWER) y GAP (VERIFIER)."
    - "A.SPEC con owner/approver -> sin hallazgo de governance."
```

## Structural Constraints

```yaml
structural_constraints:
  primary_rule: campos en template + norma corta + dimensiones en jueces
  entrypoints_must_stay_thin: true
  review_threshold_lines: 400
  extraction_threshold_lines: 600
  preferred_new_logic_locations:
    - ADD/ASPEC-TEMPLATE.md
    - ADD/SPECIFICATION.md
```

## Traceability

- Requirement: plan de madurez ADD — mejora nº6 (governance/ownership),
  acordado en sesión 2026-08-26. Definida aquí: owner/approver estructurales,
  escalación por approver, presencia verificada por jueces.
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