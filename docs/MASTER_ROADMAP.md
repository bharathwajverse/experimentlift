# ExperimentLift master roadmap

Updated: 2026-11-21. This is the one-time quarter plan. Update only affected
milestones and decisions as evidence changes.

## Delivery rules

- Phase status is one of `PASS`, `FAIL`, `BLOCKED` or `NOT TESTED`.
- A milestone exits only when its acceptance evidence exists on the remote
  default branch and required CI is green.
- Statistics remain independent from API, persistence, AI and presentation.
- PostgreSQL evidence requires PostgreSQL; SQLite is never substitute evidence.
- All demonstrations use synthetic data until separately approved.
- One implementer writes at a time. A reviewer inspects actual code and evidence.

## Milestone map

| Milestone | Objective | Dependencies | Likely surfaces | Exit and GitHub delivery |
|---|---|---|---|---|
| M0 | Establish a reproducible reviewed baseline | audited Phase 0–2 | `.github/`, package metadata, governance docs | remote `main` contains reviewed source; clean CI passes; KI-009/KI-011 close with evidence |
| M1 | Add a real PostgreSQL 16 schema and migrations | M0 PASS; approved dependency install | `db/`, Alembic, models, migration/integration tests | upgrade and supported rollback pass against PostgreSQL in CI; constraints demonstrated |
| M2 | Deliver durable, authorized experiment APIs | M1 PASS | FastAPI, repositories/services, auth, API/E2E tests | restart, concurrency, lifecycle, idempotency and cross-workspace denial tests pass |
| M3 | Add provider-neutral, review-gated AI assistance | M2 PASS | AI ports/adapters, brief/hypothesis schemas, provenance | deterministic demo adapter passes; human approval and failure isolation demonstrated |
| M4 | Deliver the accessible Next.js application shell | M2 PASS; API contract stable | frontend app, tokens, typed client, UI/E2E tests | core API workflows pass at defined viewports and accessibility findings are tracked |
| M5 | Deliver EvidenceGuard setup and reporting | M2 and M4 PASS | wizard, report history, charts, explanation layer | independent values match; invalid evidence cannot become actionable; synthetic labels pass |
| M6 | Verify security, reliability and measured performance | M2–M5 PASS | security checks, load/concurrency tests, query profiling | no critical finding open; budgets have measurements; recovery paths pass |
| M7 | Package and demonstrate the verified MVP | M6 PASS; deployment approval | deployment config, runbooks, README, demo script | release commit CI passes; approved deployment is reproducible; claims match evidence |

## M0 — Verified GitHub baseline

**Boundary:** preserve the current implementation, add CI/governance, establish
the first `main` commit and verify the exact remote SHA. No product behavior
changes.

**Contracts:** Python package metadata is authoritative; CI installs from
`pyproject.toml`, imports `experimentlift`, runs all tests and validates both CLI
formats. GitHub token permissions are read-only.

**Failure modes:** wrong remote, unassociated author identity, leaked artifact,
dependency unavailable on a supported Python, push authentication failure,
workflow failure or local/remote SHA mismatch.

**Security:** scan staged content, ignore credentials/caches/build output, pin
third-party actions to reviewed commit SHAs, never print credentials.

**Tests:** 65-test regression, compile, dependency check, package wheel, import
and JSON/Markdown CLI smoke tests on clean Linux runners.

**Acceptance/exit:** remote `main` contains the baseline; CI reports real
results; clean installation passes; remote SHA equals local SHA; KI-009 and
KI-011 close only after those facts are observed.

## M1 — PostgreSQL foundation

**Boundary:** SQLAlchemy 2 and Alembic only; workspace, experiment, revision,
variant, assignment, exposure, conversion-event, analysis-result and audit
tables. No HTTP API yet.

**Contracts:** UUID identifiers; UTC timestamps; workspace-scoped foreign keys;
immutable revision snapshots; unique participant assignment and event
idempotency; explicit analysis configuration/result JSON versions; append-only
audit events.

**Failure modes:** cross-workspace references, duplicate assignment/event races,
mutable activated revision, orphan records, unsafe downgrade, timezone loss.

**Security:** least-privilege CI database credentials, parameterized SQL, no
record payloads or secrets in migration logs.

**Tests:** PostgreSQL 16 service readiness, migration upgrade, supported
rollback/re-upgrade, FK/unique/check constraints, transaction rollback and
concurrent uniqueness.

**Acceptance/exit:** real PostgreSQL tests pass in CI for the tested commit.
Local PostgreSQL absence remains disclosed. Feature branch is reviewed and
merged without force push.

