# Verify Binding ADD

## Purpose

Skill for defining and maintaining explicit project verification bindings for
ADD.

Primary goal:

> Translate project-specific commands into stable proof entries without making
> verifier guess.

## Use When

- a project wants reusable verification commands across many A.SPECs
- `VERIFICATION` sections keep repeating same commands
- CI needs one canonical source for project checks
- scripts or command paths changed and verification docs drifted

## Do Not Use When

- you only need to judge one A.SPEC with already explicit commands
- you want verifier itself to infer stack or repair commands
- project has not yet agreed on canonical checks

## Core Law

Binding is explicit project policy.

It exists so `verifier-add` can stay dumb, narrow, and deterministic.

## Canonical Artifact

Suggested location:

```text
ADD/VERIFY.yaml
```

This file is project-specific. Not ADD core doctrine.

## Minimal Shape

```yaml
verification:
  checks: []
```

## Suggested Entry Shape

```yaml
verification:
  checks:
    - id: frontend-build
      run: npm run build
      cwd: apps/web
      covers:
        contract: []
        invariants: []
```

## Required Output

Produce:

1. canonical check list
2. stable IDs
3. command, cwd, and scope per check
4. explicit `covers` mapping when project wants reusable coverage labels
5. drift notes when documented commands no longer match repo reality

## Drift Scope

This skill may inspect repo artifacts only to maintain binding accuracy.

Allowed:

- detect missing script path
- detect renamed command
- detect dead check ID
- propose exact binding patch

Not allowed:

- silently bless guessed commands as canonical
- mark an A.SPEC `PASS`
- mix CI platform policy into binding design

## Example Drift Report

```text
Binding drift:
- check frontend-build points to apps/web-old
- replacement candidate: apps/web
```

## Completion Checklist

- [ ] canonical binding artifact created or updated
- [ ] checks have stable IDs
- [ ] commands and cwd are explicit
- [ ] drift recorded as exact patchable facts
- [ ] no A.SPEC verdict mixed in
