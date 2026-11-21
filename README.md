# ExperimentLift

Evidence-first marketing experimentation. This repository currently contains
**Phase 0–2 only**: a local, synthetic-data Python vertical slice for a
fixed-horizon two-arm email-conversion experiment.

It does **not** send email, connect to marketing platforms, retain customer
data, call an AI provider, expose an API, provide authentication, or make
business claims from synthetic output.

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

Planned: persistence, FastAPI, workspace authorization, AI creative review,
frontend, email-provider integrations, and deployment.

See `docs/PROGRESS.md` for the authoritative status.
