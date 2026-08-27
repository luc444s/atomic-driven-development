# A.SPEC CORE-005 — Composition gate: integración de A.SPEC con dueño

> `risk: normal` — canon, sin señales de high (§4.1)

## WHY

SPECIFICATION §10 declara que una secuencia de A.SPEC localmente correctas puede
ser globalmente incorrecta, y que "una release o capability compuesta MAY
requerir checks propios de integración, orden o sistema". Pero eso es
**advertencia, no mecanismo**: hoy cada A.SPEC se cierra con su propio DO y no
existe un gate que ejecute los `composition_checks` de un conjunto antes de
integrarlo como release. El CI wrapper lo sugiere pero no hay artefacto que
defina quién es el dueño de la composición, qué chequeos corren, en qué orden,
ni qué veredicto bloquea. Resultado: integraciones que fallan por interacción
entre A.SPEC se descubren en runtime, no en la puerta de entrega.

## WHAT

Una propiedad estructural nueva del canon: **todo conjunto de A.SPEC que se
integra como release/capability tiene una A.SPEC de integración (compuesta)
con `composition_checks` ejecutables, un dueño declarado, y un veredicto de
composición que bloquea la integración si falla.**

1. `ADD/task-tools/COMPOSER.md` — nuevo task tool (juez, contexto limpio) con
   modo `compose-gate` (nombre propio, SIN colisión con el modo
   `verify-composition` de VERIFIER): toma la A.SPEC de integración, extrae
   `composition.systemic_invariants` + `composition_checks`, ejecuta los checks
   en el orden declarado, y emite `PASS`/`FAIL`/`GAP`. Un check roto o ausente
   → `GAP`; un check que corre y falla → `FAIL`; todo verde → `PASS`.
   **División de trabajo (explícita):** `composition_checks` de una A.SPEC
   hoja/individual → los juzga `VERIFIER.verify-composition`. Los
   `composition_checks` de una A.SPEC de integración (nivel set/release) → los
   juzga `COMPOSER.compose-gate`. No se corren dos jueces sobre el mismo check.
2. `ADD/SPECIFICATION.md` §10.1 — norma: una release/capability compuesta exige
   una A.SPEC de integración que declara `composition` con `owner`, `checks`
   ordenados y `systemic_invariants`. Sin A.SPEC de integración o sin owner:
   la integración del conjunto queda `GAP`. COMPOSER bloquea: `FAIL` o `GAP`,
   nunca `PASS` sin evidencia de composición. División de trabajo: los
   `composition_checks` de A.SPEC hoja los juzga VERIFIER (verify-composition);
   los de la A.SPEC de integración (nivel set) los juzga COMPOSER
   (compose-gate). Verificación de `owner`: COMPOSER verifica **presencia**
   (ausencia → `GAP`); la *humanidad* del owner es norma de autoría y, en
   conjuntos tiering high, la puerta humana la da CORE-003 (`approver`).
3. `ADD/ASPEC-TEMPLATE.md` — hint en la sección Composition: cuando la A.SPEC
   sea de integración, declarar `owner:` y `composition_checks` ordenados y
   ejecutables. Las A.SPEC hoja MANTIENEN su `composition.must_compose_with`,
   sin necesidad de nueva sección.
4. `ADD/task-tools/README.md` + `ADD/README.md` — COMPOSER en índices con rol
   RELEASE/COMPOSE.

El `owner` es una persona o rol humano responsable de la integración del
conjunto; el agente ejecuta COMPOSER pero no puede auto-aprobarse como owner.

## SCOPE

- `ADD/task-tools/COMPOSER.md` — task tool nuevo.
- `ADD/SPECIFICATION.md` — §10.1 norma de composition gate.
- `ADD/ASPEC-TEMPLATE.md` — hint en Composition (owner + checks ordenados).
- `ADD/task-tools/README.md`, `ADD/README.md` — índices.
- `SPEC-ADD/core/CORE-005.md` — esta A.SPEC.

## OUT OF SCOPE

- CI real que ejecute COMPOSER en pipeline (requiere A.SPEC de CI/binding
  futura).
- Ownership como rol permanente con aprobación de integraciones (CORE-006;
  aquí `owner` es el campo de la A.SPEC de integración, no el sistema de
  aprobaciones).
- Risk-tiering de la integración (normal por defecto; si el conjunto toca
  señales high, la A.SPEC de integración declara `risk: high` y aplica CORE-003).
- Cambios en VERIFIER, TRACE, SPEC-REVIEWER, GENERATOR, SPECCER, ATOMIZER.
- Cualquier cambio de código de producto.

## CONTRACT

Precondiciones:

- La A.SPEC de integración declara `composition` (template §Composition) con
  `owner`, `composition_checks` y `systemic_invariants`.
- Cada check es un comando/procedimiento ejecutable y nombrado.

Postcondiciones:

- COMPOSER extrae checks en orden declarado y los ejecuta.
- `PASS` solo con todos los checks verdes; `FAIL` si un check declarado corre y
  falla; `GAP` si falta un check, un objetivo es vago o el owner no está.
- Sin A.SPEC de integración, un conjunto no pasa COMPOSER → `GAP`.
- El `owner` es verificado por COMPOSER en **presencia** (ausencia → GAP); la
  naturaleza humana del owner es norma de autoría, y para conjuntos con señales
  de tiering high la puerta humana la exige CORE-003 (`approver`). El agente no
  puede aprobarse a sí mismo como owner.
