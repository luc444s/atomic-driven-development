# CI Wrapper ADD

## Purpose

Skill for wiring explicit ADD verification into a CI platform.

Primary goal:

> Keep CI thin. Run explicit checks. Fail on verifier verdict.

## Use When

- project already has explicit `VERIFICATION` commands or `ADD/VERIFY.yaml`
- a team wants merge gating from ADD rules
- a workflow file must call verifier consistently

## Do Not Use When

- verifier rules are still undefined
- project verification binding is still unstable
- you expect CI wrapper to invent commands or coverage

## Core Law

CI wrapper executes policy. It does not create policy.

## Required Inputs

- current A.SPEC or changed A.SPEC set
- explicit verification commands or `ADD/VERIFY.yaml`
- target CI platform

## Required Output

Produce:

1. thin workflow/pipeline definition
2. step order
3. failure conditions
4. artifact or log retention notes if needed

## Thin CI Shape

Preferred flow:

1. checkout repo
2. load A.SPEC context
3. execute explicit verification commands
4. run `verifier-add` on resulting evidence
5. fail pipeline on `FAIL` or `GAP`

## Non-Goals

CI wrapper must not:

- infer project stack
- invent missing commands
- redefine contract or invariants
- downgrade `GAP` into success

## Example Failure Policy

```text
FAIL if:
- any required command fails
- verifier verdict is FAIL
- verifier verdict is GAP
```

## Completion Checklist

- [ ] workflow stays thin
- [ ] commands come from explicit source
- [ ] verifier verdict gates merge
- [ ] no hidden stack inference added
