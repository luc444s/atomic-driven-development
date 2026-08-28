# Composer Gate ADD

## Purpose

Skill para ejecutar el **compose-gate** (§10.1) como **acción de primer plano**
del agente principal (función de COMPOSER absorbida). COMPOSER no es una task
tool automática ni un subagente: el agente principal actúa como COMPOSER y
ejecuta el gate de forma deliberada, en orden y sin consumir toolcall.

> El agente principal ES COMPOSER cuando cierra una A.SPEC de integración.

## Use When

- hay una A.SPEC de integración (set/release compuesto) lista para cerrar
- el approver pide cerrar una Versión Base o release (p.ej. COMPRAS-019)
- la A.SPEC declara `composition.owner`, `composition_checks` y
  `composition.systemic_invariants`

## Do Not Use When

- no hay set compuesto (A.SPEC hoja individual): el contract/invariantes de la
  hoja los juzga VERIFIER, no el gate
- no existe task tool COMPOSER (retirada 2026-08-28): esta skill es la única
  materialización del compose-gate, en cualquier modo del ciclo

## Core Law

El agente principal es COMPOSER: ejecuta el gate en primer plano, en el orden
declarado. No re-juzga las hojas — la división de trabajo (§10.1) deja
contract/invariantes de cada miembro a VERIFIER; este gate juzga el SET.

## Inputs

- `integration_spec_path` — la A.SPEC de integración (requerido)
- lista de A.SPECs hoja del set (contexto; NO se re-verifican)
- resultados de `composition_checks` si ya fueron almacenados

## Checks (en el orden declarado por la A.SPEC)

1. **owner presente** — `composition.owner` existe y es no vacío. Ausente → `GAP`.
2. **checks ordenados y ejecutables** — `composition_checks` es lista no vacía
   de comandos/procedimientos nombrados; cada uno ejecutable. Vacío/vago → `GAP`.
3. **ejecutar en orden** — correr cada check y registrar resultado:
   - corre y falla → `FAIL`
   - no puede correr (comando faltante, target ambiguo, entorno) → `GAP`
4. **systemic_invariants evaluables** — cada una es una propiedad SISTÉMICA del
   set (no un restatement leaf) y queda cubierta por los checks. No evaluable → `GAP`.
5. **presence-check del approver** — registro de quién presenció la ejecución
   del gate y cuándo. Sin esto, el release NO se libera (§10.2).

## Veredictos

- `PASS` — owner presente; todos los checks corrieron en orden y pasaron;
  invariantes sistémicas evaluables y cubiertas; presence-check registrado.
- `FAIL` — un check declarado corrió y falló.
- `GAP` — owner ausente, check faltante/vago/inejecutable, invariante sistémica
  no evaluable, presencia del approver ausente, o el conjunto no tiene A.SPEC
  de integración.

## Output

```text
VERDICT: <PASS|FAIL|GAP>

Composition map:
- owner: <presente | GAP: ausente>
- systemic_invariant.<x> -> <cubierta por check(s) | GAP>
- composition_check.<n> -> <PASS | FAIL: <resultado> | GAP: <por qué>
- presence-check: <approver + fecha | GAP>

Failed:
- <fallo concreto del check>
```

## Rules

1. Ejecutar en el ORDEN declarado por la A.SPEC; jamás reordenar.
2. No inventar checks, targets ni owners.
3. No juzgar contract/invariantes de las hojas (división VERIFIER).
4. No auto-asignarse como owner ni como approver.
5. Registrar el resultado de cada check (proof) — nunca `PASS` sin ejecución.
6. No consume toolcall: es acción de primer plano del agente principal.

## Completion Checklist

- [ ] owner presente y validado
- [ ] todos los checks ejecutados en orden, con resultado registrado
- [ ] systemic_invariants evaluables y cubiertas
- [ ] presence-check del approver registrado (quién + cuándo)
- [ ] veredicto emitido con evidencia (sin `PASS` sin ejecución)
