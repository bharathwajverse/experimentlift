# Implementation plan

1. **Complete — Phase 0:** source verification and MVP boundary.
2. **Complete — Phase 1 design subset:** product, architecture, statistics,
   privacy and persistence/API plans.
3. **Complete — Phase 2:** pure Python synthetic vertical slice and tests.
4. **Next — Phase 3 (BLOCKED):** PostgreSQL/Alembic, FastAPI, authenticated
   workspace authorization, durable allocation/idempotency and versioned
   analysis records. Blocked on PostgreSQL availability: no Docker daemon, no
   `psql`/`pg_ctl`/`initdb`/`postgres` binary and no listener on 5432.
5. **Later:** AI provenance/review, EvidenceGuard UI, security hardening and
   external pilot.
