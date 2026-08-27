# A.SPEC CORE-004 — Reversibilidad probada: downgrade ejecutado y verificado

> `risk: normal` — reversible del canon, sin señales de high (§4.1)

## WHY

El campo `ROLLBACK` es prosa. "revertir commit" asume que la migración se puede
deshacer, pero el `downgrade()` de una migración nunca se ejecuta: se declara,
se commit y se archiva. TRACE (CORE-002) verifica que la función `downgrade(`
**exista** en el tree — no que **funcione**. Resultado: una migración con
downgrade escrito pero roto (drop engañoso, referencia a columna inexistente,
orden invertido) deja al equipo con una reversión declarada que no revierte.
La reversibilidad no es una promesa: es una prueba.

## WHAT

Una propiedad operacional nueva del canon: **toda A.SPEC con cambio de schema o
migración debe probar el downgrade ejecutándolo en verification (comando
nombrado + resultado registrado). Sin ejecución probada → la reversibilidad no
es verificable y el A.SPEC queda `GAP`.**

1. `ADD/SPECIFICATION.md` §9.1 — norma: si el `ROLLBACK` de la A.SPEC es por
   migración/downgrade físico, el `VERIFICATION` DEBE incluir el comando que
   ejecuta el downgrade (+ resultado registrado). Sin prueba de ejecución →
   `GAP`, nunca `PASS`. La mera presencia de `def downgrade(` no basta.
2. `ADD/ASPEC-TEMPLATE.md` — hint en ROLLBACK y VERIFICATION: para reversión
   por migración, el downgrade se demuestra con un comando ejecutado en
   verification (ej. `alembic downgrade <base>`, `python -m` del downgrade),
   no con prosa.
3. `ADD/task-tools/VERIFIER.md` — nuevo check de reversibilidad probada:
   por cada migración del SCOPE con reversibilidad física, el mapa de cobertura
   exige proof explícita de ejecución del downgrade (comando en VERIFICATION
   + resultado). Proof aún sin ejecutar → `GAP`.
4. `ADD/task-tools/TRACE.md` — sin cambio de regla: TRACE sigue verificando
   presencia (`downgrade(` en el tree). VERIFIER verifica **ejecución**. Son
   dos hechos complementarios y no contradictorios.

## SCOPE

- `ADD/SPECIFICATION.md` — §9.1 norma de reversibilidad probada.
- `ADD/ASPEC-TEMPLATE.md` — hints en ROLLBACK y VERIFICATION.
- `ADD/task-tools/VERIFIER.md` — check de reversibilidad probada en
  `verify-run`.
- `SPEC-ADD/core/CORE-004.md` — esta A.SPEC.

## OUT OF SCOPE

- Cambiar la regla de presencia de TRACE (CORE-002 mantiene su scope).
- Reversibilidad por compensación (ya cubierta §9 para irreversibles).
- CI real que ejecute downgrades (requiere A.SPEC de CI/binding futura).
- Risk-tiering (ya CORE-003); ownership (CORE-006 futura); composición/dueño
  (CORE-005 futura).
- Cambios en GENERATOR, SPECCER, ATOMIZER, SPEC-REVIEWER.
- Cualquier cambio de código de producto.

## CONTRACT

Precondiciones:

- A.SPEC con SCOPE que incluye una migración (path `migrations/*.py`) o cambio
  de schema con reversibilidad física declarada en ROLLBACK.
- TRACE activo (existe `downgrade(`).

Postcondiciones:

- VERIFIER: migración reversible con `ROLLBACK` por downgrade y VERIFICATION
  sin comando ejecutado → `GAP`.
- VERIFIER: idem pero con comando + resultado pasando → proof válida (el check
  agrega cobertura, no cambia PASS/FAIL de otras cláusulas).
- SPECIFICATION §9.1 redactado con la frase normativa exacta (ver
  VERIFICATION pin).
- §9.1 no contradice §9 (compensación/contención para irreversibles siguen
  intactas).

## INVARIANTS

