# Speccer ADD

## Purpose

Skill for turning a loose request into an honest A.SPEC draft.

Primary goal:

> Define smallest truthful A.SPEC. Reject fake atomicity.

## Use When

- a request exists but no A.SPEC exists yet
- atomicity boundary is unclear
- a change may be one A.SPEC or several
- a human or agent needs help writing `WHY` through `ROLLBACK`

## Do Not Use When

- an A.SPEC is already drafted and only needs verification
- you want CI wiring or command discovery
- you want broad release planning instead of one honest change boundary

## Core Law

Speccer is judge of `DEFINE`.

It must decide whether a proposal is:

1. one honest A.SPEC
2. several A.SPECs
3. not yet an A.SPEC because it is only preparation

## Required Inputs

- loose request or problem statement
- optional repo context
- optional constraints, invariants, or non-goals

## Required Output

Produce:

1. normalized problem statement
2. candidate truth introduced now
3. verdict: `ACCEPT_ONE`, `SPLIT`, or `REJECT_AS_PREPARATORY`
4. atomicity reasoning
5. A.SPEC draft when acceptance is possible

## Atomicity Test

Accept as one A.SPEC only if all are true:

- one independent falsable truth appears now
- that truth has its own verification now
- rollback / compensation can be stated honestly now
- the promise does not depend on future A.SPEC to become true
- scope and out-of-scope can be stated cleanly

If one fails, do not force single-A.SPEC output.

## Verdicts

### `ACCEPT_ONE`

Use when request already describes one honest change.

### `SPLIT`

Use when request bundles several truths.

Output a minimal A.SPEC set where each item has:

- different `WHAT`
- different verification
- different rollback / compensation story

### `REJECT_AS_PREPARATORY`

Use when request only says:

- prepare groundwork
- add plumbing
- leave base ready
- enable future phase

without a new independent falsable truth now.

## Drafting Rules

When drafting an A.SPEC, speccer must fill or propose:

- `WHY`
- `WHAT`
- `SCOPE`
- `OUT OF SCOPE`
- `CONTRACT`
- `INVARIANTS`
- `VERIFICATION`
- `ROLLBACK`
- `Composition` when capability depends on multiple A.SPEC

## Composition Rule

Speccer may declare `composition` only to describe real dependencies or
systemic invariants.

It must not use `composition` to excuse a partial truth.

Bad:

```text
This A.SPEC is only useful after two future A.SPECs.
```

Good:

```text
This A.SPEC is already true now, but the full customer flow also requires
composition checks owned by an integration A.SPEC.
```

## Output Shape

```text
VERDICT: SPLIT

Truths:
- backend permission enforcement
- frontend navigation visibility

Reason:
- each truth has different verification and different rollback story
```

## Anti-Noise Rules

Speccer must not:

- invent implementation detail as if it were product truth
- accept preparatory scaffolding as atomic value
- design a whole roadmap when one A.SPEC is enough
- invent CI or verification commands from thin air

## Related Skills

- `verifier-add` judges explicit proof after the A.SPEC exists
- `verify-binding-add` defines reusable project proof bindings
- `ci-wrapper-add` runs explicit proof in CI

## Completion Checklist

- [ ] candidate truth stated in present tense
- [ ] verdict chosen: `ACCEPT_ONE`, `SPLIT`, or `REJECT_AS_PREPARATORY`
- [ ] atomicity reasoning stated explicitly
- [ ] A.SPEC draft emitted when applicable
- [ ] no fake preparatory value accepted
