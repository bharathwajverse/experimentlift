# ExperimentLift agent instructions

These rules apply to every repository task, including OpenCode and Codex work.

## Required execution loop

`UNDERSTAND -> INSPECT -> PLAN TESTS -> IMPLEMENT -> EXECUTE -> VERIFY -> REPAIR -> REGRESSION TEST -> REVIEW -> REPORT -> PROCEED`

1. Extract explicit requirements and acceptance evidence.
2. Inspect relevant code, tests, docs, Git state and dependent work.
3. Update `docs/VERIFICATION_MATRIX.md` before implementation.
4. Write or improve a failing test for each behavior or confirmed defect.
5. Make the smallest safe change; keep statistics independent from API code.
6. Run focused tests, then the broader applicable suite.
7. Inspect behavior and artifacts, not only process exit codes.
8. Record unresolved reproducible defects in `docs/KNOWN_ISSUES.md`.
9. Update `docs/PROGRESS.md` only with demonstrated results.
10. Do not advance a dependent phase while a critical requirement is FAIL,
    BLOCKED or NOT TESTED.

## Evidence rules

- Distinguish generated code, executed commands, passing checks and proven
  requirements.
- Never weaken assertions only to make a suite green.
- Never hide skipped, blocked, unavailable or flaky checks.
- Statistical methods need independent reference calculations, not circular
  tests against the same helper.
- Keep synthetic data and outputs unmistakably labelled.
- A test pass is evidence only for the behavior its assertions exercise.

## Safety and scope

- Work only in this repository and disposable local test resources.
- No production data, real email, paid API, public deployment or remote push
  without explicit approval.
- No destructive Git commands or overwriting unrelated user work.
- Do not log raw assignment salts, credentials or participant PII.
- PostgreSQL claims require PostgreSQL; SQLite is not substitute evidence.

## Coordination

One implementer edits at a time. Reviewers inspect actual code/diffs and return
specific findings. If Codex or another independent model is unavailable, run a
separate adversarial review pass and disclose that limitation.

## GitHub delivery

- Default branch is `main`; expected remote is
  `https://github.com/bharathwajverse/experimentlift.git`.
- Bootstrap the empty remote once; afterward use focused feature branches and
  reviewed pull requests when practical.
- Before committing, inspect branch, status, staged files and secret patterns.
- Never force-push or invent author identity. Confirm the local and remote SHA.
- CI failures block milestone completion and merge.