- §10 (advertencia) queda complementada por §10.1 (mecanismo) sin contradicción.

## INVARIANTS

```yaml
invariants:
  - "COMPOSER es juez: ejecuta y juzga los checks declarados; no inventa checks
    ni objetivos ni owners."
  - "El protocolo clean-context de los jueces se preserva (COMPOSER vía Task,
    contexto limpio)."
  - "El veredicto de composición no re-juzga contract/invariants de las hojas
    (eso es VERIFIER); juzga SOLO el conjunto."
  - "Las A.SPEC hoja no requieren sección nueva; su composition.must_compose_with
    se mantiene como hoy."
  - "La estructura task-tools no se reorganiza; solo se agrega COMPOSER.md."
  - "Sin cambios de código de producto."
  - "A.SPECs integradas existentes quedan grandfathered; la norma aplica a
    conjuntos nuevos o re-abiertos."
```

Correspondencia `must_not_affect` → INVARIANTS (§7.1):

- verdict routing de hojas (VERIFIER) → invariante "no re-juzga contract/invariants de las hojas".
- clean-context → invariante "protocolo clean-context se preserva".
- estructura task-tools → invariante "estructura task-tools no se reorganiza".
- A.SPECs integradas → invariante "grandfathered".
- runtime/producto → invariante "sin cambios de código de producto".
- hoja sin sección nueva → invariante "A.SPEC hoja conserva su formato".

## VERIFICATION

- `grep -F "A.SPEC de integración" ADD/SPECIFICATION.md` → §10.1 presente
  (frase pinneada; el §10 preexistente no vale).
- `ls ADD/task-tools/COMPOSER.md` → existe.
- COMPOSER incluye modo `compose-gate` y extrae `owner` (inspección del
  archivo).
- Enforced-by-change-surface (proof de invariantes estructurales):
  `git diff --name-only <base> <head>` → todos los paths bajo
  `change_surface.allowed`, ninguno bajo `prohibited` (cubre estructura
  task-tools + formato de A.SPEC hoja + sin cambios de producto).
  `grep -F "grandfathered" ADD/SPECIFICATION.md` → grandfathered intacto.
  `grep -F "Subagent system prompt" ADD/task-tools/COMPOSER.md` → COMPOSER es
  juez con contexto limpio (cubre clean-context).
- Ejecución de prueba (fixtures inline, sin archivos en el repo):
  - Caso `GAP`: A.SPEC de integración ficticia con `composition_checks: []` o
    sin `owner` → COMPOSER `GAP`.
  - Caso `FAIL`: con `composition_checks` que incluye un check que falla →
    `FAIL`.
  - Caso `PASS`: con checks ejecutables verdes + owner → `PASS`.
  - Caso "hoja": una A.SPEC hoja ficticia sin `owner` ni checks → COMPOSER no
    bloquea por eso (sigue siendo tarea de VERIFIER); si un conjunto sin A.SPEC
    de integración se somete → `GAP` por falta de integración.

## ROLLBACK

Reversible: revertir commit del submódulo; COMPOSER.md se elimina, §10.1 y
hints se revientan. Sin migraciones.

## Change Surface

```yaml
change_surface:
  allowed:
    - ADD/task-tools/COMPOSER.md
    - ADD/SPECIFICATION.md
    - ADD/ASPEC-TEMPLATE.md
    - ADD/task-tools/README.md
    - ADD/README.md
    - SPEC-ADD/core/CORE-005.md
  prohibited:
    - plugins/**
    - apps/**
    - vendor/**
    - ADD/task-tools/VERIFIER.md
    - ADD/task-tools/TRACE.md
    - ADD/task-tools/SPEC-REVIEWER.md
    - ADD/task-tools/GENERATOR.md
    - ADD/task-tools/SPECCER.md
    - ADD/task-tools/ATOMIZER.md
```

## Blast Radius

```yaml
blast_radius:
  direct:
    - add.composer.task_tool
    - add.specification.composition_gate
  indirect:
    - releases/capabilities futuras (integraciones exigen A.SPEC de integración
      con owner y checks)
  must_not_affect:
    - verdict routing de VERIFIER/TRACE/SPEC-REVIEWER (hojas)
    - clean-context protocol de jueces
    - estructura task-tools (fuente única de verdad)
    - formato de A.SPEC hoja
    - A.SPECs integradas existentes
    - runtime/producto del sistema
```

## Composition

```yaml
composition:
  requires_aspecs: []
  must_compose_with:
    - CORE-006 # ownership permanente (futura; owner se consolidará ahí)
  systemic_invariants:
    - "Todo conjunto integrado como release/capability pasa por COMPOSER."
  composition_checks:
    - "Conjunto de 2 A.SPEC hoja sin A.SPEC de integración -> COMPOSER GAP."
    - "A.SPEC de integración con checks verdes + owner -> COMPOSER PASS."
```

## Structural Constraints

```yaml
structural_constraints:
  primary_rule: COMPOSER es juez delgado (leer composition, ejecutar checks,
    emitir veredicto)
  entrypoints_must_stay_thin: true
  review_threshold_lines: 400
  extraction_threshold_lines: 600
  preferred_new_logic_locations:
    - ADD/task-tools/COMPOSER.md
```

## Traceability

- Requirement: plan de madurez ADD — mejora nº5 (composición/release gate con
  dueño), acordado en sesión 2026-08-26. Definida aquí: A.SPEC de integración
  con owner + checks ordenados, juzgada por COMPOSER antes de integrar el set.
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