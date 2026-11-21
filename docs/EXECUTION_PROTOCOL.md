# Execution and verification protocol

`AGENTS.md` is the reusable repository contract. For each request:

1. Build requirement IDs in `VERIFICATION_MATRIX.md`.
2. Capture the pre-change environment, Git state and relevant baseline checks.
3. Add tests that fail for missing or defective behavior.
4. Implement in dependency order.
5. Run focused, regression, integration and smoke checks as applicable.
6. Independently review formulas, security boundaries and test quality.
7. Mark each requirement PASS, FAIL, BLOCKED or NOT TESTED with concrete
   evidence.
8. Update progress and known issues before reporting.

Warnings are classified as informational, material or blocking. A command that
cannot run is BLOCKED, never PASS. Phase 3 database evidence requires a
disposable PostgreSQL instance and migration/API execution against it.
