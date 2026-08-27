# A.SPEC CORE-007 — Consistencia normativa del canon: cierre del meta-review

> `risk: normal` — canon, derivación §4.1: cambio reversible (revert del commit
> del submódulo); sin señales high (no dinero/stock/auth/tenancy/lg_* ni
> migraciones destructivas). No es `low` porque el blast radius indirecto toca
> el comportamiento de todos los jueces vía lectura fresca del canon.

## WHY

Hoy persistió el meta-review normativo de `ADD/SPECIFICATION.md` con veredicto
**REVISE-CANON**: la revisión cruzó seis dimensiones (consistency, evaluability,
coverage, factual, ambiguity, redundancy) y arrojó nueve findings (F1–F9,
preservados verbatim al final de esta A.SPEC). Dejan el canon con **normas
huérfanas** (MUST sin juez asignado: F2, F5, F7), **referencias desactualizadas**
(tabla §1 faltante vs template: F3; árbol §11 mismatch: F4), convenciones sin
base normativa que causan FAILs sistemáticos (F1), cláusulas solo-prosa fuera de
sus checks mecánicos (F6), riesgo de divergencia silenciosa canon↔tool (F8) y el
propio tamaño/sincronización del monolito (F9, decisión del owner declarada como
límite honesto, no promesa diferida). El veredicto obliga a restaurar el canon;
esta A.SPEC materializa ese cierre según el patrón de familia CORE-001..006.

## WHAT

Una verdad nueva del propio canon: **re-ejecutar el mapa de cobertura de jueces
+ mapa factual + detección de ambigüedades sobre el canon parchado rinde cero
findings** — el canon queda sin normas huérfanas ni referencias desactualizadas
según las seis dimensiones del meta-review.

La transición completa se materializa con NUEVE parches de texto en
`ADD/SPECIFICATION.md`, cada uno resolviendo su finding SIN tocar ningún
task-tool (superficie mínima honesta por fix, ver Change Surface):

1. **F1 → §5**: cláusula formalizando el convenio ausente: *el `.md` de la
   propia A.SPEC entra en su propia `change_surface.allowed` cuando su contrato
   viaja en el mismo commit* (hoy carece de base normativa y causa FAILs
   sistemáticos de TRACE check 2). Fix = 1 línea/cláusula en §5.
2. **F2 → §7.1**: frase que hace evaluable el contrast-check: la cobertura de
   proof NO termina en coincidencia nominal — VERIFIER está OBLIGADO a
   contrastar cada proof nombrada contra el artefacto real (leer el test /
   ejecutar); una proof inflada no cierra PASS. Verifier ya lee SPECIFICATION
   fresca en cada corrida (procedimiento VERIFIER paso 1) → basta canon.
3. **F3 → §1**: actualizar la tabla de secciones obligatorias contra
   ASPEC-TEMPLATE/canon, agregando las filas faltantes: risk (§4.1),
   Change Surface (§5), Blast Radius (§6), Composition (§10.1),
   Structural Constraints (§12), Traceability owner/approver (§10.2), DoD (§8).
4. **F4 → §11**: corregir el árbol de estructura MISMATCH: agregar README.md,
   LICENSE, task-tools/, skills/ (examples//schemas/ quedan correctamente
   marcados opcionales).
5. **F5 → §12.4–12.5**: asignar dueño ejecutor/juez para las MUST estructurales
   post-IMPLEMENT: **ATOMIZER es el juez estructural ejecutor** al cruzar
   umbrales (ya lee el canon fresco y tiene orden de juicio cohesión→acoplamiento
   →navegabilidad→tamaño y red flags propios); SPEC-REVIEWER mantiene su chequeo
   del plan pre-implementación (dimensión 8, sin cambio). Cruce de trigger
   §12.4 sin invocación de ATOMIZER y sin A.SPEC estructural pareada abierta
   se emite como **GAP estructural por VERIFIER** sobre hechos del árbol
   (conteo de líneas/motivos de cambio), nunca PASS. Evaluación por fix:
   supercie mínima honesta es solo canon porque ambos jueces ya derivan sus
   deberes de SPECIFICATION.md en cada corrida.
