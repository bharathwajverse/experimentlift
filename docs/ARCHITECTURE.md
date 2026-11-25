# Architecture

Phase 2 is an importable Python modular core:

`models -> assignment -> event inputs -> analysis -> report/CLI`

The core has no HTTP, database, frontend or model-provider dependency.
M1 introduces a separate `experimentlift.db` SQLAlchemy/Psycopg boundary:
relational models and idempotent transaction helpers do not import the
statistical core. It is not an HTTP service or an authorization layer. PostgreSQL
16 CI is required to establish whether its migration and triggers work.
`AssignmentStore` preserves the first allocation only in memory. Analysis
consumes frozen Pydantic configuration with a SHA-256 configuration hash.

Planned system boundary:

`Next.js -> FastAPI application services -> repository ports -> PostgreSQL`

The existing statistical core remains independently testable and receives
immutable domain records rather than database sessions or HTTP objects.
SQLAlchemy/Alembic implement persistence without duplicating statistical logic.
Provider-neutral AI adapters can propose typed briefs and creative alternatives
but cannot alter assignments, events, computed statistics or verdicts.

Workspace authorization is enforced in backend service/repository boundaries.
Activated experiment revisions are immutable. Assignment and event idempotency
are transactional database constraints, not application-only checks. Analysis
results are versioned snapshots bound to configuration and source-data
provenance hashes.

See `MASTER_ROADMAP.md` for milestone boundaries, failure modes and gates.
