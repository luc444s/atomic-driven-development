# Verifier ADD

## Purpose

Skill for validating an A.SPEC with objective evidence and minimum noise.

Primary goal:

> Reduce ambiguity between declared change and proof.

This skill does not review style, architecture, or product direction. It only
judges whether the A.SPEC's declared contract and invariants are covered by
real checks.

## Use When

- an A.SPEC has `CONTRACT`, `INVARIANTS`, and `VERIFICATION` drafted
- a branch is near merge or release
- CI must decide pass/fail on a bounded change
- a project needs a generic verification interface not tied to one language
- the repo may have drift between its actual toolchain and its documented checks

## Do Not Use When

- the request is still vague and no A.SPEC exists yet
- implementation is still exploratory and contract is changing every minute
- you want general code review, refactor advice, or design critique
- the project has no stable way to execute any verification yet

## Core Law

Verifier judges coverage, not taste.

It answers only five things:

1. what contract the A.SPEC declares
2. what invariants the A.SPEC declares
3. what checks objectively cover them
4. what evidence each check produced
5. whether result is `PASS`, `FAIL`, or `GAP`

If it says more than that, it is probably generating noise.

## Inputs

- current A.SPEC
- repository tree
- optional diff or changed-files list
- optional project verification binding: `ADD/VERIFY.yaml`
- optional CI context

## Required Output

Produce:

1. normalized verification plan
2. coverage map: contract clauses -> checks
3. coverage map: invariants -> checks
4. evidence table
5. final verdict: `PASS`, `FAIL`, or `GAP`

## Verdict Semantics

### PASS

- every declared contract clause has objective coverage
- every declared invariant has objective coverage
- all required checks executed successfully
- no blocking drift exists between repo reality and verification binding

### FAIL

- one or more required checks executed and failed
- evidence contradicts declared contract or invariants
- change touched prohibited surface and A.SPEC does not allow it

### GAP

- a declared contract clause has no objective check
- a declared invariant has no objective check
- repo verification binding is missing, stale, or ambiguous
- required command cannot be selected with enough confidence

`GAP` is not success. It means verification design incomplete.

## Modes

### `verify-plan`

Read-only mode.

Produces coverage plan without executing full verification suite unless a small
probe is needed to confirm tool existence.

Use when:

- drafting or reviewing an A.SPEC
- checking whether CI is sufficiently specified
- detecting missing coverage early

### `verify-run`

Execution mode.

Runs selected checks, captures evidence, and emits final verdict.

Use when:

- branch is ready for merge
- CI is running
- release or hotfix gate is needed

### `verify-drift`

Binding health mode.

Checks whether documented verification commands still match repo reality.

Use when:

- scripts were renamed
- toolchain changed
- CI started failing because docs and repo diverged

## Project Binding

Verifier should prefer explicit project binding over stack guesswork.

Canonical location:

```text
ADD/VERIFY.yaml
```

This file is project-specific. It is not part of ADD core doctrine.

Minimal shape:

```yaml
verification:
  static_checks: []
  contract_checks: []
  invariant_checks: []
  build_checks: []
  smoke_checks: []
```

Suggested entry shape:

```yaml
verification:
  static_checks:
    - id: frontend-lint
      cwd: apps/web
      when:
        paths_exist: [package.json]
      run: npm run lint
      covers:
        contract: []
        invariants: []

  build_checks:
    - id: frontend-build
      cwd: apps/web
      when:
        paths_exist: [package.json]
      run: npm run build
      covers:
        contract: []
        invariants: []

  contract_checks:
    - id: api-acceptance
      cwd: .
      when:
        paths_exist: [docker-compose.yml]
      run: ./scripts/test-api.sh
      covers:
        contract:
          - creates-site
        invariants:
          - tenant-isolation
```

## Discovery Fallback

If `ADD/VERIFY.yaml` does not exist, verifier may infer candidates from repo
artifacts, but must stay conservative.

Common signals:

- `package.json`
- `pyproject.toml`
- `go.mod`
- `Cargo.toml`
- `composer.json`
- `pom.xml`
- `Makefile`
- `Dockerfile`
- CI workflow files
- executable test scripts under `scripts/`

Inference may propose a plan. It must not silently upgrade guesswork into
`PASS` when coverage is uncertain.

## Selection Rules

Order of preference:

1. explicit checks referenced by A.SPEC `VERIFICATION`
2. explicit checks from `ADD/VERIFY.yaml`
3. stable project scripts discoverable from repo artifacts
4. conservative fallback probes

When multiple candidates exist, prefer:

1. narrower surface
2. lower runtime cost
3. more direct coverage of current A.SPEC
4. existing project convention over new invention

## Coverage Discipline

Verifier must build explicit mapping.

Example:

```text
contract.create-domain -> check api-domain-create
contract.delete-domain -> check api-domain-delete
invariant.tenant-isolation -> check test-tenant-isolation
invariant.read-only-discovery -> check test-discovery-readonly
```

If a clause has no mapping, verdict cannot be `PASS`.

## Evidence Model

Each executed check should emit, at minimum:

- `id`
- `command`
- `cwd`
- `status`: pass | fail | skipped
- `covers`
- short evidence note

Example:

```text
- id: test-tenant-isolation
  command: python3 -m pytest tests/test_tenant_isolation.py -q
  cwd: vendor/systutor-core
  status: pass
  covers: invariant.tenant-isolation
  evidence: 1 passed
```

## Anti-Noise Rules

Verifier must not:

- invent new invariants that A.SPEC did not declare
- expand scope into unrelated lint, style, or architecture checks
- report broad best-practice advice
- block on weak heuristics alone
- bury verdict under long prose

Good output is short, tabular, and binary.

## Autocorrection Policy

Verifier may be self-correcting only in bounded ways.

Allowed:

- detect stale command path and propose exact replacement
- detect missing `ADD/VERIFY.yaml` and generate draft from repo artifacts
- detect renamed script or workflow and propose patch
- detect clause without coverage and suggest exact missing check slot

Not allowed:

- invent fake evidence
- mark `PASS` on partial coverage
- rewrite A.SPEC intent without explicit human approval
- broaden CI into full-repo governance unrelated to current A.SPEC

## CI Wrapper

CI should stay thin.

Preferred model:

1. checkout repo
2. load current A.SPEC or changed A.SPEC set
3. run verifier in `verify-run` mode
4. fail pipeline on `FAIL` or `GAP`

CI system may be GitHub Actions, GitLab CI, Jenkins, local hooks, or anything
else. ADD does not require a specific platform.

## Minimal Report Shape

```text
VERDICT: GAP

Covered:
- contract.create-domain -> api-domain-create
- invariant.tenant-isolation -> test-tenant-isolation

Missing coverage:
- invariant.rollback-safe

Executed checks:
- PASS api-domain-create
- PASS test-tenant-isolation

Drift:
- ADD/VERIFY.yaml references scripts/test-api.sh but file does not exist
```

## Completion Checklist

- [ ] A.SPEC clauses normalized into explicit contract/invariant items
- [ ] project binding loaded or missing state declared
- [ ] each clause mapped to at least one objective check or marked `GAP`
- [ ] executed evidence recorded for selected checks
- [ ] final verdict emitted as `PASS`, `FAIL`, or `GAP`
- [ ] no unrelated review noise added
