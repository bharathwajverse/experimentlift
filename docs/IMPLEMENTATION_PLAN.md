# Implementation plan

1. **Complete — Phase 0:** source verification and MVP boundary.
2. **Complete — Phase 1 design subset:** product, architecture, statistics,
   privacy and persistence/API plans.
3. **Complete — Phase 2:** pure Python synthetic vertical slice and tests.
4. **Complete — M1:** PostgreSQL/Alembic schema, frozen migration, database
   integrity and concurrency tests passed against PostgreSQL 16 CI. PR #3
   merged at `c9fd52b`; post-merge run `45653341203` passed all five jobs.
   Local Docker remains unavailable.
5. **Later — M2:** FastAPI, authentication and workspace authorization;
   durable application services require M1 PASS.
6. **Later:** AI provenance/review, EvidenceGuard UI, security hardening and
   external pilot.
