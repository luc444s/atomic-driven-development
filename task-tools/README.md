# ADD Task Tools

Subagent-ready prompts for the ADD/A.SPEC workflow. Each file under
`ADD/task-tools/` is a **self-contained system prompt**: launch it via the
`Task` tool with `subagent_type=general` and a FRESH context so the worker runs
with clean memory (no main-thread conversation bleed).

These three are task tools by nature: they need clean context to judge
honestly.

| Task tool | File | Judges | Use when | Default mode (§4.2) |
|-----------|------|--------|----------|---------------------|
| SPECCER | `SPECCER.md` | `DEFINE` — atomicity of a request | request exists, no A.SPEC yet | skipped: mechanical (mode A) / pure presentation |
| SPEC-REVIEWER | `SPEC-REVIEWER.md` | A.SPEC quality (atomicity, scope drift, contract, invariants, composition) | A.SPEC(s) written, before implementation | runs unless mode A; always in judges-lite for docs/canon |
| ATOMIZER | `ATOMIZER.md` | file cohesion / split boundary | Python file mixes responsibilities or is too big | on structural signals only |
| VERIFIER | `VERIFIER.md` | `PROVE` — declared clause vs explicit proof | A.SPEC has CONTRACT/INVARIANTS/VERIFICATION | skipped: mechanical / presentation / frontend-consumer; lite-proof in docs |
| GENERATOR | `GENERATOR.md` | `BUILD` — A.SPEC → code in change_surface | A.SPEC finalized, needs implementation | skipped: surface ≤3 files non-trivial → main thread; backend-decide governs mixed specs |
| TRACE | `TRACE.md` | integration traceability vs repo facts (SHA-anchored) | A.SPEC integrated, needs trace validation (§13.5) | minimal ALWAYS when contracts/migrations exist; optional for pure presentation |
| COMPOSER | `COMPOSER.md` | `compose-gate` — integration A.SPEC's checks, owner, systemic invariants | composed set/release needs gate before integrate (§10.1) | unchanged (set-level gate, any mode) |

Default modes per SPECIFICATION §4.2: ceremony scales with risk signals ×
proof nature × surface — never with file count or file type alone.
Backend-decide rule applies to mixed frontend/backend specs. Absence of
`mode:` = full cycle (Mode C).

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

- Each subagent reads what its own procedure's step 1 declares (per-tool
  reading budget, SPECIFICATION §4.2): task tools are self-contained;
  SPEC-REVIEWER additionally reads the canon it judges against.
- Subagent must not invent commands, invariants, or redesign behavior.
- Speccer/Verifier/Spec-Reviewer/Trace/Composer are judges: they emit verdicts,
  not implementations.
- Atomizer splits structure only; it preserves semantics and verification.
- Generator implements only inside `change_surface.allowed`; never touches
  `prohibited`; runs the explicit `VERIFICATION` commands and reports.
- Trace only reads repo facts (git + files); it never parses prose, invents
  commands, or judges test quality.
- After a task tool returns, the main thread still owns the edit/commit decision.

## Why clean context

Speccer must not be biased by partially-formed main-thread reasoning. Verifier
must not "discover" proof from ambient repo noise. Atomizer must not inherit the
main thread's refactor temptations. Isolating them keeps each judgment honest
and reproducibility high.