## M2 — Durable experimentation backend

**Boundary:** FastAPI modular monolith around the existing statistical core.
Add typed contracts, service/repository boundaries, lifecycle state machine,
transactional assignment, idempotent ingestion, versioned analyses, secure
workspace authentication and authorization.

**Contracts:** consistent API error envelope; authenticated workspace context;
state transition allow-list; immutable activated config; replay-safe event
keys; stored report/configuration hashes.

**Failure modes:** authorization bypass, race-driven reassignment, duplicate
conversion, stale revision write, partial transaction, report/config mismatch.

**Security:** password/token material outside records and logs; backend
authorization on every workspace resource; validated inputs; deliberate CORS
and CSRF/session design; rate limits before public exposure.

**Tests:** unit state-machine tests, PostgreSQL integration, authorization
negative paths, concurrent allocation, replay/conflict ingestion, restart
persistence and full synthetic API-to-database E2E.

**Acceptance/exit:** all stated persistence and denial behaviors are observed in
CI, and the existing statistical regression suite remains green.

## M3 — AI-assisted experimentation

**Boundary:** provider-neutral interface, structured brief/hypothesis/creative
schemas, bounded alternatives, provenance and explicit human approval. Provide
a deterministic local demo adapter; no paid provider call.

**Contracts:** typed request/response, provider/model/prompt/version provenance,
validation errors and approval records. AI output never writes analysis results.

**Failure modes:** malformed output, timeout, duplicate generation, prompt/data
leak, unapproved creative activation, AI explanation contradicting statistics.

**Security/tests:** minimize prompt data, redact logs, cap output and retries;
contract tests with deterministic mocks, malformed/timeout tests, approval and
transaction-isolation tests.

**Acceptance/exit:** traceability and approval are demonstrated; provider
failure cannot corrupt experiments; demo mode needs no paid service.

## M4 — Frontend foundation

**Boundary:** Next.js/TypeScript shell, design tokens, responsive navigation,
experiment list/detail and campaign workspace using actual typed APIs.

**Contracts:** generated or schema-checked API types; explicit loading, empty,
error and unauthorized states.

**Failure modes:** stale state, misleading optimistic UI, inaccessible controls,
layout overflow, client-only authorization assumptions.

**Security/tests:** no secrets in browser bundles; secure cookie/token approach;
component, accessibility and Playwright E2E tests at defined viewports.

**Acceptance/exit:** core workflows use real APIs, keyboard essentials work and
automated/manual accessibility findings are recorded.

## M5 — EvidenceGuard and reporting

**Boundary:** setup wizard, sample-size planning, integrity diagnostics,
absolute/relative lift and uncertainty, validity explanations and versioned
history. AI may explain only computed structured results.

**Contracts:** report schema versions and provenance hashes; chart values derive
from report fields; synthetic/real source label is mandatory.

**Failure modes:** denominator mismatch, clipped uncertainty, invalid actionable
win, stale report, ungrounded explanation.

**Security/tests:** escaped report content and workspace authorization;
independent numeric references, invalid/provisional/inconclusive UI E2E, chart
scale/label tests and reproducibility checks.

**Acceptance/exit:** rendered values match independent calculations and invalid
experiments cannot display actionable wins.

## M6 — Reliability and security

**Boundary:** audit and measured repair, not speculative scaling.

**Contracts/budgets:** establish representative data sizes before measurement;
record p50/p95 API latency, report generation time, query counts and initial
page-load budget with environment details.

**Failure modes:** dependency vulnerability, authorization regression,
connection exhaustion, slow query, memory growth, unhandled failure/retry storm.

**Tests/security:** dependency/SAST checks, threat review, concurrency and
transaction tests, query plans, bounded load tests, failure recovery and full
regression/E2E.

**Acceptance/exit:** no unresolved critical security finding; measured budgets
and limitations are published; only measured bottlenecks are optimized.

## M7 — Deployment and final demonstration

**Boundary:** reproducible packaging, environment validation, health/readiness,
approved synthetic deployment, portfolio README and demonstration script.

**Contracts:** documented environment schema, health vs readiness semantics,
version/build metadata and rollback procedure.

**Failure modes:** missing secret/config, migration race, false-ready instance,
non-reproducible build, synthetic output presented as real.

**Security/tests:** least-privilege runtime, secret manager/environment input,
container/dependency scan, deployment smoke and independent demo rehearsal.

**Acceptance/exit:** release SHA has green CI; deployment can be reproduced and
operated from docs; known issues and evidence limitations remain visible.
