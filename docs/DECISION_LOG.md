# Decision log

| Date | Decision | Rationale |
|---|---|---|
| 2026-11-20 | Use Python 3.11.9, `requires-python >=3.11`. | Installed environment supports selected libraries; a future container can pin 3.12+. |
| 2026-11-20 | Build only pure Python first. | Validate measurement before APIs/UI/models. |
| 2026-11-20 | Newcombe RD CI + score test; Fisher fallback. | Boundary-safe interval and explicit valid two-proportion test. |
| 2026-11-20 | Unknown default outcomes invalidate analysis. | Avoid silently converting telemetry absence into non-conversion. |
| 2026-11-20 | Persist first allocation in process. | Demonstrates no re-randomization; Phase 3 must make it transactional. |
| 2026-11-20 | Use 4,000/arm for the high-power simulation check. | The executed 2,000/arm scenario produced 0.848 actionable-win rate, so it could not honestly support a >0.95 acceptance criterion. |
| 2026-11-21 | Restore SRM to p < 0.001 only at total n >= 1,000. | Matches the approved product policy; avoids silently substituting the research article's stricter example threshold. |
| 2026-11-21 | Emit Wald RD CI as diagnostic, retain Newcombe for decisions. | Meets diagnostic traceability without using a boundary-fragile interval as the decision interval. |
| 2026-11-21 | Reject conflicting event identity or terminal outcomes. | Silent conflict resolution would make results input-order dependent and weaken auditability. |
| 2026-11-21 | Bind assignment, outcome and exposure records to experiment key and revision. | Prevents cross-revision collisions and foreign data from being attributed to a report configuration. |
| 2026-11-21 | Restrict observations to assignment time through `min(now, ends_at)`. | Preserves temporal causality and prevents future data from entering provisional analysis. |
| 2026-11-21 | Reuse production statistical routing in simulations. | Operating-characteristic claims must exercise the same score/Fisher policy and correction setting as production analysis. |
| 2026-11-21 | Raise `StatisticUnavailableError` instead of fabricating a Newcombe interval. | A made-up `(-1.0, 1.0)` interval could be read as decision evidence; an explicit failure is honest. |
| 2026-11-21 | Track `ignored_exposures` separately from `ignored_events`. | Exposure records are not outcome events; conflating them overstated ignored evidence and mislabelled warnings. |
| 2026-11-21 | Emit critical `arm_without_assignments` for a zero-assignment arm. | A report must not claim `COMPLETE/VALID` when one arm cannot be estimated. |
| 2026-11-21 | Phase 0–2 gate: **PASS** (14 PASS, 0 FAIL, 0 NOT TESTED among P02 rows). | Evidence: 65 collected tests passing, `compileall`, `pip check`, JSON/Markdown CLI smoke and reconciled matrix rows. Disclosed limitations: remote cross-version clean-install evidence and the unavailable external review. |
| 2026-11-21 | Do **not** start Phase 3 while PostgreSQL is unavailable. | Phase 3 acceptance requires real PostgreSQL migration, API and database E2E evidence; SQLite cannot substitute, so any Phase 3 code written now would be unverifiable and would break the evidence rules. |
| 2026-11-21 | Bootstrap the verified source directly to the empty remote `main`, then use feature branches. | The remote has no refs, so a PR cannot precede the initial commit; direct bootstrap is the narrow exception. |
| 2026-11-21 | Test clean installs on GitHub-hosted Linux for Python 3.11–3.14. | The package declares Python `>=3.11`; a fresh matrix exposes wheel and dependency compatibility rather than relying on the existing Windows venv. |
| 2026-11-21 | Pin GitHub Actions by full commit SHA with read-only contents permission. | Reduces workflow supply-chain and token-permission risk while retaining version comments for maintainability. |
| 2026-11-21 | M0 gate: **PASS** on bootstrap commit `cba2539656e97e91a725f950ab6c770ea7333685`. | Remote `main` matches the local SHA and Actions run `44875593856` passed artifact installs, 65 tests and CLI smokes on Python 3.11–3.14. KI-009 and KI-011 are closed. |
| 2026-11-21 | Keep M0 **PASS** after reviewed closeout PR #1 and the action-runtime upgrade. | PR run `44876024706` and post-merge run `44876111286` passed Python 3.11–3.14 with zero annotations; merge `472e80a553122f859c533049aa2e57940b8631d2` was verified on remote `main`. |