```yaml
invariants:
  - "La semántica de §9 queda intacta: compensación/contención/no-repetición
    siguen siendo el ROLLBACK de las A.SPEC irreversibles."
  - "La verificación de presencia de TRACE (CORE-002) no cambia; VERIFIER
    agrega el hecho de ejecución (complementa, no reemplaza)."
  - "Veredictos de SPEC-REVIEWER y TRACE no cambian con esta norma."
  - "El protocolo clean-context de los jueces se preserva."
  - "Sin cambios de código de producto."
  - "A.SPECs integradas existentes quedan grandfathered; la norma aplica a
    nuevas o re-abiertas."
  - "La estructura task-tools no se reorganiza; VERIFIER solo gana un check."
```

Correspondencia `must_not_affect` → INVARIANTS (§7.1):

- semántica §9 irreversible → invariante "semántica de §9 queda intacta".
- TRACE presencia → invariante "verificación de presencia de TRACE no cambia".
- verdict routing → invariante "Veredictos de SPEC-REVIEWER y TRACE no cambian".
- clean-context → invariante "protocolo clean-context se preserva".
- estructura task-tools → invariante "estructura task-tools no se reorganiza".
- grandfathered → invariante "A.SPECs integradas existentes quedan grandfathered".
- producto → invariante "sin cambios de código de producto".

## VERIFICATION

- `grep -F "La reversibilidad de un cambio de schema NO es una promesa" ADD/SPECIFICATION.md`
  → §9.1 presente (frase pinneada del cuerpo; el título "Reversibilidad probada"
  y el término vago "ROLLBACK" ya existían y no valen).
- VERIFIER incluye check de reversibilidad probada (inspección del archivo).
- Ejecución de prueba (fixtures inline, sin archivos en el repo):
  - Caso `GAP` (migración sin downgrade probado): A.SPEC ficticia con migración
    en SCOPE, `ROLLBACK` por downgrade, VERIFICATION solo con tests de negocio
    (sin comando de downgrade) → VERIFIER `GAP` por reversibilidad no probada,
    sin emitir `FAIL`.
  - Caso `PASS` (downgrade probado): la misma A.SPEC con VERIFICATION que
    ejecuta `alembic downgrade` con resultado registrado → pasan: presencia
    (TRACE) y ejecución (VERIFIER) → veredicto consistente (sin falso-GAP sobre
    la superficie de reversibilidad).

## ROLLBACK

Reversible: revertir commit del submódulo; §9.1 y hints se revientan con el
revert. Sin migraciones.

## Change Surface

```yaml
change_surface:
  allowed:
    - ADD/SPECIFICATION.md
    - ADD/ASPEC-TEMPLATE.md
    - ADD/task-tools/VERIFIER.md
    - SPEC-ADD/core/CORE-004.md
  prohibited:
    - plugins/**
    - apps/**
    - vendor/**
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
    - add.verifier.reversibility_proof
    - add.specification.reversibility_norm
  indirect:
    - revisiones de A.SPECs futuras con migraciones (exigen ejecución de
      downgrade en verification)
  must_not_affect:
    - semántica de §9 (compensación/contención irreversibles)
    - regla de presencia de TRACE (CORE-002)
    - verdict routing de SPEC-REVIEWER/TRACE
    - clean-context protocol de jueces
    - estructura task-tools
    - A.SPECs integradas existentes
    - runtime/producto del sistema
```

## Composition

```yaml
composition:
  requires_aspecs:
    - CORE-002 # TRACE verifica presencia de downgrade; VERIFIER agrega ejecución
  must_compose_with:
    - CORE-005 # release/composition gate (futura)
  systemic_invariants:
    - "Un downgrade declarado, sin ejecutar, no cuenta como reversibilidad."
  composition_checks:
    - "A.SPEC con migración y VERIFICATION sin comando de downgrade -> GAP en
      VERIFIER; con comando + resultado -> pass en presencia (TRACE) y
      ejecución (VERIFIER)."
```

## Structural Constraints

```yaml
structural_constraints:
  primary_rule: VERIFIER gana un check; normas cortas en SPECIFICATION
  entrypoints_must_stay_thin: true
  review_threshold_lines: 400
  extraction_threshold_lines: 600
  preferred_new_logic_locations:
    - ADD/task-tools/VERIFIER.md
```

## Traceability

- Requirement: plan de madurez ADD — mejora nº4 (reversibilidad probada),
  acordado en sesión 2026-08-26. Definida aquí: el downgrade se ejecuta y se
  verifica en VERIFICATION; la presencia solo la valida TRACE.
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