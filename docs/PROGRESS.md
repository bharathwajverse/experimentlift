# Progress

## Current phase: M0 baseline delivery in progress; Phase 3 gated

Implemented: configuration validation, deterministic HMAC allocation with
in-process first-assignment persistence, terminal outcomes, dedupe,
fixed-horizon analysis, validity gates, reports, seeded simulation checks and
CLI.

The audit added canonical allocation, opaque assignment IDs, ITT-consistent
summaries, conflict rejection, timestamp/window validation, corrected
unequal-arm expected cells, independent statistical references, a Wald
diagnostic, exposure diagnostics and simulation uncertainty/coverage outputs.
The first adversarial pass then found and drove repairs for non-finite/mutable
allocation, experiment-revision provenance, observation causal ordering,
simulation/production method drift and incomplete warning rendering. The
follow-up in-session review of all eight source modules added repairs for the
fabricated Newcombe fallback, exposure records inflating ignored events, and
zero-assignment arms reporting `COMPLETE/VALID`.

Not implemented: database, FastAPI, authz, durable audit events, durable exposure
ingestion, creative storage, AI generation, frontend, Docker configuration, deployment,
production observability, deletion workflow, provider integrations or
real-world validation.

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
- Phase 3: **BLOCKED** — PostgreSQL absent (no daemon, no binaries, closed
  port 5432); Phase 3 implementation deliberately deferred.
- Open, disclosed limitations: KI-009 (no commit history), KI-010 (PostgreSQL),
  KI-011 (remote clean-install matrix), KI-020 (transitive lock policy), KI-021
  (project license), external Phase 0–2 review unavailable.

## M0 evidence in progress (2026-11-21)

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
  the wheel); it was repaired before commit. Remote push and CI remain pending,
  so KI-009 and KI-011 remain open.

## Phase 3 unblock prerequisites

1. Reachable PostgreSQL 16+ instance (Docker Desktop Linux engine or a local
   server install) accepting connections on an approved disposable port.
2. Approval to install SQLAlchemy/Alembic/FastAPI/uvicorn/test dependencies.
3. Then implement migrations, lifecycle rules, authentication and workspace
   authorization, with PostgreSQL-backed API and database E2E tests.
