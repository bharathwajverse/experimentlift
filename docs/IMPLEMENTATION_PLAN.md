# Implementation plan

1. **Complete — Phase 0:** source verification and MVP boundary.
2. **Complete — Phase 1 design subset:** product, architecture, statistics,
   privacy and persistence/API plans.
3. **Complete — Phase 2:** pure Python synthetic vertical slice and tests.
4. **Pending PR merge/post-merge CI — M1:** PostgreSQL/Alembic schema, frozen
   migration, database integrity and concurrency tests passed against the
   PostgreSQL 16 CI service (run `45652442606`). Local Docker is unavailable;
   `main` acceptance still requires PR merge and post-merge CI evidence.
5. **Later — M2:** FastAPI, authentication and workspace authorization;
   durable application services require M1 PASS.
6. **Later:** AI provenance/review, EvidenceGuard UI, security hardening and
   external pilot.
