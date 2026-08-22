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
- explicit composition commands when the A.SPEC declares `composition_checks`
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
5. if `composition_checks` exist, execute them and run `verifier-add` in `verify-composition`
6. fail pipeline on `FAIL` or `GAP`

If composition belongs to an integration A.SPEC rather than a leaf A.SPEC, the
CI wrapper runs those `composition_checks` on the integration A.SPEC pipeline,
not on every leaf branch.

## Non-Goals

CI wrapper must not:

- infer project stack
- invent missing commands
- invent missing composition checks
- redefine contract or invariants
- downgrade `GAP` into success

## Example Failure Policy

```text
FAIL if:
- any required command fails
- verifier verdict is FAIL
- verifier verdict is GAP
- composition verifier verdict is FAIL
- composition verifier verdict is GAP
```

## Completion Checklist

- [ ] workflow stays thin
- [ ] commands come from explicit source
- [ ] verifier verdict gates merge
- [ ] composition checks run when declared or in integration A.SPEC when owned there
- [ ] no hidden stack inference added