6. **F6 → §10.2**: aclarar explícitamente que el presence-check NO verifica la
   regla de no-auto-asignación (no-self-assign); esa prohibición queda como
   norma de governance de autoría, fuera del check mecánico.
7. **F7 → §10.1**: cláusula de hoja: quien **ejecuta y registra los resultados**
   de los `composition_checks` de una A.SPEC hoja es VERIFIER (`verify-composition`)
   durante VERIFY, y los resultados quedan registrados como proof de composición
   junto al cierre (complementa la división de trabajo existente COMPOSER/VERIFIER).
8. **F8 → §13.5**: cláusula que cita `ADD/task-tools/TRACE.md` como fuente
   espejada de las reglas de discovery de checks (commit→test, commit→migración):
   esas reglas viven SOLO en el task-tool y toda enmienda futura debe
   sincronizar canon↔tool en el mismo cambio.
9. **F9 → límite estructural (no patch de norma diferida)**: decisión del owner
   escrita así: opción (b) dividir el canon en artículos es EXPLÍCITAMENTE OUT
   OF SCOPE aquí (se reabre solo si cruza 600 líneas o nueva ronda CORE). La
    opción (a) MANTENER monolito mientras <= 600 líneas se declara como invariante
   de sincronización: las tablas §1 y el árbol §11 se sincronizan en TODA
   enmienda futura al canon (nota normativa corta bajo §11).

Ningún `.md` de task-tool cambia: cada fix es puro de canon y el juez/ejecutor
que cada norma requiere ya existe entre los herramientas actuales leyendo el
canon fresco (SPECCER/SPEC-REVIEWER/GENERATOR/VERIFIER/COMPOSER/TRACE/ATOMIZER).

## SCOPE

- `ADD/SPECIFICATION.md` — los nueve parches F1–F9 descritos en WHAT.
- `SPEC-ADD/core/CORE-007.md` — esta A.SPEC (repo padre).

## OUT OF SCOPE

- **Split del canon en artículos (opción b de F9)**: EXPLÍCITAMENTE FUERA DE
  SCOPE — decisión futura del owner; se reabre solo si SPECIFICATION.md cruza
  600 líneas o hay nueva ronda CORE. Este límite es parte del contrato de esta
  A.SPEC, no una promesa diferida de verdad propia.
- Cambios en CUALQUIER task-tool (`ADD/task-tools/**`), incluido TRACE.md
  aunque F8 lo cite: la fuente espejada se declara desde el canon, el espejo
  queda intacto en este cambio.
- `ADD/MANIFESTO.md` y `ADD/ASPEC-TEMPLATE.md`.
- CI/binding automatizando jueces o greps.
- Código de producto (plugins/apps/vendor).
- Re-edición de otras A.SPECs integradas (grandfathered).

## CONTRACT

Precondiciones:

- Canon actual = resultado integrado de CORE-001..CORE-006 (frases pinneadas y
  secciones existentes operativas).
- Meta-review REVISE-CANON persistido (source de verdad de F1–F9).
- Task tools actuales operativos (jueces existentes).

Postcondiciones:

- Las nueve cláusulas/normas descritas existen en el canon AHORA (pins
  verificables por grep, listados en VERIFICATION).
- Re-ejecución de los tres mapas del meta-review sobre el canon parchado:
  **0 findings** (F1–F9 resueltos uno a uno + barrido de nuevos hallazgos
  introducidos por el propio parche, incluida la prohibición de huérfanas
  nuevas: toda cláusula añadida tiene juez o executor ya declarado entre los
  jueces existentes).
