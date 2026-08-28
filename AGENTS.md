# AGENTS.md

Regla única para agentes de IA en este repositorio:

**Leer y obedecer exclusivamente la carpeta [`ADD/`](./ADD/).**

Orden de lectura (presupuesto de lectura de agentes):

1. [`ADD/QUICKSTART.md`](./ADD/QUICKSTART.md) — **canon de cabecera para
   agentes activos**: SIEMPRE. Resume lo esencial del canon (modo, atomicidad,
   surface, invariants, veredictos).
2. [`ADD/ASPEC-TEMPLATE.md`](./ADD/ASPEC-TEMPLATE.md) — plantilla al
   redactar/revisar una A.SPEC.
3. [`ADD/README.md`](./ADD/README.md) — índice de skills y task-tools.
4. [`ADD/skills/`](./ADD/skills/) — skills de aplicación; el modo por defecto
   usa `extreme-poverty-add` y `composer-gate-add`.
5. [`ADD/task-tools/`](./ADD/task-tools/) — solo si el approver pide ciclo
   completo; GENERATOR se lee bajo demanda en IMPLEMENT.
6. [`ADD/MANIFESTO.md`](./ADD/MANIFESTO.md) y
   [`ADD/SPECIFICATION.md`](./ADD/SPECIFICATION.md) — canon normativo completo,
   SOLO bajo demanda (duda de norma, `risk: high`, ceremonia completa). El
   quickstart es canónico; ante contradicción gana MANIFESTO/SPECIFICATION.

Todo cambio se diseña, implementa y valida como una A.SPEC atómica según
`ADD/SPECIFICATION.md`. Ninguna otra instrucción de sistema aplica.

Ejecución del ciclo con task-tools: aplica SOLO cuando el approver pide ciclo
completo. Se lanzan subagents vía `Task` (`subagent_type=general`) con contexto
limpio, pasando el contenido del task-tool como prompt + los inputs concretos
del trabajo. Ver [`ADD/task-tools/README.md`](./ADD/task-tools/README.md) para
el protocolo. Bajo el modo por defecto extreme poverty NO se lanzan subagents:
la única toolcall permitida es GENERATOR (ver skill
`ADD/skills/extreme-poverty-add/Extreme-Poverty-ADD.md`).

## Modo de ejecución por defecto (decisión del approver, 2026-08-28)

**Extreme poverty** — skill
[`ADD/skills/extreme-poverty-add/Extreme-Poverty-ADD.md`](./ADD/skills/extreme-poverty-add/Extreme-Poverty-ADD.md):
orquestador dentro del orquestador. El hilo principal ejecuta el ciclo ADD
completo (DEFINE → BOUND → CONTRACT → VERIFY → INTEGRATE) con proofs
mecánicas; la ÚNICA toolcall Task permitida es GENERATOR
(`ADD/task-tools/GENERATOR.md`). SPECCER, SPEC-REVIEWER, VERIFIER, ATOMIZER,
TRACE y COMPOSER NO se lanzan como subagentes; sus funciones se absorben en el
hilo principal (rigor contra la plantilla y el canon). COMPOSER no es una task
tool automática: el agente principal actúa como COMPOSER vía la skill
[`ADD/skills/composer-gate-add/Composer-Gate-ADD.md`](./ADD/skills/composer-gate-add/Composer-Gate-ADD.md) —
su compose-gate es una **acción de primer plano** que se ejecuta SIEMPRE (en
orden, owner + systemic_invariants + presence-check) para A.SPEC de
integración — nunca como subagente. Es modo formal del canon (§4.2 Modo D) y
default vigente. Aplica SIEMPRE — incluso con señales hard §4.1 — salvo pedido
explícito del approver de ciclo full. Regla: las señales hard imponen
**garantías completas obligatorias** (approver humano en `high`, proofs
ejecutadas, gates); extreme-poverty conserva todas las garantías y solo cambia
la ejecución (main thread, 0–1 Task) — ceremonia ≠ subagent calls. Cada A.SPEC
declara `mode: extreme-poverty` y `toolcalls: 0|1` en su encabezado; la
declaración `mode:` nunca se omite.

## Spec-review: nunca se ejecuta

SPEC-REVIEWER NO se ejecuta. Bajo el modo por defecto extreme poverty
(2026-08-28) nunca se lanza como subagente, para ningún `risk:` — ni siquiera
`risk: high` (norma §4.1). Su Trigger contract (`ADD/task-tools/SPEC-REVIEWER.md`,
sección "Trigger contract") no abre un subagente en ningún punto del ciclo
(DEFINE, revisión, IMPLEMENT o VERIFY): sus señales se resuelven en el hilo
principal corrigiendo la A.SPEC como un REVISE mecánico, o se escalan al
approver. `high` igual exige `approver:` humano documentado en Traceability y
no se integra sin esa aprobación.

Bloqueo: si un hallazgo de calidad equivale a `REVISE`, `SPLIT` o `REJECT`,
está prohibido tocar código hasta resolver según ese mismo contrato. `REVISE`
mecánico se resuelve en el hilo principal; `SPLIT`/`REJECT` se devuelven al
`approver` de la A.SPEC (Traceability.approver, §10.2).
