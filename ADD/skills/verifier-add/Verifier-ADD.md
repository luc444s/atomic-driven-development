# Verifier ADD

## Purpose

Skill for judging whether an A.SPEC has enough explicit evidence.

Primary goal:

> Judge declared contract against declared proof. Nothing else.

## Use When

- an A.SPEC already has `CONTRACT`, `INVARIANTS`, and `VERIFICATION`
- a branch is near merge
- CI or a reviewer needs a bounded pass/fail/gap judgment
- evidence already exists or commands are already explicit

## Do Not Use When

- no A.SPEC exists yet
- `VERIFICATION` is still being invented
- you want stack discovery, CI design, or command generation
- you want general code review or architecture advice

## Core Law

Verifier is a judge, not a discoverer.

It answers only:

1. what contract clauses were declared
2. what invariants were declared
3. what proof was explicitly provided
4. whether that proof covers every declared clause
5. verdict: `PASS`, `FAIL`, or `GAP`

If input is ambiguous, answer `GAP`.

## Inputs

- current A.SPEC
- explicit commands or explicit evidence referenced by `VERIFICATION`
- optional command results
- optional changed-files list for scope sanity check

No repo inference required.

## Required Output

Produce:

1. normalized contract clause list
2. normalized invariant list
3. explicit proof list
4. coverage map: clause -> proof
5. final verdict: `PASS`, `FAIL`, or `GAP`

## Verdict Semantics

### PASS

- every contract clause has explicit proof
- every invariant has explicit proof
- every required proof passed

### FAIL

- an explicit proof ran and failed
- an explicit proof contradicts declared contract
- an explicit proof contradicts declared invariant

### GAP

- a clause has no explicit proof
- evidence is missing or ambiguous
- verification text exists but cannot be mapped objectively

`GAP` means verification incomplete.

## What Counts As Proof

Accepted proof must be explicit and inspectable.

Examples:

- named test command
- named build command
- named smoke command
- stored command result
- short evidence note attached to a command result

Bad proof examples:

- "should be covered by CI"
- "probably safe"
- inferred toolchain guesses
- broad repo heuristics

## Coverage Discipline

Verifier must map each declared clause to explicit proof.

Example:

```text
contract.create-domain -> proof api-domain-create
contract.delete-domain -> proof api-domain-delete
invariant.tenant-isolation -> proof test-tenant-isolation
```

If no explicit mapping exists, verdict cannot be `PASS`.

## Output Shape

Keep output short and binary.

```text
VERDICT: GAP

Covered:
- contract.create-domain -> api-domain-create
- invariant.tenant-isolation -> test-tenant-isolation

Missing:
- invariant.rollback-safe

Failed:
- none
```

## Anti-Noise Rules

Verifier must not:

- discover commands from repo artifacts
- invent invariants not declared by A.SPEC
- rewrite A.SPEC intent
- propose CI architecture
- propose binding files
- drift into style or design review

If broader help is needed, use separate skills.

## Related Skills

- `verify-binding-add` defines project verification bindings
- `ci-wrapper-add` wires explicit verification into CI

## Completion Checklist

- [ ] contract clauses normalized
- [ ] invariants normalized
- [ ] explicit proof list extracted
- [ ] each clause mapped or marked `GAP`
- [ ] final verdict emitted as `PASS`, `FAIL`, or `GAP`
- [ ] no discovery or design advice mixed in