- SPECIFICATION.md mantiene arquitectura monolítica dentro del presupuesto
  <= 600 líneas (wc -l; límite contract unificado con invariante #6 y F9).
- Ninguna sección del canon pierde frase pinneada histórica (suite greps
  previa sigue pasando).

## INVARIANTS

```yaml
invariants:
  - "Los archivos ADD/task-tools/*.md quedan byte-idénticos (NINGÚN task-tool
    se modifica)."
  - "ADD/MANIFESTO.md y ADD/ASPEC-TEMPLATE.md quedan byte-idénticos."
  - "La semántica de veredictos del ciclo (REVISE/SPLIT/REJECT/PASS/FAIL/GAP)
    no cambia; los parches agregan cláusulas, no redefinen veredictos."
  - "El protocolo clean-context de los jueces se preserva."
  - "Las normas grandfathered se mantienen: las A.SPECs integradas existentes
    no quedan invalidadas (frase 'Aplica a A.SPECs nuevas o re-abiertas' y
    equivalente del patch preservan esa lógica)."
  - "El presupuesto estructural se respeta: SPECIFICATION.md <= 600 líneas tras
    el parche (límite honesto de F9), sin split en artículos."
  - "No se introduce NINGUNA nueva norma huérfana: cada cláusula añadida nombra
    juez/executor existente (verifier/reviewer/atomizer/composer/trace)."
  - "Sin cambios de código de producto."
```

Correspondencia `must_not_affect` → INVARIANTS (§7.1):

- ADD/task-tools/** → invariante "byte-idénticos".
- MANIFESTO.md / ASPEC-TEMPLATE.md → ídem.
- veredict routing global → invariante "semántica de veredictos no cambia".
- clean-context → invariante "protocolo clean-context se preserva".
- A.SPECs integradas → invariante "grandfathered se mantienen".
- monolito del canon → invariante "<=600 líneas, sin split" (límite F9).
- integridad del propio patch → invariante "ningún nuevo huérfano introducido".
- runtime/producto → invariante "sin cambios de código de producto".

## VERIFICATION

Convención: comandos desde el root del repo padre; SHA placeholder `<base>`
= estado integrado pre-CORE-007, `<head>` = commit de integración de esta
A.SPEC (llenar con SHAs literales al ejecutar, patrón TRACE).

Comprobación de superficies (dif por diffs):

- `git -C ADD diff --name-only <base> <head>` → única entrada
  `SPECIFICATION.md` (prueba invariante #1).
- `git diff --name-only <padre-base> <padre-head>` → solo el gitlink `ADD`
  y `SPEC-ADD/core/CORE-007.md` (prueba invariante #8; MANIFESTO/TEMPLATE
  incluidos en el no-diff del submódulo → invariantes #2).

Comprobación de veredictos/clean-context/grandfathered (inspección de dif +
grep pinneado):

- Inspección del dif completo de SPECIFICATION.md: ninguna línea definitoria
  de veredictos eliminada o alterada (invariante #3).
- `grep -F "Aplica a A.SPECs nuevas o re-abiertas" ADD/SPECIFICATION.md` →
  presente (invariante #5).
- Frases pinneadas históricas siguen presentes:
  `grep -F "presence-check" ADD/SPECIFICATION.md`,
  `grep -F "no puede auto-asignarse" ADD/SPECIFICATION.md`.
- Para clean-context (invariante #4): inspección del dif del submódulo —
  los archivos `ADD/task-tools/*.md`, `ADD/MANIFESTO.md` y
  `ADD/ASPEC-TEMPLATE.md` no aparecen en el diff (byte-identity según
  invariantes #1/#2) Y ninguna línea de sus secciones "Clean-context note"
  cambia (no basta el file-set). Patrón familia CORE-006.

Grep pins por fix (nuevos, en el módulo después del parche):

- F1: `grep -F "entra en su propia change_surface.allowed" ADD/SPECIFICATION.md`
- F2: `grep -F "coincidencia nominal" ADD/SPECIFICATION.md`
- F3: tabla §1 contiene las 7 filas nuevas:
  `grep -Fn "risk (§4.1)" ADD/SPECIFICATION.md`,
  `grep -Fn "Change Surface (§5)" ADD/SPECIFICATION.md`,
  `grep -Fn "Blast Radius (§6)" ADD/SPECIFICATION.md`,
  `grep -Fn "Composition (§10.1)" ADD/SPECIFICATION.md`,
  `grep -Fn "Structural Constraints (§12)" ADD/SPECIFICATION.md`,
  `grep -Fn "Traceability (§10.2)" ADD/SPECIFICATION.md`,
  `grep -Fn "DoD (§8)" ADD/SPECIFICATION.md`
- F4: árbol §11 contiene:
  `grep -F "README.md" ADD/SPECIFICATION.md`,
  `grep -F "LICENSE" ADD/SPECIFICATION.md`,
  `grep -F "task-tools/" ADD/SPECIFICATION.md`,
  `grep -F "skills/" ADD/SPECIFICATION.md`
- F5: `grep -F "juez estructural ejecutor" ADD/SPECIFICATION.md`
- F6: `grep -F "El presence-check NO verifica" ADD/SPECIFICATION.md`
- F7: `grep -F "ejecuta y registra los resultados" ADD/SPECIFICATION.md`
- F8: `grep -F "fuente espejada" ADD/SPECIFICATION.md`
- F9: `wc -l ADD/SPECIFICATION.md` → <= 600 (misma cota que invariante #6);
  y NOT-inverted:
  `! grep -F "dividirá el canon" ADD/SPECIFICATION.md`

Presupuesto huérfano-cero (invariante #7, borde del patch): inspección del
dif — cada cláusula añadida referencia juez/executor nombrado
(verifier/spec-reviewer/atomizer/composer/trace).

Enforcement-by-change-surface (proof de invariantes estructurales):

- Dif por dif demostrando superficie mínima: solo el archivo canónico cambia.

Ejecución de prueba (fixtures inline, sin archivos en el repo):

- Caso `GAP` (contraste F2): A.SPEC ficticia cuya proof nombrada apunta a un
  artefacto que no existe/no coincide (test distinto al declarado) → VERIFIER
  contrasta artefacto real vs proof nombrada → `GAP` (nunca `PASS` por mapeo
  nominal).
- Caso `PASS` (contraste F2): misma A.SPEC con proof contrastable (artefacto
  real leído/ejecutado con resultado registrado) → coverage válido sin
  hallazgo de contraste.
- Caso `GAP` (estructural F5): archivo sintético >400 líneas con nueva
  responsabilidad observable y multi-motivo de cambio, sin invocación de
  ATOMIZER y sin A.SPEC estructural pareada en el árbol → obligación
  §12.4 violada se evalúa como `GAP` estructural (nunca `PASS`), y con
  tratamiento ATOMIZER/A.SPEC pareada cerrado → sin hallazgo estructural.

VERIFICACIÓN CLAVE — re-review delta (demuestra la verdad candidata):

- Relanzar los tres mapas del meta-review (mapa de cobertura de jueces, mapa
  factual, detección de ambigüedades) sobre el canon parchado, mismo alcance
  dimensional (consistency, evaluability, coverage, factual, ambiguity,
  redundancy), modo delta: la lista F1–F9 se re-verifica finding por finding
  (cada uno pasa a estado RESUELTO citando el pinneado correspondiente) y se
  barre el dif completo buscando hallazgos NUEVOS introducidos por el parche
  (incluye la regla "sin huérfanas nuevas").
- Resultado exigible: reporte de re-review con contador **0 findings**
  almacenado/citado como evidence al ejecutar. Un solo hallazgo pendiente →
  el cierre de esta A.SPEC queda FAIL (nunca PASS parcial).

## ROLLBACK

Reversible: `git -C ADD revert <head>` deshace el parche de canon; en el repo
padre, restaurar el gitlink anterior de `ADD`. Sin migraciones, sin datos, sin
side-effects externos: el estado pre-meta-review queda exactamente reproducible.

## Change Surface

```yaml
change_surface:
  allowed:
    - ADD/SPECIFICATION.md
    - SPEC-ADD/core/CORE-007.md
  prohibited:
    - ADD/MANIFESTO.md
    - ADD/ASPEC-TEMPLATE.md
    - ADD/task-tools/SPECCER.md
    - ADD/task-tools/SPEC-REVIEWER.md
    - ADD/task-tools/GENERATOR.md
    - ADD/task-tools/VERIFIER.md
    - ADD/task-tools/COMPOSER.md
    - ADD/task-tools/TRACE.md
    - ADD/task-tools/ATOMIZER.md
    - ADD/task-tools/README.md
    - ADD/examples/**
    - ADD/schemas/**
    - AGENTS.md
    - plugins/**
    - apps/**
    - vendor/**
```

Nota TRACE check 2: el presente `.md` entra en su propia `change_surface.allowed`
conforme a la convención formalizada por F1 (su contrato viaja en este mismo
cambio); viniendo de padre, vive en repo padre — no usa la vía submodule.

## Blast Radius

```yaml
blast_radius:
  direct:
    - add.specification.canon_text (§1, §5, §7.1, §10.1, §10.2, §11, §12.4–12.5, §13.5)
  indirect:
    - comportamiento de SPECCER/SPEC-REVIEWER/GENERATOR/VERIFIER/COMPOSER/TRACE/
      ATOMIZER vía lectura fresca del canon (reglas asociadas: evaluability de
      proof, escalación de descubrimiento TRACE, extracción ATOMIZER)
    - flujo futuras rondas CORE (presupuesto de líneas del monolito)
  must_not_affect:
    - contenido de task-tools (add.task_tools)
    - manifest/template del canon (add.manifesto, add.template)
    - semántica de veredictos del ciclo
    - protocolo clean-context de jueces
    - A.SPECs integradas existentes
    - runtime/producto del sistema
```

## Composition

```yaml
composition:
  requires_aspecs:
    - CORE-006 # F6 enmienda la norma de presence-check que introdujo §10.2
    - CORE-002 # F8 declara fuente espejada sobre las reglas TRACE ancladas en §13.5
  must_compose_with: []
  systemic_invariants:
    - "El canon ADD no contiene normas huérfanas ni referencias desactualizadas
      según las seis dimensiones del meta-review."
  composition_checks:
    - "Suite de greps pinneados (históricos + nuevos pins F1–F9) verde."
    - "wc -l ADD/SPECIFICATION.md -> a lo sumo 600 líneas (misma cota que invariante #6)."
    - "Dif por dif: único archivo cambiado en el submódulo es
       SPECIFICATION.md; sin archivos de producto tocados."
```

Los `composition_checks` de esta hoja los juzga VERIFIER (`verify-composition`),
y sus resultados se registran como proof de composición conforme a la cláusula
de ejecutor/registro que este mismo cambio añade a §10.1 (auto-coherencia del
parche, verificación VIVA del convenio F7).

## Structural Constraints

```yaml
structural_constraints:
  primary_rule: parches de canon como una sola transición textual coherente
  entrypoints_must_stay_thin: true
  review_threshold_lines: 400
  extraction_threshold_lines: 600
  preferred_new_logic_locations:
    - ADD/SPECIFICATION.md
```

## Traceability

- Requirement: meta-review normativo de ADD/SPECIFICATION.md con veredicto
  REVISE-CANON (persistido hoy). El cierre del canon según esas nueve señales
  ES el requisito; el mismo veredicto obligó a este DEFINE. Definida aquí:
  cierre de las 9 señales con verdad única "re-review rinde 0 findings".
  Los findings transcritos son la fuente normativa de los nueve parches.
- owner: Owner del canon ADD (rol)
- approver: Approver del repo padre Systutor-oss (rol)
- Commit: d91694d (submódulo `ADD`, canon) + b9d4eb7 (bump gitlink en repo
  padre, incluye este .md).
- Deployment: canon ADD vía commit del submódulo + bump del gitlink.

### Fuente normativa — findings del meta-review (verbatim)

- F1 (major/consistency §5): convenio "el .md de la A.SPEC entra en su propia
  change_surface.allowed cuando su contrato viaja en el mismo commit" no tiene
  base normativa — causa FAILs sistemáticos de TRACE check 2. Fix = 1
  línea/cláusula en §5.
- F2 (major/evaluability §7.1): validación de proof explícita HUÉRFANA —
  GENERATOR auto-cuenta resultados de comandos y VERIFIER no está OBLIGADO a
  contrastar el proof nombrado contra el artefacto real (leer el test/ejecutar),
  solo a mapearlo nominalmente → proof inflada pasa. Fix = 1 frase en §7.1 que
  haga evaluable el contrast-check.
- F3 (major/coverage §1): tabla de secciones obligatorias desactualizada vs
  ASPEC-TEMPLATE/canon — faltan risk (§4.1), Change Surface (§5), Blast Radius
  (§6), Composition (§10.1), Structural Constraints (§12), Traceability
  owner/approver (§10.2), DoD (§8). Fix = actualizar tabla.
- F4 (minor/factual §11): árbol de estructura MISMATCH — faltan README.md,
  LICENSE, task-tools/, skills/ (examples//schemas/ opcionales están ok
  ausentes).
- F5 (major/evaluability §12.4–12.5): MUST estructurales post-IMPLEMENT
  (extracción obligatoria al cruzar umbrales) SIN JUEZ asignado — nadie puede
  emitir GAP por su violación. Fix = asignar dueño ejecutor (candidatos:
  ATOMIZER como juez estructural; SPEC-REVIEWER ya chequea el plan en dim 8;
  decláralo tú coherentemente con los task tools existentes).
- F6 (minor/ambiguity §10.2): prohibición de auto-asignación owner/approver es
  solo-prosa fuera del presence-check mecánico → aclarar explícitamente que el
  presence-check NO verifica no-self-assign (queda como norma de governance,
  no check mecánico).
- F7 (minor/ambiguity §10.1): composition_checks de hoja — juez asignado
  (VERIFIER verify-composition) pero EJECUTOR y REGISTRO de resultados sin
  dueño. Fix = cláusula: quien ejecuta y registra resultados de checks de hoja.
- F8 (minor/redundancy §13.5 ↔ ADD/task-tools/TRACE.md): reglas discovery de
  TRACE viven SOLO en el task-tool; espejo canon↔tool puede divergir
  silenciosamente. Fix = cláusula en §13.5 que norme la sincronización o cite
  el task-tool como fuente espejada.
- F9 (structura/tamaño del propio canon, elevado por el owner tras el review):
  SPECIFICATION.md tiene 531 líneas (>400 umbral revisión). Decisión del owner
  declarada aquí: opción (a) MANTENER monolito mientras <= 600 líneas, pero
  convertir en INVARIANTE estructural del canon que las tablas §1 y árbol §11
  se sincronicen en TODA enmienda futura; la opción (b) split en artículos es
  EXPLÍCITAMENTE OUT OF SCOPE / decisión futura (reabrir solo si cruza 600 o
  nueva ronda CORE). Esto debe quedar escrito así en la spec (no como
  promesa diferida de verdad propia — como límite honesto de esta).

> **Nota (CORE-009, 2026-08-27):** el presupuesto de líneas `<=600` dejó de
> ser contrato duro. §4.2 del canon ahora trata los umbrales como heurística
> de cohesión también para SPECIFICATION.md; el trigger real de división es
> que el documento pierda su única razón de cambio, no una cifra. El monolito
> se mantiene mientras cumpla esa función única (decisión owner).

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
