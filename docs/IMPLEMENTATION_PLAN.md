# Implementation plan

1. **Complete — Phase 0:** source verification and MVP boundary.
2. **Complete — Phase 1 design subset:** product, architecture, statistics,
   privacy and persistence/API plans.
3. **Complete — Phase 2:** pure Python synthetic vertical slice and tests.
4. **In progress — M1:** PostgreSQL/Alembic schema, migrations, database
   integrity tests and CI service. Local Docker daemon unavailable; PostgreSQL
   CI and migration-history freezing remain required before acceptance.
5. **Later — M2:** FastAPI, authentication and workspace authorization;
   durable application services require M1 PASS.
6. **Later:** AI provenance/review, EvidenceGuard UI, security hardening and
   external pilot.
