# ADD Task Tools

Subagent-ready prompts for the ADD/A.SPEC workflow. Each file under
`ADD/task-tools/` is a **self-contained system prompt**: launch it via the
`Task` tool with `subagent_type=general` and a FRESH context so the worker runs
with clean memory (no main-thread conversation bleed).

These four are task tools by nature: they need clean context to do their job
honestly.

| Task tool | File | Role | Use when |
|-----------|------|------|----------|
| SPEC-REVIEWER | `SPEC-REVIEWER.md` | A.SPEC quality (atomicity, scope drift, contract, invariants, composition) | A.SPEC(s) written, before implementation |
| VERIFIER | `VERIFIER.md` | `PROVE` — declared clause vs explicit proof | A.SPEC has CONTRACT/INVARIANTS/VERIFICATION |
| TRACE | `TRACE.md` | integration traceability vs repo facts (SHA-anchored) | A.SPEC integrated, needs trace validation (§13.5) |

> COMPOSER no es task tool (2026-08-28, decisión approver): su compose-gate
> es una **skill** — `ADD/skills/composer-gate-add/Composer-Gate-ADD.md` — que
> el agente principal ejecuta como acción de primer plano (§10.1).

> ATOMIZER no es task tool: es una **skill** — `ADD/skills/atomizer-add/Atomizer-ADD.md` —
> que el agente principal ejecuta como acción de primer plano.

> GENERATOR no es judge: implementa el cambio dentro de `change_surface.allowed`.

## Launch protocol (main thread)

For each tool, create a `Task` call whose `prompt` = the file content
(feed it literally) + the concrete inputs for that job. Example shape:

```text
<contents of ADD/task-tools/GENERATOR.md>

---
INPUT:
request: "<loose request>"
constraints: "<...>"
target_path: "SPEC-ADD/compras/COMPRAS-012.md"   # optional
```

Run several `Task` calls in ONE message to parallelize (each gets its own clean
context). The main thread collects results and integrates; it does NOT forward
conversation history into the subagent.

## Rules

- Each subagent reads what its own procedure's step 1 declares: task tools are
  self-contained; SPEC-REVIEWER additionally reads the canon it judges against.
- Subagent must not invent commands, invariants, or redesign behavior.
- SPEC-REVIEWER, VERIFIER, and TRACE are judges: they emit verdicts, not
  implementations.
- GENERATOR is an implementer: it changes only `change_surface.allowed`, never
  `prohibited`, and reports the explicit `VERIFICATION` commands it ran.
- TRACE only reads repo facts (git + files); it never parses prose, invents
  commands, or judges test quality.
- After a task tool returns, the main thread still owns the edit/commit decision.

## Why clean context

Verifier must not "discover" proof from ambient repo noise. Atomizer must not
inherit the main thread's refactor temptations. Isolating them keeps each
judgment honest and reproducibility high.
