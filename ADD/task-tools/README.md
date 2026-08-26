# ADD Task Tools

Subagent-ready prompts for the ADD/A.SPEC workflow. Each file under
`ADD/task-tools/` is a **self-contained system prompt**: launch it via the
`Task` tool with `subagent_type=general` and a FRESH context so the worker runs
with clean memory (no main-thread conversation bleed).

These three are task tools by nature: they need clean context to judge
honestly.

| Task tool | File | Judges | Use when |
|-----------|------|--------|----------|
| SPECCER | `SPECCER.md` | `DEFINE` — atomicity of a request | request exists, no A.SPEC yet |
| ATOMIZER | `ATOMIZER.md` | file cohesion / split boundary | Python file mixes responsibilities or is too big |
| VERIFIER | `VERIFIER.md` | `PROVE` — declared clause vs explicit proof | A.SPEC has CONTRACT/INVARIANTS/VERIFICATION |
| GENERATOR | `GENERATOR.md` | `BUILD` — A.SPEC → code in change_surface | A.SPEC finalized, needs implementation |

## Launch protocol (main thread)

For each, create a `Task` call whose `prompt` = the task-tool file content
(feed it literally) + the concrete inputs for that job. Example shape:

```text
<contents of ADD/task-tools/SPECCER.md>

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

- Subagent reads `ADD/MANIFESTO.md`, `ADD/SPECIFICATION.md`,
  `ADD/ASPEC-TEMPLATE.md` and the target files itself.
- Subagent must not invent commands, invariants, or redesign behavior.
- Speccer/Verifier are judges: they emit verdicts, not implementations.
- Atomizer splits structure only; it preserves semantics and verification.
- Generator implements only inside `change_surface.allowed`; never touches
  `prohibited`; runs the explicit `VERIFICATION` commands and reports.
- After a task tool returns, the main thread still owns the edit/commit decision.

## Why clean context

Speccer must not be biased by partially-formed main-thread reasoning. Verifier
must not "discover" proof from ambient repo noise. Atomizer must not inherit the
main thread's refactor temptations. Isolating them keeps each judgment honest
and reproducibility high.
