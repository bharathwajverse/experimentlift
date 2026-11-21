# Known issues

Updated: 2026-11-21.

| ID | Severity | Reproduction / evidence | Consequence | State |
|---|---|---|---|---|
| KI-001 | High | Reverse allocation mapping order. | Assignment changed for equivalent allocation. | Resolved by canonical arm order; regression test passes |
| KI-002 | High | Analyze unequal arm sizes and inspect expected cells. | Fisher fallback selection could be wrong. | Resolved with row/column marginal formula and regression |
| KI-003 | High | Reuse an idempotency key with changed payload. | Conflict was silently discarded. | Resolved; changed payload now rejected |
| KI-004 | High | Analyze default missing outcomes. | Displayed conversion denominator differed from ITT effect. | Resolved; assigned denominator used consistently |
| KI-005 | Medium | Inspect report schema. | Wald diagnostic CI was absent. | Resolved in report v0.2 with independent reference test |
| KI-006 | Medium | Supply arm-asymmetric exposures. | Differential exposure was not diagnosed. | Resolved with optional diagnostic rates/test |
| KI-007 | Medium | Supply naive timestamps or out-of-window assignment. | Validation was incomplete. | Resolved with model/analysis validators |
| KI-008 | Medium | Review A/A operating-characteristic output. | Only positive wins and no Monte Carlo interval were reported. | Resolved with decision rate, Wilson intervals and coverage |
| KI-009 | Process | `git log` has no commits; all files are untracked. | No reviewable repository history or clean baseline exists. | Open; no commit requested |
| KI-010 | Blocker for Phase 3 | `docker version` cannot connect to Docker Desktop Linux engine; no `psql`/`pg_ctl`/`initdb`/`postgres` on PATH; `localhost:5432` refuses connections. | Disposable PostgreSQL integration/migration/E2E tests cannot currently run. | Open |
| KI-011 | Low | Install `.[dev]` into a new temporary Python 3.11 venv. | Local clean install now succeeds: `pip check` passes and 65 tests pass; cross-version Linux artifact installation remains unverified until CI runs. | Open; close only after remote CI passes |
| KI-012 | High | Supply NaN/infinite or mutate validated allocation. | SRM could fail open and frozen configuration could change. | Resolved with finite validation, immutable serializable allocation and regressions |
| KI-013 | High | Analyze records created for another experiment revision. | Foreign data could be attributed to the current configuration. | Resolved with required experiment/revision provenance and mismatch rejection |
| KI-014 | High | Supply pre-assignment or post-analysis outcomes/exposures/assignments. | Pre-treatment or unavailable future data could affect results. | Resolved with assignment-relative analysis cutoff enforcement |
| KI-015 | High | Compare sparse simulation decision with production. | Simulation used different correction/routing and overstated sparse wins. | Resolved by sharing production statistics helper; sparse Fisher regression passes |
| KI-016 | Medium | Render both critical issues and warnings or ignore an exposure. | Markdown could suppress warnings and ignored-exposure warning was absent. | Resolved with separate rendering and post-exposure warning calculation |
| KI-017 | High | Force the Newcombe interval computation to fail. | The analysis substituted a fabricated `(-1.0, 1.0)` decision interval. | Resolved; raises typed `StatisticUnavailableError` naming Newcombe (`tests/test_analysis.py::test_newcombe_failure_is_not_papered_over_with_fabricated_bounds`) |
| KI-018 | Medium | Supply exposure records outside the window or for an unassigned participant. | Ignored exposures were counted as ignored outcome events. | Resolved; separate `ignored_exposures` field and distinct `out_of_window_or_unassigned_exposures_ignored` warning |
| KI-019 | High | Analyze a configuration where one arm has zero assignments. | Report could claim `COMPLETE/VALID` with no estimate from that arm. | Resolved; critical `arm_without_assignments` issue forces `INVALID` |
| KI-020 | Low | Inspect package resolution inputs. | Direct dependencies are pinned, but transitive dependencies and `setuptools>=68` resolve online without hashes, so installs are compatible and repeatable by direct versions but not bit-for-bit locked. | Open; add reviewed cross-version constraints or lock policy |
| KI-021 | Process | Inspect public repository metadata and root files. | No project license is declared; public visibility does not grant reuse rights. | Open; repository owner must select a license |

## In-session adversarial review conclusions (2026-11-21)

Reviewed all eight source modules end to end:

| Module | Conclusion |
|---|---|
| `analysis.py` | KI-001–KI-008, KI-012–KI-019 findings above; all repaired with regressions |
| `models.py` | Frozen schemas, revision provenance, finite/immutable allocation; no additional defects |
| `report.py` | JSON round-trip and non-estimable Markdown covered by `tests/test_report.py`; no additional defects |
| `cli.py` | Synthetic-only scenario, fixed seed, no provider dependency; no additional defects |
| `power.py` | Planning-only normal approximation, documented as such; no additional defects |
| `simulation.py` | Reuses production `calculate_proportion_statistics`; parity regression passes; no additional defects |
| `generator.py` | Seeded synthetic generation with explicit synthetic labels; no additional defects |
| `__init__.py` | Package docstring only; no defects |

Probes that were adjudicated as non-defects and dismissed:

- `nan` score-test path — unreachable; inputs route to Fisher instead.
- `total_assigned == 0` SRM guard — guarded; no fail-open.
- Degenerate Newcombe probes `(0,1,0,1)`, `(1,1000000,0,1000000)`, `(999999,1000000,1000000,1000000)` — all returned finite intervals.
- `(5,10,5,10)`, `(0,100,0,100)`, `(100,100,100,100)`, `(3,100,2,100)` — all finite, no spurious warnings.

Limitation: the delegated independent review process could not run (provider usage limit), so this in-session pass substitutes for it and is disclosed as such.
