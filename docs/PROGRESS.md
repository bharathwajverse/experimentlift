# Progress

## Current phase: M0 PASS; M1 PostgreSQL foundation PASS; M2 not started

M0 merged at `3226b7eef9cf3b21007462fd24cc8c5130d43080` with
post-merge CI run `44876504981` passing Python 3.11–3.14.

**M1 PostgreSQL evidence is now demonstrated in CI.** Branch
`feat/m1-postgresql-foundation` (PR #3) reaches SHA
`110c323fad1a9e582d582b485c41911236e41f35`; Actions run `45652442606`
completed `success` with 5/5 jobs green — `PostgreSQL 16 integration`,
`Python 3.11`, `Python 3.12`, `Python 3.13`, `Python 3.14`. The PostgreSQL
job reported `1 passed` (migration), `12 passed` (integration) and `65 passed`
(statistical baseline), with no skips, confirming
`EXPERIMENTLIFT_TEST_DATABASE_URL` was set and tests hit a real
`postgres:16` service. Server logs show each immutability guard rejecting the
invalid write it exists to reject.

**M1 merged** as PR #3 at `c9fd52bb08b949501dd592d81d717691e1963028`.
Post-merge Actions run `45653341203` passed all five jobs on that exact
`main` SHA. M1 is PASS; no M2 work has begun.

Repair history for the M1 feature branch (now merged):

- `3fe427d` added the schema, Alembic config, migration and CI job.
- `95b310e` added revision/variant/history immutability guards and closed a
  hole where a metric could move between revisions; CI run `44887532959`
  then failed the PostgreSQL job (`10 failed`, `fk_experiment_workspace`).
- Root cause: the models intentionally declare table-level
  `ForeignKeyConstraint`s with no ORM `relationship()`s, so a `Session`
  derives no parent/child dependency edges and falls back to mapper-name
  ordering — `"Experiment"` sorts before `"Workspace"`, so a single flush
  emitting a child before its parent is rejected by PostgreSQL.
  Reproduced DB-free with a mock-engine probe (first INSERT was `experiments`).
- `c80b8c7` ordered parent flushes before child inserts in the affected tests
  and documented the flush-order contract in `models.py`; the probe then
  observed `workspaces`, `experiments`, `experiment_revisions`, `variants`.
  Production `store.py` paths use Core inserts and were unaffected.
- `681c370` added a concurrent-activation reproducer. CI run `45652067417`
  failed it (`1 failed, 10 passed`): activation committed against old variant
  allocations while a variant edit was uncommitted.
- `110c323` serialized variant and metric edits with activation by locking
  the parent revision row. CI run `45652442606` passed both race regressions,
  the migration round trip, and all statistical tests.

Implemented: configuration validation, deterministic HMAC allocation with
in-process first-assignment persistence, terminal outcomes, dedupe,
fixed-horizon analysis, validity gates, reports, seeded simulation checks and
CLI, plus the M1 persistence foundation (12 workspace-scoped tables, frozen
initial migration, immutability triggers, assignment/event idempotency with
typed conflicts).

Not implemented: FastAPI, authz, durable audit-event ingestion, durable exposure
ingestion, creative storage, AI generation, frontend, Docker configuration,
deployment, production observability, deletion workflow, provider
integrations or real-world validation. The `ai_generations` table is deferred
until a documented AI-milestone requirement exists.

The 2026-11-21 audit first ran the pre-audit suite, then repaired the
documented gaps test-first. Current local evidence is 65 passing tests,
successful `compileall`, `pip check`, JSON/Markdown CLI smoke tests and
a clean whitespace scan of all source/documentation candidates. The in-session
adversarial review of all eight modules is complete (see `KNOWN_ISSUES.md`); the
independent external review could not run because the provider usage limit was
reached, and that limitation is recorded.
Phase 3 has not started: its PostgreSQL gate is BLOCKED. `docker version` cannot
reach the Docker Desktop Linux engine, no `psql`/`pg_ctl`/`initdb`/`postgres`
binary exists on PATH, and `localhost:5432` refuses connections. Because Phase 3
acceptance requires real PostgreSQL migration, API and database E2E evidence,
no Phase 3 code was written; see `DECISION_LOG.md` for the gate decision.

## Gate decision (2026-11-21)

- Phase 0–2: **PASS** — 14/14 P02 requirements PASS, 0 FAIL, 0 NOT TESTED;
  65 collected tests pass, `compileall` and `pip check` succeed, JSON and
  Markdown CLI smoke runs exit 0 and label output `SYNTHETIC`.
- Phase 3: **BLOCKED** — local PostgreSQL absent (no daemon, no binaries,
  closed port 5432); Phase 3 implementation deliberately deferred. This block
  is about *local* availability only: CI supplies a disposable `postgres:16`
  service, which is how M1 was verified.
- M1: **PASS** — PR #3 merged and post-merge CI on `main` passed; see the
  M1 gate section below.
- Open, disclosed limitations: KI-010 (local PostgreSQL), KI-020 (transitive
  lock policy), KI-021 (project license), KI-022 (branch protection), and
  external Phase 0–2 review unavailable.

## M1 gate: PASS on merged `main` (2026-11-25)

- Feature branch `feat/m1-postgresql-foundation`, fix SHA
  `110c323fad1a9e582d582b485c41911236e41f35`, merged via PR #3.
- Actions run `45652442606` concluded `success`; 5/5 jobs green:
  `PostgreSQL 16 integration` (`139340220768`), `Python 3.11`, `3.12`, `3.13`,
  `3.14`.
- PostgreSQL job evidence: `1 passed in 1.93s` (migration upgrade/downgrade/
  re-upgrade/drift), `12 passed in 1.90s` (integration), `65 passed in 3.61s`
  (statistical baseline). No skips, so the real-database path executed.
- Server-side log confirms each guard rejected the invalid write it exists to
  reject: `activated revision is immutable`, `activated revision variants are
  immutable`, `revisions must be inserted as draft`, `metric identity is
  immutable`, `experiment identity is immutable`, `immutable historical row`,
  plus the FK and unique-constraint rejections.
- Failed predecessor run `44887532959` at `95b310e` (`10 failed`,
  `fk_experiment_workspace`) is repaired by `c80b8c7` and recorded as KI-026.
- Independent security-review agent found no critical/high findings; its
  trigger-owner and destructive-downgrade caveats are documented in
  `docs/DATABASE_SCHEMA.md`. The separate code-review agent failed to start
  (provider usage limit); a distinct in-session adversarial diff review
  found the concurrency bug and produced RED/GREEN CI evidence. This is
  **not** represented as a successful second independent agent review.
- PR #3 merged at `c9fd52bb08b949501dd592d81d717691e1963028`; the
  remote `main` SHA matched, and post-merge run `45653341203` passed the
  PostgreSQL integration job and Python 3.11–3.14 matrix (5/5). Local
  PostgreSQL remains unavailable (KI-010).

## M0 gate: PASS (2026-11-21)

- Reproduced 65 passing tests in the existing environment.
- A new temporary Python 3.11 environment installed `.[dev]`; `pip check` and
  all 65 tests passed there.
- Built `experimentlift-0.1.0-py3-none-any.whl`, installed it into a second
  clean environment, and passed `pip check`, all 65 tests and the JSON CLI smoke.
- Verified authenticated GitHub account `bharathwajverse`, author-email
  attribution, the empty public target repository and default branch `main`.
- Configured local `main`, verified local author config and added the expected
  `origin`.
- Added SHA-pinned, read-only GitHub Actions CI that installs the built wheel in
  a fresh environment across Python 3.11–3.14.
- Independent M0 review found one high issue (editable install did not exercise
  the wheel); it was repaired before commit. The follow-up review found no
  critical/high blockers.
- Bootstrap commit `cba2539656e97e91a725f950ab6c770ea7333685` was pushed to
  remote `main`; local and remote SHAs matched.
- GitHub Actions run `44875593856` passed on that exact SHA. Python 3.11, 3.12,
  3.13 and 3.14 each built and installed the wheel, passed `pip check`, import,
  compile, all 65 tests, and JSON/Markdown CLI smokes.
- KI-009 and KI-011 are closed by remote history and clean cross-version CI
  evidence. Branch protection is not enabled (KI-022).
- PR CI annotations exposed deprecated Node.js 20 action runtimes (KI-023);
  action pins were upgraded to `checkout@v5` and `setup-python@v6`. PR run
  `44876024706` and post-merge run `44876111286` passed all four Python jobs
  with zero annotations.
- PR #1 was squash-merged as `472e80a553122f859c533049aa2e57940b8631d2`;
  local and remote `main` matched before this final evidence update.

## Phase 3 unblock prerequisites

1. Reachable PostgreSQL 16+ instance accepting connections on an approved
   disposable port. **Satisfied for M1 verification via the CI
   `postgres:16` service**; still unsatisfied *locally* (no Docker engine, no
   `psql`/`pg_ctl`/`initdb`/`postgres`, closed port 5432), so any Phase 3 E2E
   work must either run in CI or wait for a local server (KI-010).
2. Approval to add/install SQLAlchemy/Alembic/FastAPI/uvicorn/test
   dependencies. **Partially satisfied**: SQLAlchemy 2.0.58, Alembic 1.18.5,
   Mako 1.4.3, psycopg 3.3.9 and psycopg-binary 3.3.9 are installed and
   pinned for M1; FastAPI/uvicorn are not yet added. Transitive locking policy
   remains open (KI-020).
3. Then implement migrations, lifecycle rules, authentication and workspace
   authorization, with PostgreSQL-backed API and database E2E tests.
