# ExperimentLift

Evidence-first marketing experimentation. The runnable Phase 0–2 slice uses
local synthetic data for a fixed-horizon two-arm email-conversion experiment.
The repository also contains an M1 PostgreSQL 16 persistence foundation; no
application API or authenticated service is implemented.

It does **not** send email, connect to marketing platforms, retain customer
data, call an AI provider, expose an API, provide authentication, or make
business claims from synthetic output.

M1 provides a PostgreSQL schema, frozen initial migration and transaction
helpers, merged via PR #3. Its migration and integration tests passed against
an ephemeral PostgreSQL 16 service in post-merge CI; see
`docs/VERIFICATION_MATRIX.md` for exact run evidence. Run migration tests
only with an explicitly disposable PostgreSQL 16 database:
`alembic downgrade base` destroys M1 data.

## Install and run

Requires Python 3.11+ (the local environment uses 3.11.9).

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -e ".[dev]"
.\.venv\Scripts\python -m pytest -q
.\.venv\Scripts\python -m experimentlift.cli run --scenario ab_known_effect --format markdown
```

The CLI has a fixed seed and its output is explicitly synthetic. Read
`docs/STATISTICAL_DESIGN.md` before interpreting a result.

## Current scope

Implemented: typed frozen configuration, persisted-in-process deterministic
assignment, separately modelled events, idempotency-key deduplication, SRM and
missing-outcome gates, score/Fisher testing, Newcombe confidence intervals,
seeded simulation checks, reports, tests.

M1 adds 12 workspace-scoped persistence tables, integrity guards and
idempotent assignment/event helpers. Planned after M1 acceptance: FastAPI,
workspace authorization, AI creative review, frontend, email-provider
integrations, and deployment.

See `docs/PROGRESS.md` for the authoritative status.
