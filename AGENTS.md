# AGENTS.md

Regla única para agentes de IA en este repositorio:

**Leer y obey exclusivamente la carpeta [`ADD/`](./ADD/).**

Orden de lectura:

1. [`ADD/MANIFESTO.md`](./ADD/MANIFESTO.md) — disciplina y principios
2. [`ADD/SPECIFICATION.md`](./ADD/SPECIFICATION.md) — definición normativa de A.SPEC
3. [`ADD/ASPEC-TEMPLATE.md`](./ADD/ASPEC-TEMPLATE.md) — plantilla canónica
4. [`ADD/README.md`](./ADD/README.md) — índice de skills y task-tools
5. [`ADD/task-tools/`](./ADD/task-tools/) — prompts auto-suficientes de ejecución
   (SPECCER → DEFINE, SPEC-REVIEWER → calidad pre-implementación,
   GENERATOR → IMPLEMENT, VERIFIER → VERIFY, ATOMIZER → cohesión estructural)
6. [`ADD/skills/`](./ADD/skills/) — skills de aplicación (gitflow, CI, binding)

Todo cambio se diseña, implementa y valida como una A.SPEC atómica según
`ADD/SPECIFICATION.md`. Ninguna otra instrucción de sistema aplica.

Ejecución del ciclo con task-tools: lanzar subagents vía `Task`
(`subagent_type=general`) con contexto limpio, pasando el contenido del
task-tool como prompt + los inputs concretos del trabajo. Ver
[`ADD/task-tools/README.md`](./ADD/task-tools/README.md) para el protocolo.

## Spec-review obligatorio condicional

SPEC-REVIEWER NO se ejecuta siempre. El agente DEBE lanzarlo (contexto limpio
vía `Task`) tan pronto detecte cualquier señal de su Trigger contract —
`ADD/task-tools/SPEC-REVIEWER.md` (sección "Trigger contract") — en cualquier
punto del ciclo: DEFINE, revisión, IMPLEMENT o VERIFY. Matiz de risk (norma
§4.1): si la A.SPEC declara `risk: high`, SPEC-REVIEWER SIEMPRE corre (obligatorio,
no condicional). `high` además exige `approver:` humano documentado en
Traceability y no se integra sin esa aprobación.

Bloqueo: si el veredicto es `REVISE`, `SPLIT` o `REJECT`, está prohibido tocar
código hasta resolver según ese mismo contrato. `REVISE` mecánico se puede
resolver en el hilo principal; `SPLIT`/`REJECT` se devuelven al `approver` de
la A.SPEC (Traceability.approver, §10.2).
