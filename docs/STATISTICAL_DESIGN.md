# Statistical design

## Estimand

The fixed-horizon ITT primary estimand is `p(treatment) - p(control)` for a
binary conversion. Every initially assigned participant remains in its arm;
exposure is a separately modelled future entity and never redefines the primary
denominator.

## Methods

- Primary effect: absolute risk difference. Relative lift is descriptive and
  `not estimable` when control conversion is zero.
- CI: two-sided Newcombe hybrid-score interval for two proportions
  (`statsmodels`, `method="newcomb"`), selected over a fragile Wald interval at
  boundaries. An unpooled Wald interval is also emitted as a diagnostic only;
  it is not used for decisions.
- Primary test: two-sided **score test** for equality of two proportions
  (`test_proportions_2indep`, `compare="diff"`, `method="score"`). This uses a
  null-constrained estimate; it is not an unpooled Wald test.
- Small-cell fallback: when any expected 2x2 cell is below five, two-sided
  Fisher exact test of equal odds is reported. The Newcombe risk-difference CI
  is retained and the differing null parameter is explicit.
- Planning: equal-allocation normal-approximation two-proportion calculation;
  planning is not achieved-power evidence.
- Exposure: when supplied, unique in-window exposure rates and their score or
  Fisher comparison are diagnostic only. They never replace assigned ITT
  denominators. A statistically detectable arm difference is warned as
  `differential_exposure`.

## Decision semantics

| Value | Meaning |
|---|---|
| `COMPLETE` | Window ended, no critical issue. |
| `PROVISIONAL` | Window not ended; no action. |
| `INVALID` | SRM or unresolved missing outcomes; causal claim blocked. |
| `win` | Complete/valid, p < alpha, CI lower bound exceeds predeclared practical threshold. |
| `loss` | Complete/valid and CI upper bound below zero. |
| `inconclusive` | Everything else, including provisional/invalid. |

Statistical and practical significance are distinct; neither alone creates a
win. No repeated unadjusted-peeking stop rule is implemented.

## Missingness/data quality

Assigned population is retained. By default, absent terminal outcome is
**unknown**, not a non-conversion; this forces `INVALID` and blocks a causal
recommendation. A future collection contract can opt into absent-is-zero only
when it establishes a complete closed window. SRM is chi-square goodness of fit
on assigned counts and is activated only at total `n >= 1,000`, using the
predeclared threshold p `<0.001`. Idempotency keys deduplicate identical
replays; reused keys with changed payloads and contradictory terminal outcomes
are rejected.

## Simulation diagnostics

Seeded Monte Carlo checks report positive actionable-win rate, total actionable
decision rate, Wilson Monte Carlo intervals for each, mean risk-difference bias and
Newcombe interval coverage. These are finite-run diagnostics, not proof of
nominal behavior for every parameter combination.
